"""B1b：重建固定候選的基本包、對照內容並準備測試版。

政策從控制端目前的登記／證據讀取，payload 始終 checkout 固定候選。兩者的提交分開記錄，
不把 workflow 的 GITHUB_SHA 冒充 payload 來源。試跑只輸出文字報告，安裝包留在 runner。
"""
import argparse
import base64
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import tomllib
import urllib.error
import urllib.request

import base_content_equivalence as equivalence

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ChouTa-chuan/MarkItDown-exe'
SOURCE = 'b17d51bc99f8402f16b99f98bbe3b3370530bc6c'
REVIEW = 'docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json'
RETENTION_DAYS = 30
# 只在 B1b 核准的公開期間開啟。完成一次公開後另開 PR 關回。
PUBLIC_UPLOAD_ENABLED = True
MAIN_REF = 'refs/heads/main'
DISCLOSURES = ('known-gaps.json', 'known-gaps.md', 'test-build-limitations.md')
NATIVE_SOURCE = '_internal/desktop_app/data/native/source.json'
REPORT_NAMES = {'CONTENT-EQUIVALENCE.json', 'BUILD-INFO.json', 'LICENSE-FILES.json', 'package-audit.json', 'plan.json', 'SHA256SUMS.txt',
                'README.md', *DISCLOSURES}
FLAGS = ('runtime_sbom_complete', 'runtime_sbom_disclosed', 'redistribution_approved', 'release_ready')
EXPECTED_FLAGS = dict(zip(FLAGS, (False, True, True, False)))


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4*1024**2,
            'Missing, linked or oversized JSON: '+str(path))
    return json.loads(path.read_text(encoding='utf-8'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')


def copy_verified(source, target):
    """副本要對原件重核，不可把已損壞的副本反過來當成 manifest 的真值。"""
    expected = (digest(source), Path(source).stat().st_size)
    shutil.copyfile(source, target)
    require((digest(target), Path(target).stat().st_size) == expected and digest(source) == expected[0],
            'Copied attachment fingerprint differs: '+Path(target).name)


def git_source(root):
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()


def policy(root=ROOT):
    import redistribution_gates as gates
    registry = gates.read_json(root/'packaging/redistribution/obligations.json')
    review = gates.read_json(root/REVIEW)
    require(registry['profiles']['base']['source_commit'] == SOURCE == review['selection']['source_commit'],
            'Test build source must remain the approved fixed candidate')
    result = gates.assess(review, registry, root=root)
    flags = {key:result[key] for key in FLAGS}
    require(flags == EXPECTED_FLAGS, 'Base test-build approval/limitations differ from the recorded policy')
    return dict(source_commit=git_source(root), registry_sha256=digest(root/'packaging/redistribution/obligations.json'),
                source_review=dict(path=REVIEW, sha256=digest(root/REVIEW)), flags=flags)


def api_get(path):
    """只讀本 repo 的 Actions metadata；不輸出 token、signed URL 或安裝包。"""
    token = os.environ.get('GITHUB_TOKEN')
    require(token, 'Actions metadata needs the read-only workflow token')
    url = 'https://api.github.com/repos/'+REPOSITORY+'/'+path
    for attempt in range(4):
        request = urllib.request.Request(url, headers={'Authorization':'Bearer '+token,
            'Accept':'application/vnd.github+json', 'X-GitHub-Api-Version':'2022-11-28'})
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            if attempt == 3 or exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError('Actions metadata request failed: HTTP '+str(exc.code)) from None
            time.sleep(min(int(exc.headers.get('Retry-After', 2*(attempt+1))), 30))
    raise RuntimeError('Actions metadata retries exhausted')


def select_inputs(run_id=None, *, api=api_get, now=None):
    """重用既有驗證流程的短期 OCR 輸入，不在 B1a 試跑上傳新的 executable／模型 artifact。

    來源是否合用仍由下載後的固定 Tesseract／四語 SHA 檢查；同名 artifact 不是信任依據。
    """
    now = now or datetime.now(timezone.utc)
    if run_id:
        require(re.fullmatch('[1-9][0-9]{0,19}', str(run_id)), 'Invalid OCR input run id')
        runs = [api('actions/runs/'+str(run_id))]
    else:
        runs = api('actions/workflows/windows-base-validation.yml/runs?status=success&per_page=30')['workflow_runs']
    for run in runs:
        if run['status'] != 'completed' or run['conclusion'] != 'success' or run['path'] != '.github/workflows/windows-base-validation.yml':
            continue
        artifacts = api(f'actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
        matches = [a for a in artifacts if a['name']=='windows-ocr-ci-inputs' and not a['expired']
                   and datetime.fromisoformat(a['expires_at'].replace('Z', '+00:00')) > now]
        if not matches:
            continue
        require(len(matches) == 1, 'Ambiguous OCR input artifact')
        artifact = matches[0]
        require(re.fullmatch(r'sha256:[0-9a-f]{64}', artifact.get('digest') or ''), 'Input artifact lacks an integrity digest')
        return dict(run_id=run['id'], producer_head=run['head_sha'], artifact_name=artifact['name'],
                    artifact_id=artifact['id'], artifact_digest=artifact['digest'], expires_at=artifact['expires_at'])
    raise ValueError('No unexpired validated OCR input artifact; first rerun Windows base validation, then retry B1a')


def check_publish_request(publish):
    require(type(publish) is bool, 'Invalid publish request')
    if publish:
        require(os.environ.get('GITHUB_REF') == MAIN_REF, 'Public upload requires refs/heads/main')
        require(PUBLIC_UPLOAD_ENABLED, 'Public package upload is disabled')


def make_plan(input_run=None, *, publish=False, baseline_run=None, retained_review=False, root=ROOT, api=api_get):
    check_publish_request(publish)
    require(not baseline_run or re.fullmatch('[1-9][0-9]{0,19}', str(baseline_run)), 'Invalid baseline run')
    require(not retained_review or (not baseline_run and datetime.now(timezone.utc) >= equivalence.DEADLINE),
            'Retained review is only available after the deadline and without a saved baseline')
    if publish:
        require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Public run cannot be rerun')
        require(input_run, 'Public upload requires the explicit fresh main validation run')
    current = policy(root)
    # 版本從固定 Git 樹讀取，不能從可能已推進的控制端版本推測。
    raw = subprocess.check_output(['git', 'show', SOURCE+':pyproject.toml'], cwd=root)
    version = tomllib.loads(raw.decode())['project']['version']
    inputs = select_inputs(input_run, api=api)
    if publish:
        require(inputs['producer_head'] == current['source_commit'], 'OCR inputs must come from validation of current main')
    return dict(baseline_run=int(baseline_run or equivalence.BASELINE_RUN), retained_review=retained_review,
                baseline_artifact=equivalence.SAVED_ARTIFACT if baseline_run else equivalence.BASELINE_ARTIFACT,
                check='base-test-build-plan', schema_version=1, candidate_source=SOURCE, source_version=version,
                retention_days=RETENTION_DAYS, publish_requested=publish,
                public_upload_enabled=PUBLIC_UPLOAD_ENABLED, publish_allowed=publish and PUBLIC_UPLOAD_ENABLED,
                approval_policy=current, ocr_inputs=inputs)


def validate_inputs(inputs, candidate, review):
    require(git_source(candidate) == SOURCE, 'Payload checkout differs from the fixed candidate')
    records = {r['path']:r['sha256'] for r in review['classification']['files']}
    mappings = {'candidate/tesseract.exe':'_internal/desktop_app/data/native/bin/tesseract.exe'}
    mappings.update({'models/'+name+'.traineddata':'_internal/desktop_app/data/native/tessdata/'+name+'.traineddata'
                     for name in ('chi_tra', 'eng', 'jpn', 'kor')})
    for incoming, bundled in mappings.items():
        path = inputs/incoming
        require(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
                and path.resolve().is_relative_to(inputs.resolve()), 'Unsafe or missing OCR input: '+incoming)
        require(digest(path) == records[bundled], 'OCR input bytes differ from the fixed candidate: '+incoming)
    receipt = load(inputs/'build-evidence.json')
    require(receipt['candidate']['sha256'] == records[mappings['candidate/tesseract.exe']]
            and receipt['source_contract_sha256'] == digest(candidate/'packaging/native/minimal-windows.json'),
            'OCR input build receipt differs from the fixed candidate')


def checked_file(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative
            and not relative.startswith('/') and all(p not in ('', '.', '..') for p in relative.split('/')),
            'Unsafe package relative path')
    path = root/relative
    require(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
            and path.resolve().is_relative_to(root.resolve()), 'Missing or linked package file: '+relative)
    return path


def validate_generated_receipt(bundle, inputs, candidate):
    """source.json 綁本次輸入 receipt，不應要求另一次 CI 的時間／路徑產生相同 hash。

    只對這個固定生成檔改用結構與本次原始 receipt SHA 比對；Tesseract、模型與原文仍驗舊候選 bytes。
    windows_executed=false 是該交叉建置輸入的原始語意，不代表本次 Windows 驗收未執行。
    """
    receipt = load(inputs/'build-evidence.json')
    expected = dict(kind='ci-rebuilt-windows-minimal', evidence_sha256=digest(inputs/'build-evidence.json'),
                    source_contract_sha256=digest(candidate/'packaging/native/minimal-windows.json'),
                    upstream_version='5.5.3', windows_executed=False, windows_utf8_manifest=receipt['windows_utf8_manifest'])
    actual = checked_file(bundle, NATIVE_SOURCE)
    require(load(actual)==expected, 'Generated native receipt is not bound to the actual verified inputs')
    return digest(actual)


def assemble(bundle, installer, product, reports, plan, review, *, candidate, comparison):
    """組裝後再由實際檔案重核，報告與產品嚴格分目錄；單元測試使用明標合成 fixture。"""
    require(not product.exists(), 'Use a fresh product directory')
    require(not product.resolve().is_relative_to(reports.resolve())
            and not reports.resolve().is_relative_to(product.resolve()), 'Product and report directories must be disjoint')
    require(review['selection']['source_commit'] == SOURCE == plan['candidate_source'], 'Package source differs')
    profile = load(checked_file(bundle, '_internal/desktop_app/data/build-profile.json'))
    require(profile['source_version'] == plan['source_version'], 'Bundle version differs from the fixed candidate')
    require(installer.is_file() and not installer.is_symlink()
            and installer.name == 'MarkItDownBase-Setup-'+plan['source_version']+'-windows-x64.exe', 'Unexpected installer')
    # 所有固定原生依賴都需相同，不能用同版本套件或另一份 DLL 偷換固定候選。
    for row in review['classification_input']['report']['native_files']:
        require(digest(checked_file(bundle, '_internal/'+row['file'])) == row['bundled_sha256'],
                'Bundled native bytes differ from the fixed candidate: '+row['file'])
    for row in review['classification']['files']:
        if row['category'] in ('pinned-model', 'project-native-payload'):
            if row['path']==NATIVE_SOURCE:
                # collect 另以 validate_generated_receipt 核對本次來源；此處僅例外這一個固定生成檔。
                checked_file(bundle, NATIVE_SOURCE)
                continue
            require(digest(checked_file(bundle, row['path'])) == row['sha256'], 'Bundled OCR payload differs: '+row['path'])
    # 套件原文的 hash 必須與固定候選相同；生成清單另以本次實際 bytes 列舉，不假稱逐位元重建。
    for package in review['packages']:
        for notice in package['notices']:
            require(digest(checked_file(bundle, notice['path'])) == notice['sha256'],
                    'Bundled original notice differs: '+notice['path'])
    license_root = bundle/'_internal/desktop_app/data/licenses'
    license_files = []
    for path in sorted(license_root.rglob('*')):
        require(not path.is_symlink(), 'Linked license path')
        if path.is_file():
            relative = path.relative_to(bundle).as_posix()
            checked_file(bundle, relative)
            license_files.append(dict(path=relative, sha256=digest(path), bytes=path.stat().st_size))
    require(license_files, 'Missing delivered license inventory')
    product.mkdir(parents=True)
    reports.mkdir(parents=True, exist_ok=True)
    copy_verified(installer, product/installer.name)
    licenses = dict(scope='All delivered license-directory files: original notices and supporting metadata, not a legal-completeness claim',files=license_files)
    write(product/'LICENSE-FILES.json', licenses)
    for name in DISCLOSURES:
        actual = checked_file(license_root, name)
        source = checked_file(candidate/'src/desktop_app/data/licenses', name)
        require(digest(actual) == digest(source), 'Disclosure differs from the fixed source: '+name)
        copy_verified(actual, product/name)
    info = dict(check='base-test-build',schema_version=1,candidate_source=SOURCE,
                workflow_source=plan['approval_policy']['source_commit'],source_version=plan['source_version'],
                approval_policy=plan['approval_policy'],retention_days=RETENTION_DAYS,
                installer=dict(file=installer.name,sha256=digest(installer),bytes=installer.stat().st_size),
                fixed_review_installer_sha256=review['candidate']['sha256'],
                byte_identical_installer_to_original=(digest(installer)==review['candidate']['sha256']),
                scope='Fixed application source and native/input/original-notice bytes verified; generated metadata and installer may have build differences',
                package_upload_allowed=plan['publish_allowed'],public_upload_enabled=PUBLIC_UPLOAD_ENABLED)
    write(product/'CONTENT-EQUIVALENCE.json', comparison)
    info['content_equivalence_sha256'] = digest(product/'CONTENT-EQUIVALENCE.json')
    info['content_equivalence_mode'] = comparison['mode']
    write(product/'BUILD-INFO.json', info)
    readme = checked_file(ROOT/'docs', 'base-test-build-download.md').read_text(encoding='utf-8')
    if comparison['mode'] == 'retained-review':
        readme += ('\n逐檔原始清單已到期。本次使用 repo 內保留的分類、原生檔、原文、模組雜湊及檔案數查驗。'
                   '這份依據無法確認所有路徑相等或所有檔案內容相同。\n')
    (product/'README.md').write_text(readme, encoding='utf-8', newline='\n')
    files = {p.name:digest(p) for p in sorted(product.iterdir()) if p.is_file()}
    (product/'SHA256SUMS.txt').write_text(''.join(h+'  '+name+'\n' for name,h in files.items()),encoding='utf-8')
    for name in REPORT_NAMES-{'plan.json', 'package-audit.json', 'README.md'}:
        copy_verified(product/name, reports/name)
    (reports/'README.md').write_text(
        '# 基本包測試版報告\n\n報告內的 SHA256SUMS.txt 對應產品目錄，包括 Setup 與產品 README。'
        '本報告歸檔有自己的 README，並另外提供組裝稽核及工作流程計畫。\n',
        encoding='utf-8', newline='\n')
    # 重讀輸出，證明複製後檔案及 manifest 不是只存在記憶體中的宣告。
    for name, expected in files.items():
        require(digest(checked_file(product, name)) == expected, 'Staged product fingerprint differs')
    audit = dict(check='base-test-build-audit',schema_version=1,accepted=True,candidate_source=SOURCE,
                 package_files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in sorted(product.iterdir())},
                 license_files=len(license_files),report_only=not plan['publish_allowed'],
                 package_upload_allowed=plan['publish_allowed'],retention_days=RETENTION_DAYS)
    write(reports/'package-audit.json', audit)
    for path in reports.iterdir():
        require(path.name in REPORT_NAMES and path.is_file() and not path.is_symlink(), 'Unexpected report attachment')
        require(path.suffix.lower() in ('.json', '.txt', '.md'), 'Report must not contain executable or package bytes')
    return audit


def collect(plan_path, inputs, candidate, build, product, reports, *, baseline=None, baseline_copy=None, root=ROOT):
    require(sys.platform == 'win32' and os.environ.get('GITHUB_ACTIONS')=='true', 'Real test-build collection requires hosted Windows')
    plan = load(plan_path)
    require(plan['check']=='base-test-build-plan' and plan['approval_policy']==policy(root), 'Approval policy changed during build')
    check_publish_request(plan['publish_requested'])
    require(plan['publish_allowed'] is plan['publish_requested'], 'Publish plan is inconsistent')
    review = load(root/REVIEW)
    validate_inputs(inputs,candidate,review)
    build_report = load(build/'reports/windows-build.json')
    for field in ('build_verified','validation_accepted','installer_accepted','provenance_accepted','qt_replacement_accepted','overall_accepted'):
        require(build_report.get(field) is True, 'Windows build/installer validation incomplete: '+field)
    provenance = load(build/'reports/bundle-provenance.json')
    # 固定候選的舊 provenance 以 GITHUB_SHA 記 workflow 提交，並非 payload 的 Git HEAD。
    # 保留此原始語意；payload 已由 validate_inputs 的獨立 Git checkout 檢查綁定。
    require(provenance['source_commit']==plan['approval_policy']['source_commit']
            and build_report['commit']==plan['approval_policy']['source_commit'],
            'Build/provenance workflow source differs from the controller checkout')
    require(provenance.get('accepted') is True and provenance.get('profile')=='base'
            and provenance.get('source_version')==plan['source_version'], 'Invalid built provenance result')
    installer = build/'installer-work/setup'/('MarkItDownBase-Setup-'+plan['source_version']+'-windows-x64.exe')
    lifecycle = load(build/'reports/installer/installer-lifecycle.json')
    acceptance = load(build/'reports/acceptance/windows-acceptance.json')
    require(lifecycle.get('accepted') is True and lifecycle.get('windows_executed') is True
            and lifecycle.get('source_version')==plan['source_version']
            and lifecycle.get('installer_sha256')==digest(installer)
            and all(lifecycle.get(k) is True for k in ('install_verified','repair_verified','uninstall_verified')),
            'Actual tested installer differs from staged installer or lifecycle incomplete')
    require(acceptance.get('accepted') is True and acceptance.get('windows_executed') is True,
            'Actual Windows application acceptance incomplete')
    receipt_sha = validate_generated_receipt(build/'dist/MarkItDownBase',inputs,candidate)
    bundle = build/'dist/MarkItDownBase'
    original = None
    if not plan['retained_review']:
        origin, original = equivalence.provenance_input(baseline, review, SOURCE)
        if not plan['publish_requested'] and baseline_copy is not None:
            baseline_copy.parent.mkdir(parents=True, exist_ok=True)
            copy_verified(origin, baseline_copy)
    comparison = equivalence.compare(bundle, provenance, review, original, baseline_run=plan['baseline_run'])
    audit = assemble(bundle,installer,product,reports,plan,review,candidate=candidate,comparison=comparison)
    staged = checked_file(product, installer.name)
    require(digest(staged) == lifecycle['installer_sha256'], 'Staged Setup does not match accepted lifecycle SHA-256')
    audit['lifecycle_installer_sha256'] = lifecycle['installer_sha256']
    audit['windows_executed'] = True
    audit['hosted_runner'] = True
    audit['clean_machine_accepted'] = False
    audit['gpu_executed'] = False
    audit['generated_native_source_sha256'] = receipt_sha
    audit['native_build_evidence_sha256'] = digest(inputs/'build-evidence.json')
    audit['application_checks_passed'] = acceptance['checks_passed']
    audit['lifecycle'] = {k:lifecycle[k] for k in ('install_verified','repair_verified','uninstall_verified')}
    audit['environment'] = {k:build_report.get(k) for k in ('runner_os','image_version','platform')}
    audit['windows_build_report_sha256'] = digest(build/'reports/windows-build.json')
    audit['installer_validation_sha256'] = digest(build/'reports/installer/installer-lifecycle.json')
    write(reports/'package-audit.json',audit)
    return audit



def authorize_upload(plan_path, build, product, reports, *, root=ROOT):
    """只在上傳前重新核對本輪證據與實際 Setup，避免只依賴 plan 的輸出。"""
    plan = load(plan_path)
    require(plan['publish_requested'] is True and plan['publish_allowed'] is True, 'Missing publish intent')
    check_publish_request(True)
    require(os.environ.get('GITHUB_RUN_ATTEMPT') == '1', 'Public run cannot be rerun')
    require(plan['approval_policy'] == policy(root), 'Approval policy changed before upload')
    info = load(checked_file(product, 'BUILD-INFO.json'))
    comparison = checked_file(product, 'CONTENT-EQUIVALENCE.json')
    result = load(comparison)
    require(result['accepted'] is True and result['candidate_source'] == SOURCE
            and result['mode'] == ('retained-review' if plan['retained_review'] else 'full-inventory')
            and result['full_path_set_verified'] is (not plan['retained_review'])
            and digest(comparison) == info['content_equivalence_sha256']
            and digest(checked_file(reports, comparison.name)) == info['content_equivalence_sha256'],
            'Accepted content comparison is missing or changed')
    audit = load(checked_file(reports, 'package-audit.json'))
    lifecycle_path = build/'reports/installer/installer-lifecycle.json'
    lifecycle = load(lifecycle_path)
    require(audit['accepted'] is True and audit['installer_validation_sha256'] == digest(lifecycle_path)
            and lifecycle['accepted'] is True, 'Accepted installer lifecycle evidence is missing or changed')
    require(audit['package_files'] == {p.name: dict(sha256=digest(checked_file(product,p.name)), bytes=p.stat().st_size)
                                      for p in product.iterdir()}, 'Staged product files differ from accepted audit')
    installer = checked_file(product, info['installer']['file'])
    require(lifecycle['installer_sha256'] == info['installer']['sha256'] == digest(installer),
            'Upload Setup does not match accepted lifecycle SHA-256')

def public_parts(reports):
    """只發布預定的文字報告；不把 installer bytes 或任意目錄打包成註記。"""
    files = {}
    for path in sorted(reports.iterdir()):
        require(path.name in REPORT_NAMES and path.is_file() and not path.is_symlink(), 'Unsafe public report file')
        require(path.stat().st_size <= 256*1024, 'Oversized report attachment')
        # bytes 解碼保留 Windows 原始 CRLF；read_text 的換行正規化會使重組後 SHA 不同。
        files[path.name] = path.read_bytes().decode('utf-8')
    raw = json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',', ':')).encode()
    require(len(raw) <= 512*1024, 'Report metadata too large')
    data = base64.b64encode(gzip.compress(raw,mtime=0)).decode()
    require(len(data) <= 32*2800, 'Report annotation budget exceeded')
    parts = [data[i:i+2800] for i in range(0,len(data),2800)]
    return [dict(check='base-test-build-report-part',schema_version=1,sha256=hashlib.sha256(raw).hexdigest(),
                 encoding='gzip+base64',part=i+1,parts=len(parts),data=part) for i,part in enumerate(parts)]


def verify_report_artifact(reports, downloaded):
    """由 runner 下載剛上傳的報告重核，驗證實際 artifact 而非只驗待上傳目錄。"""
    for directory in (reports, downloaded):
        paths=list(directory.iterdir())
        require({p.name for p in paths}==REPORT_NAMES
                and all(p.is_file() and not p.is_symlink() for p in paths),
                'Downloaded report artifact has missing, extra, linked or nested content')
    files={}
    for name in sorted(REPORT_NAMES):
        expected=checked_file(reports,name)
        actual=checked_file(downloaded,name)
        fingerprint=dict(sha256=digest(actual),bytes=actual.stat().st_size)
        require(fingerprint==dict(sha256=digest(expected),bytes=expected.stat().st_size),
                'Downloaded report artifact bytes differ: '+name)
        files[name]=fingerprint
    return dict(check='base-test-build-artifact-roundtrip',accepted=True,files=files,installer_present=False)


def decode_parts(parts):
    """只接受完整、有界且同一 fingerprint 的報告分片，不接受軟體 bytes 或任意附件。"""
    import io
    require(parts and len(parts) <= 32, 'Missing or excessive report parts')
    first = parts[0]
    require(type(first.get('parts')) is int and first['parts'] == len(parts), 'Incomplete report parts')
    keys = {'check', 'schema_version', 'sha256', 'encoding', 'part', 'parts', 'data'}
    require(all(isinstance(p, dict) and set(p) == keys and type(p['part']) is int
                and p['check']=='base-test-build-report-part' and p['schema_version']==1
                and p['encoding']=='gzip+base64' and p['sha256']==first['sha256']
                and p['parts']==len(parts) and isinstance(p['data'], str) and len(p['data'])<=2800 for p in parts),
            'Invalid report part identity')
    require({p['part'] for p in parts} == set(range(1,len(parts)+1)), 'Duplicate or out-of-range report part')
    data = ''.join(p['data'] for p in sorted(parts,key=lambda p:p['part']))
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(data,validate=True))) as stream:
        raw = stream.read(512*1024+1)
    require(len(raw)<=512*1024 and hashlib.sha256(raw).hexdigest()==first['sha256'], 'Report metadata fingerprint differs')
    files = json.loads(raw)
    require(set(files)==REPORT_NAMES and all(isinstance(v,str) for v in files.values()), 'Unexpected or missing report attachment')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',action='store_true')
    mode.add_argument('--verify-inputs',action='store_true')
    mode.add_argument('--collect',action='store_true')
    mode.add_argument('--authorize-upload',action='store_true')
    mode.add_argument('--verify-report-artifact',action='store_true')
    mode.add_argument('--publish-page',type=int,choices=range(4))
    parser.add_argument('--ocr-input-run')
    parser.add_argument('--baseline-run')
    parser.add_argument('--baseline',type=Path)
    parser.add_argument('--baseline-copy',type=Path)
    parser.add_argument('--retained-review',choices=('true','false'),default='false')
    parser.add_argument('--publish',choices=('true','false'),default='false')
    parser.add_argument('--plan-file',type=Path,required=True)
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--build',type=Path)
    parser.add_argument('--product',type=Path)
    parser.add_argument('--reports',type=Path)
    parser.add_argument('--downloaded',type=Path)
    args = parser.parse_args()
    if args.plan:
        require(not args.plan_file.exists(), 'Plan output must be new')
        plan = make_plan(args.ocr_input_run,publish=args.publish=='true',baseline_run=args.baseline_run,
                         retained_review=args.retained_review=='true')
        args.plan_file.parent.mkdir(parents=True,exist_ok=True)
        write(args.plan_file,plan)
        if os.environ.get('GITHUB_OUTPUT'):
            with Path(os.environ['GITHUB_OUTPUT']).open('a',encoding='utf-8') as stream:
                for key,value in dict(candidate_source=SOURCE,source_version=plan['source_version'],
                      inputs_run=plan['ocr_inputs']['run_id'],inputs_name=plan['ocr_inputs']['artifact_name'],
                      baseline_run=plan['baseline_run'], baseline_artifact=plan['baseline_artifact'],
                      retained_review=str(plan['retained_review']).lower(),
                      publish_allowed=str(plan['publish_allowed']).lower()).items():
                    stream.write(key+'='+str(value)+'\n')
    elif args.authorize_upload:
        authorize_upload(args.plan_file,args.build,args.product,args.reports)
    elif args.verify_inputs:
        validate_inputs(args.inputs,args.candidate,load(ROOT/REVIEW))
    elif args.verify_report_artifact:
        result=verify_report_artifact(args.reports,args.downloaded)
        print('::notice title=B1a actual artifact roundtrip::'+json.dumps(result,separators=(',', ':')))
    elif args.publish_page is not None:
        for part in public_parts(args.reports)[args.publish_page*8:(args.publish_page+1)*8]:
            print('::notice title=B1b report metadata::'+json.dumps(part,separators=(',', ':')).replace('%','%25'))
    else:
        collect(args.plan_file,args.inputs,args.candidate,args.build,args.product,args.reports,
                baseline=args.baseline,baseline_copy=args.baseline_copy)
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        # artifact／完整日誌不可讀時仍保留本流程的有界錯誤，不輸出環境變數或產品內容。
        if os.environ.get('GITHUB_ACTIONS')=='true':
            detail=(type(exc).__name__+': '+str(exc))[:600]
            detail=detail.replace('%','%25').replace('\r','%0D').replace('\n','%0A')
            print('::error title=B1b collection failure::'+detail,flush=True)
        raise

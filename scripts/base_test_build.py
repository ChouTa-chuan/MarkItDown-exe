"""B1a：固定候選的測試版組裝與報告；公開上傳留待 planner 複查後的 B1b。

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

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'ChouTa-chuan/MarkItDown-exe'
SOURCE = 'b17d51bc99f8402f16b99f98bbe3b3370530bc6c'
REVIEW = 'docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json'
RETENTION_DAYS = 30
# 這是使用者指定的階段界線：B1b 必須待 Claude planner 複查，不以 dispatch 勾選取代。
PUBLIC_UPLOAD_ENABLED = False
DISCLOSURES = ('known-gaps.json', 'known-gaps.md', 'test-build-limitations.md')
REPORT_NAMES = {'BUILD-INFO.json', 'LICENSE-FILES.json', 'package-audit.json', 'plan.json', 'SHA256SUMS.txt',
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
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


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


def make_plan(input_run=None, *, publish=False, root=ROOT, api=api_get):
    require(type(publish) is bool and (not publish or PUBLIC_UPLOAD_ENABLED),
            'Public package upload remains disabled until the separate B1b planner review')
    current = policy(root)
    # 版本從固定 Git 樹讀取，不能從可能已推進的控制端版本推測。
    raw = subprocess.check_output(['git', 'show', SOURCE+':pyproject.toml'], cwd=root)
    version = tomllib.loads(raw.decode())['project']['version']
    return dict(check='base-test-build-plan', schema_version=1, candidate_source=SOURCE, source_version=version,
                retention_days=RETENTION_DAYS, publish_requested=publish,
                public_upload_enabled=PUBLIC_UPLOAD_ENABLED, publish_allowed=publish and PUBLIC_UPLOAD_ENABLED,
                approval_policy=current, ocr_inputs=select_inputs(input_run, api=api))


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


def assemble(bundle, installer, product, reports, plan, review, *, candidate):
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
    write(product/'BUILD-INFO.json', info)
    (product/'README.md').write_text('# MarkItDown 基本包測試版\n\n來源提交：'+SOURCE+'\n\n版本：'+plan['source_version']+'\n\n安裝包 SHA-256 與目前政策見 BUILD-INFO.json；實際授權目錄清單見 LICENSE-FILES.json。\n限制見 test-build-limitations.md；已知缺口見 known-gaps.json／known-gaps.md。\n',encoding='utf-8')
    files = {p.name:digest(p) for p in sorted(product.iterdir()) if p.is_file()}
    (product/'SHA256SUMS.txt').write_text(''.join(h+'  '+name+'\n' for name,h in files.items()),encoding='utf-8')
    for name in REPORT_NAMES-{'plan.json', 'package-audit.json', 'README.md'}:
        copy_verified(product/name, reports/name)
    (reports/'README.md').write_text('# B1a 試跑報告\n\n此 artifact 只有報告，不含安裝包。安裝包仍只留在可拋棄 runner；planner 複查後才另行開始 B1b。\n',encoding='utf-8')
    # 重讀輸出，證明複製後檔案及 manifest 不是只存在記憶體中的宣告。
    for name, expected in files.items():
        require(digest(checked_file(product, name)) == expected, 'Staged product fingerprint differs')
    audit = dict(check='base-test-build-audit',schema_version=1,accepted=True,candidate_source=SOURCE,
                 package_files={p.name:dict(sha256=digest(p),bytes=p.stat().st_size) for p in sorted(product.iterdir())},
                 license_files=len(license_files),installer_uploaded=False,report_only=not plan['publish_allowed'],
                 package_upload_allowed=plan['publish_allowed'],retention_days=RETENTION_DAYS)
    write(reports/'package-audit.json', audit)
    for path in reports.iterdir():
        require(path.name in REPORT_NAMES and path.is_file() and not path.is_symlink(), 'Unexpected report attachment')
        require(path.suffix.lower() in ('.json', '.txt', '.md'), 'Report must not contain executable or package bytes')
    return audit


def collect(plan_path, inputs, candidate, build, product, reports, *, root=ROOT):
    require(sys.platform == 'win32' and os.environ.get('GITHUB_ACTIONS')=='true', 'Real test-build collection requires hosted Windows')
    plan = load(plan_path)
    require(plan['check']=='base-test-build-plan' and plan['approval_policy']==policy(root), 'Approval policy changed during build')
    require(not plan['publish_requested'] or PUBLIC_UPLOAD_ENABLED, 'B1b public upload is not enabled')
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
    installer = build/'installer-work/setup'/('MarkItDownBase-Setup-'+plan['source_version']+'-windows-x64.exe')
    audit = assemble(build/'dist/MarkItDownBase',installer,product,reports,plan,review,candidate=candidate)
    audit['windows_executed'] = True
    audit['windows_build_report_sha256'] = digest(build/'reports/windows-build.json')
    audit['installer_validation_sha256'] = digest(build/'reports/installer/installer-lifecycle.json')
    write(reports/'package-audit.json',audit)
    return audit


def public_parts(reports):
    """只發布預定的文字報告；不把 installer bytes 或任意目錄打包成註記。"""
    files = {}
    for path in sorted(reports.iterdir()):
        require(path.name in REPORT_NAMES and path.is_file() and not path.is_symlink(), 'Unsafe public report file')
        require(path.stat().st_size <= 256*1024, 'Oversized report attachment')
        files[path.name] = path.read_text(encoding='utf-8')
    raw = json.dumps(files,ensure_ascii=False,sort_keys=True,separators=(',', ':')).encode()
    require(len(raw) <= 512*1024, 'Report metadata too large')
    data = base64.b64encode(gzip.compress(raw,mtime=0)).decode()
    require(len(data) <= 32*2800, 'Report annotation budget exceeded')
    parts = [data[i:i+2800] for i in range(0,len(data),2800)]
    return [dict(check='base-test-build-report-part',schema_version=1,sha256=hashlib.sha256(raw).hexdigest(),
                 encoding='gzip+base64',part=i+1,parts=len(parts),data=part) for i,part in enumerate(parts)]


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
    mode.add_argument('--publish-page',type=int,choices=range(4))
    parser.add_argument('--ocr-input-run')
    parser.add_argument('--publish',choices=('true','false'),default='false')
    parser.add_argument('--plan-file',type=Path,required=True)
    parser.add_argument('--inputs',type=Path)
    parser.add_argument('--candidate',type=Path)
    parser.add_argument('--build',type=Path)
    parser.add_argument('--product',type=Path)
    parser.add_argument('--reports',type=Path)
    args = parser.parse_args()
    if args.plan:
        require(not args.plan_file.exists(), 'Plan output must be new')
        plan = make_plan(args.ocr_input_run,publish=args.publish=='true')
        args.plan_file.parent.mkdir(parents=True,exist_ok=True)
        write(args.plan_file,plan)
        if os.environ.get('GITHUB_OUTPUT'):
            with Path(os.environ['GITHUB_OUTPUT']).open('a',encoding='utf-8') as stream:
                for key,value in dict(candidate_source=SOURCE,source_version=plan['source_version'],
                      inputs_run=plan['ocr_inputs']['run_id'],inputs_name=plan['ocr_inputs']['artifact_name'],
                      publish_allowed=str(plan['publish_allowed']).lower()).items():
                    stream.write(key+'='+str(value)+'\n')
    elif args.verify_inputs:
        validate_inputs(args.inputs,args.candidate,load(ROOT/REVIEW))
    elif args.publish_page is not None:
        for part in public_parts(args.reports)[args.publish_page*8:(args.publish_page+1)*8]:
            print('::notice title=B1a report metadata::'+json.dumps(part,separators=(',', ':')).replace('%','%25'))
    else:
        collect(args.plan_file,args.inputs,args.candidate,args.build,args.product,args.reports)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

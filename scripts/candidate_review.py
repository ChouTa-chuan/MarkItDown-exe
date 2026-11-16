"""固定候選的來源重分類與審閱資料；只發布有限 JSON metadata，不發布產品。

完整候選由既有 audit 重驗。本模組保存可重跑分類的精簡輸入、所有待審檔案及
原生／套件來源摘要；工程證據完整與權利／再散布核准分開，所有發行旗標維持 false。
"""
import argparse
import base64
import collections
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
from email.parser import BytesParser

import classify_unresolved_sources as classifier
from build_provenance import sha256
from candidate_inventory import verify_inventory, component_inventory

ROOT = Path(__file__).resolve().parents[1]
MAX_JSON = 4*1024*1024
MAX_ENCODED = 96_000
PART_SIZE = 2900


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')


def read_json(path):
    if not path.is_file() or path.is_symlink() or path.stat().st_size > MAX_JSON:
        raise ValueError('Missing, linked or oversized review input: '+str(path))
    return json.loads(path.read_text(encoding='utf-8'))


def check_source(repo, expected):
    """要求明確完整 SHA、實際 HEAD 與乾淨的追蹤檔，避免 branch 名稱漂移或暫存改動。"""
    if not re.fullmatch('[0-9a-f]{40}', expected):
        raise ValueError('Candidate source must be a full immutable commit')
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True, timeout=30).strip()
    if git('rev-parse', 'HEAD') != expected or git('status', '--porcelain'):
        raise ValueError('Candidate source differs from clean checked-out HEAD')
    fixed = os.environ.get('MARKITDOWN_CANDIDATE_SOURCE', '')
    if fixed and (fixed != expected or os.environ.get('GITHUB_EVENT_NAME') != 'workflow_dispatch'):
        raise ValueError('Fixed candidate requires workflow_dispatch at the selected source')
    return dict(source_commit=expected, explicitly_pinned=bool(fixed),
                event=os.environ.get('GITHUB_EVENT_NAME', 'local-review'),
                ref=os.environ.get('GITHUB_REF'), run_id=os.environ.get('GITHUB_RUN_ID'),
                run_attempt=os.environ.get('GITHUB_RUN_ATTEMPT'))


def report_indexes(directory):
    """只索引 CI 自身 JSON 報告；不把整個 bundle 複製後當作來源已確認的證據。"""
    members, payload, inputs = {}, {}, []
    for path in sorted(directory.rglob('*.json')):
        relative = path.relative_to(directory).as_posix()
        if relative.startswith('source-review'):
            continue
        if path.is_symlink() or path.stat().st_size > MAX_JSON:
            raise ValueError('Unsafe review report: '+relative)
        raw = path.read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        inputs.append(dict(path=relative, bytes=len(raw), sha256=digest))
        if relative != 'bundle-provenance.json':
            members.setdefault(digest, relative)
        if relative in classifier.NATIVE_PAYLOADS:
            for name, row in json.loads(raw).get('files', {}).items():
                payload[row['sha256']] = relative+'#'+name
    return members, payload, inputs


def package_context(bundle, packages, inventory_files):
    """從已由 audit 綁 hash 的實際 METADATA 取來源入口，原文仍以包內檔案指紋追溯。"""
    rows = []
    files = {r['path']:r for r in inventory_files}
    for p in packages:
        if (p['metadata_path'] not in files
                or files[p['metadata_path']]['sha256'] != p['metadata_sha256']):
            raise ValueError('Package metadata is outside the verified candidate inventory')
        path = bundle/p['metadata_path']
        if sha256(path) != p['metadata_sha256']:
            raise ValueError('Package metadata changed before review')
        metadata = BytesParser().parsebytes(path.read_bytes())
        rows.append(dict(name=p['name'], version=p['version'], metadata_sha256=p['metadata_sha256'],
                         project_urls=metadata.get_all('Project-URL', []), homepage=metadata.get('Home-page'),
                         declared_license_expression=p.get('declared_license_expression'),
                         declared_license_sha256=hashlib.sha256(str(p.get('declared_license', '')).encode()).hexdigest(),
                         notices=p['notices']))
    return rows


def package_identity(profile, directory, report):
    """只計算候選檔案指紋，不複製、上傳或替換 installer／worker。"""
    if profile == 'base':
        path = directory/f'MarkItDownBase-Setup-{report["source_version"]}-windows-x64.exe'
        expected = None
    else:
        path = directory/'onnx-cpu-ocr-development.zip'
        expected = report['package_inventory']['archive_sha256']
    if not path.is_file() or path.is_symlink():
        raise ValueError('Candidate package missing or linked')
    digest = sha256(path)
    if expected and digest != expected:
        raise ValueError('Candidate CPU archive changed')
    identity = dict(file=path.name, bytes=path.stat().st_size, sha256=digest)
    if profile == 'cpu':
        current = component_inventory(directory, report['candidate_inventory'])
        if current['archive_sha256'] != expected:
            raise ValueError('CPU package descriptor or payload changed')
        identity.update(descriptor_sha256=current['descriptor_sha256'],
                        component_id=current['component_id'], component_version=current['component_version'])
    return identity


def make_review(profile, bundle, reports, package, expected, repo=ROOT):
    """重驗同一候選快照後分類；精簡輸入可在 Linux 以同一 Git commit 重跑。"""
    selection = check_source(repo, expected)
    path = reports/'bundle-provenance.json'
    report = read_json(path)
    version = tomllib.loads((repo/'pyproject.toml').read_text(encoding='utf-8'))['project']['version']
    if (report.get('profile') != profile or report.get('source_commit') != expected
            or report.get('source_version') != version or report.get('accepted') is not True
            or report.get('host_platform') != 'win32' or report.get('inventory_reverified') is not True):
        raise ValueError('Provenance is not the accepted Windows report for the selected source')
    for flag in ('redistribution_approved', 'release_ready'):
        if report.get(flag) is not False:
            raise ValueError('Candidate review cannot grant product approval')
    if any(report['candidate_inventory']['summary'].get(f) is not False
           for f in ('runtime_sbom_complete', 'redistribution_approved', 'release_ready')):
        raise ValueError('Candidate inventory cannot pre-approve product gates')
    verify_inventory(bundle, report['candidate_inventory'])
    identity = package_identity(profile, package, report)
    if profile == 'base':
        installer = read_json(reports/'installer/installer-lifecycle.json')
        if not installer.get('accepted') or installer.get('installer_sha256') != identity['sha256']:
            raise ValueError('Base installer does not match accepted installer evidence')
    members, payload, inputs = report_indexes(reports)
    if profile == 'base' and (reports/'acceptance/build-profile.json').exists():
        report['python_version'] = read_json(reports/'acceptance/build-profile.json').get('python')
    # 保留所有待審列（不只未對照），其餘已對照實體檔案留原完整報告及 hash。
    pending = [r for r in report['candidate_inventory']['files'] if r['review_reasons']]
    reduced = {k:report[k] for k in ('profile', 'source_commit', 'source_version', 'native_files')}
    reduced.update(packages=[dict(name=p['name'], version=p['version']) for p in report['packages']],
                   python_version=report.get('python_version'),
                   cpython_components=report.get('cpython_components'),
                   python_archives=dict(base_library=report['python_archives']['base_library']),
                   candidate_inventory=dict(files=pending, summary=report['candidate_inventory']['summary']))
    model_manifest = json.loads(classifier.git_file(repo, expected, classifier.MODEL_MANIFEST))
    models = {digest:name for name, digest in model_manifest['files'].items()}
    rows = classifier.classify(reduced, classifier.git_blob_index(repo, expected), members, models, payload)
    declared = report['candidate_inventory']['summary']['unresolved_files']
    if len(rows) != declared or len({r['path'] for r in rows}) != len(rows):
        raise ValueError('Source classification does not cover exactly the declared unresolved files')
    reasons = collections.Counter(reason for r in pending for reason in r['review_reasons'])
    result = dict(check='candidate-source-review', schema_version=1, profile=profile, accepted=True,
                  selection=selection, candidate=identity, provenance_report_sha256=sha256(path),
                  inventory_sha256=hashlib.sha256(canonical(report['candidate_inventory'])).hexdigest(),
                  inventory_summary=report['candidate_inventory']['summary'],
                  classification=dict(unresolved_declared=declared, classified=len(rows),
                      by_category=dict(sorted(collections.Counter(r['category'] for r in rows).items())),
                      by_status=dict(sorted(collections.Counter(r['status'] for r in rows).items())), files=rows),
                  review_reasons=dict(sorted(reasons.items())),
                  packages=package_context(bundle, report['packages'], report['candidate_inventory']['files']),
                  python_archive_summary=report['python_archives']['summary'],
                  pure_modules_sha256=hashlib.sha256(canonical(report['python_archives']['pure_modules'])).hexdigest(),
                  classification_input=dict(report=reduced, members=members, payload=payload),
                  report_inputs=inputs, runtime_sbom_complete=False, redistribution_approved=False,
                  release_ready=False, complete_candidate_inventory_embedded=False,
                  scope='Source classification and review metadata; accepted is evidence consistency, not legal approval')
    # 一般外部原文／vendor 閉包與人工義務不能由計數或套件宣告自動認證。
    result['remaining_review'] = [
        'All pending review_reasons and origin-known/candidate/gap rows require individual assessment',
        'Wheel-embedded native third-party source/license closure is not certified by wheel ownership',
        'Qt build patches/settings and replacement verification remain separate from release source mapping',
        'Microsoft redistribution terms and statically linked native notice coverage require final review',
        'CPU model/GEOS obligations, clean-machine/manual and GPU acceptance remain outside this report']
    return result


def replay(report, repo=ROOT):
    """只靠保存的精簡輸入與固定 Git 樹重跑；完整 inventory 未內嵌的限制仍保留。"""
    encoded_parts(report)
    inputs = report['classification_input']
    source = report['selection']['source_commit']
    if inputs['report']['source_commit'] != source:
        raise ValueError('Replay source differs from selected commit')
    model_manifest = json.loads(classifier.git_file(repo, source, classifier.MODEL_MANIFEST))
    models = {digest:name for name, digest in model_manifest['files'].items()}
    rows = classifier.classify(inputs['report'], classifier.git_blob_index(repo, source),
                               inputs['members'], models, inputs['payload'])
    c = report['classification']
    if (rows != c['files'] or len(rows) != c['unresolved_declared'] or len(rows) != c['classified']
            or dict(sorted(collections.Counter(r['status'] for r in rows).items())) != c['by_status']
            or dict(sorted(collections.Counter(r['category'] for r in rows).items())) != c['by_category']):
        raise ValueError('Replayed source classification differs from preserved evidence')
    return True


def encoded_parts(report):
    """以有界、可驗 hash 的 metadata 分片保存；不接受 installer／模型的原始位元組。"""
    if (report.get('check') != 'candidate-source-review' or report.get('schema_version') != 1
            or any(report.get(f) is not False for f in ('runtime_sbom_complete', 'redistribution_approved', 'release_ready'))):
        raise ValueError('Only unapproved source-review JSON metadata may be published')
    raw = canonical(report)
    if len(raw) > MAX_JSON:
        raise ValueError('Review JSON exceeds evidence limit')
    encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')
    if len(encoded) > MAX_ENCODED:
        raise ValueError('Review metadata exceeds annotation budget')
    total = (len(encoded)+PART_SIZE-1)//PART_SIZE
    digest = hashlib.sha256(raw).hexdigest()
    return [dict(check='candidate-review-part', schema_version=1, profile=report['profile'],
                 source_commit=report['selection']['source_commit'], sha256=digest,
                 part=i+1, parts=total, encoding='gzip+base64', data=encoded[i*PART_SIZE:(i+1)*PART_SIZE])
            for i in range(total)]


def decode_parts(parts):
    """離線重新組合必須完整、不重複且 source/profile/hash 一致；解壓也限制大小。"""
    if not parts or len(parts) > (MAX_ENCODED+PART_SIZE-1)//PART_SIZE:
        raise ValueError('Missing or excessive review parts')
    first = parts[0]
    keys = ('check', 'schema_version', 'profile', 'source_commit', 'sha256', 'parts', 'encoding')
    if (first.get('check') != 'candidate-review-part' or first.get('schema_version') != 1
            or first.get('encoding') != 'gzip+base64' or first.get('parts') != len(parts)
            or {p.get('part') for p in parts} != set(range(1, len(parts)+1))
            or any(any(p.get(k) != first.get(k) for k in keys) for p in parts)):
        raise ValueError('Inconsistent or incomplete review parts')
    encoded = ''.join(p['data'] for p in sorted(parts, key=lambda p:p['part']))
    if len(encoded) > MAX_ENCODED:
        raise ValueError('Review parts exceed limit')
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded, validate=True))) as stream:
        raw = stream.read(MAX_JSON+1)
    if len(raw) > MAX_JSON or hashlib.sha256(raw).hexdigest() != first['sha256']:
        raise ValueError('Review evidence size or hash mismatch')
    result = json.loads(raw)
    if (result.get('check') != 'candidate-source-review' or result['profile'] != first['profile']
            or result['selection']['source_commit'] != first['source_commit']):
        raise ValueError('Decoded review identity mismatch')
    encoded_parts(result)  # 重驗 schema 與不准產品核准的旗標。
    return result


def publish(report, page=0):
    if page not in range(5):
        raise ValueError('Review publication page outside bounded range')
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    # 每步最多八個 notice，總分片加既有摘要仍低於 job annotation 上限。
    for p in encoded_parts(report)[page*8:(page+1)*8]:
        message = json.dumps(p, separators=(',', ':'))
        if len(message.encode()) > 3800:
            raise ValueError('Review annotation exceeds public limit')
        print('::notice title=Candidate review metadata::'+message)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--expected-source')
    parser.add_argument('--repo', type=Path, default=ROOT)
    parser.add_argument('--publish', type=Path, help='分頁發布已保存的 metadata，不建立新候選')
    parser.add_argument('--page', type=int, default=0)
    parser.add_argument('--replay', type=Path, help='只讀保存的 source-review JSON 及其固定 Git 樹重跑分類')
    parser.add_argument('--check-source', action='store_true')
    parser.add_argument('--profile', choices=('base', 'cpu'))
    parser.add_argument('--bundle', type=Path)
    parser.add_argument('--reports', type=Path)
    parser.add_argument('--package-directory', type=Path)
    args = parser.parse_args()
    if args.replay:
        replay(read_json(args.replay), args.repo)
        print('Preserved source classification replayed without changing evidence')
        return 0
    if not args.expected_source:
        parser.error('Expected source is required for a new review')
    if args.publish:
        check_source(args.repo, args.expected_source)
        report = read_json(args.publish)
        if report['selection']['source_commit'] != args.expected_source:
            raise ValueError('Publication source differs from selected commit')
        publish(report, args.page)
        return 0
    if args.check_source:
        print(json.dumps(check_source(args.repo, args.expected_source)))
        return 0
    if not all((args.profile, args.bundle, args.reports, args.package_directory)):
        parser.error('Review requires profile, bundle, reports and package directory')
    output = args.reports/'source-review.json'
    if output.exists():
        parser.error('Source review output already exists')
    report = make_review(args.profile, args.bundle, args.reports, args.package_directory, args.expected_source, args.repo)
    output.write_bytes(canonical(report)+b'\n')
    print(json.dumps({k:report[k] for k in ('check', 'profile', 'selection', 'candidate', 'inventory_summary',
                                           'review_reasons', 'runtime_sbom_complete', 'redistribution_approved')}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

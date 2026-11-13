"""把候選報告中「來源未對照」的檔案依可重驗的證據分類；不判定授權、不改報告旗標。

責任與限制：
- 輸入是已保存的 CI artifact ZIP（內含 bundle-provenance.json）與同一 source commit 的 Git 樹。
  只讀取兩者，不需要 Windows、也不重新建置；輸出另存新檔，不覆寫原報告。
- 每個檔案只接受下列證據，依強度由上而下取第一個成立者：
  1. 位元組與 source commit 的某個 Git blob 相同（列出 repo 路徑）；零位元組檔案另列，不當來源證據。
  2. 位元組與同一次 CI artifact 的成員相同。
  3. SHA-256 與 repo 內固定模型清單相同。
  4. SHA-256 與同次 CI 的 native payload 清單相同（專案由固定原始碼建置的原生檔）。
  5. 報告的 Analysis 原生來源標記（來源檔與收集後雜湊相同）：建置用 CPython 或系統路徑。
  6. 安裝工具在安裝時產生的 dist-info/RECORD（由目錄名對回報告的套件表）。
  7. 專案建置腳本產生的 manifest 等（依固定路徑表；內容每次建置不同，無法逐位元對照）。
- 名稱推測不當作已確認擁有者：系統路徑來的 DLL 即使檔名像 Microsoft／OpenSSL，
  也只列為 candidate，註明需在 Windows 上驗簽章／版本資源。
- status 的意思：confirmed＝來源由雜湊或同次建置清單證明；origin-known＝知道從哪個安裝位置
  收集，但上游版本／再散布條款尚未逐檔核對；candidate＝僅名稱與收集位置；gap＝沒有證據。
  任何 status 都不代表再散布已核准。
"""
import argparse
import collections
import hashlib
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path, PurePosixPath

UNRESOLVED = 'source-owner-unresolved'
MODEL_MANIFEST = 'src/desktop_app/data/ocr-four-languages.json'
NATIVE_PAYLOADS = ('acceptance/native-payload.json',)
# 專案建置腳本的固定輸出路徑（去掉 _internal/ 前綴後比對）→ 產生它的腳本。
GENERATED = {
    'desktop_app/data/licenses/bootloader/manifest.json': 'scripts/build_provenance.py',
    'desktop_app/data/licenses/installed/manifest.json': 'scripts/prepare_base_assets.py',
    'desktop_app/data/licenses/native/manifest.json': 'scripts/prepare_base_assets.py',
    'desktop_app/data/native/source.json': 'scripts/prepare_bundled_ocr.py',
    'desktop_app/data/native/manifest.json': 'scripts/prepare_bundled_ocr.py',
    'desktop_app/data/third-party.md': 'scripts/prepare_base_assets.py',
    'desktop_app/data/build-profile.json': 'scripts/prepare_base_assets.py',
    'worker-assets/bootloader/manifest.json': 'scripts/build_provenance.py',
    'worker-assets/installed-manifest.json': 'scripts/prepare_worker_assets.py',
    'worker-assets/native/manifest.json': 'scripts/prepare_worker_assets.py',
}
PYTHON_LICENSE = ('desktop_app/data/licenses/python-runtime/LICENSE.txt', 'worker-assets/python-runtime/LICENSE.txt')
# 僅用來替 system-native 檔案標示「候選」發行者，不構成已確認擁有者。
NAME_CANDIDATES = (
    (re.compile(r'^(api-ms-win-.*|ucrtbase|msvcp140.*|vcruntime140.*|concrt140|vccorlib140)\.dll$', re.I),
     'Microsoft Universal CRT／Visual C++ runtime'),
    (re.compile(r'^lib(crypto|ssl)-3(-x64)?\.dll$', re.I), 'OpenSSL 3'),
)


def canonical(name):
    return re.sub('[-_.]+', '-', name).lower()


def git_blob_index(repo, commit):
    """回傳 {sha256: [repo 路徑…]}；以 cat-file --batch 讀 blob，不 checkout、不改工作區。"""
    listing = subprocess.run(['git', '-C', str(repo), 'ls-tree', '-r', '-z', commit],
                             capture_output=True, check=True).stdout
    entries = []
    for line in listing.split(b'\0'):
        if line:
            meta, path = line.split(b'\t', 1)
            mode, kind, oid = meta.split()
            if kind == b'blob':
                entries.append((oid, path.decode('utf-8', 'surrogateescape')))
    index = collections.defaultdict(list)
    process = subprocess.Popen(['git', '-C', str(repo), 'cat-file', '--batch'],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    try:
        for oid, path in entries:
            process.stdin.write(oid + b'\n')
            process.stdin.flush()
            header = process.stdout.readline().split()
            if len(header) != 3 or header[1] != b'blob':
                raise ValueError('Unexpected git object for ' + path)
            data = process.stdout.read(int(header[2]))
            process.stdout.read(1)
            index[hashlib.sha256(data).hexdigest()].append(path)
    finally:
        process.stdin.close()
        process.stdout.close()
        process.wait()
    return index


def git_file(repo, commit, path):
    return subprocess.run(['git', '-C', str(repo), 'show', f'{commit}:{path}'],
                          capture_output=True, check=True).stdout


def inner(path):
    """bundle 內路徑去掉 PyInstaller 的 _internal/ 前綴，與 Analysis 清單同一命名。"""
    return path[len('_internal/'):] if path.startswith('_internal/') else path


def closest(path, candidates):
    """同雜湊的多個 repo 路徑中，優先列出結尾路徑段最相近、且不在歷史證據目錄下的來源。"""
    target = PurePosixPath(path).parts[::-1]
    def shared(candidate):
        parts = PurePosixPath(candidate).parts[::-1]
        return next((index for index, (a, b) in enumerate(zip(target, parts)) if a != b), min(len(target), len(parts)))
    return sorted(candidates, key=lambda candidate: (-shared(candidate), candidate.startswith('docs/'), candidate))


def classify(report, blobs, members, models, payload):
    """回傳逐檔分類列。report 為 bundle-provenance.json 內容；其餘為各證據索引。"""
    native = {item['file']: item for item in report['native_files']}
    packages = {canonical(item['name']): item['version'] for item in report['packages']}
    python = report.get('python_version')
    rows = []
    for item in report['candidate_inventory']['files']:
        if UNRESOLVED not in (item.get('review_reasons') or []):
            continue
        path, digest, name = item['path'], item['sha256'], PurePosixPath(item['path']).name
        relative, source = inner(path), native.get(inner(path))
        row = dict(path=path, bytes=item['bytes'], sha256=digest, role=item['role'])
        if item['bytes'] == 0:
            # 空檔的雜湊與任何空檔相同，不能當成來源證據；單獨列出、不指向特定 repo 路徑。
            row.update(category='empty-file', status='confirmed', evidence=[],
                       note='零位元組檔案，沒有可授權的內容；不以雜湊相同推定來源')
        elif digest in blobs:
            row.update(category='repo-blob', status='confirmed', evidence=closest(path, blobs[digest])[:5],
                       note='與 source commit 的 repo 檔案位元組相同')
        elif digest in members:
            row.update(category='ci-artifact-member', status='confirmed', evidence=[members[digest]],
                       note='與同次 CI artifact 成員位元組相同（當次建置產生）')
        elif digest in models:
            row.update(category='pinned-model', status='confirmed', evidence=[MODEL_MANIFEST + '#' + models[digest]],
                       note='與固定模型清單的 SHA-256 相同')
        elif digest in payload:
            row.update(category='project-native-payload', status='confirmed', evidence=[payload[digest]],
                       note='與同次 CI 的 native payload 清單相同；由固定原始碼在 CI 建置')
        elif source and source['origin'] == 'python-runtime':
            unchanged = source['source_sha256'] == source['bundled_sha256'] == digest
            row.update(category='cpython-runtime', status='origin-known' if unchanged else 'gap',
                       evidence=['native_files:' + source['file']],
                       note='自建置用 CPython 安裝目錄收集，來源與收集後雜湊相同；'
                            '其中可能含 CPython 隨附的第三方元件，逐檔上游與條款待核對')
        elif source and source['origin'] == 'system-native':
            candidate = next((label for pattern, label in NAME_CANDIDATES if pattern.match(name)), None)
            row.update(category='system-native', status='candidate' if candidate else 'gap',
                       evidence=['native_files:' + source['file']],
                       note=('自建置機系統路徑收集；檔名推測為 ' + candidate + '，簽章／版本資源未驗') if candidate
                       else '自建置機系統路徑收集，發行者未知')
        elif name == 'RECORD' and PurePosixPath(path).parent.name.endswith('.dist-info'):
            folder = PurePosixPath(path).parent.name[:-len('.dist-info')]
            package, _, version = folder.rpartition('-')
            known = packages.get(canonical(package)) == version
            row.update(category='installer-generated-record', status='confirmed' if known else 'gap',
                       evidence=[f'packages:{canonical(package)}=={version}'] if known else [],
                       note='安裝工具於安裝時產生的檔案清單，RECORD 不記錄自身雜湊；套件版號與報告套件表相符'
                       if known else 'dist-info 目錄無法對回報告套件表')
        elif relative in GENERATED:
            row.update(category='project-generated', status='origin-known', evidence=[GENERATED[relative]],
                       note='專案建置腳本的固定輸出路徑；內容隨建置產生，未逐位元對照')
        elif relative in PYTHON_LICENSE:
            row.update(category='cpython-license-text', status='origin-known',
                       evidence=['scripts/prepare_base_assets.py', 'scripts/prepare_worker_assets.py'],
                       note='建置用 CPython 的 LICENSE.txt 複本' + (f'（建置 Python {python}）' if python else '')
                            + '；尚未與 python.org 同版原文獨立比對')
        elif item['role'] == 'archive':
            row.update(category='archive-members-not-enumerated', status='gap', evidence=[],
                       note='PyInstaller 產生的 Python 標準庫封存，成員未展開；需另做成員層級 SBOM')
        else:
            row.update(category='unknown', status='gap', evidence=[], note='沒有可用證據')
        rows.append(row)
    return rows


def load(archive_path, repo):
    """讀 artifact 與 Git，組成 classify() 需要的索引。"""
    with zipfile.ZipFile(archive_path) as archive:
        raw = archive.read('bundle-provenance.json')
        report = json.loads(raw)
        members, payload = {}, {}
        for name in archive.namelist():
            if name.endswith('/') or name == 'bundle-provenance.json':
                continue
            body = archive.read(name)
            members.setdefault(hashlib.sha256(body).hexdigest(), name)
            if name in NATIVE_PAYLOADS:
                for file, entry in json.loads(body).get('files', {}).items():
                    payload[entry['sha256']] = f'{name}#{file}'
            if name.endswith('acceptance/build-profile.json') and 'python_version' not in report:
                report['python_version'] = json.loads(body).get('python')
    commit = report['source_commit']
    blobs = git_blob_index(repo, commit)
    manifest = json.loads(git_file(repo, commit, MODEL_MANIFEST))
    models = {digest: name for name, digest in manifest['files'].items()}
    return raw, report, blobs, members, models, payload


def summarize(profile, archive_path, raw, report, rows):
    declared = report['candidate_inventory']['summary']['unresolved_files']
    by_category, by_status = collections.Counter(), collections.Counter()
    for row in rows:
        by_category[row['category']] += 1
        by_status[row['status']] += 1
    return dict(
        check='unresolved-source-classification', schema_version=1, profile=profile,
        source_commit=report['source_commit'], source_version=report['source_version'],
        archive=Path(archive_path).name, archive_sha256=hashlib.sha256(Path(archive_path).read_bytes()).hexdigest(),
        report_sha256=hashlib.sha256(raw).hexdigest(),
        unresolved_declared=declared, classified=len(rows),
        # 分類數必須等於報告自述的未對照數；不符即不接受，避免遺漏或重複。
        accepted=len(rows) == declared,
        by_status=dict(sorted(by_status.items())), by_category=dict(sorted(by_category.items())),
        remaining_gap_or_candidate=by_status['gap'] + by_status['candidate'],
        runtime_sbom_complete=False, redistribution_approved=False, release_ready=False,
        files=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--profile', required=True, choices=('base', 'cpu'))
    parser.add_argument('--archive', required=True, type=Path, help='保存的 CI artifact ZIP')
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', required=True, type=Path, help='新的 JSON 輸出；已存在則拒絕')
    arguments = parser.parse_args()
    if arguments.output.exists():
        parser.error('Output already exists; classification evidence is never overwritten')
    raw, report, blobs, members, models, payload = load(arguments.archive, arguments.repo)
    if report['profile'] != arguments.profile:
        parser.error('Report profile does not match --profile')
    result = summarize(arguments.profile, arguments.archive, raw, report,
                       classify(report, blobs, members, models, payload))
    arguments.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('profile', 'accepted', 'unresolved_declared', 'classified',
                                                    'by_status', 'by_category')}, ensure_ascii=False))
    return 0 if result['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

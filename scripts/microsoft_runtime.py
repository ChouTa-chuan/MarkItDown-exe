"""A10：唯讀探測 Microsoft 執行期複本，並把目錄綁到 A6；不作再散布核准。

Windows 探測只讀已建置 bundle、原來源及 Visual Studio 的官方 Redist；不替換 DLL，
不以同名、版本相同或簽章有效推論位元組相同，更不把 hash 相同當作授權。
公開註記僅含有界的 JSON metadata；原始 DLL 不得上傳。條款另存開發證據，不進產品。
"""
import argparse
import base64
import gzip
import hashlib
import importlib.metadata
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys

from bundle_filters import find_vc_redist
from candidate_review import canonical, check_source
from native_identity import describe

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = 'packaging/microsoft/base-windows.json'
BASIS_PATH = 'docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json'
MAX_BYTES = 256 * 1024
MAX_ENCODED = 8 * 2900
FLAGS = ('runtime_sbom_complete', 'redistribution_approved', 'release_ready')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def official_name(name):
    """改名只移除這兩個已登記複本的 hash 後綴，不猜測任意 DLL 的身分。"""
    if re.fullmatch(r'(numpy|pandas)\.libs/msvcp140-[0-9a-f]{32}\.dll', name):
        return 'msvcp140.dll'
    return PurePosixPath(name).name.lower()


def targets(root=ROOT):
    registry = json.loads((root/'packaging/redistribution/obligations.json').read_text(encoding='utf-8'))
    return next(e['native_files'] for e in registry['profiles']['base']['entries'] if e['id'] == 'base-microsoft')


def probe(bundle, review, *, root=ROOT, redist=None, identity=describe):
    """逐檔核對 provenance 後才讀身分；A6 不同的位元組明記，不沿用其身分資料。"""
    require(sys.platform == 'win32', 'Microsoft runtime probe requires Windows')
    require(review.get('profile') == 'base' and review.get('accepted') is True, 'Not an accepted base source-review')
    names = targets(root)
    current = {r['file']: r for r in review['classification_input']['report']['native_files']}
    basis = json.loads((root/BASIS_PATH).read_text(encoding='utf-8'))
    historical = {r['file']: r for r in basis['classification_input']['report']['native_files']}
    redist = Path(redist or find_vc_redist() or '')
    require(redist.is_dir() and redist.name.startswith('Microsoft.VC') and redist.name.endswith('.CRT'),
            'Official VS Redist directory missing')
    available = {p.name.lower(): p for p in redist.iterdir() if p.is_file()}
    files = {n: bundle/'_internal'/n for n in names}
    refs = {official_name(n): available.get(official_name(n)) for n in names}
    require(all(refs.values()), 'Official Redist same-name reference missing')
    sources = {}
    for name in names:
        row = current[name]
        if row['origin'] == 'installed-wheel':
            owners = row['distributions']
            require(len(owners) == 1, 'Ambiguous Microsoft wheel owner')
            distribution = importlib.metadata.distribution(owners[0]['name'])
            require(distribution.version == owners[0]['version'], 'Installed wheel version differs from provenance')
            sources[name] = Path(distribution.locate_file(name))
        else:
            sources[name] = Path(row['source_directory'])/PurePosixPath(name).name
        require(files[name].is_file() and not files[name].is_symlink(), 'Missing runtime: '+name)
        require(digest(files[name]) == row['bundled_sha256'] == row['source_sha256'] == digest(sources[name]),
                'Bundle or source differs from provenance: '+name)
    identities = identity(list(files.values()) + list(refs.values()))
    references = {name: dict(path=str(path), sha256=digest(path), identity=identities[path]) for name, path in refs.items()}
    rows = []
    for name in names:
        row = current[name]
        original = official_name(name)
        actual = digest(files[name])
        rows.append(dict(file=name, sha256=actual, bytes=files[name].stat().st_size,
                         a6_sha256=historical[name]['bundled_sha256'], matches_a6=actual == historical[name]['bundled_sha256'],
                         origin=row['origin'], distributions=row['distributions'], source_path=str(sources[name]),
                         source_sha256=digest(sources[name]), identity=identities[files[name]],
                         renamed=PurePosixPath(name).name.lower() != original,
                         official_name=original, official_sha256=references[original]['sha256'],
                         matches_official=actual == references[original]['sha256']))
    return dict(check='microsoft-runtime-probe', schema_version=1, profile='base',
                selection=review['selection'], basis=dict(path=BASIS_PATH, sha256=digest(root/BASIS_PATH),
                                                        source_commit=basis['selection']['source_commit']),
                runner=dict(os=os.environ.get('RUNNER_OS'), image_version=os.environ.get('ImageVersion')),
                official_redist_directory=str(redist), references=references, files=rows,
                **{f: False for f in FLAGS})


def validate_probe(report):
    require(report.get('check') == 'microsoft-runtime-probe' and report.get('schema_version') == 1
            and report.get('profile') == 'base' and all(report.get(f) is False for f in FLAGS), 'Invalid Microsoft probe')
    require(re.fullmatch('[0-9a-f]{40}', report.get('selection', {}).get('source_commit', '')),
            'Missing immutable probe source')
    require(len(report.get('files', [])) == 14 and len({r['file'] for r in report['files']}) == 14,
            'Probe must contain exactly fourteen separate files')
    for row in report['files']:
        require(row['official_name'] == official_name(row['file']), 'Wrong official filename')
        ref = report['references'][row['official_name']]
        require(row['official_sha256'] == ref['sha256'] and type(row['matches_official']) is bool
                and row['matches_official'] == (row['sha256'] == ref['sha256']), 'Inconsistent official comparison')
        require(row['source_sha256'] == row['sha256'], 'Source bytes differ from bundle')
        require(type(row['matches_a6']) is bool and row['matches_a6'] == (row['sha256'] == row['a6_sha256']),
                'Inconsistent A6 comparison')
        require(type(row['renamed']) is bool
                and row['renamed'] == (PurePosixPath(row['file']).name.lower() != row['official_name']), 'Wrong rename marker')


def encoded_parts(report):
    """上限八片，避免占滿既有 source-review 註記額度；超限即拒絕，不截斷。"""
    validate_probe(report)
    raw = canonical(report)
    require(len(raw) <= MAX_BYTES, 'Microsoft metadata too large')
    encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')
    require(len(encoded) <= MAX_ENCODED, 'Microsoft annotation budget exceeded')
    parts = (len(encoded)+2899)//2900
    return [dict(check='microsoft-runtime-part', schema_version=1, sha256=hashlib.sha256(raw).hexdigest(),
                 source_commit=report['selection']['source_commit'], part=i+1, parts=parts,
                 data=encoded[i*2900:(i+1)*2900]) for i in range(parts)]


def decode_parts(parts):
    require(parts and len(parts) <= 8, 'Missing or excessive Microsoft parts')
    first = parts[0]
    require(first.get('check') == 'microsoft-runtime-part' and first.get('schema_version') == 1
            and first.get('parts') == len(parts) and {p.get('part') for p in parts} == set(range(1,len(parts)+1))
            and all(all(p.get(k) == first.get(k) for k in ('check','schema_version','sha256','source_commit','parts'))
                    for p in parts), 'Incomplete or inconsistent Microsoft parts')
    text = ''.join(p['data'] for p in sorted(parts, key=lambda p:p['part']))
    require(len(text) <= MAX_ENCODED, 'Microsoft encoded metadata too large')
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(text, validate=True))) as stream:
        raw = stream.read(MAX_BYTES+1)
    require(len(raw) <= MAX_BYTES and hashlib.sha256(raw).hexdigest() == first['sha256'], 'Microsoft metadata hash mismatch')
    result = json.loads(raw)
    require(result['selection']['source_commit'] == first['source_commit'], 'Microsoft source mismatch')
    validate_probe(result)
    return result


def check_catalog(catalog, *, report, entry, root=ROOT):
    """hash 綁定小型目錄及探測；查不到的身分不能宣告證據完整，法律決定永遠另列。"""
    import redistribution_gates as gates
    require(catalog.get('schema_version') == 1 and catalog.get('profile') == 'base'
            and catalog.get('registry_entry') == 'base-microsoft', 'Invalid Microsoft catalog')
    require(entry['requires_user_decision'], 'Microsoft needs A13 user decision')
    require(any(ref['path'] == CATALOG_PATH for ref in entry['evidence']), 'Registry does not reference Microsoft catalog')
    for ref in [catalog['basis'], catalog['probe'], *[d['snapshot'] for d in catalog['documents']]]:
        gates.reference({k:ref[k] for k in ('path','sha256')}, root)
    require(catalog['basis']['path'] == BASIS_PATH and catalog['source_commit'] == report['selection']['source_commit'],
            'Microsoft catalog source mismatch')
    observed = gates.read_json(root/catalog['probe']['path'])
    validate_probe(observed)
    require(observed['basis'] == {**catalog['basis'], 'source_commit':catalog['source_commit']}, 'Probe basis differs')
    names = entry['native_files']
    require(sorted(catalog['files']) == sorted(names) == sorted(r['file'] for r in observed['files']),
            'Microsoft native coverage differs')
    natives = {r['file']:r for r in report['classification_input']['report']['native_files']}
    gaps = []
    for row in observed['files']:
        require(row['a6_sha256'] == natives[row['file']]['bundled_sha256'], 'Microsoft A6 file hash differs')
        identity = row['identity']
        if (not row['matches_a6'] or identity.get('identity_error') or identity.get('company') != 'Microsoft Corporation'
                or not identity.get('file_version') or identity.get('signature_status') != 'Valid'
                or 'O=Microsoft Corporation' not in (identity.get('signer') or '')):
            gaps.append(row['file'])
    # 所有候選條款均只是供 A13 審閱；條款標題、版本與適用性仍需使用者逐項確認。
    require(catalog['documents'] and catalog['legal_approval'] is False, 'Missing terms or premature legal approval')
    if gaps:
        require(entry['status'] == 'open', 'Incomplete Microsoft identity must stay open')
    return dict(catalog=CATALOG_PATH, files=len(names), identity_gaps=gaps,
                renamed_files=[r['file'] for r in observed['files'] if r['renamed']],
                official_matches=sum(r['matches_official'] for r in observed['files']), legal_approval=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--bundle', required=True, type=Path)
    parser.add_argument('--source-review', required=True, type=Path)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    check_source(ROOT, args.expected_source)
    require(not args.output.exists(), 'Probe output must be new')
    review = json.loads(args.source_review.read_text(encoding='utf-8'))
    require(review['selection']['source_commit'] == args.expected_source, 'Review source mismatch')
    result = probe(args.bundle, review)
    parts = encoded_parts(result)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        for part in parts:
            print('::notice title=Microsoft runtime evidence::'+json.dumps(part, separators=(',', ':')))
    print(json.dumps(dict(check='microsoft-runtime-summary', files=len(result['files']),
                         matches_a6=sum(r['matches_a6'] for r in result['files']),
                         matches_official=sum(r['matches_official'] for r in result['files']),
                         metadata_sha256=hashlib.sha256(canonical(result)).hexdigest())))


if __name__ == '__main__':
    main()

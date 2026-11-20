"""在 Windows 讀 CPU 鎖定 wheel 的原生版本和簽章，僅輸出小型證據。"""
import argparse
import base64
import ctypes
import gzip
import hashlib
from importlib import import_module, metadata
import json
import os
from pathlib import Path
import re
import sys
import sysconfig

from candidate_review import canonical, check_source
from native_identity import describe

ROOT = Path(__file__).resolve().parents[1]
BASIS = 'docs/development-records/runs/a13b-fixed-review-2026-11-18/cpu-source-review.json'
MS_CATALOG = 'packaging/microsoft/cpu-windows.json'
MS_REFERENCE = 'docs/development-records/runs/a13b-fixed-review-2026-11-18/microsoft-probe-7cf098e.json'
APIS = {
    'pyyaml/libyaml': ('yaml._yaml.get_version_string', {'yaml/_yaml.cp312-win_amd64.pyd'}),
    'opencv-python/opencv': ('cv2.getVersionString', {'cv2/cv2.pyd'}),
}
CHECK = 'cpu-native-observation'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def native_files(report):
    return {row['file']: row for row in report['classification_input']['report']['native_files']}


def check_observation(value, report, root):
    """以固定 CPU 候選的實際原生檔綁 Windows 觀測，而非只核對版本號。"""
    from embedded_components import check_pin

    basis = value['basis']
    need(value.get('check') == CHECK and value.get('schema_version') == 1
         and value.get('platform') == 'win32' and report['profile'] == 'cpu'
         and re.fullmatch('[0-9a-f]{40}', value['selection']['source_commit'])
         and value['selection']['event'] in ('workflow_dispatch','pull_request'), 'Invalid CPU Windows observation')
    check_pin({k: basis[k] for k in ('path','sha256')}, BASIS, root, 'CPU basis')
    need(basis['source_commit'] == report['selection']['source_commit'], 'Wrong CPU observation source')
    expected = dict(
        APIS,
        **{'shapely/geos': ('GEOSversion', {f for f in native_files(report) if f.startswith('Shapely.libs/geos')})})
    native = native_files(report)
    need(set(value['records']) == set(expected), 'CPU observations missing or extra')
    for identity,(api,paths) in expected.items():
        row = value['records'][identity]
        need(row['api'] == api and set(row['binaries']) == paths
             and re.fullmatch(r'\d+\.\d+\.\d+(?:[-.][a-zA-Z0-9.]+)?', row['version']),
             'Invalid CPU observation or wrong binary: ' + identity)
        for file, digest in row['binaries'].items():
            source = native[file]
            need(digest == source['bundled_sha256'] == source['source_sha256'], 'CPU observation hash differs: ' + file)
            need(any(p['name'].lower() == identity.split('/')[0] for p in source['distributions']),
                 'CPU observation belongs to another wheel: ' + file)
    geos = value['records']['shapely/geos']
    need(geos['raw_version'].startswith(geos['version']+'-CAPI-'), 'GEOS version differs from C API')


def check_component(component, wheel, observation, report, root):
    check_observation(observation, report, root)
    identity = wheel['distribution']+'/'+component['id']
    record = observation['records'].get(identity)
    need(record and record['version'] == component['version'], 'CPU catalog version differs from runtime API')
    # 靜態內含元件與外層套件共用承載檔，目錄只將單一原生路徑登記一次。
    paths = component['native_files'] or [p for c in wheel['components'] if c['kind'] == 'wheel-own'
                                          for p in c['native_files']]
    need(set(record['binaries']) <= set(paths), 'CPU observed binary missing from component')


def check_microsoft(catalog, *, entry, report, root):
    """沿用 A10 六欄逐檔比較，區分宿主觀測與固定候選的已保存 PE 身分。"""
    from embedded_components import check_pin
    from redistribution_gates import reference

    need(catalog['profile'] == report['profile'] == 'cpu' and catalog['registry_entry'] == entry['id']=='cpu-microsoft'
         and catalog['source_commit'] == report['selection']['source_commit'] and catalog['legal_approval'] is False
         and entry['requires_user_decision'], 'Invalid CPU Microsoft catalog')
    check_pin(catalog['basis'], BASIS, root, 'CPU Microsoft basis')
    check_pin(catalog['redist_probe'], MS_REFERENCE, root, 'A13b Redist')
    official = json.loads((root/MS_REFERENCE).read_text(encoding='utf-8'))['references']
    reference(catalog['observation'], root)
    need(catalog['observation'] in entry['evidence'], 'CPU Microsoft observation is not bound to registry')
    observation = json.loads((root/catalog['observation']['path']).read_text(encoding='utf-8'))
    check_observation(observation, report, root)
    native = native_files(report)
    need(len(entry['native_files']) == 6 and sorted(r['file'] for r in catalog['files']) == sorted(entry['native_files']),
         'Missing, repeated or wrong CPU Microsoft file')
    need(set(observation['microsoft']) == {r['file'] for r in catalog['files'] if r['renamed']},
         'Wrong renamed Microsoft observation')
    keys = ('source_directory','company','product','file_version','signature_status','signer')
    for row in catalog['files']:
        file = row['file']
        actual = native[file]
        name = Path(file).name.lower()
        renamed = name.startswith('msvcp140-')
        original_name = 'msvcp140.dll' if renamed else name
        need(row['renamed'] is renamed and row['official_name'] == original_name
             and row['official_sha256'] == official[original_name]['sha256']
             and row['matches_official'] is (row['sha256'] == row['official_sha256']), 'Incorrect Redist comparison: ' + file)
        need((row['sha256'],row['bytes'],row['origin'],row['distributions']) == (
            actual['bundled_sha256'],actual['bundled_bytes'],actual['origin'],actual['distributions'])
            and row['sha256'] == actual['source_sha256'], 'CPU Microsoft candidate fingerprint differs: ' + file)
        if renamed:
            observed = observation['microsoft'][file]
            need(observed['sha256'] == row['sha256'] and observed['identity'] == row['identity'], 'Wrong Microsoft observation: ' + file)
        else:
            need(row['identity'] == {k:actual[k] for k in keys}, 'Wrong historical PE identity: ' + file)
        need(row['identity'].get('file_version') and 'signature_status' in row['identity'], 'Missing PE evidence: ' + file)
    return dict(catalog=MS_CATALOG, files=6, official_matches=sum(r['matches_official'] for r in catalog['files']),
                renamed_files=[r['file'] for r in catalog['files'] if r['renamed']], legal_approval=False)


def observe(expected, root=ROOT):
    need(sys.platform == 'win32' and os.getenv('GITHUB_ACTIONS') == 'true', 'Hosted Windows required')
    selection = check_source(root, expected)
    basis_path = root/BASIS
    basis = json.loads(basis_path.read_text(encoding='utf-8'))
    native = native_files(basis)
    site = Path(sysconfig.get_path('platlib')).resolve()

    def exact(file):
        path = site/file
        row = native[file]
        need(sha(path) == row['source_sha256'] == row['bundled_sha256'], 'CPU candidate bytes differ: ' + file)
        owner, = row['distributions']
        need(owner['version'] == metadata.version(owner['name']), 'CPU wheel version differs: ' + file)
        return path

    records = {}
    for identity, (qualified_api, files) in APIS.items():
        module_name, api = qualified_api.rsplit('.', 1)
        file, = files
        path = exact(file)
        module = import_module(module_name)
        # cv2 是 Python 載入器，原生模組另掛在 _native。
        extension = getattr(module, '_native', module)
        need(Path(extension.__file__).resolve() == path.resolve(), 'Wrong version API module: ' + file)
        records[identity] = dict(api=qualified_api, version=getattr(module, api)(), binaries={file: sha(path)})

    # 確認 Shapely 實際載入的是已核對的外部 DLL，避免只以編譯版本或字串推定。
    geos_files = sorted(f for f in native if f.startswith('Shapely.libs/geos'))
    dlls = {f: exact(f) for f in geos_files}
    need(len(dlls) == 2, 'Unexpected GEOS pair')
    from shapely import box
    need(box(0, 0, 2, 3).area == 6, 'Shapely GEOS smoke test failed')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    handle = kernel.GetModuleHandleW
    handle.argtypes, handle.restype = [ctypes.c_wchar_p], ctypes.c_void_p
    module_path = kernel.GetModuleFileNameW
    module_path.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    module_path.restype = ctypes.c_uint
    paths = {}
    capi_handle = None
    for file, path in dlls.items():
        loaded = handle(path.name)
        buffer = ctypes.create_unicode_buffer(32768)
        need(loaded and 0 < module_path(loaded, buffer, len(buffer)) < len(buffer), 'GEOS DLL not loaded: ' + file)
        need(Path(buffer.value).resolve() == path.resolve(), 'Loaded GEOS path differs: ' + file)
        paths[file] = sha(path)
        if path.name.startswith('geos_c-'):
            capi_handle = loaded
    need(capi_handle, 'GEOS C API handle missing')
    version = ctypes.CDLL('geos_c', handle=capi_handle).GEOSversion
    version.argtypes, version.restype = [], ctypes.c_char_p
    raw_version = version().decode('ascii')
    records['shapely/geos'] = dict(api='GEOSversion', version=raw_version.split('-CAPI-',1)[0],
                                   raw_version=raw_version, binaries=paths)

    import cv2
    build = cv2.getBuildInformation()
    # build 資料只證明編譯時宣告，不轉稱內含函式庫的 runtime 版本。
    build_lines = [line.strip() for line in build.splitlines()
                   if re.match(r'^\s*(IPP|JPEG|WEBP|PNG|TIFF|JPEG 2000|OpenEXR|AVIF|zlib|Protobuf|FFMPEG|GStreamer|Media Foundation)(?:\s|:)', line, re.I)]
    records['opencv-python/opencv']['build_declarations'] = build_lines

    renamed = {f: exact(f) for f in native if re.fullmatch(r'(?:numpy|Shapely)\.libs/msvcp140-[0-9a-f]{32}\.dll', f)}
    need(len(renamed) == 2, 'Missing renamed Microsoft runtime sources')
    identity = describe(renamed.values())
    microsoft = {file: dict(sha256=sha(path), identity=identity[path]) for file,path in renamed.items()}
    need(all(r['identity'].get('file_version') and 'signature_status' in r['identity']
             and not r['identity'].get('identity_error') for r in microsoft.values()), 'Missing Microsoft PE or signature evidence')
    return dict(check=CHECK, schema_version=1, platform=sys.platform, selection=selection,
                basis=dict(path=BASIS, sha256=sha(basis_path), source_commit=basis['selection']['source_commit']),
                records=records, microsoft=microsoft)


def publish(value):
    data = canonical(value)
    encoded = base64.b64encode(gzip.compress(data, mtime=0)).decode('ascii')
    need(0 < len(encoded) <= 12000, 'CPU observation annotation exceeds budget')
    chunks = [encoded[i:i+2400] for i in range(0,len(encoded),2400)]
    for i, part in enumerate(chunks,1):
        print('::notice title=CPU native observation::'+json.dumps(
            dict(check=CHECK, sha256=hashlib.sha256(data).hexdigest(), part=i, parts=len(chunks), data=part),
            separators=(',', ':')))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    value = observe(args.expected_source)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(value, output, ensure_ascii=False, indent=2)
        output.write('\n')
    publish(value)


if __name__ == '__main__':
    main()

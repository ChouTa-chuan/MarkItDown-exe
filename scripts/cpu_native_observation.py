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
APIS = {
    'pyyaml/libyaml': ('yaml._yaml', 'get_version_string', 'yaml/_yaml.cp312-win_amd64.pyd'),
}
CHECK = 'cpu-native-observation'


def need(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(expected, root=ROOT):
    need(sys.platform == 'win32' and os.getenv('GITHUB_ACTIONS') == 'true', 'Hosted Windows required')
    selection = check_source(root, expected)
    basis_path = root/BASIS
    basis = json.loads(basis_path.read_text(encoding='utf-8'))
    native = {row['file']: row for row in basis['classification_input']['report']['native_files']}
    site = Path(sysconfig.get_path('platlib')).resolve()

    def exact(file):
        path = site/file
        row = native[file]
        need(sha(path) == row['source_sha256'] == row['bundled_sha256'], 'CPU candidate bytes differ: ' + file)
        owner, = row['distributions']
        need(owner['version'] == metadata.version(owner['name']), 'CPU wheel version differs: ' + file)
        return path

    records = {}
    for identity, (module_name, api, file) in APIS.items():
        path = exact(file)
        module = import_module(module_name)
        need(Path(module.__file__).resolve() == path.resolve(), 'Wrong version API module: ' + file)
        records[identity] = dict(api=module_name+'.'+api, version=getattr(module, api)(),
                                 binaries={file: sha(path)})

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

    cv = exact('cv2/cv2.pyd')
    import cv2
    build = cv2.getBuildInformation()
    # build 資料只證明編譯時宣告，不轉稱內含函式庫的 runtime 版本。
    build_lines = [line.strip() for line in build.splitlines()
                   if re.match(r'^\s*(IPP|JPEG|WEBP|PNG|TIFF|JPEG 2000|OpenEXR|AVIF|zlib|Protobuf|FFMPEG|GStreamer|Media Foundation)(?:\s|:)', line, re.I)]
    records['opencv-python/opencv'] = dict(api='cv2.getVersionString',version=cv2.getVersionString(),
                                            binaries={'cv2/cv2.pyd': sha(cv)}, build_declarations=build_lines)

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

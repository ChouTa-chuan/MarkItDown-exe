"""A12d：只讀實際載入的版本 API，以固定候選原生檔 bytes 綁定觀測；不改安裝內容。

沒有 API、API 未提供值、或 Windows 需要包外 DLL 時保留未知。公開註記只保存有界 JSON，
不包含 wheel／DLL。此證據不判斷原文或散布義務是否充分。
"""
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
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'packaging/embedded/base-windows.json'
# 僅允許已核對上游實作的 API；不能以任意字串、編譯版本或外層套件版本代替。
APIS = {
    'lxml/libxml2': ('lxml.etree.LIBXML_VERSION', 'lxml/etree.cp312-win_amd64.pyd'),
    'lxml/libxslt': ('lxml.etree.LIBXSLT_VERSION', 'lxml/etree.cp312-win_amd64.pyd'),
    'pillow/raqm': ('PIL.features.version_feature(raqm)', 'PIL/_imagingft.cp312-win_amd64.pyd'),
    'pillow/fribidi': ('PIL.features.version_feature(fribidi)', 'PIL/_imagingft.cp312-win_amd64.pyd'),
    'pillow/libaom': ('PIL._avif.codec_versions(aom)', 'PIL/_avif.cp312-win_amd64.pyd'),
    'pillow/dav1d': ('PIL._avif.codec_versions(dav1d)', 'PIL/_avif.cp312-win_amd64.pyd'),
    'numpy/numpy-lapack': ('scipy_LAPACKE_ilaver64_', None),
}
RECORD_KEYS = {'component', 'distribution_version', 'api', 'status', 'version', 'raw_value', 'binary', 'reason'}
BINARY_KEYS = {'file', 'sha256'}
REPORT_KEYS = {'check', 'schema_version', 'platform', 'observed_source', 'basis_review', 'basis_source',
               'records', 'not_probed', 'accepted', 'redistribution_approved'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def version_tuple(value):
    require(isinstance(value, (list, tuple)) and len(value) == 3
            and all(type(x) is int and 0 <= x < 10000 for x in value) and value[0] > 0,
            'Invalid runtime version tuple')
    return '.'.join(map(str, value))


def codec_version(text, codec):
    """libavif 回傳各 codec 的實際版本；不以 libavif 自己的版本替代 aom／dav1d。"""
    require(isinstance(text, str) and len(text) < 1024, 'Invalid codec version API result')
    match = re.search(r'(?:^|,\s*)'+re.escape(codec)+r' \[[a-z/]+\]:([^,\s]+)', text)
    return match[1] if match else None


def numpy_lapack():
    import numpy
    directory = Path(numpy.__file__).resolve().parent.parent/'numpy.libs'
    libraries = list(directory.glob('libscipy_openblas64_*.dll'))
    require(len(libraries) == 1, 'Expected one locked numpy OpenBLAS DLL')
    path = libraries[0]
    library = ctypes.CDLL(str(path))
    # 已查驗同一份 Windows wheel 的匯出及 USE64BITINT；先核對整數寬度，再呼叫 LAPACKE。
    config = library.scipy_openblas_get_config64_
    config.argtypes = []
    config.restype = ctypes.c_char_p
    text = config().decode('ascii')
    require('USE64BITINT' in text, 'LAPACKE integer ABI not verified')
    function = library.scipy_LAPACKE_ilaver64_
    integer = ctypes.c_longlong
    function.argtypes = [ctypes.POINTER(integer)]*3
    function.restype = None
    values = [integer() for _ in range(3)]
    function(*(ctypes.byref(x) for x in values))
    # 完整路徑載入仍須核對真正 module handle，避免同名已載入 DLL 取代指定來源。
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    get_name = kernel.GetModuleFileNameW
    get_name.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.c_uint]
    get_name.restype = ctypes.c_uint
    buffer = ctypes.create_unicode_buffer(32768)
    require(0 < get_name(library._handle, buffer, len(buffer)) < len(buffer), 'Missing loaded numpy DLL path')
    require(Path(buffer.value).resolve() == path.resolve(), 'Loaded numpy DLL differs from requested source')
    numbers = [x.value for x in values]
    return version_tuple(numbers), path, dict(version_values=numbers, openblas_configuration=text)


def call_api(identity):
    """回傳版本、真正的承載原生檔與原始 API 值；不可觀測與載入錯誤由控制端明確區分。"""
    if identity.startswith('lxml/'):
        module = import_module('lxml.etree')
        value = getattr(module, 'LIBXML_VERSION' if identity.endswith('/libxml2') else 'LIBXSLT_VERSION')
        return version_tuple(value), Path(module.__file__), list(value)
    if identity in ('pillow/raqm', 'pillow/fribidi'):
        features = import_module('PIL.features')
        module = import_module('PIL._imagingft')
        value = features.version_feature(identity.split('/')[1])
        # Windows 的 FriBidi 是 optional dynamic load。僅綁 _imagingft 不能證明包外 DLL 的 bytes。
        if identity == 'pillow/fribidi':
            return None, Path(module.__file__), value
        return value, Path(module.__file__), value
    if identity in ('pillow/libaom', 'pillow/dav1d'):
        module = import_module('PIL._avif')
        text = module.codec_versions()
        return codec_version(text, 'aom' if identity.endswith('/libaom') else 'dav1d'), Path(module.__file__), text
    return numpy_lapack()


def validate_record(record, native, versions):
    require(isinstance(record, dict) and set(record) == RECORD_KEYS, 'Invalid runtime record structure')
    identity = record['component']
    require(identity in APIS and record['api'] == APIS[identity][0], 'Unreviewed runtime version API')
    dist = identity.split('/')[0]
    require(record['distribution_version'] == versions.get(dist), 'Runtime distribution version differs')
    require(record['status'] in ('observed', 'unavailable', 'error'), 'Invalid runtime observation status')
    if record['status'] != 'observed':
        require(record['version'] is None, 'Unobserved component cannot carry a known version')
        return
    require(identity != 'pillow/fribidi', 'External FriBidi cannot be bound through the Pillow extension alone')
    version = record['version']
    require(isinstance(version, str) and re.fullmatch(r'v?\d+\.\d+\.\d+(?:[-+._a-zA-Z0-9]*)', version),
            'Missing runtime version')
    binary = record['binary']
    require(isinstance(binary, dict) and set(binary) == BINARY_KEYS, 'Missing runtime native identity')
    name = binary['file']
    if APIS[identity][1] is not None:
        require(name == APIS[identity][1], 'Runtime API binary differs')
    else:
        require(re.fullmatch(r'numpy\.libs/libscipy_openblas64_-[0-9a-f]+\.dll', name), 'Unexpected LAPACK binary')
        raw = record['raw_value']
        require(isinstance(raw, dict) and set(raw) == {'version_values', 'openblas_configuration'}
                and isinstance(raw['openblas_configuration'], str) and 'USE64BITINT' in raw['openblas_configuration'],
                'Unverified LAPACKE integer ABI')
        require(version_tuple(raw['version_values']) == version, 'LAPACKE runtime version differs')
    source = native.get(name)
    require(source is not None and binary['sha256'] == source['source_sha256'] == source['bundled_sha256'],
            'Runtime binary differs from candidate bytes')
    owners = source.get('distributions') or []
    require(any(x['name'].lower() == dist and x['version'] == versions[dist] for x in owners),
            'Runtime binary belongs to another distribution')
    if identity.startswith('lxml/'):
        require(version_tuple(record['raw_value']) == version, 'lxml API version differs')
    elif identity.startswith('pillow/'):
        expected = (record['raw_value'] if identity == 'pillow/raqm' else
                    codec_version(record['raw_value'], 'aom' if identity.endswith('/libaom') else 'dav1d'))
        require(expected == version, 'Pillow API version differs')


def validate_report(value):
    require(isinstance(value, dict) and set(value) == REPORT_KEYS and value['check'] == 'embedded-runtime-observation'
            and type(value['schema_version']) is int and value['schema_version'] == 1,
            'Invalid embedded runtime observation')
    require(value['platform'] == 'win32' and value['accepted'] is True
            and value['redistribution_approved'] is False, 'Runtime observation needs successful hosted Windows evidence')
    require(isinstance(value['observed_source'], str) and re.fullmatch('[0-9a-f]{40}', value['observed_source'])
            and isinstance(value['basis_source'], str) and re.fullmatch('[0-9a-f]{40}', value['basis_source']),
            'Invalid runtime source identity')
    require(isinstance(value['records'], list) and {r['component'] for r in value['records']} == set(APIS)
            and len(value['records']) == len(APIS), 'Missing or duplicate runtime API records')
    require(all(isinstance(r, dict) and set(r) == RECORD_KEYS and r['status'] in ('observed', 'unavailable')
                for r in value['records']), 'Runtime report contains errors or invalid records')


def check_component(component, wheel, proof, report, root=ROOT):
    """觀測可在後續候選沿用的唯一依據是同一原生檔 bytes；原觀測來源與 A12 基準保留。"""
    validate_report(proof)
    pin = proof['basis_review']
    require(isinstance(pin, dict) and set(pin) == {'path', 'sha256'}
            and pin['path'].startswith('docs/development-records/runs/') and '..' not in pin['path'].split('/')
            and '\\' not in pin['path'], 'Invalid runtime basis path')
    path = root/pin['path']
    require(path.is_file() and not path.is_symlink() and sha(path) == pin['sha256'], 'Runtime basis fingerprint differs')
    basis = json.loads(path.read_text(encoding='utf-8'))
    require(basis['selection']['source_commit'] == proof['basis_source'], 'Runtime basis source differs')
    identity = wheel['distribution']+'/'+component['id']
    record = next((r for r in proof['records'] if r['component'] == identity), None)
    require(record is not None and record['status'] == 'observed', 'Component has not been runtime observed')
    versions = {wheel['distribution']:wheel['version']}
    for source in (basis, report):
        native = {r['file']:r for r in source['classification_input']['report']['native_files']}
        validate_record(record, native, versions)
    require(component['version'] == record['version'], 'Catalog version differs from runtime API')


def observe(expected_source, root=ROOT):
    require(sys.platform == 'win32', 'Runtime evidence must be observed on Windows')
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=root, text=True).strip()
    require(actual == expected_source and re.fullmatch('[0-9a-f]{40}', actual), 'Runtime checkout source differs')
    catalog = json.loads((root/CATALOG).read_text(encoding='utf-8'))
    pin = catalog['source_review']
    require(sha(root/pin['path']) == pin['sha256'], 'Candidate basis fingerprint differs')
    basis = json.loads((root/pin['path']).read_text(encoding='utf-8'))
    native = {r['file']:r for r in basis['classification_input']['report']['native_files']}
    versions = {w['distribution']:w['version'] for w in catalog['wheels']}
    records = []
    for identity, (api, _) in APIS.items():
        dist = identity.split('/')[0]
        row = dict(component=identity, distribution_version=metadata.version(dist), api=api,
                   status='unavailable', version=None, raw_value=None, binary=None, reason=None)
        try:
            version, path, raw = call_api(identity)
            path = path.resolve()
            # 原生檔必須真的來自所宣告套件的安裝位置。
            site = Path(metadata.distribution(dist).locate_file('')).resolve()
            require(path.is_relative_to(site), 'Runtime module outside installed distribution')
            row.update(raw_value=raw, binary=dict(file=path.relative_to(site).as_posix(), sha256=sha(path)))
            if version:
                row.update(status='observed', version=version)
            else:
                row['reason'] = ('Optional Windows FriBidi needs a separately bound loaded DLL; retained unknown'
                                 if identity == 'pillow/fribidi' else 'Version API unavailable or did not report this codec')
            validate_record(row, native, versions)
        except Exception as exc:
            row.update(status='error', version=None, reason=type(exc).__name__+': '+str(exc))
        records.append(row)
    value = dict(check='embedded-runtime-observation', schema_version=1, platform=sys.platform,
                 observed_source=actual, basis_review=pin, basis_source=basis['selection']['source_commit'],
                 records=records, not_probed=[w['distribution']+'/'+c['id'] for w in catalog['wheels']
                    for c in w['components'] if c['version_basis'] == 'unknown' and w['distribution']+'/'+c['id'] not in APIS],
                 accepted=not any(r['status'] == 'error' for r in records), redistribution_approved=False)
    return value


def receipt(value):
    raw = canonical(value)
    require(len(raw) <= 64*1024, 'Runtime report too large')
    result = dict(check='embedded-runtime-receipt', schema_version=1, sha256=hashlib.sha256(raw).hexdigest(),
                  encoding='gzip+base64', data=base64.b64encode(gzip.compress(raw, mtime=0)).decode())
    require(len(canonical(result)) < 3800, 'Runtime annotation exceeds bounded budget')
    return result


def decode(value):
    require(set(value) == {'check', 'schema_version', 'sha256', 'encoding', 'data'}
            and value['check'] == 'embedded-runtime-receipt' and value['schema_version'] == 1
            and value['encoding'] == 'gzip+base64' and len(value['data']) < 3800, 'Invalid runtime receipt')
    import io
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(value['data'], validate=True))) as stream:
        raw = stream.read(64*1024+1)
    require(len(raw) <= 64*1024 and hashlib.sha256(raw).hexdigest() == value['sha256'], 'Runtime receipt fingerprint differs')
    return json.loads(raw)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--expected-source', required=True)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    require(not args.output.exists(), 'Runtime report output must be new')
    value = observe(args.expected_source)
    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        print('::notice title=embedded runtime observation::'+canonical(receipt(value)).decode().replace('%', '%25'))
    return 0 if value['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

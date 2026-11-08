"""基本包內含 OCR 的唯讀解析；缺檔、損毀或平台不符時不借用 PATH。"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

from . import build_profile
from .languages import model_manifest
from .native_assets import file_hash, inspect_pe, is_system_dll

LANGUAGES = ('chi_tra', 'eng', 'jpn', 'kor')
ORIGIN = '程式內含基本引擎'


def validate_payload(directory, *, expected_platform=None, assets=None):
    """驗完整 payload 與固定四語 hash；這只是完整性驗證，不是 Windows 或品質驗收。"""
    directory = Path(directory)
    path = directory / 'manifest.json'
    digest, _ = file_hash(path, 256 * 1024)
    if assets is not None and assets.get('native/manifest.json') != digest:
        raise ValueError('內含 OCR 清單與建置 profile 不符。')
    if assets is not None and file_hash(directory.parent / 'ocr-four-languages.json')[0] != assets.get('ocr-four-languages.json'):
        raise ValueError('固定四語模型清單與建置 profile 不符。')
    with path.open('rb') as source:
        raw = source.read(256 * 1024 + 1)
    if len(raw) > 256 * 1024 or hashlib.sha256(raw).hexdigest() != digest:
        raise ValueError('內含 OCR 清單在讀取期間已變更。')
    spec = json.loads(raw)
    if (spec.get('schema_version') != 1 or spec.get('id') != 'bundled-tesseract'
            or spec.get('platform') not in ('windows', 'linux')
            or spec.get('development_only') is not True or spec.get('redistribution_approved') is not False):
        raise ValueError('內含 OCR 契約無效；不能以資料旗標宣稱發行核准。')
    if expected_platform is not None and spec['platform'] != expected_platform:
        raise ValueError('內含 OCR 與執行平台不同，未改用外部引擎。')
    entry = 'bin/tesseract.exe' if spec['platform'] == 'windows' else 'bin/tesseract'
    if spec.get('entrypoint') != entry or spec.get('languages') != list(LANGUAGES):
        raise ValueError('內含 OCR 固定入口或語言清單不符。')
    files = spec.get('files')
    if not isinstance(files, dict) or not 7 <= len(files) <= 128 or entry not in files:
        raise ValueError('內含 OCR 檔案清單不完整。')
    fixed = model_manifest()
    if spec.get('model_commit') != fixed['commit']:
        raise ValueError('內含模型來源不是固定四語提交。')
    for name, expected in fixed['files'].items():
        if files.get('tessdata/' + name, {}).get('sha256') != expected:
            raise ValueError('內含四語模型／原授權與固定來源不符。')
    for name, record in files.items():
        relative = PurePosixPath(name)
        if (relative.is_absolute() or '..' in relative.parts or relative.as_posix() != name
                or '\\' in name or ':' in name or name == 'manifest.json'
                or not re.fullmatch('[0-9a-f]{64}', record['sha256'])
                or type(record['bytes']) is not int or not 0 < record['bytes'] <= 16 * 1024**2):
            raise ValueError('內含 OCR 路徑、大小或雜湊不合法。')
        if assets is not None and assets.get('native/' + name) != record['sha256']:
            raise ValueError('內含 OCR 檔案未被建置 profile 固定：' + name)
        if file_hash(directory / name, 16 * 1024**2) != (record['sha256'], record['bytes']):
            raise ValueError('內含 OCR 完整性不符：' + name)
    observed = set()
    for path in directory.rglob('*'):
        if path.is_symlink():
            raise ValueError('內含 OCR 不接受連結。')
        if path.is_file():
            observed.add(path.relative_to(directory).as_posix())
    if observed != set(files) | {'manifest.json'}:
        raise ValueError('內含 OCR 混入未列出的檔案。')
    with (directory / entry).open('rb') as source:
        payload = source.read(16 * 1024**2 + 1)
    if len(payload) != files[entry]['bytes'] or hashlib.sha256(payload).hexdigest() != files[entry]['sha256']:
        raise ValueError('內含原生入口在解析前已變更。')
    if spec['platform'] == 'windows':
        pe = inspect_pe(payload)
        if pe['is_dll'] or any(not is_system_dll(name) for name in pe['imports'] + pe['delay_imports']):
            raise ValueError('內含 Windows 入口架構或 DLL 相依不符。')
    elif payload[:6] != b'\x7fELF\x02\x01' or payload[18:20] != b'\x3e\x00':
        raise ValueError('Linux 開發入口不是 AMD64 ELF。')
    return spec


def bindings(executable=None, data_dir=None):
    """明確自備引擎保留原行為；只有自動引擎才解析建置時固定的內含資產。"""
    if executable is not None:
        return executable, data_dir, None
    profile = build_profile.load_profile()
    if profile is None:
        return None, data_dir, None  # 未帶 profile 的既有來源／開發包沿用本機選擇。
    if not profile.get('native_ocr_integrated'):
        raise RuntimeError('此基本核心包未內含 OCR；未改用 PATH 或系統模型。')
    target = {'win32': 'windows', 'linux': 'linux'}.get(sys.platform)
    if target is None:
        raise RuntimeError('不支援此內含 OCR 執行平台。')
    root = build_profile.data_root() / 'native'
    spec = validate_payload(root, expected_platform=target, assets=profile['assets'])
    return str(root / spec['entrypoint']), data_dir if data_dir is not None else str(root / 'tessdata'), ORIGIN

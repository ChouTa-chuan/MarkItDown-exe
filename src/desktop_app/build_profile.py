"""讀取建置時固定的基本版能力與資產清單，不從使用者設定選擇信任來源。"""
import hashlib
from importlib import metadata, resources, util
import json
from pathlib import Path, PurePosixPath
import re

FORBIDDEN_MODULES = ('rapidocr_onnxruntime', 'cv2', 'pyclipper', 'shapely', 'yaml', 'docx', 'reportlab')


def data_root():
    return Path(resources.files('desktop_app').joinpath('data'))


def load_profile(root=None):
    root = Path(root) if root is not None else data_root()
    path = root/'build-profile.json'
    if not path.exists():
        if path.is_symlink(): raise ValueError('建置 profile 不得是懸空連結。')
        return None  # 未帶新 profile 的來源／歷史開發包維持原行為。
    if path.is_symlink() or path.stat().st_size > 1024*1024:
        raise ValueError('建置 profile 不合法。')
    profile = json.loads(path.read_text(encoding='utf-8'))
    if (profile.get('schema_version') not in (1, 2) or profile.get('id') != 'base'
            or profile.get('native_ocr_required') is not True or profile.get('release_ready') is not False):
        raise ValueError('建置 profile 契約不符，不得宣告發行就緒。')
    integrated = profile.get('native_ocr_integrated')
    if (type(integrated) is not bool or (profile['schema_version'] == 1 and integrated)
            or (integrated and profile.get('native_ocr_manifest') != 'native/manifest.json')):
        raise ValueError('內含 OCR 必須使用新版明確資產契約。')
    if not isinstance(profile.get('runtime_packages'), dict) or not profile['runtime_packages']:
        raise ValueError('缺少固定相依清單。')
    if not isinstance(profile.get('assets'), dict) or not profile['assets']:
        raise ValueError('缺少資產雜湊清單。')
    required = {'user-guide.md','third-party.md','base-runtime-lock.txt',
                'licenses/python-runtime/LICENSE.txt','licenses/installed/manifest.json'}
    if integrated:
        required |= {'native/manifest.json', 'ocr-four-languages.json'}
    if not required <= profile['assets'].keys():
        raise ValueError('profile 必要手冊／鎖定／授權資產不完整。')
    if (set(profile.get('local_packages', {})) != {'markitdown-desktop','markitdown'}
            or profile.get('notice_packages') != len(profile['runtime_packages'])+2):
        raise ValueError('profile 本地專案或授權套件數不符。')
    for name, digest in profile['assets'].items():
        path = PurePosixPath(name)
        if (not name or '\\' in name or ':' in name or path.is_absolute() or '..' in path.parts
                or path.as_posix() != name or not re.fullmatch('[0-9a-f]{64}', digest)):
            raise ValueError('profile 資產路徑或雜湊不合法。')
    return profile


def verify_assets(profile, root=None):
    root = Path(root) if root is not None else data_root()
    for name, expected in profile['assets'].items():
        path = root/name
        if path.is_symlink() or not path.is_file() or path.stat().st_size > 8*1024**2:
            raise RuntimeError('profile 資產缺少或類型不符：'+name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('profile 資產雜湊不符：'+name)
    return f"基本版資產 {len(profile['assets'])} 份、實際安裝授權 {profile['notice_packages']} 個套件"


def verify_runtime(profile):
    for name, version in {**profile['runtime_packages'], **profile['local_packages']}.items():
        if metadata.version(name) != version:
            raise RuntimeError('profile 相依版本不符：'+name)
    if metadata.version('markitdown-desktop') != profile['source_version']:
        raise RuntimeError('profile 與主程式版本不符。')
    found = [name for name in FORBIDDEN_MODULES if util.find_spec(name) is not None]
    if found:
        raise RuntimeError('基本版混入選配／測試模組：'+', '.join(found))
    return f"{len(profile['runtime_packages'])} 個固定 runtime；未帶 RapidOCR／OpenCV／測試產生工具"

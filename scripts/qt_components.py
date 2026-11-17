"""Qt 第三方來源上位集合與隨包原文；不把來源宣告當成實際編譯證明。"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import shutil

from build_provenance import sha256
import qt_sources

ROOT = Path(__file__).resolve().parents[1]
CATALOG = 'packaging/qt/6.12.0/thirdparty/catalog.json'
STAGED = 'licenses/qt-thirdparty'


def checked_file(directory, name):
    """上游可有 ../ 的原始引用；目錄內已正規化的保存路徑不接受越界或連結。"""
    if (not isinstance(name, str) or not name or '\\' in name or ':' in name
            or PurePosixPath(name).is_absolute() or any(p in ('', '.', '..') for p in name.split('/'))):
        raise ValueError('Unsafe Qt source path')
    path = directory/name
    if (not path.is_file() or any(p.is_symlink() for p in (path, *path.parents))
            or not path.resolve().is_relative_to(directory.resolve())):
        raise ValueError('Qt original missing or linked: '+name)
    return path


def load_catalog(root=ROOT):
    """重驗固定發布來源、原文 Git blob、版本宣告與每個 attribution 子項。"""
    root = Path(root)
    path = root/CATALOG
    directory = path.parent
    value = json.loads(path.read_text(encoding='utf-8'))
    release = qt_sources.load_catalog(root)
    if (value.get('schema_version') != 1 or value.get('version') != qt_sources.VERSION
            or value.get('check') != 'qt-thirdparty-catalog'
            or any(value.get(k) is not False for k in ('binary_build_configuration_complete',
                'thirdparty_runtime_closure_verified', 'redistribution_approved', 'runtime_sbom_complete'))):
        raise ValueError('Qt catalog cannot approve missing build or redistribution evidence')
    reference = value['release_catalog']
    if reference['path'] != 'packaging/qt/6.12.0/catalog.json' or sha256(root/reference['path']) != reference['sha256']:
        raise ValueError('Qt release catalog differs')
    reference = value['replacement_input']
    if (reference['path'] != 'packaging/qt/6.12.0/replacement-input.json'
            or sha256(root/reference['path']) != reference['sha256']):
        raise ValueError('Qt replacement input differs')
    commits = {'qt/'+name:release['modules'][name] for name in ('qtbase', 'qtsvg', 'qtimageformats')}
    commits['pyside/pyside-setup'] = release['pyside_commit']
    originals = {}
    declarations = {}
    for row in value['evidence_files']:
        name = row['path']
        if (name in originals or row['repository'] not in commits
                or row['commit'] != commits[row['repository']]
                or name != 'raw/'+row['repository']+'/'+row['upstream_path']
                or row['url'] != 'https://raw.githubusercontent.com/'+row['repository']+'/'+row['commit']+'/'+row['upstream_path']):
            raise ValueError('Qt original source binding differs')
        original = checked_file(directory, name)
        data = original.read_bytes()
        blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
        if sha256(original) != row['sha256'] or len(data) != row['bytes'] or blob != row['git_blob']:
            raise ValueError('Qt original fingerprint differs: '+name)
        originals[name] = row
        if name.endswith('/qt_attribution.json'):
            # 少數固定上游 JSON 的字串含字面換行。保留原位元組，只在讀取時容許控制字元。
            raw = json.loads(data, strict=False)
            declarations[name] = raw if isinstance(raw, list) else [raw]
    seen = set()
    for row in value['components']:
        ref = row['attribution']
        key = (ref['path'], ref['index'])
        if key in seen or ref['path'] not in declarations or type(ref['index']) is not int:
            raise ValueError('Duplicate or unknown Qt attribution')
        seen.add(key)
        try:
            original = declarations[ref['path']][ref['index']]
        except IndexError:
            raise ValueError('Unknown Qt attribution index') from None
        version = original.get('Version') or None
        if (row['name'] != original['Name'] or row['source_id'] != original['Id']
                or row['version'] != version
                or row['version_basis'] != ('source-declared' if version else 'unknown')
                or row['declared_license'] != (original.get('LicenseId') or original.get('License'))
                or row['compiled_into_windows_wheel'] != 'unverified'):
            raise ValueError('Qt source declaration relabelled as runtime evidence')
        if not row['original_notices'] or any(n not in originals for n in row['original_notices']):
            raise ValueError('Qt attribution lacks original notice binding')
    if seen != {(name, i) for name, rows in declarations.items() for i in range(len(rows))}:
        raise ValueError('Qt attribution coverage differs')
    if 'windows_evidence' in value:
        verify_windows_evidence(value, root)
    return value


def verify_windows_evidence(value, root):
    """把實際 hosted Windows 小型結果綁回固定來源；不提高義務或產品旗標。"""
    from check_qt_replacement import validate_report
    saved = {}
    for key in ('replacement', 'build_info'):
        ref = value['windows_evidence'][key]
        path = checked_file(root, ref['path'])
        if sha256(path) != ref['sha256']:
            raise ValueError('Qt Windows evidence fingerprint differs')
        saved[key] = json.loads(path.read_text(encoding='utf-8'))
    original = next(r for r in value['native_files'] if r['file'] == 'PySide6/Qt6Core.dll')
    profile = value['replacement_input']
    record = json.loads((root/profile['path']).read_text(encoding='utf-8'))
    validate_report(saved['replacement'], record, original['bundled_sha256'], profile['sha256'])
    build = saved['build_info']
    observed = build['observed']
    core = next(r for r in value['native_files'] if r['file'] == 'PySide6/QtCore.pyd')
    if (build.get('check') != 'qt-release-sources' or build.get('release_source_map_verified') is not True
            or build.get('catalog_sha256') != value['release_catalog']['sha256']
            or observed.get('platform') != 'Windows' or observed.get('shared_build') is not True
            or observed.get('debug_build') is not False or not observed.get('qt_build')
            or any(observed.get(k) != value['version'] for k in ('qt_version', 'library_version', 'pyside_version', 'shiboken_version'))
            or observed.get('core_extension_sha256') != core['source_sha256']
            or any(build.get(k) is not False for k in ('binary_reproduction_verified',
                'upstream_build_patch_set_verified', 'redistribution_approved', 'runtime_sbom_complete'))):
        raise ValueError('Qt Windows build observation differs')


def stage(root, assets):
    """只加入第三方宣告與原文，不收集替換測試 DLL、wheel 或測試目錄。"""
    catalog = load_catalog(root)
    source = Path(root)/CATALOG
    target = Path(assets)/STAGED
    target.mkdir(parents=True)
    shutil.copyfile(source, target/'catalog.json')
    for row in catalog['evidence_files']:
        destination = target/row['path']
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source.parent/row['path'], destination)


def verify(assets, root=ROOT):
    """即使資產 manifest 被重算，缺檔／改原文仍須拒絕。"""
    catalog = load_catalog(root)
    target = Path(assets)/STAGED
    if sha256(checked_file(target, 'catalog.json')) != sha256(Path(root)/CATALOG):
        raise ValueError('Bundled Qt catalog differs')
    for row in catalog['evidence_files']:
        if sha256(checked_file(target, row['path'])) != row['sha256']:
            raise ValueError('Bundled Qt original differs: '+row['path'])
    return catalog


def check_profile(value, *, entry, report, root=ROOT):
    """登記表只持有本目錄 hash；逐檔資料在這裡與 A6 輸入核對，原計數不變。"""
    if value != load_catalog(root) or entry['id'] != 'base-qt' or not entry['requires_user_decision']:
        raise ValueError('Qt catalog needs its A13 user decision binding')
    files = value['native_files']
    if (value['source_commit'] != report['selection']['source_commit']
            or len({r['file'] for r in files}) != len(files)
            or {r['file'] for r in files} != set(entry['native_files'])):
        raise ValueError('Qt native source coverage differs')
    native = {r['file']:r for r in report['classification_input']['report']['native_files']}
    for row in files:
        if any(row[k] != native[row['file']][k] for k in ('source_sha256', 'bundled_sha256')):
            raise ValueError('Qt native fingerprint differs')
    return dict(catalog=CATALOG, source_declarations=len(value['components']),
                native_files=len(files), thirdparty_runtime_closure_verified=False,
                binary_build_configuration_complete=False, redistribution_approved=False)

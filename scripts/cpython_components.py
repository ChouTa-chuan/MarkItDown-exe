"""CPython 隨附第三方元件的逐檔版本／原文證據；不核准再散布。

僅盤點真正由 Windows CPython 目錄收集的目標檔案。檔案版本、官方建置宣告、
目前載入程式庫的版本分開記錄；libffi 沒有穩定版本查詢 API，不能拿 ABI 檔名當版本。
來源 profile 與原文固定提交／SHA-256，建置時不連網，也不改第三方原始位元組。
"""
import ctypes
import json
import platform
import re
import shutil
import sys
import sysconfig
from pathlib import Path
from xml.etree import ElementTree

from build_provenance import sha256

ROOT = Path(__file__).resolve().parents[1]
REPORT = 'cpython-components.json'
COMPONENTS = ('openssl', 'libffi', 'sqlite')


def contained(root, relative):
    """只接受目錄內普通檔案，拒絕原文索引的路徑逃脫與連結。"""
    parts = str(relative).split('/')
    if not relative or '\\' in relative or ':' in relative or any(p in ('', '.', '..') for p in parts):
        raise ValueError('Unsafe CPython evidence path: ' + str(relative))
    path = Path(root).joinpath(*parts)
    if path.is_symlink() or any(p.is_symlink() for p in path.parents) or not path.is_file():
        raise ValueError('Missing or linked CPython evidence: ' + str(relative))
    if not path.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('CPython evidence escapes root')
    return path


def load_profile(version, root=ROOT):
    """只讀完全相同 patch 版的固定 profile；沒有就失敗，不套用其他版本。"""
    if not re.fullmatch(r'\d+\.\d+\.\d+', version):
        raise ValueError('Invalid CPython version')
    directory = Path(root)/'packaging/cpython'/('windows-' + version)
    if not directory.is_dir():
        raise ValueError('Missing pinned Windows CPython profile for ' + version)
    path = contained(directory, 'profile.json')
    profile = json.loads(path.read_text(encoding='utf-8'))
    if (profile.get('schema_version') != 1 or profile.get('cpython_version') != version
            or profile.get('platform') != 'windows' or profile.get('architecture') != 'x64'
            or set(profile.get('components', {})) != set(COMPONENTS)):
        raise ValueError('Invalid CPython source profile')
    if not re.fullmatch('[0-9a-f]{40}', profile.get('cpython_commit', '')):
        raise ValueError('Unpinned CPython source')
    sources = {row['file']: row for row in profile['sources']}
    if len(sources) != len(profile['sources']):
        raise ValueError('Duplicate CPython source file')
    for name, row in sources.items():
        file = contained(directory, name)
        if sha256(file) != row['sha256'] or file.stat().st_size != row['bytes']:
            raise ValueError('CPython original source fingerprint mismatch: ' + name)
        if not re.fullmatch('[0-9a-f]{40}', row.get('commit', '')):
            raise ValueError('Unpinned CPython external source')
        if row.get('repository') == 'python/cpython' and row['commit'] != profile['cpython_commit']:
            raise ValueError('Mixed CPython source commits')
    header = contained(directory, 'sources/patchlevel.h').read_text(encoding='utf-8')
    declared_python = re.search(r'^#define\s+PY_VERSION\s+"([^"]+)"', header, re.MULTILINE)
    if not declared_python or declared_python.group(1) != version:
        raise ValueError('CPython source version mismatch')
    # 宣告值必須能對到真正保存的 python.props，不能只改 JSON 版本就通過。
    props = ElementTree.parse(contained(directory, 'sources/python.props'))
    ns = {'m': 'http://schemas.microsoft.com/developer/msbuild/2003'}
    for name, tag, prefix in (('openssl', 'opensslDir', 'openssl-'),
                              ('libffi', 'libffiDir', 'libffi-'),
                              ('sqlite', 'sqlite3Dir', 'sqlite-')):
        node = props.find('.//m:' + tag, ns)
        expected = profile['components'][name]['declared_version']
        if node is None or prefix + expected + '\\' not in (node.text or ''):
            raise ValueError('CPython build declaration mismatch: ' + name)
        if profile['components'][name]['notice'] not in sources:
            raise ValueError('Missing CPython original notice: ' + name)
    return directory, profile


def runtime_probe():
    """Windows 建置程序內查實際版本與載入檔 hash，避免把另一份同名 DLL 的版本套上來。"""
    import ssl
    import sqlite3
    from ctypes import wintypes

    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel.GetModuleHandleW.restype = wintypes.HMODULE
    kernel.GetModuleFileNameW.argtypes = [wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD]
    kernel.GetModuleFileNameW.restype = wintypes.DWORD
    files = {}
    for name in ('libssl-3.dll', 'libcrypto-3.dll', 'libffi-8.dll', 'sqlite3.dll',
                 '_ssl.pyd', '_hashlib.pyd', '_ctypes.pyd', '_sqlite3.pyd'):
        handle = kernel.GetModuleHandleW(name)
        if not handle:
            continue
        buffer = ctypes.create_unicode_buffer(32768)
        count = kernel.GetModuleFileNameW(handle, buffer, len(buffer))
        if not count or count >= len(buffer):
            continue
        path = Path(buffer.value)
        files[name] = dict(path=str(path), sha256=sha256(path))
    match = re.match(r'OpenSSL (\d+\.\d+\.\d+)', ssl.OPENSSL_VERSION)
    return dict(versions={'openssl': match.group(1) if match else None,
                          'sqlite': sqlite3.sqlite_version}, files=files)


def numeric_version(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d+(?:\.\d+)+', value):
        raise ValueError('Invalid observed component version')
    parts = list(map(int, value.split('.')))
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return parts


def target_rows(native, profile):
    """檔名只用於固定 profile 的路由；來源必須已是 python-runtime，其他同名 DLL 不認領。"""
    lookup = {name.casefold(): (component, role)
              for component, config in profile['components'].items() for name, role in config['files'].items()}
    result = []
    for row in native:
        name = row.get('source_basename', Path(row['file']).name).casefold()
        if row['origin'] == 'python-runtime' and name in lookup:
            component, role = lookup[name]
            result.append((row, name, component, role))
    return sorted(result, key=lambda item: item[0]['file'])


def require_runtime_probes(report):
    """Windows 適用清單不接受 OpenSSL／SQLite 只有宣告；本機、CI 與離線重驗一致。

    Linux 不適用清單保持不適用。libffi 沒有支援的查詢 API，不能套用同一門檻。
    產生端先保存診斷再拒絕，重驗端也執行，避免重算 manifest hash 就能繞過。
    """
    if report.get('applicable') is not True:
        return
    if 'probe_error' in report:
        raise ValueError('CPython runtime probe failed: '+str(report['probe_error'])[:160])
    for row in report['files']:
        if row['component'] in ('openssl', 'sqlite') and (
                row.get('version_status') != 'matched-runtime-probe'
                or row.get('loaded_source_matched') is not True
                or not row.get('observed_version')):
            raise ValueError('CPython runtime probe required: '+row['file'])


def write_inventory(native, output, *, root=ROOT, target=None, version=None, license_path=None, probe=None):
    """在 native manifest 同目錄寫清單及原文；原生資產後續既有 rglob 會一併納入。"""
    target = sys.platform if target is None else target
    version = platform.python_version() if version is None else version
    output = Path(output)
    report = dict(schema_version=1, platform=target, cpython_version=version,
                  applicable=target == 'win32', files=[], notices=[],
                  redistribution_approved=False, runtime_sbom_complete=False)
    if target != 'win32':
        report['scope'] = 'Windows CPython component inventory is not applicable on this platform'
    else:
        if ctypes.sizeof(ctypes.c_void_p) != 8 or platform.machine().lower() not in ('amd64', 'x86_64'):
            raise ValueError('CPython component profile requires Windows x64')
        directory, profile = load_profile(version, root)
        if license_path is None:
            license_path = next((p for p in (Path(sys.base_prefix)/'LICENSE.txt',
                                Path(sysconfig.get_path('stdlib'))/'LICENSE.txt') if p.is_file()), None)
        if license_path is None or not Path(license_path).is_file() or not Path(license_path).stat().st_size:
            raise ValueError('Missing actual CPython runtime license')
        report.update(architecture='x64', cpython_commit=profile['cpython_commit'], profile_sha256=sha256(directory/'profile.json'),
                      python_license_sha256=sha256(license_path),
                      scope='Collected source hashes, PE file versions, matched runtime probes and upstream declarations; '
                            'libffi declaration is not an independent binary version certification')
        try:
            probed = runtime_probe() if probe is None else probe
        except Exception as error:
            probed = dict(versions={}, files={})
            report['probe_error'] = type(error).__name__ + ': ' + str(error)[:160]
        sources = {row['file']: row for row in profile['sources']}
        original = output.parent/'cpython-original'
        original.mkdir(exist_ok=False)
        for component, config in profile['components'].items():
            source = contained(directory, config['notice'])
            dest = original/(component + '.txt')
            shutil.copyfile(source, dest)
            report['notices'].append(dict(component=component, path='cpython-original/' + dest.name,
                                         sha256=sha256(dest), bytes=dest.stat().st_size,
                                         source=sources[config['notice']]))
        for row, name, component, role in target_rows(native, profile):
            config = profile['components'][component]
            loaded = probed.get('files', {}).get(name, {})
            matched = loaded.get('sha256') == row['source_sha256']
            observed = probed.get('versions', {}).get(component) if matched and component != 'libffi' else None
            if observed and numeric_version(observed) != numeric_version(config['declared_version']):
                raise ValueError('CPython runtime version differs from pinned declaration: ' + component)
            report['files'].append(dict(file=row['file'], component=component, role=role,
                source_sha256=row['source_sha256'], source_bytes=row['source_bytes'],
                file_version=row.get('file_version'), declared_version=config['declared_version'],
                observed_version=observed, loaded_source_matched=matched,
                loaded_source_sha256=loaded.get('sha256'),
                version_status='matched-runtime-probe' if observed else 'build-declaration-only',
                notice='cpython-original/' + component + '.txt'))
        report['components_not_collected'] = sorted(set(COMPONENTS) - {r['component'] for r in report['files']})
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    require_runtime_probes(report)
    return report


def verify_inventory(path, native, python_license, *, root=ROOT, target=None):
    """重驗包內清單、版本宣告及原文位元組；不把缺少的觀測值補成通過。"""
    target = sys.platform if target is None else target
    path = Path(path)
    report = json.loads(path.read_text(encoding='utf-8'))
    if report.get('schema_version') != 1 or report.get('platform') != target:
        raise ValueError('Invalid CPython component manifest')
    if report.get('redistribution_approved') is not False or report.get('runtime_sbom_complete') is not False:
        raise ValueError('CPython inventory cannot grant redistribution approval')
    if target != 'win32':
        if report.get('applicable') is not False or report.get('files') or report.get('notices'):
            raise ValueError('Non-Windows evidence cannot claim Windows components')
        return report
    if report.get('applicable') is not True:
        raise ValueError('Missing applicable Windows CPython inventory')
    if report.get('architecture') != 'x64':
        raise ValueError('Invalid CPython component architecture')
    directory, profile = load_profile(report['cpython_version'], root)
    if (report.get('cpython_commit') != profile['cpython_commit']
            or report.get('profile_sha256') != sha256(directory/'profile.json')
            or report.get('python_license_sha256') != sha256(python_license)):
        raise ValueError('CPython source profile or runtime notice mismatch')
    notices = {r['component']: r for r in report['notices']}
    if len(notices) != 3 or set(notices) != set(COMPONENTS) or len(report['notices']) != 3:
        raise ValueError('Incomplete CPython original notices')
    for component, config in profile['components'].items():
        notice = notices[component]
        original = contained(path.parent, notice['path'])
        if (notice['path'] != 'cpython-original/' + component + '.txt'
                or sha256(original) != sha256(contained(directory, config['notice']))
                or notice['sha256'] != sha256(original) or notice['bytes'] != original.stat().st_size
                or notice.get('source') != next(s for s in profile['sources'] if s['file'] == config['notice'])):
            raise ValueError('CPython original notice mismatch: ' + component)
    expected = {row['file']: (row, component, role) for row, _, component, role in target_rows(native, profile)}
    rows = {r['file']: r for r in report['files']}
    if len(rows) != len(report['files']) or set(rows) != set(expected):
        raise ValueError('CPython component native file coverage differs')
    for file, (source, component, role) in expected.items():
        row = rows[file]
        config = profile['components'][component]
        if any(row.get(key) != value for key, value in dict(component=component, role=role,
                source_sha256=source['source_sha256'], source_bytes=source['source_bytes'],
                file_version=source.get('file_version'), declared_version=config['declared_version'],
                notice='cpython-original/' + component + '.txt').items()):
            raise ValueError('CPython component file mismatch: ' + file)
        matched = row.get('loaded_source_sha256') == source['source_sha256']
        observed = row.get('observed_version')
        if component == 'libffi' and observed is not None:
            raise ValueError('libffi has no supported runtime version probe')
        if row.get('loaded_source_matched') != matched or (observed and not matched):
            raise ValueError('Unmatched CPython runtime probe: ' + file)
        if observed and numeric_version(observed) != numeric_version(config['declared_version']):
            raise ValueError('CPython runtime version mismatch: ' + file)
        expected_status = 'matched-runtime-probe' if observed else 'build-declaration-only'
        if row.get('version_status') != expected_status:
            raise ValueError('Misleading CPython version status: ' + file)
    if report.get('components_not_collected') != sorted(set(COMPONENTS) - {r['component'] for r in rows.values()}):
        raise ValueError('Incorrect CPython component presence summary')
    require_runtime_probes(report)
    return report


def public_summary(report):
    """獨立 annotation 的小型摘要，避免擠進既有原生身分摘要後遭平台截斷。"""
    keys = ('file', 'component', 'role', 'file_version', 'declared_version', 'observed_version',
            'version_status', 'loaded_source_matched', 'source_sha256')
    return dict(check='cpython-components', cpython_version=report['cpython_version'],
                applicable=report['applicable'], files=[{k:r[k] for k in keys} for r in report['files']],
                notices=[{k:r[k] for k in ('component', 'path', 'sha256')} for r in report['notices']],
                redistribution_approved=False, runtime_sbom_complete=False)

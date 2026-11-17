"""Qt 發布來源與實際建置環境的版本對應，不核准再散布。

來源使用官方 tag 解參照後的固定提交，以及 Qt supermodule 的完整 gitlink。
只證明發布版來源位置與版本一致；不能據此聲稱 wheel 可逐位元組重建、
沒有上游建置修補，或完整 LGPL／原生相依義務已關閉。
"""
import hashlib
from importlib import metadata
import json
import os
import platform
import re
from pathlib import Path

from build_provenance import sha256

ROOT = Path(__file__).resolve().parents[1]
VERSION = '6.12.0'
STAGED = 'qt-sources.json'


def load_catalog(root=ROOT):
    """離線重驗原始版本宣告、官方 tag 與 gitlink，不以套件版號猜 Qt 版本。"""
    root = Path(root)
    directory = root/'packaging/qt'/VERSION
    catalog = json.loads((directory/'catalog.json').read_text(encoding='utf-8'))
    if catalog.get('schema_version') != 1 or catalog.get('version') != VERSION:
        raise ValueError('Unsupported Qt source catalog')
    if catalog.get('redistribution_approved') is not False or catalog.get('runtime_sbom_complete') is not False:
        raise ValueError('Qt source map cannot approve redistribution')
    for row in catalog['evidence_files']:
        path = directory/row['path']
        if (not path.resolve().is_relative_to(directory.resolve()) or path.is_symlink()
                or sha256(path) != row['sha256'] or path.stat().st_size != row['bytes']):
            raise ValueError('Qt source evidence fingerprint mismatch')
        if 'git_blob' in row:
            data = path.read_bytes()
            blob = hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
            if blob != row['git_blob']:
                raise ValueError('Qt source Git blob mismatch')
    refs = json.loads((directory/'official-refs.json').read_text(encoding='utf-8'))
    for repo, field in (('qt/qt5', 'qt5_commit'), ('qt/qtbase', 'qtbase_commit'),
                        ('pyside/pyside-setup', 'pyside_commit')):
        source = refs[repo]
        obj = source['ref']['object']
        if source['ref']['ref'] != 'refs/tags/'+catalog['tag']:
            raise ValueError('Qt official release tag mismatch')
        for tag in source['tags']:
            if obj['type'] != 'tag' or obj['sha'] != tag['sha']:
                raise ValueError('Qt annotated tag chain mismatch')
            obj = tag['object']
        if (obj['type'] != 'commit' or obj['sha'] != catalog[field]
                or source['commit'] != obj['sha'] or not re.fullmatch('[0-9a-f]{40}', obj['sha'])):
            raise ValueError('Qt source commit mismatch')
    modules = {r['path']:r['sha'] for r in refs['qt/qt5']['tree']['tree'] if r['type'] == 'commit'}
    if modules != catalog['modules'] or modules.get('qtbase') != catalog['qtbase_commit']:
        raise ValueError('Qt source module gitlink mismatch')
    qt_conf = (directory/'sources/qtbase/.cmake.conf').read_text(encoding='utf-8')
    if not re.search(r'set\(QT_REPO_MODULE_VERSION\s+"'+re.escape(VERSION)+r'"\)', qt_conf):
        raise ValueError('Qt source version declaration mismatch')
    for module in ('pyside', 'shiboken'):
        text = (directory/'sources/pyside-setup/sources'/(module+'6')/'.cmake.conf').read_text(encoding='utf-8')
        values = [re.search(r'set\('+module+'_'+part+r'_VERSION\s+"(\d+)"\)', text)
                  for part in ('MAJOR', 'MINOR', 'MICRO')]
        if not all(values) or '.'.join(v.group(1) for v in values) != VERSION:
            raise ValueError('PySide source version declaration mismatch')
    inventory = json.loads((root/'src/desktop_app/data/licenses/windows/inventory.json').read_text(encoding='utf-8'))
    packages = {p['name']:p for p in inventory['packages']}
    if {p['name'] for p in catalog['windows_wheels']} != {'pyside6-essentials', 'shiboken6'}:
        raise ValueError('Incomplete Qt Windows wheel correspondence')
    for wheel in catalog['windows_wheels']:
        if wheel['version'] != VERSION or any(packages[wheel['name']][k] != v for k, v in wheel.items()):
            raise ValueError('Qt Windows wheel correspondence differs from locked inventory')
    return catalog


def observe():
    """在建置解譯器讀取真正 Qt runtime；本機 Linux 觀測不能冒充 Windows。"""
    from PySide6 import QtCore
    return dict(platform=platform.system(), qt_version=QtCore.qVersion(),
                pyside_version=metadata.version('pyside6-essentials'),
                shiboken_version=metadata.version('shiboken6'),
                qt_build=QtCore.QLibraryInfo.build(),
                library_version=QtCore.QLibraryInfo.version().toString(),
                shared_build=QtCore.QLibraryInfo.isSharedBuild(),
                debug_build=QtCore.QLibraryInfo.isDebugBuild(),
                core_extension_sha256=sha256(QtCore.__file__))


def stage(root, output, observation=None):
    """產生隨包的固定來源連結與建置觀測，並由既有資產 manifest 覆蓋其 hash。"""
    catalog = load_catalog(root)
    observed = observe() if observation is None else observation
    if any(observed.get(key) != VERSION for key in ('qt_version', 'pyside_version', 'shiboken_version')):
        raise ValueError('Actual Qt/PySide runtime differs from pinned release sources')
    sources = {module:dict(commit=commit, repository='https://github.com/qt/'+module,
                archive='https://codeload.github.com/qt/'+module+'/tar.gz/'+commit)
               for module, commit in catalog['modules'].items()}
    report = dict(schema_version=1, check='qt-release-sources', version=VERSION,
                  qt5_commit=catalog['qt5_commit'], qtbase_commit=catalog['qtbase_commit'],
                  pyside_commit=catalog['pyside_commit'],
                  pyside_archive='https://codeload.github.com/pyside/pyside-setup/tar.gz/'+catalog['pyside_commit'],
                  qt5_archive='https://codeload.github.com/qt/qt5/tar.gz/'+catalog['qt5_commit'],
                  modules=sources, observed=observed,
                  catalog_sha256=sha256(Path(root)/'packaging/qt'/VERSION/'catalog.json'),
                  release_source_map_verified=True, binary_reproduction_verified=False,
                  upstream_build_patch_set_verified=False,
                  redistribution_approved=False, runtime_sbom_complete=False)
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def public_summary(report):
    """獨立小型 CI 摘要，保留平台與證據界線，不擠入既有原生來源摘要。"""
    keys = ('check', 'version', 'qt5_commit', 'qtbase_commit', 'pyside_commit', 'observed',
            'catalog_sha256', 'release_source_map_verified', 'binary_reproduction_verified',
            'upstream_build_patch_set_verified', 'redistribution_approved', 'runtime_sbom_complete')
    return {k:report[k] for k in keys}


def publish_annotation(report):
    """控制端重送子程序的小型 Qt 摘要；一般 CLI 不額外輸出 JSON。"""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    message = json.dumps(public_summary(report), ensure_ascii=False, separators=(',', ':'))
    if len(message.replace('%', '%25').encode('utf-8')) > 3900:
        raise ValueError('Qt public summary exceeds annotation budget')
    print('::notice title=Qt release sources::'+message.replace('%', '%25')
          .replace('\n', '%0A').replace('\r', '%0D'))

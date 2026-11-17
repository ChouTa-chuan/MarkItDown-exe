"""從基本 build 環境準備真正 runtime 授權與能力清單，禁止混入完整開發環境。"""
import argparse
from importlib import metadata
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import shutil
import sys
import sysconfig
import tempfile
import tomllib

from cryptography_notice import stage as stage_crypto_notice
from packaging.utils import canonicalize_name
from packaging_profiles import ROOT, read_lock, verify_profiles
from build_provenance import bootloader_notices, is_notice_entry
from base_own_license import OWN_PACKAGE, OWN_LICENSE, stage_own_license, verify_own_license
from qt_sources import STAGED as QT_SOURCES, stage as stage_qt_sources, publish_annotation as publish_qt_sources


QT_NOTICE = 'qt-lgpl-notice.md'
OWN_LICENSE_LINE = '本程式自有部分採 MIT，全文見 '+OWN_LICENSE+'。'
QT_NOTICE_LINE = ('Qt／LGPL-3.0 使用說明（授權原文位置、原始碼取得方式、如何替換 Qt 程式庫）見 licenses/'+QT_NOTICE+'。')


def base_guide(version, notices, native):
    """組出隨包 third-party.md 的各行；抽成函式以便測試輸出內容。"""
    guide = ['# 基本 profile 第三方來源與限制', '', f'程式 {version}；38 個第三方 runtime，另有本地專案與 Python 原授權。',
             '', 'licenses/installed 保存實際建置環境的 runtime METADATA 與可取得的原始授權；licenses/native 保存實際 Analysis 的系統來源與 copyright。',
             '', 'Magika 仍使用 CPU ONNX Runtime；沒有 RapidOCR OCR 模型。原生 Tesseract 尚未整合，本包只驗核心功能，未達完整基本版離線 OCR／Windows 發行門檻。',
             '', QT_NOTICE_LINE,
             '', OWN_LICENSE_LINE,
             '', '實際原文與 binary 來源證據不取代完整再散布／Qt 義務或最終 SBOM 審核。部分套件無 wheel 內原文，仍可對照原 Windows 上位授權資料，不宣稱已全部審查。', '', '| 套件 | 版本 |', '| --- | --- |']
    guide += [f'| {p["name"]} | {p["version"]} |' for p in notices]
    if native:
        guide = [line.replace('原生 Tesseract 尚未整合，本包只驗核心功能，未達完整基本版離線 OCR／Windows 發行門檻。',
                              '已內含 Tesseract 與四語模型，原文／來源位於 native/；Linux 開發包與 Windows 候選分開，完整 Windows 發行仍待驗。') for line in guide]
    return guide


def stage_qt_notice(source, staged):
    """在資產 hash 計算前放入 Qt 說明與實際版本／固定來源表；來源或 runtime 不符就失敗。"""
    shutil.copyfile(source/'licenses'/QT_NOTICE, staged/'licenses'/QT_NOTICE)
    report = stage_qt_sources(source.parents[2], staged/'licenses'/QT_SOURCES)
    publish_qt_sources(report)


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def refresh_manifest(directory):
    path = directory/'build-profile.json'
    profile = json.loads(path.read_text())
    profile['assets'] = {p.relative_to(directory).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(directory.rglob('*')) if p.is_file() and p != path}
    save_json(path, profile)


def attach_native(staged, native_assets, target):
    """原生 payload 必須符合真正建置平台；Windows 檔不能混進 Linux frozen 驗收。"""
    from desktop_app.bundled_ocr import validate_payload
    validate_payload(native_assets, expected_platform=target)
    shutil.copytree(native_assets, staged / 'native')
    validate_payload(staged / 'native', expected_platform=target)


def prepare(output, root=ROOT, *, native_assets=None):
    if output.exists(): raise FileExistsError(output)
    target = {'Linux':'linux', 'Windows':'windows'}.get(platform.system())
    if target is None or sys.version_info[:2] != (3, 12):
        raise ValueError('基本 profile 建置需要原生 Windows／Linux x64 CPython 3.12。')
    import struct
    if struct.calcsize('P') != 8 or platform.machine().lower() not in ('amd64', 'x86_64'):
        raise ValueError('目前只支援 x64 profile。')
    profiles = verify_profiles(root)['profiles']
    runtime = read_lock(root/profiles[target+'-runtime']['lock'])
    build = read_lock(root/profiles[target+'-build']['lock'])
    installed = {canonicalize_name(p.metadata['Name']):p.version for p in metadata.distributions()}
    expected_version = tomllib.loads((root/'pyproject.toml').read_text())['project']['version']
    if installed.get('markitdown-desktop') != expected_version:
        raise ValueError('請先安裝目前專案版本，再準備基本 profile 資產。')
    if set(installed) != set(build) | {'markitdown-desktop', 'markitdown', 'pip'}:
        raise ValueError('需要獨立且完整的基本 build 環境，不能使用開發包或缺建置套件。')
    if any(installed[name] != record['version'] for name, record in build.items()):
        raise ValueError('基本 build 版本不符。')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.base-assets-', dir=output.parent) as temporary:
        staged = Path(temporary)/'data'
        staged.mkdir()
        source = root/'src/desktop_app/data'
        for name in ['user-guide.md','ocr-models.json','ocr-four-languages.json','worker-health.png','worker-health.json',
                     'setup-chinese.png','setup-chinese.json','setup-japanese.png','setup-japanese.json','setup-korean.png','setup-korean.json']:
            shutil.copyfile(source/name, staged/name)
        for name in ['models','standards','markitdown']:
            shutil.copytree(source/'licenses'/name, staged/'licenses'/name)
        stage_qt_notice(source, staged)
        stage_own_license(root, staged)
        if native_assets is not None:
            attach_native(staged, Path(native_assets), target)
        python_license = next((p for p in [Path(sys.base_prefix)/'LICENSE.txt',Path(sysconfig.get_path('stdlib'))/'LICENSE.txt'] if p.is_file()), None)
        if python_license is None: raise ValueError('缺少實際 Python runtime 原授權。')
        destination = staged/'licenses/python-runtime/LICENSE.txt'
        destination.parent.mkdir(parents=True)
        shutil.copyfile(python_license, destination)
        bootloader_notices(staged/'licenses/bootloader')
        notices = []
        notice_root = staged/'licenses/installed'
        notice_root.mkdir()
        original_inventory = json.loads((source/'licenses/windows/inventory.json').read_text())
        original_packages = {item['name']:item for item in original_inventory['packages']}
        for name in sorted(set(runtime) | {'markitdown-desktop','markitdown'}):
            distribution = metadata.distribution(name)
            files = []
            package_root = notice_root/name
            package_root.mkdir()
            raw = distribution.read_text('METADATA')
            if raw is None: raise ValueError('缺少實際安裝 METADATA：'+name)
            (package_root/'METADATA').write_bytes(raw.encode('utf-8'))
            for entry in distribution.files or ():
                # 主程式 wheel 中的歷史 Windows 授權上位集合不再整份複製；
                # 第三方 runtime 各由自己的實際 distribution 保存原文。
                if name == 'markitdown-desktop': continue
                path = PurePosixPath(str(entry))
                # 某些 wheel 在 licenses 目錄內用 Apache-2.0.txt 等名稱，須連目錄一起判斷。
                if not is_notice_entry(path): continue
                original = Path(distribution.locate_file(entry))
                if not original.is_file() or original.stat().st_size > 5*1024**2: continue
                destination = package_root/'original'/Path(*path.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(original, destination)
                files.append(destination.relative_to(staged).as_posix())
            if name == OWN_PACKAGE:
                # 已隨包的自有 MIT 直接綁入清單，不再複製一份或僅靠名稱略過待審。
                files.append(OWN_LICENSE)
            supplements=[]
            for reference in original_packages.get(name,{}).get('supplemental_sources',[]):
                original = source/'licenses/windows'/reference['path']
                destination = staged/'licenses'/reference['path']
                destination.parent.mkdir(parents=True,exist_ok=True)
                shutil.copyfile(original,destination)
                supplements.append(dict(reference,path=destination.relative_to(staged).as_posix()))
            notices.append(dict(name=name,version=distribution.version,notice_files=files,supplemental_sources=supplements))
        stage_crypto_notice(root, staged, notices)
        verify_own_license(staged, notices, root=root)
        save_json(notice_root/'manifest.json', dict(scope='Actual installed runtime metadata/notices, not final redistribution clearance', packages=notices))
        shutil.copyfile(root/profiles[target+'-runtime']['lock'], staged/'base-runtime-lock.txt')
        guide = base_guide(installed['markitdown-desktop'], notices, native_assets is not None)
        (staged/'third-party.md').write_text('\n'.join(guide)+'\n', encoding='utf-8')
        save_json(staged/'build-profile.json', dict(schema_version=2 if native_assets is not None else 1,id='base',source_version=installed['markitdown-desktop'],
            platform=target,python=platform.python_version(),native_ocr_required=True,native_ocr_integrated=native_assets is not None,
            native_ocr_manifest='native/manifest.json' if native_assets is not None else None,release_ready=False,
            runtime_packages={name:record['version'] for name,record in runtime.items()},
            local_packages={name:installed[name] for name in ['markitdown-desktop','markitdown']},
            notice_packages=len(notices), assets={}))
        refresh_manifest(staged)
        shutil.move(str(staged), output)
    return json.loads((output/'build-profile.json').read_text())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--native-assets', type=Path, help='已離線驗證且與建置平台相符的四語 OCR payload')
    args = parser.parse_args()
    result = prepare(args.output, native_assets=args.native_assets)
    print('Prepared base assets:', len(result['runtime_packages']), 'runtime packages;', len(result['assets']), 'assets')

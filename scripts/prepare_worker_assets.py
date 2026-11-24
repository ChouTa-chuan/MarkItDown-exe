"""保存實際 worker 建置環境的 metadata／原授權及 CPython 授權，不改寫既有清單。"""
import argparse
from importlib import metadata
from typing import NamedTuple
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import sys
import sysconfig
import subprocess
from build_provenance import bootloader_notices, distribution_sources, is_notice_entry, sha256


# 固定 CPU 候選的 METADATA 與 repo 原文共同約束套件；原文已在 worker 的 licenses 內。
WINDOWS_LICENSES = 'licenses/windows'
# 鍵是原文名（supplemental/<鍵>.txt）；owner 是實際安裝且持有該原文的套件（同一列可有多份原文）；
# url 含上游 commit，上游檔名取自 url 最後一段；sha256 與 size 為原文位元組。
# 結構說明見 docs/development-records/runs/b3-1-libyaml-paddleocr-notices-2026-11-21/README.md。
class WorkerNoticePin(NamedTuple):
    owner: str
    version: str
    metadata_sha256: str
    url: str
    sha256: str
    size: int


WORKER_NOTICE_PINS = {
    'flatbuffers': WorkerNoticePin(
        'flatbuffers', '25.12.19', '9f38239f96faa21522a6aadab6912e1e560708bbe9c9f696a0679c9403fa089e',
        'https://raw.githubusercontent.com/google/flatbuffers/7e163021e59cca4f8e1e35a7c828b5c6b7915953/LICENSE',
        'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30', 11358),
    'rapidocr-onnxruntime': WorkerNoticePin(
        'rapidocr-onnxruntime', '1.4.4', '1ac15bed7c7fb77d3fac58c2aba0a4d3e2da48de5c65badd3503900acebcf1df',
        'https://raw.githubusercontent.com/RapidAI/RapidOCR/86ae3f5079df3422c1829cd84baf19bc8a7a9453/LICENSE',
        '3e0af25fdd06aa9586ae97adb00ea927ebe5a3805ac77d2d3a81ce5f55693333', 11422),
    # PaddleOCR 的權重與 ONNX 由 rapidocr 套件內附；採 v4 模型索引同 commit 的 v2.9.1 原文。
    'paddleocr': WorkerNoticePin(
        'rapidocr-onnxruntime', '1.4.4', '1ac15bed7c7fb77d3fac58c2aba0a4d3e2da48de5c65badd3503900acebcf1df',
        'https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/07603421c20a96bb94bb87d0c4211032527ae706/LICENSE',
        'ff6311c56c1b22c9209c96cc8afc16da91c24ee55a15e14ebc46fe1960dbd856', 11438),
    # LibYAML 0.2.5 靜態併入 PyYAML 的 Windows .pyd；版本依據為上游建置設定，不是執行期觀測。
    # 擁有者 METADATA 雜湊取 prepare 實際寫入的 LF 正規化內容（wheel 原檔為 CRLF，見 README）。
    'libyaml': WorkerNoticePin(
        'pyyaml', '6.0.3', '03c3b415ed38d09faedc49360e930769b40c58f68585e6de00e2e4916a858d34',
        'https://raw.githubusercontent.com/yaml/libyaml/2c891fc7a770e8ba2fec34fc6b545c672beb37e6/License',
        'c40112449f254b9753045925248313e9270efa36d226b22d82d4cc6c43c57f29', 1101),
    # B3-2a：Pillow 13.0.0 的 dav1d 1.5.3（靜態併入 _avif.pyd）與 Raqm 0.11.0（Pillow 內附原始碼編入 _imagingft.pyd）。
    # 版本依據與綁定說明見 docs/development-records/runs/b3-2a-pillow-pyclipper-notices-2026-11-21/README.md。
    'dav1d': WorkerNoticePin(
        'pillow', '13.0.0', 'dba7fdfe24e302f46bae562f55d66cc367c0618abae9894a1ebec93dc8f0e511',
        'https://raw.githubusercontent.com/videolan/dav1d/b546257f770768b2c88258c533da38b91a06f737/COPYING',
        'dd92c3c2247c5651606fc23a5e2d6a1ebc5ace9a3e49cbde0e12f05ad1cb1ee5', 1317),
    'raqm': WorkerNoticePin(
        'pillow', '13.0.0', 'dba7fdfe24e302f46bae562f55d66cc367c0618abae9894a1ebec93dc8f0e511',
        'https://raw.githubusercontent.com/HOST-Oman/libraqm/08ee1537e63f93bf926498e12b12ed15ee383216/COPYING',
        'f6baa5c872ed0c35cde377735f930d97a23e08065d87cf34d766b3aad5beed1e', 1180),
    # B3-2a 續：Pillow 的 libaom 3.14.1（靜態編入 _avif.pyd）LICENSE 與 PATENTS，來源為 aom 標籤 v3.14.1 的固定 commit。
    'libaom': WorkerNoticePin(
        'pillow', '13.0.0', 'dba7fdfe24e302f46bae562f55d66cc367c0618abae9894a1ebec93dc8f0e511',
        'https://aomedia.googlesource.com/aom/+/03087864cf4bea6abb0d28f95cf7843511413d8f/LICENSE?format=TEXT',
        '4764a286d8b2faeaf42f4418e7d7a28d58fc8fd4d00a3d0a7f44b0a4099de7f2', 1316),
    'libaom-PATENTS': WorkerNoticePin(
        'pillow', '13.0.0', 'dba7fdfe24e302f46bae562f55d66cc367c0618abae9894a1ebec93dc8f0e511',
        'https://aomedia.googlesource.com/aom/+/03087864cf4bea6abb0d28f95cf7843511413d8f/PATENTS?format=TEXT',
        '661fb8e504744e95587b556b94a58343448300606a41bea8c7a9b97125696e61', 5701),
    # B3-2a：pyclipper 1.4.0 的 Clipper 6.4.2（靜態編入 _pyclipper.pyd）；檔頭第 1–32 行為 clipper.hpp 的著作權與授權聲明，url 指向整檔。
    'clipper-header': WorkerNoticePin(
        'pyclipper', '1.4.0', '2a2d7b4ef4dd2764ee10701dd84741876680af346570dd8fac922795eb9ddf91',
        'https://raw.githubusercontent.com/fonttools/pyclipper/f998920369565dca56d346bb30c5741e273f0b9b/src/clipper.hpp',
        '8fa62835d1b88be098193df53e921475d6a7119a3f3de8046eed81b9ffa23f67', 2624),
    'bsl-1.0': WorkerNoticePin(
        'pyclipper', '1.4.0', '2a2d7b4ef4dd2764ee10701dd84741876680af346570dd8fac922795eb9ddf91',
        'https://raw.githubusercontent.com/boostorg/boost/1bed2b0712b2119f20d66c5053def9173c8462a5/LICENSE_1_0.txt',
        'c9bff75738922193e67fa726fa225535870d2aa1059f91452c411736284ad566', 1338),
    # B3-2b：OpenCV 5.0.0.93 的 cv2.pyd 靜態編入 zlib 1.3.2 與 libpng 1.6.57（Windows）；wheel 原文只標示 Linux／macOS 段落。
    # 版本依據：hosted Windows run 44755140396 以 cv2.getBuildInformation() 觀測（同一 cv2.pyd sha256）。
    'opencv-zlib': WorkerNoticePin(
        'opencv-python', '5.0.0.93', '20749df4e7500c53075dee344cd02f63d4df0dce93526e49e7e1c90fbc094e3e',
        'https://raw.githubusercontent.com/madler/zlib/da607da739fa6047df13e66a2af6b8bec7c2a498/LICENSE',
        'e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2', 1002),
    'opencv-libpng': WorkerNoticePin(
        'opencv-python', '5.0.0.93', '20749df4e7500c53075dee344cd02f63d4df0dce93526e49e7e1c90fbc094e3e',
        'https://raw.githubusercontent.com/pnggroup/libpng/95ab3fdca83ea294efd3b092e9a53c5a39886444/LICENSE',
        'bdb0a645ea18c60507d0368379b1ac5474b92255fcc2d115e07486a7672ba526', 5345),
}


def worker_notice_bindings(assets, packages, locked=None):
    """核對擁有者的 METADATA、版本、固定上游來源與原文位元組；回傳 {原文名: (擁有者, 路徑, 雜湊)}。"""
    root = assets/WINDOWS_LICENSES
    inventory = json.loads((root/'inventory.json').read_text(encoding='utf-8'))
    sources = json.loads((root/'supplemental/sources.json').read_text(encoding='utf-8'))
    bindings = {}
    for key, pin in WORKER_NOTICE_PINS.items():
        name = pin.owner
        installed = [row for row in packages if row['name'] == name]
        records = [row for row in inventory['packages'] if row['name'] == name]
        original = f'supplemental/{key}.txt'
        path = root/original
        meta = assets/'installed'/name/'METADATA'
        if (len(installed) != 1 or installed[0]['version'] != pin.version
                or not meta.is_file() or sha256(meta) != pin.metadata_sha256):
            raise ValueError(f'Worker notice package/version mismatch: {name} {pin.version}')
        if not path.is_file() or path.stat().st_size != pin.size or sha256(path) != pin.sha256:
            raise ValueError(f'Worker original missing or changed: {original}')
        expected = dict(name=key, url=pin.url, sha256=pin.sha256, bytes=pin.size)
        # 擁有者列必須恰好帶一筆此原文；原文只能由一個列宣告（唯一擁有者）。
        claims = [row['name'] for row in inventory['packages'] for item in row['supplemental_sources']
                  if item.get('path') == original]
        if (len(records) != 1 or records[0]['version'] != pin.version
                or [dict(item) for item in records[0]['supplemental_sources'] if item.get('path') == original]
                != [dict(expected, path=original)]
                or [row for row in sources if row['name'] == key] != [expected]
                or inventory['files'].get(original) != pin.sha256 or claims != [name]):
            raise ValueError(f'Worker notice source mismatch: {key} {pin.version}')
        if locked is not None and (name not in locked or locked[name]['version'] != pin.version
                                  or records[0]['wheel_sha256'] not in locked[name]['hashes']):
            raise ValueError(f'Worker notice lock mismatch: {name} {pin.version}')
        bindings[key] = (name, f'{WINDOWS_LICENSES}/{original}', pin.sha256)
    return bindings


def verify_worker_notice_bindings(assets, manifest):
    """重驗原文與唯一擁有者，拒絕只重算 manifest 雜湊的錯綁。"""
    packages = manifest['packages']
    for key, (name, path, digest) in worker_notice_bindings(assets, packages).items():
        owners = [row['name'] for row in packages
                  for notice in (*row['notice_files'], *(item['path'] for item in row.get('supplemental_sources', [])))
                  if notice.casefold() == path.casefold()]
        package = next(row for row in packages if row['name'] == name)
        if owners != [name] or path not in package['notice_files'] or manifest['files'].get(path) != digest:
            raise ValueError(f'Invalid worker notice binding: {key}')


def prepare(output, project):
    from packaging_profiles import read_lock

    if output.exists():
        raise ValueError('Output exists; choose a fresh worker assets directory')
    output.mkdir(parents=True)
    runtime_license=next((path for path in (Path(sys.base_prefix)/'LICENSE.txt',Path(sysconfig.get_path('stdlib'))/'LICENSE.txt') if path.is_file()),None)
    if runtime_license is None:
        raise ValueError('Actual Python runtime license missing')
    (output/'python-runtime').mkdir()
    shutil.copyfile(runtime_license,output/'python-runtime/LICENSE.txt')
    shutil.copytree(project/'src/desktop_app/data/licenses',output/'licenses')
    bootloader_notices(output/'bootloader')
    stored={}
    packages=[]
    for distribution in sorted(metadata.distributions(),key=lambda value:value.metadata['Name'].lower()):
        name=re.sub('[-_.]+','-',distribution.metadata['Name']).lower()
        paths=[]
        raw=distribution.read_text('METADATA')
        if raw is not None:
            target=output/'installed'/name/'METADATA'
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw.encode('utf-8'))
            stored[target.relative_to(output).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
        for entry in distribution.files or ():
            relative=PurePosixPath(str(entry))
            if relative.is_absolute() or '..' in relative.parts:
                continue
            if not is_notice_entry(relative):
                continue
            source=Path(distribution.locate_file(entry))
            if not source.is_file() or source.stat().st_size>5*1024**2:
                continue
            target=output/'installed'/name/'original'/Path(*relative.parts)
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(source,target)
            key=target.relative_to(output).as_posix()
            stored[key]=hashlib.sha256(target.read_bytes()).hexdigest()
            paths.append(key)
        packages.append(dict(name=name,version=distribution.version,notice_files=paths))
    locked = read_lock(project/'packaging/profiles/cpu-windows-build.txt')
    bindings = worker_notice_bindings(output, packages, locked)
    for name, path, digest in bindings.values():
        row = next(row for row in packages if row['name'] == name)
        row['notice_files'].append(path)
        stored[path] = digest
    manifest=dict(scope='Actual installed build-environment notices plus existing locked dependency superset; native final release clearance remains pending',packages=packages,files=stored)
    (output/'installed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Prepared actual installed notices:',len(packages),'packages,',len(stored),'files')


def native_notices(binaries, output):
    """從實際 Analysis binary 來源保存 Debian 原生授權；wheel／CPython 另有原文。"""
    output.mkdir(parents=True,exist_ok=False)
    packages = {}
    records = []
    sources = []
    site=Path(sysconfig.get_path('purelib')).resolve()
    interpreter=Path(sys.base_prefix).resolve()
    owners=distribution_sources()
    for destination,source,kind in binaries:
        # Analysis 在 Windows 使用反斜線；跨平台證據一律保存 POSIX 相對路徑。
        destination=destination.replace('\\','/')
        path=Path(source).resolve()
        if path.is_relative_to(site):
            origin='installed-wheel'
            package=None
        elif path.is_relative_to(interpreter):
            origin='python-runtime'
            package=None
        else:
            origin='system-native'
            package=None
            for candidate in (str(path),str(path).removeprefix('/usr') if str(path).startswith('/usr/lib/') else '/usr'+str(path)):
                if sys.platform!='linux':break
                query=subprocess.run(['dpkg-query','-S',candidate],capture_output=True,text=True,timeout=5)
                if query.returncode==0:
                    package=query.stdout.split(': ',1)[0].split(':',1)[0]
                    break
            if package is not None and re.fullmatch('[a-z0-9][a-z0-9.+-]*',package):
                license_path=Path('/usr/share/doc')/package/'copyright'
                if license_path.is_file():
                    target=output/(package+'-copyright.txt')
                    if not target.exists():shutil.copyfile(license_path,target)
                    packages[package]=dict(file=target.name,sha256=hashlib.sha256(target.read_bytes()).hexdigest())
            else:package=None
        records.append(dict(file=destination,source_basename=path.name,origin=origin,system_package=package,
                            source_sha256=sha256(path),source_bytes=path.stat().st_size,
                            distributions=owners.get(path,[])))
        sources.append(path)
    # 非 wheel 來源的原生檔另記來源目錄、版本資源與簽章，供判定發行者；wheel 來源已有套件對照。
    from native_identity import describe
    identities = describe([path for path, row in zip(sources, records) if row['origin'] != 'installed-wheel'])
    for path, row in zip(sources, records):
        row.update(identities.get(path, {}))
    report=dict(schema_version=2,scope='Actual bundled binaries and native package copyright evidence; final Windows/native release clearance remains pending',
                files=records,native_copyrights=packages)
    # 此時已有真正 Analysis 來源／PE 身分，才產生逐檔 CPython 元件證據；
    # Linux 只記不適用，不把系統函式庫當成 Windows CPython 隨附元件。
    from cpython_components import REPORT, write_inventory
    write_inventory(records, output/REPORT)
    report.update(cpython_components=REPORT, cpython_components_sha256=sha256(output/REPORT))
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    prepare(args.output,Path(__file__).resolve().parents[1])

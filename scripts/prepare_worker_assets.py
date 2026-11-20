"""保存實際 worker 建置環境的 metadata／原授權及 CPython 授權，不改寫既有清單。"""
import argparse
from importlib import metadata
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
WORKER_NOTICE_PINS = {
    'flatbuffers': (
        '25.12.19', 'google/flatbuffers/7e163021e59cca4f8e1e35a7c828b5c6b7915953',
        '9f38239f96faa21522a6aadab6912e1e560708bbe9c9f696a0679c9403fa089e',
        'cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30',
    ),
    'rapidocr-onnxruntime': (
        '1.4.4', 'RapidAI/RapidOCR/86ae3f5079df3422c1829cd84baf19bc8a7a9453',
        '1ac15bed7c7fb77d3fac58c2aba0a4d3e2da48de5c65badd3503900acebcf1df',
        '3e0af25fdd06aa9586ae97adb00ea927ebe5a3805ac77d2d3a81ce5f55693333',
    ),
}


def worker_notice_bindings(assets, packages, locked=None):
    """核對同版 wheel 的 METADATA、既有來源目錄與隨包原文字節。"""
    root = assets/WINDOWS_LICENSES
    inventory = json.loads((root/'inventory.json').read_text(encoding='utf-8'))
    sources = json.loads((root/'supplemental/sources.json').read_text(encoding='utf-8'))
    bindings = {}
    for name, (version, source, metadata_hash, notice_hash) in WORKER_NOTICE_PINS.items():
        installed = [row for row in packages if row['name'] == name]
        records = [row for row in inventory['packages'] if row['name'] == name]
        original = f'supplemental/{name}.txt'
        path = root/original
        meta = assets/'installed'/name/'METADATA'
        if (len(installed) != 1 or installed[0]['version'] != version
                or not meta.is_file() or sha256(meta) != metadata_hash):
            raise ValueError(f'Worker notice package/version mismatch: {name} {version}')
        if not path.is_file() or sha256(path) != notice_hash:
            raise ValueError(f'Worker original missing or changed: {original}')
        expected = dict(name=name, url=f'https://raw.githubusercontent.com/{source}/LICENSE',
                        sha256=notice_hash, bytes=path.stat().st_size)
        if (len(records) != 1 or records[0]['version'] != version
                or records[0]['supplemental_sources'] != [dict(expected, path=original)]
                or [row for row in sources if row['name'] == name] != [expected]
                or inventory['files'].get(original) != notice_hash):
            raise ValueError(f'Worker notice source mismatch: {name} {version}')
        if locked is not None and (name not in locked or locked[name]['version'] != version
                                  or records[0]['wheel_sha256'] not in locked[name]['hashes']):
            raise ValueError(f'Worker notice lock mismatch: {name} {version}')
        bindings[name] = (f'{WINDOWS_LICENSES}/{original}', notice_hash)
    return bindings


def verify_worker_notice_bindings(assets, manifest):
    """重驗原文與唯一擁有者，拒絕只重算 manifest 雜湊的錯綁。"""
    packages = manifest['packages']
    for name, (path, digest) in worker_notice_bindings(assets, packages).items():
        owners = [row['name'] for row in packages
                  for notice in (*row['notice_files'], *(item['path'] for item in row.get('supplemental_sources', [])))
                  if notice.casefold() == path.casefold()]
        package = next(row for row in packages if row['name'] == name)
        if owners != [name] or path not in package['notice_files'] or manifest['files'].get(path) != digest:
            raise ValueError(f'Invalid worker notice binding: {name}')


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
    for row in packages:
        if row['name'] in bindings:
            path, digest = bindings[row['name']]
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

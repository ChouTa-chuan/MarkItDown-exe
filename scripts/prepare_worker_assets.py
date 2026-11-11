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


def prepare(output, project):
    if output.exists():raise ValueError('Output exists; choose a fresh worker assets directory')
    output.mkdir(parents=True)
    runtime_license=next((path for path in (Path(sys.base_prefix)/'LICENSE.txt',Path(sysconfig.get_path('stdlib'))/'LICENSE.txt') if path.is_file()),None)
    if runtime_license is None:raise ValueError('Actual Python runtime license missing')
    (output/'python-runtime').mkdir();shutil.copyfile(runtime_license,output/'python-runtime/LICENSE.txt')
    shutil.copytree(project/'src/desktop_app/data/licenses',output/'licenses')
    bootloader_notices(output/'bootloader')
    stored={};packages=[]
    for distribution in sorted(metadata.distributions(),key=lambda value:value.metadata['Name'].lower()):
        name=re.sub('[-_.]+','-',distribution.metadata['Name']).lower()
        paths=[]
        raw=distribution.read_text('METADATA')
        if raw is not None:
            target=output/'installed'/name/'METADATA';target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(raw.encode('utf-8'));stored[target.relative_to(output).as_posix()]=hashlib.sha256(target.read_bytes()).hexdigest()
        for entry in distribution.files or ():
            relative=PurePosixPath(str(entry))
            if relative.is_absolute() or '..' in relative.parts:continue
            if not is_notice_entry(relative):continue
            source=Path(distribution.locate_file(entry))
            if not source.is_file() or source.stat().st_size>5*1024**2:continue
            target=output/'installed'/name/'original'/Path(*relative.parts)
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target)
            key=target.relative_to(output).as_posix();stored[key]=hashlib.sha256(target.read_bytes()).hexdigest();paths.append(key)
        packages.append(dict(name=name,version=distribution.version,notice_files=paths))
    manifest=dict(scope='Actual installed build-environment notices plus existing locked dependency superset; native final release clearance remains pending',packages=packages,files=stored)
    (output/'installed-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    print('Prepared actual installed notices:',len(packages),'packages,',len(stored),'files')


def native_notices(binaries, output):
    """從實際 Analysis binary 來源保存 Debian 原生授權；wheel／CPython 另有原文。"""
    output.mkdir(parents=True,exist_ok=False)
    packages={};records=[]
    site=Path(sysconfig.get_path('purelib')).resolve()
    interpreter=Path(sys.base_prefix).resolve()
    owners=distribution_sources()
    for destination,source,kind in binaries:
        path=Path(source).resolve()
        if path.is_relative_to(site):origin='installed-wheel';package=None
        elif path.is_relative_to(interpreter):origin='python-runtime';package=None
        else:
            origin='system-native';package=None
            for candidate in (str(path),str(path).removeprefix('/usr') if str(path).startswith('/usr/lib/') else '/usr'+str(path)):
                if sys.platform!='linux':break
                query=subprocess.run(['dpkg-query','-S',candidate],capture_output=True,text=True,timeout=5)
                if query.returncode==0:
                    package=query.stdout.split(': ',1)[0].split(':',1)[0];break
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
    report=dict(schema_version=2,scope='Actual bundled binaries and native package copyright evidence; final Windows/native release clearance remains pending',
                files=records,native_copyrights=packages)
    (output/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();prepare(args.output,Path(__file__).resolve().parents[1])

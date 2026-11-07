"""把本機 frozen worker 組成 C01 ZIP／描述；僅開發離線驗收，不簽署或發布。"""
import argparse
import hashlib
import json
from pathlib import Path
import platform
import stat
import zipfile

from desktop_app.components.contracts import ComponentSpec, relative_path
from desktop_app.components.registry import canonical_spec
from desktop_app.component_workers import protocol as wire


def package(bundle, output):
    bundle=bundle.resolve()
    if output.exists():raise ValueError('Output exists; choose a fresh package output')
    files=[];sources=[]
    for path in sorted(bundle.rglob('*')):
        if path.is_dir():
            if path.is_symlink():raise ValueError('Directory links are not supported')
            continue
        relative=path.relative_to(bundle).as_posix();relative_path(relative)
        resolved=path.resolve()
        if not resolved.is_relative_to(bundle) or not resolved.is_file():raise ValueError('Unsafe bundle file/link')
        digest=hashlib.sha256()
        with resolved.open('rb') as source:
            while block:=source.read(65536):digest.update(block)
        files.append(dict(path=relative,size=resolved.stat().st_size,sha256=digest.hexdigest()))
        sources.append((relative,resolved))
    output.mkdir(parents=True)
    notice=output/'NOTICE.txt'
    notice.write_text('Development-only ONNX CPU worker. No production catalog/key or release is published.\n'
        'Contains RapidOCR/PP-OCR, ONNX Runtime, Python and native runtime dependencies.\n'
        'See _internal/worker-assets for actual installed original notices, native notices and the dependency superset.\n'
        'Application source license and final native redistribution clearance remain pending.\n',encoding='utf-8')
    data=notice.read_bytes();files.append(dict(path='NOTICE.txt',size=len(data),sha256=hashlib.sha256(data).hexdigest()))
    sources.append(('NOTICE.txt',notice))
    archive=output/'onnx-cpu-ocr-development.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=False) as target:
        for relative,path in sources:
            item=zipfile.ZipInfo(relative);item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=(stat.S_IFREG | (0o755 if path.stat().st_mode & 0o111 else 0o644)) << 16
            with path.open('rb') as source,target.open(item,'w') as destination:
                while block:=source.read(65536):destination.write(block)
    digest=hashlib.sha256()
    with archive.open('rb') as source:
        while block:=source.read(65536):digest.update(block)
    system=platform.system().lower();arch=platform.machine().lower()
    if arch in ('amd64','x86_64'):arch='x86_64'
    elif arch in ('aarch64','arm64'):arch='arm64'
    bounds=dict(minimum='0.5.0',maximum_exclusive='1.0.0')
    spec=ComponentSpec.from_dict(dict(schema_version=1,component_id=wire.COMPONENT_ID,version=wire.COMPONENT_VERSION,
        kind='engine',display_name='ONNX CPU OCR（開發選配，繁體品質未達標）',
        source_url='https://example.invalid/markitdown-development/onnx-cpu-ocr-development.zip',
        license_id='Multiple; development-only bundle, see NOTICE.txt',license_path='NOTICE.txt',
        package_sha256=digest.hexdigest(),download_bytes=archive.stat().st_size,
        unpacked_bytes=sum(item['size'] for item in files),files=files,
        capabilities=['ocr.onnx.cpu','ocr.text.experimental'],platforms=[system],architectures=[arch],
        app_versions=bounds,worker_protocols=dict(minimum='1.0.0',maximum_exclusive='2.0.0'),
        dependencies=[],resources=dict(ram_mib=768,vram_mib=0,disk_mib=(sum(item['size'] for item in files)+1024**2-1)//1024**2),
        health_check='onnx.cpu.health',required=False,signature=None))
    raw=canonical_spec(spec)
    (output/'component.json').write_text(json.dumps(spec.to_dict(),ensure_ascii=False,indent=2)+'\n')
    report=dict(component_id=spec.component_id,version=str(spec.version),protocol=wire.PROTOCOL,
                files=len(files),descriptor_bytes=len(raw.encode()),package_bytes=archive.stat().st_size,
                unpacked_bytes=spec.unpacked_bytes,sha256=spec.package_sha256,
                platform=system,architecture=arch,development_only=True,production_catalog_published=False,
                source_url_is_deliberately_non_downloadable=True)
    (output/'package-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();package(args.bundle,args.output)

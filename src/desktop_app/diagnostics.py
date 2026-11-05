"""Offline installation checks using the installed runtime, without external Python.

All input documents are generated samples. Reports contain check outcomes and
runtime versions, never the user's documents, credentials or environment dump.
"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import resources
import json
import multiprocessing
import os
from pathlib import Path
import platform
import sys
import tempfile


def sample_pdf(path):
    """A small native PDF; no test-only PDF writer needs to be bundled."""
    content=b'BT /F1 16 Tf 40 100 Td (INSTALLATION PDF CHECK 12345) Tj ET'
    objects=[b'<< /Type /Catalog /Pages 2 0 R >>',
             b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
             b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 600 200] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
             b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
             b'<< /Length '+str(len(content)).encode()+b' >>\nstream\n'+content+b'\nendstream']
    data=bytearray(b'%PDF-1.4\n');offsets=[0]
    for index,obj in enumerate(objects,1):
        offsets.append(len(data));data.extend(f'{index} 0 obj\n'.encode()+obj+b'\nendobj\n')
    start=len(data);data.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:data.extend(f'{offset:010d} 00000 n \n'.encode())
    data.extend(f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n'.encode())
    path.write_bytes(data)


def verify_help():
    root=Path(resources.files('desktop_app').joinpath('data'))
    for name in ('user-guide.md','third-party.md'):
        if len((root/name).read_text(encoding='utf-8'))<100:raise RuntimeError('Offline guide missing')
    inventory=json.loads((root/'licenses/windows/inventory.json').read_text(encoding='utf-8'))
    for name,expected in inventory['files'].items():
        actual=hashlib.sha256((root/'licenses/windows'/name).read_bytes()).hexdigest()
        if actual!=expected:raise RuntimeError('Bundled license inventory mismatch')
    if getattr(sys,'frozen',False) and not (root/'licenses/python-runtime/LICENSE.txt').is_file():
        raise RuntimeError('Python runtime license missing')
    return f"Offline guide; {inventory['package_count']} packages; {len(inventory['files'])} notice files"


def _convert(source,destination,backend='tesseract'):
    from .application import Runner
    from .core import Request,State
    from .resources import Policy,MIB
    result=Runner(Policy(budget=2048*MIB,reserve=0),max_resource_wait=10).run(
        Request(source,destination,device='cpu',cpu_threads=1,ocr_backend=backend))
    if result.state!=State.COMPLETED:raise RuntimeError(result.message)
    return destination.read_text(encoding='utf-8')


def collect_report():
    report={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
            'platform':platform.system(),'architecture':platform.machine(),
            'python':platform.python_version(),'frozen':bool(getattr(sys,'frozen',False)),
            'external_python_required':not bool(getattr(sys,'frozen',False)),
            'checks':[],'scope':'Generated samples, CPU only; no general quality, GPU or human desktop acceptance',
            'tesseract_bundled':False}
    def check(name,operation):
        try:
            detail=operation()
            report['checks'].append({'name':name,'outcome':'passed','detail':detail})
        except Exception as exc:
            report['checks'].append({'name':name,'outcome':'failed','detail':f'{type(exc).__name__}: {exc}'})
    check('offline_help_and_licenses',verify_help)
    def models():
        from .onnx_ocr import verify_models
        verify_models()
        return 'Three pinned ONNX model hashes verified'
    check('onnx_model_integrity',models)
    with tempfile.TemporaryDirectory(prefix='markitdown-self-test-') as directory:
        root=Path(directory)
        def text():
            source=root/'繁體來源.txt';target=root/'繁體輸出.md'
            source.write_bytes('# 繁體中文安裝驗收\r\n\r\nUnicode 路徑測試\r\n'.encode('utf-8'))
            _convert(source,target)
            if target.read_bytes()!=source.read_bytes():raise RuntimeError('UTF-8 bytes differ')
            return 'Unicode path, exact UTF-8 bytes, spawned worker'
        check('unicode_text_spawn',text)
        def native():
            source=root/'native.pdf';target=root/'native.md';sample_pdf(source)
            content=_convert(source,target)
            if 'INSTALLATION PDF CHECK 12345' not in content or 'route: native' not in content:
                raise RuntimeError('Native PDF content/routing mismatch')
            return 'PDF native parser and spawned worker'
        check('native_pdf_spawn',native)
        def scanned():
            from PIL import Image,ImageDraw,ImageFont
            fonts=[Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts/arial.ttf',
                   Path('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')]
            font_path=next((path for path in fonts if path.is_file()),None)
            font=ImageFont.truetype(str(font_path),72) if font_path else ImageFont.load_default(size=72)
            source=root/'scan.pdf';target=root/'scan.md'
            with Image.new('RGB',(1600,600),'white') as image:
                ImageDraw.Draw(image).text((80,100),'ONNX SCAN TEST 12345',font=font,fill='black')
                image.save(source,'PDF',resolution=144)
            content=_convert(source,target,'onnx')
            if 'ONNX SCAN TEST 12345' not in content or 'route: ocr' not in content:
                raise RuntimeError('Scanned PDF OCR content/routing mismatch')
            return 'ONNX CPU scan without external Tesseract'
        check('onnx_scanned_pdf_spawn',scanned)
    report['complete']=all(item['outcome']=='passed' for item in report['checks'])
    return report


def write_report(report,path):
    # Same output protection as conversion: never replace a prior report.
    path.parent.mkdir(parents=True,exist_ok=True)
    temporary=None
    try:
        with tempfile.NamedTemporaryFile('w',encoding='utf-8',dir=path.parent,delete=False) as output:
            temporary=Path(output.name);json.dump(report,output,ensure_ascii=False,indent=2);output.write('\n')
            output.flush();os.fsync(output.fileno())
        os.link(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Offline installation self-test; generated samples only')
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args(argv)
    if args.report.exists():parser.error('Report already exists; select a new report path')
    report=collect_report();write_report(report,args.report)
    return 0 if report['complete'] else 1


if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

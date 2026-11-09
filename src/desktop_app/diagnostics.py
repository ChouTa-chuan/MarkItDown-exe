"""使用目前執行環境離線檢查安裝完整性；打包版不需要外部 Python。

全部輸入皆為生成樣本，報告只記錄結果與版本，不蒐集使用者文件或環境秘密。"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import resources, metadata
import json
import multiprocessing
import os
from pathlib import Path
import platform
import sys
import tempfile


def sample_pdf(path):
    """直接建立最小原生 PDF，避免自我檢查依賴測試專用 PDF 寫入套件。"""
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
    from .build_profile import load_profile, verify_assets
    profile = load_profile()
    if profile is not None:
        return verify_assets(profile)
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


def _convert(source,destination,backend='tesseract', *, languages=None):
    from .application import Runner
    from .core import Request,State
    from .resources import Policy,MIB
    result=Runner(Policy(budget=2048*MIB,reserve=0),max_resource_wait=10).run(
        Request(source,destination,device='cpu',cpu_threads=1,ocr_backend=backend,ocr_languages=languages))
    if result.state!=State.COMPLETED:raise RuntimeError(result.message)
    return destination.read_text(encoding='utf-8')


def bundled_native_check(directory):
    """實際探針與四個掃描 PDF 皆使用內含資產；只核對固定合成目標。"""
    from dataclasses import replace
    from threading import Event
    from PIL import Image
    from .bundled_ocr import LANGUAGES, ORIGIN
    from .onboarding.service import probe_engine
    from .settings import Settings
    observation = probe_engine(replace(Settings(), ocr_languages=LANGUAGES), directory, Event())
    if not observation.ready or observation.origin != ORIGIN:
        raise RuntimeError('內含四語引擎健康檢查未通過：' + observation.message)
    assets = Path(resources.files('desktop_app').joinpath('data'))
    for language, stem in [('eng', 'worker-health'), ('chi_tra', 'setup-chinese'),
                            ('jpn', 'setup-japanese'), ('kor', 'setup-korean')]:
        source, destination = directory / (language + '.pdf'), directory / (language + '.md')
        reference = json.loads((assets / (stem + '.json')).read_text(encoding='utf-8'))
        with Image.open(assets / (stem + '.png')) as image:
            converted = image.convert('RGB')
            try:
                converted.save(source, 'PDF', resolution=144)
            finally:
                converted.close()
        content = _convert(source, destination, languages=(language,))
        expected = reference.get('expected', reference.get('reference'))
        if ''.join(expected.split()) not in ''.join(content.split()) or 'route: ocr' not in content:
            raise RuntimeError('內含四語掃描 PDF 固定目標不符：' + language)
    return {'version': observation.version, 'languages': list(LANGUAGES),
            'health_samples': len(observation.samples), 'scanned_pdfs': 4,
            'scope': 'Bundled native CPU, fixed generated samples only; no general accuracy or GPU claim'}


def collect_report(scope='full'):
    from .build_profile import load_profile, verify_runtime
    profile = load_profile()
    if scope not in ('core', 'full') or (profile is None and scope != 'full'):
        raise ValueError('core 範圍只適用於內含明確 profile 的建置。')
    report={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
            # 升級／回復驗收需讀真正執行中的套件版本，不只看外部 registry 或 Setup 標籤。
            'app_version':metadata.version('markitdown-desktop'),
            'platform':platform.system(),'architecture':platform.machine(),
            'python':platform.python_version(),'frozen':bool(getattr(sys,'frozen',False)),
            'python_utf8_mode':bool(sys.flags.utf8_mode),
            'external_python_required':not bool(getattr(sys,'frozen',False)),
            'checks':[],'scope':'Generated samples, CPU only; no general quality, GPU or human desktop acceptance',
            'tesseract_bundled':bool(profile and profile['native_ocr_integrated']),
            'profile':profile['id'] if profile else 'legacy-development',
            'requested_scope':scope,'release_ready':False,'full_c04_complete':False}
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
    if profile is None:
        check('onnx_model_integrity',models)
    else:
        check('base_runtime_integrity',lambda:verify_runtime(profile))
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
        if profile is None:
            check('onnx_scanned_pdf_spawn',scanned)
        elif scope == 'full':
            if profile['native_ocr_integrated']:
                check('bundled_tesseract_four_language', lambda: bundled_native_check(root))
            else:
                # 舊 core profile 的缺引擎行為保留，不能借用本機 PATH 冒充內含。
                def missing_native():
                    raise RuntimeError('基本包原生 Tesseract／四語模型尚未整合；C03 待完成。')
                check('bundled_tesseract_bilingual',missing_native)
    report['complete']=all(item['outcome']=='passed' for item in report['checks'])
    report['core_complete']=all(item['outcome']=='passed' for item in report['checks']
                                if not item['name'].startswith('bundled_tesseract_'))
    report['native_ocr_required']=bool(profile)
    report['native_ocr_integrated']=bool(profile and profile['native_ocr_integrated'])
    report['native_ocr_verified']=any(item['name']=='bundled_tesseract_four_language' and item['outcome']=='passed'
                                      for item in report['checks'])
    return report


def write_report(report,path):
    # 與轉換採相同輸出保護，不覆寫先前的驗收證據。
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
    parser.add_argument('--scope',choices=('full','core'),default='full',help='core 僅驗明確 profile 的核心，不能代表完整基本版')
    args=parser.parse_args(argv)
    if args.report.exists():parser.error('Report already exists; select a new report path')
    try:
        report=collect_report() if args.scope=='full' else collect_report(scope=args.scope)
    except Exception as exc:
        report={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),
                'profile':'invalid','requested_scope':args.scope,'complete':False,'core_complete':False,
                'release_ready':False,'checks':[{'name':'build_profile','outcome':'failed',
                                                'detail':f'{type(exc).__name__}: {exc}'}]}
    write_report(report,args.report)
    return 0 if report['complete'] else 1


if __name__=='__main__':
    multiprocessing.freeze_support()
    raise SystemExit(main())

"""真正執行基本 frozen 核心；完整自檢缺 C03 必須失敗，不能當成產品就緒。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile


def check(executable, fixtures, output):
    if output.exists(): raise FileExistsError(output)
    output.mkdir(parents=True)
    executable=executable.resolve(); fixtures=fixtures.resolve(); output=output.resolve()
    environment=dict(os.environ,PATH='',TESSDATA_PREFIX='',PYTHONPATH='',QT_QPA_PLATFORM='offscreen')
    environment.pop('PYTHONHOME',None)
    invocations=[]
    with tempfile.TemporaryDirectory(prefix='markitdown-base-frozen-cwd-') as temporary:
        def run(label,arguments,expected=0):
            result=subprocess.run([str(executable),*map(str,arguments)],env=environment,cwd=temporary,
                                  text=True,capture_output=True,timeout=120)
            (output/(label+'.log')).write_text(result.stdout+result.stderr,encoding='utf-8')
            invocations.append(dict(label=label,returncode=result.returncode,expected=expected))
            assert result.returncode==expected,(label,result.stdout,result.stderr)
        core=output/'core-self-test.json'; full=output/'full-self-test.json'
        run('core-self-test',['--self-test','--scope','core','--report',core])
        core_report=json.loads(core.read_text()); assert core_report['profile']=='base' and core_report['frozen']
        assert core_report['complete'] and core_report['core_complete'] and not core_report['release_ready']
        assert len(core_report['checks'])==4 and not core_report['external_python_required']
        run('full-self-test',['--self-test','--report',full],1)
        full_report=json.loads(full.read_text()); assert not full_report['complete'] and full_report['core_complete']
        assert full_report['checks'][-1]['name']=='bundled_tesseract_bilingual'
        assert full_report['checks'][-1]['outcome']=='failed' and not full_report['native_ocr_integrated']
        run('help-assets',['--verify-help-assets'])
        results=[]
        for record in json.loads((fixtures/'fixtures.json').read_text()):
            source=fixtures/record['file']; destination=output/(source.name+'.md')
            assert hashlib.sha256(source.read_bytes()).hexdigest()==record['sha256']
            missing_native=source.name=='掃描.pdf'
            run(source.name,['--cli',source,destination,'--device','cpu','--reserve-mib','0',
                             '--ram-budget-mib','2048'],1 if missing_native else 0)
            if missing_native: assert not destination.exists()
            else:
                text=destination.read_text(encoding='utf-8'); assert all(value in text for value in record['expected'])
                if source.suffix=='.txt': assert destination.read_bytes()==source.read_bytes()
            results.append(dict(file=source.name,converted=not missing_native))
        run('optional-ocr-rejected',['--cli',fixtures/'掃描.pdf',output/'optional.md',
                                    '--ocr-backend','onnx','--device','cpu','--reserve-mib','0'],1)
        assert not (output/'optional.md').exists()
        # 核對實際 binary 收集來源與全部 bundle 檔案，供之後原生來源／大小比較。
        bundle=executable.parent; files=[]
        for path in sorted(bundle.rglob('*')):
            if path.is_symlink():
                assert path.resolve().is_relative_to(bundle.resolve()),path
                files.append(dict(file=path.relative_to(bundle).as_posix(),link=os.readlink(path)))
            elif path.is_file():
                data=path.read_bytes();files.append(dict(file=path.relative_to(bundle).as_posix(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        (output/'bundle-files.json').write_text(json.dumps(dict(files=files),ensure_ascii=False,indent=2)+'\n')
        data_root=bundle/'_internal/desktop_app/data'
        profile=json.loads((data_root/'build-profile.json').read_text())
        assert len(profile['runtime_packages'])==38 and 'rapidocr-onnxruntime' not in profile['runtime_packages']
        assert 'onnxruntime' in profile['runtime_packages']
        assert not list(bundle.rglob('*PP-OCR*')) and not list(bundle.rglob('*opencv*'))
        for name in ['build-profile.json','licenses/installed/manifest.json','licenses/native/manifest.json']:
            target=output/Path(name).name
            if name.startswith('licenses/installed'):target=output/'installed-notices-manifest.json'
            if name.startswith('licenses/native'):target=output/'native-binaries-manifest.json'
            target.write_bytes((data_root/name).read_bytes())
    report=dict(recorded_at=datetime.now(timezone.utc).isoformat(),source_version=profile['source_version'],
        check='C04-build',accepted=True,checks_passed=7,checks=['core self-test in frozen process',
        'full self-test rejects missing native OCR','selected help/assets verified','six format conversions with empty PATH',
        'missing native and optional OCR leave no output','38-runtime profile and absent OCR payloads','bundle file hashes and actual binary origins'],
        invocations=invocations,results=results,frozen=True,path_empty=True,checkout_on_pythonpath=False,
        windows_executed=False,gpu_executed=False,full_c04_complete=False,native_ocr_bundled=False,
        bundle_files=len(files),bundle_file_bytes=sum(value.get('bytes',0) for value in files))
    (output/'frozen-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Base frozen checks passed: 7; full native/Windows C04 remains pending')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable',type=Path,required=True);parser.add_argument('--fixtures',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    check(args.executable,args.fixtures,args.output)

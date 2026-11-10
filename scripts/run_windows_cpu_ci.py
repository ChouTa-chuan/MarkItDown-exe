"""Windows 原生 CPU 選配 CI：建置環境與無 OCR 控制端分開，保存原始步驟與真實退出。"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tomllib
import traceback

ROOT=Path(__file__).resolve().parents[1]


def run(output):
    # 先拒絕錯誤平台，避免在Linux創建目錄後冒充Windows編譯結果。
    if sys.platform!='win32' or sys.version_info[:2]!=(3,12) or struct.calcsize('P')!=8:
        raise RuntimeError('Requires actual Windows x64 CPython 3.12')
    output=Path(output).absolute()
    if output.exists():raise FileExistsError('Use a fresh CPU CI output directory')
    reports=output/'reports';reports.mkdir(parents=True)
    result=dict(check='windows-cpu-worker-ci',commit=os.environ.get('GITHUB_SHA'),
        source_version=tomllib.loads((ROOT/'pyproject.toml').read_text())['project']['version'],
        recorded_at=datetime.now(timezone.utc).isoformat(),accepted=False,windows_executed=True,
        build_verified=False,checks_passed=0,clean_machine_accepted=False,gpu_executed=False,
        traditional_chinese_quality_passed=False,release_ready=False,commands=[])
    env={**os.environ,'PYTHONUTF8':'1'}
    def call(label, argv):
        result['failed_step']=label;result['commands'].append(dict(label=label,argv=list(map(str,argv))))
        with (reports/(label+'.log')).open('wb') as log:
            subprocess.run(list(map(str,argv)),cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,
                           timeout=1200,check=True)
    try:
        build=output/'build-env';controller=output/'controller-env'
        python=build/'Scripts/python.exe';control=controller/'Scripts/python.exe'
        call('build-venv',[sys.executable,'-m','venv',build])
        call('build-dependencies',[python,'-m','pip','install','--require-hashes','-r',ROOT/'packaging/profiles/cpu-windows-build.txt'])
        call('build-application',[python,'-m','pip','install','--no-deps','--no-build-isolation',ROOT])
        call('verify-profiles',[python,ROOT/'scripts/cpu_worker_profiles.py'])
        call('build-pip-check',[python,'-m','pip','check'])
        assets=output/'assets'
        call('worker-assets',[python,ROOT/'scripts/prepare_worker_assets.py','--output',assets])
        env['MARKITDOWN_WORKER_ASSETS']=str(assets)
        call('pyinstaller',[python,'-m','PyInstaller','--noconfirm','--clean','--distpath',output/'dist',
                            '--workpath',output/'work',ROOT/'packaging/ocr-worker.spec'])
        result['build_verified']=True
        package=output/'package'
        call('component-package',[python,ROOT/'scripts/package_cpu_worker.py','--bundle',output/'dist/MarkItDownOCRWorker','--output',package])
        call('controller-venv',[sys.executable,'-m','venv',controller])
        call('controller-dependencies',[control,'-m','pip','install','--require-hashes','-r',ROOT/'packaging/profiles/cpu-windows-controller.txt'])
        call('controller-application',[control,'-m','pip','install','--no-deps','--no-build-isolation',ROOT])
        call('controller-pip-check',[control,'-m','pip','check'])
        call('native-acceptance',[control,ROOT/'scripts/check_cpu_worker_acceptance.py','--package-directory',package,
                                  '--report',reports/'cpu-acceptance.json'])
        value=json.loads((reports/'cpu-acceptance.json').read_text(encoding='utf-8'))
        if (not value['accepted'] or value['checks_passed']!=11 or not value['windows_executed']
                or not value['runtime']['frozen'] or not value['controller_unchanged']):
            raise RuntimeError('Actual frozen CPU acceptance incomplete')
        if not value['lifecycle']['accepted'] or value['lifecycle']['checks_passed']!=8:
            raise RuntimeError('Actual CPU maintenance acceptance incomplete')
        result.update(accepted=True,checks_passed=11,controller_unchanged=True,
            controller_native_packages=False,package_sha256=value['package_sha256'],
            actual_providers=value['actual_providers'],installed_notice_packages=value['installed_notice_packages'],
            lifecycle=value['lifecycle'])
        result.pop('failed_step',None)
    except Exception as exc:
        result['error']=type(exc).__name__+': '+str(exc)
        failed=reports/(result.get('failed_step','')+'.log')
        if failed.is_file():
            # 公開頁只能保存短摘要；優先保留真實內層錯誤，而非只留下外層CalledProcessError。
            with failed.open('rb') as log:
                log.seek(max(0,failed.stat().st_size-2000))
                result['failure_detail']=log.read().decode('utf-8',errors='replace')[-1200:]
        (reports/'driver-error.log').write_text(traceback.format_exc(),encoding='utf-8')
    (reports/'cpu-build.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # 短摘要可從公開Actions頁保存；不把大型worker、模型、套件或測試金鑰上傳。
    brief={key:value for key,value in result.items() if key not in ('commands',)}
    message=json.dumps(brief,ensure_ascii=False,separators=(',',':'))
    if os.environ.get('GITHUB_ACTIONS')=='true':
        print('::'+('notice' if result['accepted'] else 'error')+'::'+message.replace('%','%25').replace('\n','%0A').replace('\r','%0D'))
    else:print(message)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();value=run(args.output);raise SystemExit(0 if value['accepted'] else 1)

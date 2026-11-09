"""Windows CI 控制端：建立隔離基本建置環境、打包與驗收，保存每一步原始日誌。"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installer',action='store_true',help='在可拋棄 CI 另做基本包安裝／修復／移除')
    args = parser.parse_args()
    if args.output.exists():
        parser.error('CI 輸出目錄已存在。')
    reports = args.output/'reports'
    reports.mkdir(parents=True)
    summary = dict(recorded_at=datetime.now(timezone.utc).isoformat(), check='windows-base-build-ci',
                   commit=os.environ.get('GITHUB_SHA'), runner_os=os.environ.get('RUNNER_OS'),
                   image_version=os.environ.get('ImageVersion'), platform=platform.platform(),
                   build_verified=False, validation_accepted=False, clean_machine_accepted=False,
                   release_ready=False, gpu_executed=False, installer_requested=args.installer,
                   installer_accepted=False if args.installer else None,overall_accepted=False,commands=[])
    environment = {**os.environ, 'PYTHONUTF8': '1', 'QT_QPA_PLATFORM': 'offscreen'}

    def call(label, argv):
        summary['commands'].append(dict(label=label, argv=list(map(str, argv))))
        with (reports/(label+'.log')).open('wb') as log:
            subprocess.run(list(map(str, argv)), cwd=ROOT, env=environment,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1200)

    try:
        if sys.platform != 'win32' or sys.version_info[:2] != (3,12):
            raise RuntimeError('此控制端只接受真正 Windows CPython 3.12。')
        venv = args.output/'build-venv'
        call('create-venv', [sys.executable, '-m', 'venv', venv])
        python = venv/'Scripts/python.exe'
        call('locked-dependencies', [python,'-m','pip','install','--require-hashes','-r','packaging/profiles/base-windows-build.txt'])
        call('local-projects', [python,'-m','pip','install','--no-deps','--no-build-isolation','./vendor/markitdown','.'])
        call('profile-locks', [python,'scripts/packaging_profiles.py'])
        native = args.output/'native-assets'
        call('native-assets', [python,'scripts/prepare_bundled_ocr.py','--windows-candidate',args.inputs/'candidate',
             '--build-evidence',args.inputs/'build-evidence.json','--tessdata',args.inputs/'models','--output',native])
        assets = args.output/'base-assets'
        call('base-assets', [python,'scripts/prepare_base_assets.py','--native-assets',native,'--output',assets])
        environment['MARKITDOWN_BASE_ASSETS'] = str(assets.resolve())
        call('pyinstaller', [python,'-m','PyInstaller','--noconfirm','--clean','--distpath',args.output/'dist',
                            '--workpath',args.output/'work','packaging/base.spec'])
        summary['build_verified'] = True
        call('windows-validation', [python,'scripts/check_windows_base.py','--executable',
             args.output/'dist/MarkItDownBase/MarkItDownBase.exe','--output',reports/'acceptance'])
        acceptance = json.loads((reports/'acceptance/windows-acceptance.json').read_text(encoding='utf-8'))
        summary['validation_accepted'] = acceptance['accepted']
        if args.installer:
            call('installer-lifecycle',[python,'scripts/check_windows_base_installer.py','--bundle',
                 args.output/'dist/MarkItDownBase','--output',args.output/'installer-work',
                 '--reports',reports/'installer'])
            installer=json.loads((reports/'installer/installer-lifecycle.json').read_text(encoding='utf-8'))
            summary['installer_accepted']=installer['accepted']
        summary['overall_accepted']=summary['validation_accepted'] and (not args.installer or summary['installer_accepted'])
    except Exception as exc:
        summary['error'] = f'{type(exc).__name__}: {exc}'
        (reports/'build-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    (reports/'windows-build.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Native Windows build:', summary['build_verified'], '; validation:', summary['validation_accepted'])
    return 0 if summary['overall_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

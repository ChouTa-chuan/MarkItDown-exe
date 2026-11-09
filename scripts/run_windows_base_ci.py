"""Windows CI 控制端：建立隔離基本建置環境、打包與驗收，保存每一步原始日誌。"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import shutil
import traceback

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--installer',action='store_true',help='在可拋棄 CI 另做基本包安裝／修復／移除')
    parser.add_argument('--previous-source',type=Path,help='固定真實前版 checkout，另建置並驗基本包跨版重裝／明確回復')
    parser.add_argument('--recovery',action='store_true',help='另驗三個真正程序中斷停點及一般安裝器明確續修')
    args = parser.parse_args()
    args.inputs=args.inputs.absolute();args.output=args.output.absolute()
    if args.recovery and (not args.installer or args.previous_source is None):parser.error('--recovery requires --installer and --previous-source')
    if args.previous_source is not None:
        args.previous_source=args.previous_source.absolute()
        if not args.installer:parser.error('跨版驗證須同時執行 --installer。')
    if args.output.exists():
        parser.error('CI 輸出目錄已存在。')
    reports = args.output/'reports'
    reports.mkdir(parents=True)
    summary = dict(recorded_at=datetime.now(timezone.utc).isoformat(), check='windows-base-build-ci',
                   commit=os.environ.get('GITHUB_SHA'), runner_os=os.environ.get('RUNNER_OS'),
                   image_version=os.environ.get('ImageVersion'), platform=platform.platform(),
                   build_verified=False, validation_accepted=False, clean_machine_accepted=False,
                   release_ready=False, gpu_executed=False, installer_requested=args.installer,
                   installer_accepted=False if args.installer else None,
                   upgrade_accepted=False if args.previous_source else None,overall_accepted=False,commands=[])
    summary['recovery_accepted']=False if args.recovery else None
    environment = {**os.environ, 'PYTHONUTF8': '1', 'QT_QPA_PLATFORM': 'offscreen'}

    def call(label, argv):
        summary['commands'].append(dict(label=label, argv=list(map(str, argv))))
        with (reports/(label+'.log')).open('wb') as log:
            subprocess.run(list(map(str, argv)), cwd=ROOT, env=environment,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=1200)

    try:
        if sys.platform != 'win32' or sys.version_info[:2] != (3,12):
            raise RuntimeError('此控制端只接受真正 Windows CPython 3.12。')
        previous_bundle=None
        if args.previous_source is not None:
            # 以前版原 controller／spec 獨立建置，不能把目前 payload 改版本字串充當歷史版本。
            expected='990e600aed9e26011b77d46dfe5f9e5bb13ecc7a'
            observed=subprocess.run(['git','-C',str(args.previous_source),'rev-parse','HEAD'],capture_output=True,
                                    text=True,check=True,timeout=20).stdout.strip()
            if observed!=expected:raise ValueError('前版必須是固定的實際 0.16 source commit。')
            previous_output=args.output/'previous-build'
            try:
                call('previous-base-build',[sys.executable,args.previous_source/'scripts/run_windows_base_ci.py',
                     '--inputs',args.inputs,'--output',previous_output])
            finally:
                for name in ['windows-build.json','build-error.log','acceptance/windows-acceptance.json']:
                    path=previous_output/'reports'/name
                    if path.is_file():
                        target=reports/'previous-build'/name;target.parent.mkdir(parents=True,exist_ok=True)
                        shutil.copyfile(path,target)
            old=json.loads((previous_output/'reports/acceptance/windows-acceptance.json').read_text(encoding='utf-8'))
            if not old['accepted'] or old['source_version']!='0.16.0':raise ValueError('前版實際建置驗收失敗。')
            previous_bundle=previous_output/'dist/MarkItDownBase'
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
            installer_args=[python,'scripts/check_windows_base_installer.py','--bundle',
                 args.output/'dist/MarkItDownBase','--output',args.output/'installer-work',
                 '--reports',reports/'installer']
            if previous_bundle:installer_args+=['--previous-bundle',previous_bundle]
            call('installer-lifecycle',installer_args)
            installer=json.loads((reports/'installer/installer-lifecycle.json').read_text(encoding='utf-8'))
            summary['installer_accepted']=installer['accepted']
            if previous_bundle:
                version=installer['source_version']
                call('upgrade-lifecycle',[python,'scripts/check_windows_base_upgrade.py','--bundle',
                     args.output/'dist/MarkItDownBase','--previous-bundle',previous_bundle,'--previous-source',args.previous_source,
                     '--setup',args.output/'installer-work/setup'/f'MarkItDownBase-Setup-{version}-windows-x64.exe',
                     '--output',args.output/'upgrade-work','--reports',reports/'upgrade'])
                upgrade=json.loads((reports/'upgrade/upgrade-lifecycle.json').read_text(encoding='utf-8'))
                summary['upgrade_accepted']=upgrade['accepted']
                if args.recovery:
                    previous_version=upgrade['previous_version']
                    call('recovery-lifecycle',[python,'scripts/check_windows_base_recovery.py','--bundle',
                         args.output/'dist/MarkItDownBase','--previous-bundle',previous_bundle,
                         '--setup',args.output/'installer-work/setup'/f'MarkItDownBase-Setup-{version}-windows-x64.exe',
                         '--previous-setup',args.output/'upgrade-work/previous-original'/f'MarkItDownBase-Setup-{previous_version}-windows-x64.exe',
                         '--output',args.output/'recovery-work','--reports',reports/'recovery'])
                    recovery=json.loads((reports/'recovery/recovery-lifecycle.json').read_text(encoding='utf-8'))
                    summary['recovery_accepted']=recovery['accepted']
        summary['overall_accepted']=(summary['validation_accepted'] and (not args.installer or summary['installer_accepted'])
                                    and (not args.previous_source or summary['upgrade_accepted'])
                                    and (not args.recovery or summary['recovery_accepted']))
    except Exception as exc:
        summary['error'] = f'{type(exc).__name__}: {exc}'
        (reports/'build-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    (reports/'windows-build.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    print('Native Windows build:', summary['build_verified'], '; validation:', summary['validation_accepted'])
    return 0 if summary['overall_accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""在可拋棄 Windows CI 安裝／同版修復／移除基本包；不宣稱乾淨機或完整升級驗收。"""
import argparse
import ctypes
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import traceback
import uuid

from base_install_catalog import APP_ID,CATALOG,ENTRY,create,verify,assert_managed_removed
from desktop_app.components.registry import _chain
from desktop_app.native_assets import file_hash
from check_windows_base import native_environment

ROOT=Path(__file__).resolve().parents[1]
SHORTCUT='MarkItDown Base Preview.lnk'


def known_folder(number):
    from ctypes import wintypes
    shell=ctypes.windll.shell32.SHGetFolderPathW
    shell.argtypes=[wintypes.HWND,ctypes.c_int,wintypes.HANDLE,ctypes.c_uint32,wintypes.LPWSTR]
    shell.restype=ctypes.c_long
    buffer=ctypes.create_unicode_buffer(32768)
    if shell(None,number,None,0,buffer)!=0:raise RuntimeError('Windows known folder unavailable')
    return Path(buffer.value)


def registration():
    import winreg
    records=[]
    name='Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\'+APP_ID+'_is1'
    for view in [winreg.KEY_WOW64_64KEY,winreg.KEY_WOW64_32KEY]:
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,name,0,winreg.KEY_READ|view) as key:
                values={}
                for value in ['InstallLocation','Inno Setup: App Path','DisplayVersion']:
                    try:values[value]=winreg.QueryValueEx(key,value)[0]
                    except FileNotFoundError:pass
                records.append(values)
        except FileNotFoundError:pass
    return records


def wait_until(operation,*,timeout=30):
    deadline=time.monotonic()+timeout
    while True:
        try:
            if operation():return
        except (OSError,ValueError):pass
        if time.monotonic()>=deadline:raise TimeoutError('Installer finalization exceeded deadline')
        time.sleep(0.2)


def check(bundle,work,reports,*,iscc=None):
    # 必須先拒絕錯平台；Linux 單元測試不可產生假 Windows 安裝報告。
    if sys.platform!='win32':raise RuntimeError('Requires actual Windows')
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_OS')!='Windows':
        raise RuntimeError('This lifecycle tool is restricted to a disposable Windows CI account')
    bundle,work,reports=Path(bundle).absolute(),Path(work).absolute(),Path(reports).absolute()
    _chain(work);_chain(reports)
    if work.exists() or reports.exists():raise FileExistsError('Use fresh installer work and report directories')
    shortcut=known_folder(2)/SHORTCUT
    if registration() or shortcut.exists():raise RuntimeError('Existing preview registration/shortcut; refusing to replace it')
    work.mkdir(parents=True);reports.mkdir(parents=True)
    result=dict(check='C11-base-installer-smoke',recorded_at=datetime.now(timezone.utc).isoformat(),
        accepted=False,windows_executed=True,install_verified=False,repair_verified=False,
        uninstall_verified=False,user_data_preserved=False,shortcut_verified=False,
        clean_machine_accepted=False,upgrade_verified=False,rollback_verified=False,
        human_ui_accepted=False,full_c11_complete=False,release_ready=False,gpu_executed=False,
        checks=[],commands=[])
    install=work/'中文 安裝目錄'/'MarkItDownBase'
    fixture=known_folder(0x1c)/'MarkItDownDesktop/MarkItDownDesktop'/('installer-probe-'+uuid.uuid4().hex)
    source=None;expected_user={};installed=False

    def call(label,argv,*,environment=None,timeout=600):
        result['commands'].append(dict(label=label,argv=list(map(str,argv))))
        with (reports/(label+'.log')).open('wb') as log:
            subprocess.run(list(map(str,argv)),cwd=ROOT,env=environment or os.environ,
                stdout=log,stderr=subprocess.STDOUT,check=True,timeout=timeout)
    try:
        version=json.loads((bundle/'_internal/desktop_app/data/build-profile.json').read_text(encoding='utf-8'))['source_version']
        result['source_version']=version
        source=create(bundle,version)
        verify(bundle,source)
        (reports/CATALOG).write_bytes((bundle/CATALOG).read_bytes())
        result['bundle_catalog_sha256']=file_hash(bundle/CATALOG)[0]
        result['catalog_files']=len(source['files'])
        result['checks'].append('Source base bundle catalog and embedded version verified')
        compiler=Path(iscc) if iscc else Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Inno Setup 6/ISCC.exe'
        _chain(compiler)
        result['compiler_sha256']=file_hash(compiler)[0]
        license_path=compiler.parent/'license.txt'
        if license_path.is_file():
            shutil.copyfile(license_path,reports/'inno-setup-license.txt')
            result['compiler_license_sha256']=file_hash(license_path)[0]
        setup_dir=work/'setup'
        call('compile-installer',[compiler,'/DBundleDir='+str(bundle),'/DOutputDir='+str(setup_dir),
            '/DAppVersion='+version,ROOT/'packaging/base-installer.iss'])
        setup=setup_dir/f'MarkItDownBase-Setup-{version}-windows-x64.exe'
        result['installer_sha256'],result['installer_bytes']=file_hash(setup,512*1024**2)
        result['checks'].append('Actual Inno per-user base installer compiled; no Release created')
        # 只新增自己唯一的 fixture 子目錄，不覆寫真正 settings／模型／SQLite 或使用者文件。
        _chain(fixture)
        fixture.mkdir(parents=True)
        for name in ['settings.json','models/local.bin','component-state/state.sqlite','outputs/report.md','cache/local.bin']:
            target=fixture/name;target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(('KEEP SYNTHETIC USER DATA: '+name).encode())
            expected_user[name]=file_hash(target)

        def assert_user():
            for name,expected in expected_user.items():
                _chain(fixture/name)
                if file_hash(fixture/name)!=expected:raise RuntimeError('External user-data fixture changed')

        flags=['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/DIR='+str(install)]
        installed=True
        call('install',[setup,*flags,'/LOG='+str(reports/'install-inno.log')])
        result['windows_executed']=True
        registrations=registration()
        if not registrations:raise RuntimeError('Per-user uninstall registration missing')
        for item in registrations:
            location=item.get('InstallLocation',item.get('Inno Setup: App Path',''))
            if Path(location).resolve()!=install.resolve() or item.get('DisplayVersion')!=version:
                raise RuntimeError('Installer registry target/version differs from this test')
        verify(install,source,installed=True);assert_user()
        if not shortcut.is_file():raise RuntimeError('Per-user Start menu shortcut missing')
        result['shortcut_verified']=True
        result['checks'].append('Installed source hashes, per-user registry, Unicode path and Start menu verified')
        call('installed-application',[sys.executable,ROOT/'scripts/check_windows_base.py','--executable',install/ENTRY,
             '--output',reports/'installed-acceptance'])
        acceptance=json.loads((reports/'installed-acceptance/windows-acceptance.json').read_text(encoding='utf-8'))
        if not acceptance['accepted'] or acceptance['checks_passed']!=10:raise RuntimeError('Installed application did not pass all base checks')
        result['installed_app_checks']=acceptance['checks_passed'];result['install_verified']=True
        result['checks'].append('Actually installed application passes all ten Windows base checks')
        note=install/'使用者保留文件.txt';note.write_bytes('KEEP UNTRACKED USER NOTE'.encode())
        note_hash=file_hash(note)
        # 真正移除入口並破壞英語模型，再用同版安裝器修復；不冒充跨版本升級／回復。
        (install/ENTRY).unlink()
        (install/'_internal/desktop_app/data/native/tessdata/eng.traineddata').write_bytes(b'corrupt test model')
        try:verify(install,source,allowed_extras={note.name:note_hash},installed=True)
        except (OSError,ValueError,RuntimeError):pass
        else:raise RuntimeError('Damage control was not detected')
        call('repair',[setup,*flags,'/LOG='+str(reports/'repair-inno.log')])
        verify(install,source,allowed_extras={note.name:note_hash},installed=True);assert_user()
        call('repaired-self-test',[install/ENTRY,'--self-test','--report',reports/'repaired-self-test.json'],environment=native_environment())
        repaired=json.loads((reports/'repaired-self-test.json').read_text(encoding='utf-8'))
        if not repaired['complete'] or not repaired['native_ocr_verified']:raise RuntimeError('Repaired embedded OCR not healthy')
        result['repair_verified']=True
        result['checks'].append('Same-version reinstall restores missing EXE/corrupt model and four-language self-test')
        call('uninstall',[install/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',
                          '/LOG='+str(reports/'uninstall-inno.log')])
        def removed():
            assert_managed_removed(install,source)
            return not registration() and not shortcut.exists() and not (install/'unins000.exe').exists()
        wait_until(removed)
        installed=False
        assert_user()
        if file_hash(note)!=note_hash:raise RuntimeError('Uninstall removed the untracked user note')
        result['uninstall_verified']=True;result['user_data_preserved']=True
        result['checks'].append('Uninstall removes owned files/registry/shortcut and preserves external data plus untracked note')
        note.unlink()
        result['accepted']=True
    except Exception as exc:
        result['error']=f'{type(exc).__name__}: {exc}'
        (reports/'driver-error.log').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        # 失敗後只處理自己剛建立的安裝；不能以 cleanup 成功覆寫主要驗收失敗。
        if installed and (install/'unins000.exe').is_file():
            try:call('failed-test-uninstall',[install/'unins000.exe','/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'])
            except Exception as exc:result['cleanup_error']=str(exc)
        if expected_user and fixture.is_dir():
            for name in expected_user:
                path=fixture/name
                try:_chain(path);path.unlink(missing_ok=True)
                except OSError:pass
            for path in sorted(fixture.rglob('*'),reverse=True):
                if path.is_dir() and not path.is_symlink():
                    try:path.rmdir()
                    except OSError:pass
            try:fixture.rmdir()
            except OSError:pass
        result['checks_passed']=len(result['checks'])
        (reports/'installer-lifecycle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--reports',type=Path,required=True)
    args=parser.parse_args()
    outcome=check(args.bundle,args.output,args.reports)
    print('Installer lifecycle accepted:',outcome['accepted'],'checks:',outcome['checks_passed'])
    raise SystemExit(0 if outcome['accepted'] else 1)

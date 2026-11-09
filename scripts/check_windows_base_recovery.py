"""在可拋棄 Windows CI 真正終止測試 Setup，再以一般安裝器明確續修；非斷電驗收。"""
import argparse
from datetime import datetime, timezone
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import traceback
import uuid

from base_install_catalog import CATALOG, ENTRY, PENDING, verify, assert_managed_removed
from base_install_transition import write_rules, plan
from check_windows_base_installer import known_folder, registration, wait_until, SHORTCUT
from check_windows_base import native_environment
from desktop_app.components.registry import _chain
from desktop_app.native_assets import file_hash

ROOT=Path(__file__).resolve().parents[1]
STAGES=('intent','first-file','payload-written')


def registered_uninstaller(install,records):
    """中斷後可能換成 unins001；只取本次已登錄且位於測試 app 內的 Inno 入口。"""
    candidates=set()
    for row in records:
        match=re.fullmatch(r'"([^"]+)"(?:\s.*)?|([^\s"]+)',row.get('UninstallString',''))
        if not match:raise ValueError('Registered uninstaller command is ambiguous')
        path=Path(match.group(1) or match.group(2))
        _chain(path)
        if path.parent.resolve()!=Path(install).resolve() or not re.fullmatch(r'unins\d{3}\.exe',path.name):
            raise ValueError('Registered uninstaller escaped the owned application directory')
        if not path.is_file():raise FileNotFoundError(path)
        candidates.add(path)
    if len(candidates)!=1:raise ValueError('Missing or conflicting uninstall registration')
    return candidates.pop()


def check(bundle, previous_bundle, setup, previous_setup, work, reports, *, iscc=None):
    if sys.platform!='win32':raise RuntimeError('Requires actual Windows')
    if os.environ.get('GITHUB_ACTIONS')!='true' or os.environ.get('RUNNER_OS')!='Windows':
        raise RuntimeError('Requires a disposable Windows CI account')
    bundle,previous_bundle,setup,previous_setup,work,reports=[Path(p).absolute()
        for p in (bundle,previous_bundle,setup,previous_setup,work,reports)]
    for path in (bundle,previous_bundle,setup,previous_setup,work,reports):_chain(path)
    if work.exists() or reports.exists():raise FileExistsError('Use fresh interruption work/report directories')
    shortcut=known_folder(2)/SHORTCUT
    if registration() or shortcut.exists():raise RuntimeError('Existing installation; refusing to replace it')
    work.mkdir(parents=True);reports.mkdir(parents=True)
    result=dict(check='C11-base-interruption-resume',recorded_at=datetime.now(timezone.utc).isoformat(),
        accepted=False,windows_executed=True,process_termination_verified=False,pending_app_blocked=False,
        explicit_resume_required=False,user_data_preserved=False,power_loss_accepted=False,
        all_profiles_accepted=False,automatic_failure_rollback=False,full_c11_complete=False,
        clean_machine_accepted=False,release_ready=False,test_only_fault_installer=True,
        interruption_cases=0,resumed_app_checks=[],terminations=[],checks=[],commands=[])
    install=work/'中文 中斷續修'/'MarkItDownBase';note=install/'使用者保留文件.txt'
    fixture=known_folder(0x1c)/'MarkItDownDesktop/MarkItDownDesktop'/('resume-probe-'+uuid.uuid4().hex)
    user={};installed=False;new=old=None;active=None

    def call(label,argv,*,allow_failure=False,environment=None):
        result['commands'].append(dict(label=label,argv=list(map(str,argv))))
        with (reports/(label+'.log')).open('wb') as log:
            child=subprocess.run(list(map(str,argv)),cwd=ROOT,env=environment or os.environ,
                                 stdout=log,stderr=subprocess.STDOUT,timeout=600)
        if child.returncode and not allow_failure:raise subprocess.CalledProcessError(child.returncode,argv)
        return child.returncode

    def user_unchanged():
        for path,expected in user.items():
            _chain(path)
            if file_hash(path)!=expected:raise RuntimeError('Synthetic user data changed')

    def installed_state(expected):
        verify(install,expected,installed=True,allowed_extras={note.name:user[note]})
        if (install/PENDING).exists() or (install/(PENDING+'.new')).exists():raise RuntimeError('Pending state was not cleared')
        records=registration()
        if not records or not shortcut.is_file():raise RuntimeError('Registration/shortcut missing after recovery')
        for row in records:
            path=row.get('InstallLocation',row.get('Inno Setup: App Path',''))
            if Path(path).resolve()!=install.resolve() or row.get('DisplayVersion')!=expected['app_version']:
                raise RuntimeError('Recovered registration path/version differs')
        user_unchanged()

    flags=['/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-','/DIR='+str(install)]
    try:
        new,old=[json.loads((p/CATALOG).read_text(encoding='utf-8')) for p in (bundle,previous_bundle)]
        verify(bundle,new);verify(previous_bundle,old)
        rules=work/'fault-rules.iss';transition=write_rules(rules,bundle,new,previous_bundle,old)
        result.update(source_version=new['app_version'],previous_version=old['app_version'],
                      target_setup_sha256=file_hash(setup)[0])
        compiler=Path(iscc) if iscc else Path(os.environ.get('ProgramFiles(x86)','C:/Program Files (x86)'))/'Inno Setup 6/ISCC.exe'
        call('compile-fault-installer',[compiler,'/DBundleDir='+str(bundle),'/DOutputDir='+str(work/'fault-setup'),
             '/DAppVersion='+new['app_version'],'/DTransitionRules='+str(rules),'/DCiFaultInjection=1',ROOT/'packaging/base-installer.iss'])
        fault=work/'fault-setup'/f"MarkItDownBase-Setup-{new['app_version']}-windows-x64.exe"
        result['fault_setup_sha256']=file_hash(fault)[0]
        token=('v1|'+transition['target_catalog_sha256']+'|'+transition['previous_catalog_sha256']).encode('ascii')
        result['checks'].append('Normal and CI-only stop-point installers share the same verified payload catalogs')
        fixture.mkdir(parents=True);install.mkdir(parents=True)
        for name in ['settings.json','models/local.bin','component-state/state.sqlite','outputs/report.md','cache/local.bin']:
            path=fixture/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(('KEEP RESUME DATA '+name).encode())
            user[path]=file_hash(path)
        note.write_bytes(b'KEEP UNKNOWN USER DOCUMENT');user[note]=file_hash(note)
        for stage in STAGES:
            if stage!='intent':
                installed=True
                call(stage+'-previous-install',[previous_setup,*flags,'/LOG='+str(reports/(stage+'-previous-inno.log'))])
                installed_state(old)
            signal=work/(stage+'-ready.txt')
            argv=[fault,*flags,'/CISTOP='+stage,'/CISIGNAL='+str(signal),'/LOG='+str(reports/(stage+'-fault-inno.log'))]
            result['commands'].append(dict(label=stage+'-fault-process',argv=list(map(str,argv))))
            installed=True
            with (reports/(stage+'-process.log')).open('wb') as log:
                active=subprocess.Popen(list(map(str,argv)),cwd=ROOT,stdout=log,stderr=subprocess.STDOUT)
                def ready():
                    if active.poll() is not None:raise RuntimeError('Fault installer exited before its real stop point')
                    return signal.is_file() and signal.read_text(encoding='ascii')==stage
                wait_until(ready,timeout=120)
                if (install/PENDING).read_bytes()!=token:raise RuntimeError('Committed recovery intent missing at interruption')
                # 只終止自己啟動、且已完成握手的 bootstrap 與 Setup 子程序樹，不按名稱掃描或終止其他程序。
                pid=active.pid
                call(stage+'-terminate-owned-tree',['taskkill','/PID',str(pid),'/T','/F'])
                code=active.wait(timeout=30)
                if code==0:raise RuntimeError('Interruption did not produce a nonzero process exit')
                result['terminations'].append(dict(stage=stage,pid=pid,returncode=code,owned_tree=True))
                active=None
            user_unchanged()
            if stage=='intent':
                if any((install/item['path']).is_file() for item in new['files']):raise RuntimeError('Intent stop ran after payload copy')
                # 一般無確認的重跑與不匹配的 intent 都必須拒絕，不能靜默覆寫半套程式。
                if call('reject-implicit-resume',[setup,*flags],allow_failure=True)==0:raise RuntimeError('Silent resume lacked explicit consent')
                marker=install/PENDING;marker.write_bytes(b'wrong-build')
                try:
                    if call('reject-mismatched-resume',[setup,*flags,'/RESUMEINSTALL=1'],allow_failure=True)==0:
                        raise RuntimeError('Wrong recovery build was accepted')
                finally:marker.write_bytes(token)
                result['explicit_resume_required']=True
            if stage=='first-file':
                present=sum((install/item['path']).is_file() for item in new['files'])
                if not present:raise RuntimeError('First-file checkpoint did not copy a real application file')
                result['first_file_present_count']=present
            if stage=='payload-written':
                for item in new['files']:
                    if file_hash(install/item['path'])!=(item['sha256'],item['bytes']):raise RuntimeError('Payload-written checkpoint incomplete')
                blocked=reports/'must-not-run.json'
                code=call('block-incomplete-application',[install/ENTRY,'--self-test','--report',blocked],
                          allow_failure=True,environment=native_environment())
                if code!=3 or blocked.exists():raise RuntimeError('Incomplete installation entered application diagnostics')
                result['pending_app_blocked']=True
            call(stage+'-normal-resume',[setup,*flags,'/RESUMEINSTALL=1','/LOG='+str(reports/(stage+'-resume-inno.log'))])
            installed_state(new)
            for name in plan(new,old)['obsolete_directories']:
                if (install/name).exists():raise RuntimeError('Old package metadata survived resumed upgrade')
            acceptance_dir=reports/(stage+'-acceptance')
            call(stage+'-acceptance',[sys.executable,ROOT/'scripts/check_windows_base.py','--executable',install/ENTRY,'--output',acceptance_dir])
            accepted=json.loads((acceptance_dir/'windows-acceptance.json').read_text(encoding='utf-8'))
            if not accepted['accepted'] or accepted['checks_passed']!=10:raise RuntimeError('Recovered app failed installed checks')
            installed_state(new);result['resumed_app_checks'].append(10)
            uninstaller=registered_uninstaller(install,registration())
            call(stage+'-uninstall',[uninstaller,'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'])
            def removed():
                assert_managed_removed(install,new)
                return not registration() and not shortcut.exists() and not uninstaller.exists()
            wait_until(removed);installed=False;user_unchanged()
            result['interruption_cases']+=1
            result['checks'].append('Actual owned process-tree termination and normal-installer resume passes ten app checks: '+stage)
        result['process_termination_verified']=True;result['user_data_preserved']=True;result['accepted']=True
    except Exception as exc:
        result['error']=f'{type(exc).__name__}: {exc}'
        result['failed_step']=result['commands'][-1]['label'] if result['commands'] else ''
        (reports/'driver-error.log').write_text(traceback.format_exc(),encoding='utf-8')
    finally:
        if active is not None and active.poll() is None:
            try:
                call('cleanup-owned-tree',['taskkill','/PID',str(active.pid),'/T','/F']);active.wait(timeout=30)
            except Exception as exc:result['cleanup_process_error']=str(exc)
        if installed and registration():
            try:call('failed-recovery-uninstall',[registered_uninstaller(install,registration()),'/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART'])
            except Exception as exc:result['cleanup_error']=str(exc)
        for path,expected in user.items():
            try:
                _chain(path)
                if file_hash(path)==expected:path.unlink()
            except OSError:pass
        if fixture.is_dir():
            for path in sorted(fixture.rglob('*'),reverse=True):
                if path.is_dir() and not path.is_symlink():
                    try:path.rmdir()
                    except OSError:pass
            try:fixture.rmdir()
            except OSError:pass
        result['checks_passed']=len(result['checks'])
        (reports/'recovery-lifecycle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ['bundle','previous-bundle','setup','previous-setup','output','reports']:parser.add_argument('--'+name,type=Path,required=True)
    args=parser.parse_args();r=check(args.bundle,args.previous_bundle,args.setup,args.previous_setup,args.output,args.reports)
    print('Windows interrupted installation resume accepted:',r['accepted'],'cases:',r['interruption_cases'])
    raise SystemExit(0 if r['accepted'] else 1)

"""把已產生的 CI 報告附上 job summary；不推定未執行測試，也不發布安裝包。"""
import argparse
import json
import os
from pathlib import Path


def publish_annotation(records, tails):
    """公開摘要不一定可匿名讀取；另以有界 annotation 保存自身 CI 的實際結果。"""
    if os.environ.get('GITHUB_ACTIONS') != 'true':
        return
    result = records.get('windows-build.json', records.get('build-evidence.json', {}))
    accepted = result.get('overall_accepted',result.get('validation_accepted', result.get('cross_build_complete')))
    # 公開頁會截斷約 5 KB 的 annotation；優先放真正失敗步驟，完整 JSON 留在 summary／artifact。
    def brief(record):
        keys = ('check', 'source_version', 'commit', 'accepted', 'build_verified', 'validation_accepted',
                'windows_executed', 'python_utf8_mode', 'gui', 'checks_passed', 'error', 'cross_build_complete',
                'clean_machine_accepted', 'release_ready','overall_accepted','installer_accepted',
                'install_verified','repair_verified','uninstall_verified','user_data_preserved',
                'shortcut_verified','installed_app_checks','full_c11_complete','installer_sha256',
                'compiler_sha256','compiler_license_sha256','bundle_catalog_sha256','catalog_files')
        keys += ('upgrade_accepted','previous_version','upgrade_verified','rollback_verified','downgrade_blocked',
                 'obsolete_files_removed','all_profiles_accepted','automatic_failure_rollback',
                 'upgraded_app_checks','rolled_back_app_checks','previous_commit')
        keys += ('failed_step',)
        keys += ('recovery_accepted','interruption_cases','resumed_app_checks','process_termination_verified',
                 'pending_app_blocked','explicit_resume_required','power_loss_accepted','test_only_fault_installer')
        return {key: value[:250] if isinstance(value, str) else value
                for key, value in record.items() if key in keys}
    payload = dict(result=brief(result))
    if 'acceptance/windows-acceptance.json' in records:
        payload['acceptance'] = brief(records['acceptance/windows-acceptance.json'])
    if 'installer/installer-lifecycle.json' in records:
        payload['installer'] = brief(records['installer/installer-lifecycle.json'])
    if 'upgrade/upgrade-lifecycle.json' in records:
        payload['upgrade'] = brief(records['upgrade/upgrade-lifecycle.json'])
    if 'recovery/recovery-lifecycle.json' in records:
        payload['recovery'] = brief(records['recovery/recovery-lifecycle.json'])
    if not accepted:
        commands = result.get('commands', [])
        last = commands[-1].get('label', '') if commands and isinstance(commands[-1], dict) else ''
        installer=records.get('installer/installer-lifecycle.json',{})
        commands=installer.get('commands',[])
        inner=commands[-1].get('label','') if commands and isinstance(commands[-1],dict) else ''
        command_failure=str(installer.get('error','')).startswith(('CalledProcessError','TimeoutExpired'))
        candidates = ['installer/installed-acceptance/driver-error.log']
        upgrade=records.get('upgrade/upgrade-lifecycle.json',{})
        if upgrade and not upgrade.get('accepted'):
            steps=upgrade.get('commands',[])
            inner_upgrade=upgrade.get('failed_step') or (steps[-1].get('label','') if steps else '')
            # 優先最深層實際 app／編譯日誌，避免 wrapper traceback 蓋過真正原因。
            candidates=['upgrade/'+inner_upgrade+'/driver-error.log']
            # 舊報告未固定 failed_step 時，也能優先找到真正 app 自檢，不能選到空的卸載 log。
            candidates += sorted(name for name in tails if name.startswith('upgrade/') and name.endswith('-acceptance/driver-error.log'))
            if str(upgrade.get('error','')).startswith(('CalledProcessError','TimeoutExpired')):
                candidates.append('upgrade/'+inner_upgrade+'.log')
            candidates.append('upgrade/driver-error.log')
        recovery=records.get('recovery/recovery-lifecycle.json',{})
        if recovery and not recovery.get('accepted'):
            failed=recovery.get('failed_step','')
            candidates=['recovery/'+failed+'/driver-error.log']
            if str(recovery.get('error','')).startswith(('CalledProcessError','TimeoutExpired')):
                candidates.append('recovery/'+failed+'.log')
            candidates.append('recovery/driver-error.log')
        if command_failure:candidates.append('installer/'+inner+'.log')
        candidates += ['installer/driver-error.log','acceptance/driver-error.log', last+'.log']
        selected = next((name for name in candidates if name in tails), next(reversed(tails), ''))
        payload['failure_log'] = selected
        payload['failure_tail'] = tails.get(selected, '')[-750:]
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    # 字元界線上減少尾段，確保 UTF-8 與 workflow command 跳脫後也不超過公開頁截斷門檻。
    while len(body.replace('%', '%25').encode('utf-8')) > 3800:
        if len(payload.get('failure_tail', '')) > 100:
            payload['failure_tail'] = payload['failure_tail'][100:]
        else:
            payload = dict(result=brief(result), detail='Full details remain in the CI artifact and job summary.')
            break
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    if len(body.replace('%', '%25').encode('utf-8')) > 3800:
        payload = dict(result=dict(accepted=accepted is True, error=str(result.get('error', ''))[-300:]),
                       detail='Full details remain in the CI artifact and job summary.')
        body = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    # GitHub workflow command 的資料必須跳脫，避免日誌換行被誤認為下一條指令。
    body = body.replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
    severity = 'notice' if accepted else 'error'
    print(f'::{severity} title=Windows CI actual report::{body}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    records = {}
    for name in ['build-evidence.json', 'native-inputs/downloads.json', 'windows-build.json', 'acceptance/windows-acceptance.json',
                 'acceptance/core-self-test.json','acceptance/full-self-test.json',
                 'acceptance/relocated-self-test.json','installer/installer-lifecycle.json',
                 'upgrade/upgrade-lifecycle.json','previous-build/windows-build.json',
                 'previous-build/acceptance/windows-acceptance.json','recovery/recovery-lifecycle.json']:
        path = args.reports/name
        if path.is_file():
            if path.stat().st_size > 512*1024:
                raise ValueError('CI summary 報告超過限制。')
            records[name] = json.loads(path.read_text(encoding='utf-8'))
    tails = {}
    # 僅列開發管線自身的日誌末段；CI 不處理使用者文件或輸出環境秘密。
    for path in sorted(args.reports.rglob('*.log')):
        if path.stat().st_size > 8*1024**2:
            continue
        raw=path.read_bytes()
        encoding='utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig'
        tails[path.relative_to(args.reports).as_posix()] = '\n'.join(raw.decode(encoding,errors='replace').splitlines()[-35:])[-6000:]
    content = json.dumps(dict(schema_version=1, reports=records, log_tails=tails), ensure_ascii=False, indent=2)
    if len(content.encode('utf-8')) > 900*1024:
        raise ValueError('CI summary 超過平台上限。')
    with args.summary.open('a', encoding='utf-8') as output:
        output.write('\n## Windows 基本包驗證報告\n\n')
        output.write('僅為 CI 開發驗證；乾淨機、人工操作、完整安裝生命週期與 GPU 尚未驗收。\n\n')
        output.write('<!-- MARKITDOWN_WINDOWS_CI_REPORT -->\n```json\n'+content+'\n```\n')
    publish_annotation(records, tails)


if __name__ == '__main__':
    main()

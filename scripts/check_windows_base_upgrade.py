"""可拋棄 Windows CI 的真實基本包跨版重裝／明確回復；非失敗自動回滾或全 profile 驗收。"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import uuid

from base_install_catalog import CATALOG, ENTRY, verify, assert_managed_removed
from base_install_transition import write_rules, plan
from check_windows_base_installer import known_folder, registration, wait_until, SHORTCUT
from check_windows_base import native_environment
from desktop_app.components.contracts import Version
from desktop_app.components.registry import _chain
from desktop_app.native_assets import file_hash

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS_COMMIT = '43cf811356a7616b784cba09191afdfcb52e16a7'


def check(bundle, previous_bundle, previous_source, setup, work, reports, *, iscc=None):
    if sys.platform != 'win32': raise RuntimeError('Requires actual Windows')
    if os.environ.get('GITHUB_ACTIONS') != 'true' or os.environ.get('RUNNER_OS') != 'Windows':
        raise RuntimeError('Requires a disposable Windows CI account')
    bundle, previous_bundle, previous_source, setup, work, reports = [Path(p).absolute()
        for p in (bundle, previous_bundle, previous_source, setup, work, reports)]
    for path in (bundle, previous_bundle, previous_source, setup, work, reports): _chain(path)
    if work.exists() or reports.exists(): raise FileExistsError('Use fresh upgrade work/report directories')
    shortcut = known_folder(2)/SHORTCUT
    if registration() or shortcut.exists(): raise RuntimeError('Existing installation; refusing to replace it')
    work.mkdir(parents=True); reports.mkdir(parents=True)
    result = dict(check='C11-base-cross-version', recorded_at=datetime.now(timezone.utc).isoformat(),
        accepted=False, windows_executed=True, upgrade_verified=False, rollback_verified=False,
        downgrade_blocked=False, obsolete_files_removed=False, user_data_preserved=False,
        all_profiles_accepted=False, automatic_failure_rollback=False, full_c11_complete=False,
        clean_machine_accepted=False, human_ui_accepted=False, release_ready=False, gpu_executed=False,
        checks=[], commands=[])
    install = work/'中文 跨版安裝'/'MarkItDownBase'
    fixture = known_folder(0x1c)/'MarkItDownDesktop/MarkItDownDesktop'/('upgrade-probe-'+uuid.uuid4().hex)
    expected_user = {}; installed = False; old = new = None

    def call(label, argv, *, allow_failure=False, environment=None):
        result['commands'].append(dict(label=label, argv=list(map(str, argv))))
        with (reports/(label+'.log')).open('wb') as log:
            child = subprocess.run(list(map(str, argv)), cwd=ROOT, env=environment or os.environ,
                stdout=log, stderr=subprocess.STDOUT, timeout=600)
        if child.returncode and not allow_failure: raise subprocess.CalledProcessError(child.returncode, argv)
        return child.returncode

    def assert_user():
        for path, expected in expected_user.items():
            _chain(path)
            if file_hash(path) != expected: raise RuntimeError('Synthetic user data changed')

    def assert_installed(expected):
        extras = {note.name: expected_user[note]} if note in expected_user else {}
        verify(install, expected, installed=True, allowed_extras=extras)
        records = registration()
        if not records or not shortcut.is_file(): raise RuntimeError('Registration or shortcut missing')
        for row in records:
            location = row.get('InstallLocation', row.get('Inno Setup: App Path', ''))
            if Path(location).resolve() != install.resolve() or row.get('DisplayVersion') != expected['app_version']:
                raise RuntimeError('Registered path/version differs')
        assert_user()

    def full_acceptance(label, expected):
        assert_installed(expected)
        other = old if expected is new else new
        for name in plan(expected, other)['obsolete_directories']:
            if (install/name).exists(): raise RuntimeError('Obsolete package directory remains: '+name)
        call(label, [sys.executable, ROOT/'scripts/check_windows_base.py', '--executable', install/ENTRY,
                     '--output', reports/label])
        acceptance = json.loads((reports/label/'windows-acceptance.json').read_text(encoding='utf-8'))
        if (not acceptance['accepted'] or acceptance['checks_passed'] != 10
                or acceptance['source_version'] != expected['app_version']):
            raise RuntimeError('Versioned installed app did not pass all ten checks')
        assert_installed(expected)
        return acceptance

    note = install/'使用者保留文件.txt'
    try:
        observed = subprocess.run(['git', '-C', str(previous_source), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, check=True, timeout=20).stdout.strip()
        if observed != PREVIOUS_COMMIT: raise ValueError('Previous source must be the pinned real 0.15 commit')
        old, new = [json.loads((p/CATALOG).read_text(encoding='utf-8')) for p in (previous_bundle, bundle)]
        verify(previous_bundle, old); verify(bundle, new)
        if old['app_version'] != '0.15.0' or Version.parse(old['app_version']) >= Version.parse(new['app_version']):
            raise ValueError('Use a genuine earlier app version, not a relabeled current payload')
        result.update(source_version=new['app_version'], previous_version=old['app_version'], previous_commit=observed)
        for label, path in [('previous', previous_bundle/CATALOG), ('target', bundle/CATALOG)]:
            result[label+'_catalog_sha256'] = file_hash(path)[0]
            (reports/(label+'-catalog.json')).write_bytes(path.read_bytes())
        compiler = Path(iscc) if iscc else Path(os.environ.get('ProgramFiles(x86)', 'C:/Program Files (x86)'))/'Inno Setup 6/ISCC.exe'
        _chain(compiler); result['compiler_sha256'] = file_hash(compiler)[0]
        result['target_setup_sha256'] = file_hash(setup)[0]
        # 初次安裝用前版原始 .iss；回復用明確標示的新相容安裝器，payload 仍為真正前版。
        original_dir, rollback_dir = work/'previous-original', work/'previous-compatible'
        call('compile-previous-original', [compiler, '/DBundleDir='+str(previous_bundle),
             '/DOutputDir='+str(original_dir), '/DAppVersion='+old['app_version'], previous_source/'packaging/base-installer.iss'])
        rollback_rules = work/'rollback-rules.iss'
        result['rollback_rules'] = write_rules(rollback_rules, previous_bundle, old, bundle, new)
        call('compile-previous-compatible', [compiler, '/DBundleDir='+str(previous_bundle),
             '/DOutputDir='+str(rollback_dir), '/DAppVersion='+old['app_version'],
             '/DTransitionRules='+str(rollback_rules), ROOT/'packaging/base-installer.iss'])
        previous_setup = original_dir/f"MarkItDownBase-Setup-{old['app_version']}-windows-x64.exe"
        rollback_setup = rollback_dir/previous_setup.name
        result['previous_original_setup_sha256'] = file_hash(previous_setup)[0]
        result['previous_compatible_setup_sha256'] = file_hash(rollback_setup)[0]
        result['checks'].append('Two actual source versions and distinct original/compatibility installers verified')
        fixture.mkdir(parents=True)
        for name in ['settings.json', 'models/local.bin', 'component-state/state.sqlite', 'outputs/report.md', 'cache/local.bin']:
            path = fixture/name; path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(('KEEP CROSS-VERSION SYNTHETIC DATA: '+name).encode())
            expected_user[path] = file_hash(path)
        flags = ['/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART', '/SP-']
        installed = True
        call('install-previous', [previous_setup, *flags, '/DIR='+str(install), '/LOG='+str(reports/'previous-inno.log')])
        note.write_bytes(b'KEEP UNKNOWN DOCUMENT THROUGH UPGRADE AND ROLLBACK'); expected_user[note] = file_hash(note)
        full_acceptance('previous-acceptance', old)
        result['checks'].append('Original 0.15 installer and actual old application pass ten installed checks')
        # 真正破壞一個將被移除的舊檔，再還原 catalog；拒絕時不能偷偷覆寫其他前版 bytes。
        obsolete = plan(new, old)['obsolete_files']
        if not obsolete: raise RuntimeError('Fixture must include a real removed owned file between builds')
        for label, path in [('changed-obsolete', install/obsolete[0]['path']), ('changed-catalog', install/CATALOG)]:
            saved = path.read_bytes(); path.write_bytes(saved+b'controlled changed prior file')
            try:
                if call('reject-'+label, [setup, *flags, '/LOG='+str(reports/(label+'-inno.log'))], allow_failure=True) == 0:
                    raise RuntimeError('Untrusted previous state was accepted: '+label)
            finally:
                path.write_bytes(saved)
            assert_installed(old)
        old_directories = plan(new, old)['obsolete_directories']
        if not old_directories: raise RuntimeError('Fixture must include actual versioned package directories')
        unknown = install/old_directories[0]/'不可刪除的使用者文件.txt'
        unknown.write_bytes(b'KEEP UNKNOWN FILE IN OLD PACKAGE DIRECTORY'); before_unknown = file_hash(unknown)
        try:
            if call('reject-old-directory-data', [setup, *flags, '/LOG='+str(reports/'old-directory-data-inno.log')], allow_failure=True) == 0:
                raise RuntimeError('Upgrade removed an old directory containing unknown data')
            if file_hash(unknown) != before_unknown: raise RuntimeError('Unknown old-directory data was changed')
        finally:
            if unknown.is_file() and file_hash(unknown) == before_unknown: unknown.unlink()
        assert_installed(old)
        result['checks'].append('Changed obsolete file/catalog or unknown old-directory data blocks upgrade with old app intact')
        added = plan(new, old)['added_paths']
        if not added: raise RuntimeError('Fixture must include a real added owned file')
        conflict = install/added[0]; conflict.parent.mkdir(parents=True, exist_ok=True)
        conflict.write_bytes(b'UNKNOWN USER FILE AT A NEW APPLICATION PATH')
        before = file_hash(conflict)
        try:
            if call('reject-untracked-collision', [setup, *flags, '/LOG='+str(reports/'collision-inno.log')], allow_failure=True) == 0:
                raise RuntimeError('Upgrade overwrote an unknown user file at a new application path')
            if file_hash(conflict) != before: raise RuntimeError('Rejected upgrade changed the unknown file')
        finally:
            if conflict.is_file() and file_hash(conflict) == before: conflict.unlink()
        assert_installed(old)
        result['checks'].append('New owned path colliding with an unknown user file blocks upgrade without overwriting it')
        # 真建 Windows junction，目標只指向本輪唯一合成 fixture；驗新版不沿父鏈寫到其他目錄。
        junction = conflict.parent
        junction.rmdir()
        destination = fixture/'junction-target'; destination.mkdir()
        canary = destination/'KEEP.txt'; canary.write_bytes(b'KEEP JUNCTION TARGET')
        expected_user[canary] = file_hash(canary)
        call('create-junction-control', ['cmd', '/c', 'mklink', '/J', junction, destination])
        try:
            if not junction.is_junction(): raise RuntimeError('Actual Windows junction control was not created')
            if call('reject-linked-target', [setup, *flags, '/LOG='+str(reports/'linked-inno.log')], allow_failure=True) == 0:
                raise RuntimeError('Upgrade followed a linked target path')
            if list(destination.iterdir()) != [canary] or file_hash(canary) != expected_user[canary]:
                raise RuntimeError('Rejected upgrade wrote through the junction')
        finally:
            # Windows rmdir 移除 junction 本身，不能遞迴刪除它指向的目錄。
            if junction.is_junction(): junction.rmdir()
        assert_installed(old)
        result['checks'].append('Actual Windows junction target is rejected without writing through it')
        # 測試改位置會在寫入前拒絕；原安裝逐檔保持不變。
        alternate = work/'不得另建位置'
        if call('reject-moved-upgrade', [setup, *flags, '/DIR='+str(alternate), '/LOG='+str(reports/'reject-moved-inno.log')], allow_failure=True) == 0:
            raise RuntimeError('Upgrade incorrectly accepted a different installation directory')
        assert_installed(old)
        if (alternate/ENTRY).exists(): raise RuntimeError('Rejected upgrade wrote an application')
        result['checks'].append('Different-directory upgrade is rejected before replacing the previous application')
        call('upgrade', [setup, *flags, '/LOG='+str(reports/'upgrade-inno.log')])
        upgraded = full_acceptance('upgraded-acceptance', new)
        # 0.16 的自檢讀實際 distribution metadata，防止只驗 Setup／registry 的版本標籤。
        actual = json.loads((reports/'upgraded-acceptance/full-self-test.json').read_text(encoding='utf-8'))
        if actual.get('app_version') != new['app_version']: raise RuntimeError('Running app metadata does not match upgraded source')
        result['upgraded_app_checks'] = upgraded['checks_passed']; result['upgrade_verified'] = True
        result['checks'].append('Real upgrade passes target hashes, runtime version and all ten installed app checks')
        if call('reject-downgrade', [rollback_setup, *flags, '/LOG='+str(reports/'reject-downgrade-inno.log')], allow_failure=True) == 0:
            raise RuntimeError('Unrequested downgrade was accepted')
        assert_installed(new); result['downgrade_blocked'] = True
        result['checks'].append('Unrequested downgrade is blocked with the new installation intact')
        call('explicit-rollback', [rollback_setup, *flags, '/ALLOWDOWNGRADE=1', '/LOG='+str(reports/'rollback-inno.log')])
        restored = full_acceptance('rolled-back-acceptance', old)
        result['rolled_back_app_checks'] = restored['checks_passed']; result['rollback_verified'] = True
        result['checks'].append('Explicit compatibility reinstall restores the genuine previous app and all ten checks')
        call('upgrade-again', [setup, *flags, '/LOG='+str(reports/'upgrade-again-inno.log')])
        assert_installed(new)
        call('upgraded-self-test', [install/ENTRY, '--self-test', '--report', reports/'upgrade-again-self-test.json'], environment=native_environment())
        repeated = json.loads((reports/'upgrade-again-self-test.json').read_text(encoding='utf-8'))
        if not repeated['complete'] or repeated.get('app_version') != new['app_version']:
            raise RuntimeError('Re-upgraded app is not healthy')
        result['obsolete_files_removed'] = True
        result['checks'].append('Repeat upgrade removes only exact known obsolete files and preserves all synthetic data')
        call('uninstall-upgraded', [install/'unins000.exe', *flags, '/LOG='+str(reports/'uninstall-inno.log')])
        def removed():
            assert_managed_removed(install, old); assert_managed_removed(install, new)
            return not registration() and not shortcut.exists() and not (install/'unins000.exe').exists()
        wait_until(removed); installed = False; assert_user()
        result['user_data_preserved'] = True
        result['checks'].append('Final uninstall removes both versions owned files and keeps external data and unknown note')
        result['accepted'] = True
    except Exception as exc:
        result['error'] = f'{type(exc).__name__}: {exc}'
        # cleanup 會再呼叫子程序；先固定主要失敗步驟，診斷不得被清理動作蓋過。
        result['failed_step'] = result['commands'][-1]['label'] if result['commands'] else ''
        (reports/'driver-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if installed and (install/'unins000.exe').is_file():
            try: call('failed-upgrade-uninstall', [install/'unins000.exe', '/VERYSILENT', '/SUPPRESSMSGBOXES', '/NORESTART'])
            except Exception as exc: result['cleanup_error'] = str(exc)
        # 僅刪自己建立且 hash 仍匹配的哨兵；不把產品資料目錄當 fixture 遞迴清空。
        for path, expected in expected_user.items():
            try:
                _chain(path)
                if file_hash(path) == expected: path.unlink()
            except OSError: pass
        if fixture.is_dir():
            for path in sorted(fixture.rglob('*'), reverse=True):
                if path.is_dir() and not path.is_symlink():
                    try: path.rmdir()
                    except OSError: pass
            try: fixture.rmdir()
            except OSError: pass
        result['checks_passed'] = len(result['checks'])
        (reports/'upgrade-lifecycle.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['bundle', 'previous-bundle', 'previous-source', 'setup', 'output', 'reports']:
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    value = check(args.bundle, args.previous_bundle, args.previous_source, args.setup, args.output, args.reports)
    print('Real cross-version base upgrade accepted:', value['accepted'], 'checks:', value['checks_passed'])
    raise SystemExit(0 if value['accepted'] else 1)

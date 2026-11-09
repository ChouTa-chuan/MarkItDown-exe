"""中斷續修的清單、入口與診斷邊界；Linux 合成檢查不代表 Windows 程序中斷已驗收。"""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import runpy
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import base_install_catalog as catalog
from base_install_transition import write_rules,plan
import check_windows_base_recovery as recovery
from publish_windows_ci_summary import publish_annotation


class BaseRecoveryTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.bundle=self.root/'中文 bundle';self.bundle.mkdir()
        profile=self.bundle/'_internal/desktop_app/data/build-profile.json';profile.parent.mkdir(parents=True)
        profile.write_text(json.dumps(dict(id='base',platform='windows',native_ocr_integrated=True,source_version='0.17.0')))
        (self.bundle/catalog.ENTRY).write_bytes(b'synthetic entry, never executed')
        self.document=catalog.create(self.bundle,'0.17.0')
        self.loader=runpy.run_path(str(ROOT/'packaging/desktop_entry.py'),run_name='entry_test')['installation_incomplete']

    def test_recovery_names_cannot_be_owned_payload_files(self):
        for name in [catalog.PENDING,catalog.PENDING.upper(),catalog.PENDING+'.new']:
            value=deepcopy(self.document);value['files'][0]['path']=name
            with self.subTest(name=name),self.assertRaises(ValueError):catalog.validate(value)

    def test_pending_marker_cannot_be_hidden_as_an_allowed_installed_extra(self):
        marker=self.bundle/catalog.PENDING;marker.write_bytes(b'pending')
        with self.assertRaises(ValueError):catalog.verify(self.bundle,self.document,installed=True)
        with self.assertRaises(ValueError):catalog.verify(self.bundle,self.document,installed=True,
                                                         allowed_extras={marker.name:catalog.file_hash(marker)})

    def test_source_rules_bind_token_and_every_final_file_hash(self):
        rules=self.root/'rules.iss';write_rules(rules,self.bundle,self.document)
        value=plan(self.document);text=rules.read_text(encoding='utf-8-sig')
        self.assertIn("RecoveryToken = 'v1|"+value['target_catalog_sha256']+"|';",text)
        for item in self.document['files']:self.assertIn("TargetHashes.Add('"+item['sha256']+"');",text)
        self.assertEqual(text.count('TargetHashes.Add('),len(self.document['files']))

    def test_recovery_token_changes_with_real_source_catalog_bytes(self):
        changed=deepcopy(self.document);changed['files'][0]['sha256']='a'*64
        self.assertNotEqual(plan(changed)['target_catalog_sha256'],plan(self.document)['target_catalog_sha256'])
        with self.assertRaises(ValueError):write_rules(self.root/'bad.iss',self.bundle,changed)
        self.assertFalse((self.root/'bad.iss').exists())

    def test_frozen_entry_blocks_pending_temp_and_broken_link(self):
        executable=self.bundle/catalog.ENTRY
        self.assertFalse(self.loader(executable,True))
        for name in [catalog.PENDING,catalog.PENDING+'.new']:
            marker=self.bundle/name;marker.write_bytes(b'incomplete')
            self.assertTrue(self.loader(executable,True));marker.unlink()
        marker=self.bundle/catalog.PENDING;marker.symlink_to(self.root/'missing')
        self.assertTrue(self.loader(executable,True))

    def test_source_execution_is_not_blocked_by_an_unrelated_local_marker(self):
        (self.bundle/catalog.PENDING).write_bytes(b'pending')
        self.assertFalse(self.loader(self.bundle/catalog.ENTRY,False))

    def test_entry_stops_before_diagnostics_or_report_creation(self):
        (self.bundle/catalog.PENDING).write_bytes(b'pending');report=self.root/'must-not-exist.json'
        with patch.object(sys,'frozen',True,create=True),patch.object(sys,'executable',str(self.bundle/catalog.ENTRY)), \
             patch.object(sys,'argv',['app','--self-test','--report',str(report)]),patch('multiprocessing.freeze_support'), \
             patch('desktop_app.diagnostics.main') as diagnostic,patch('sys.stderr',new_callable=io.StringIO) as output:
            with self.assertRaises(SystemExit) as caught:runpy.run_path(str(ROOT/'packaging/desktop_entry.py'),run_name='__main__')
        self.assertEqual(caught.exception.code,3);diagnostic.assert_not_called()
        self.assertFalse(report.exists());self.assertIn('安裝尚未完成',output.getvalue())

    @unittest.skipIf(sys.platform=='win32','Linux platform refusal')
    def test_wrong_platform_never_starts_installer_or_queries_registry(self):
        with patch.object(recovery.subprocess,'run') as child,patch.object(recovery,'registration') as registry:
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):
                recovery.check(self.bundle,self.bundle,self.root/'setup',self.root/'old',self.root/'work',self.root/'reports')
        child.assert_not_called();registry.assert_not_called();self.assertFalse((self.root/'work').exists())

    def test_registered_uninstaller_handles_changed_inno_suffix_without_shell_arguments(self):
        exe=self.bundle/'unins001.exe';exe.write_bytes(b'synthetic, never executed')
        records=[dict(UninstallString='"'+str(exe)+'" /SILENT')]*2
        self.assertEqual(recovery.registered_uninstaller(self.bundle,records),exe)

    def test_uninstaller_rejects_escape_ambiguous_missing_or_linked_registration(self):
        outside=self.root/'unins001.exe';outside.write_bytes(b'not owned')
        inside=self.bundle/'unins000.exe';inside.write_bytes(b'synthetic')
        other=self.bundle/'unins001.exe';other.write_bytes(b'synthetic')
        for records in [[],[{}],[dict(UninstallString='"'+str(outside)+'"')],
                        [dict(UninstallString=str(inside))],
                        [dict(UninstallString='"'+str(p)+'"') for p in (inside,other)]]:
            with self.subTest(records=records),self.assertRaises(ValueError):recovery.registered_uninstaller(self.bundle,records)
        other.unlink();other.symlink_to(outside)
        with self.assertRaises(RuntimeError):recovery.registered_uninstaller(self.bundle,[dict(UninstallString='"'+str(other)+'"')])

    def test_recovery_error_is_preserved_after_successful_installer_and_cleanup(self):
        reports={'windows-build.json':dict(validation_accepted=True,installer_accepted=True,upgrade_accepted=True,
                    recovery_accepted=False,overall_accepted=False),
                 'recovery/recovery-lifecycle.json':dict(accepted=False,failed_step='payload-written-acceptance',
                    error='CalledProcessError: app failure',commands=[dict(label='failed-recovery-uninstall')])}
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as output:
            publish_annotation(reports,{'recovery/failed-recovery-uninstall.log':'',
                'recovery/payload-written-acceptance/driver-error.log':'actual recovered app failure'})
        self.assertTrue(output.getvalue().startswith('::error'));self.assertIn('actual recovered app failure',output.getvalue())
        self.assertIn('"recovery_accepted":false',output.getvalue())

    def test_public_summary_fits_all_stages_without_inventing_power_loss_acceptance(self):
        actual=json.loads((ROOT/'docs/development-records/runs/c11-upgrade-2026-11-09/public-diagnostic.json').read_text())
        actual['result'].update(recovery_accepted=True,overall_accepted=True)
        actual['recovery']=dict(check='C11-base-interruption-resume',accepted=True,source_version='0.17.0',
            interruption_cases=3,resumed_app_checks=[10,10,10],process_termination_verified=True,pending_app_blocked=True,
            explicit_resume_required=True,power_loss_accepted=False,full_c11_complete=False,all_profiles_accepted=False,
            user_data_preserved=True,automatic_failure_rollback=False,test_only_fault_installer=True,commands=['x'*50000])
        reports={'windows-build.json':actual['result'],'acceptance/windows-acceptance.json':actual['acceptance'],
                 'installer/installer-lifecycle.json':actual['installer'],'upgrade/upgrade-lifecycle.json':actual['upgrade'],
                 'recovery/recovery-lifecycle.json':actual['recovery']}
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as output:
            publish_annotation(reports,{})
        self.assertLess(len(output.getvalue().encode()),3900)
        value=json.loads(output.getvalue().split('::')[-1]);self.assertEqual(value['recovery']['interruption_cases'],3)
        self.assertFalse(value['recovery']['power_loss_accepted']);self.assertFalse(value['recovery']['full_c11_complete'])


if __name__=='__main__':unittest.main()

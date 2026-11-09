"""升級規則的真實檔案／版本信任邊界；Linux 結果不代替 Inno 或 Windows 實測。"""
from copy import deepcopy
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from base_install_catalog import create, CATALOG, ENTRY
from base_install_transition import plan, write_rules
import check_windows_base_upgrade as upgrade
from publish_windows_ci_summary import publish_annotation


class BaseUpgradeTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);self.root=Path(temp.name)
        self.old_dir,self.new_dir=self.root/'old',self.root/'new'
        for path,version in [(self.old_dir,'0.15.0'),(self.new_dir,'0.16.0')]:
            profile=path/'_internal/desktop_app/data/build-profile.json';profile.parent.mkdir(parents=True)
            profile.write_text(json.dumps(dict(id='base',platform='windows',native_ocr_integrated=True,source_version=version)))
            (path/ENTRY).write_bytes(('synthetic, never executable '+version).encode())
        (self.old_dir/"舊版'授權.txt").write_bytes(b'previous owned file')
        (self.new_dir/'新版授權.txt').write_bytes(b'new owned file')
        self.old,self.new=create(self.old_dir,'0.15.0'),create(self.new_dir,'0.16.0')

    def test_removed_files_use_only_trusted_previous_ownership_and_hashes(self):
        forward=plan(self.new,self.old);backward=plan(self.old,self.new)
        self.assertEqual([p['path'] for p in forward['obsolete_files']],["舊版'授權.txt"])
        self.assertEqual([p['path'] for p in backward['obsolete_files']],['新版授權.txt'])
        self.assertEqual(forward['added_paths'],['新版授權.txt'])
        self.assertEqual(backward['added_paths'],["舊版'授權.txt"])
        self.assertEqual(forward['obsolete_files'][0],next(p for p in self.old['files'] if p['path']=="舊版'授權.txt"))
        self.assertFalse(forward['automatic_failure_rollback'])

    def test_generator_preserves_unicode_escapes_literals_and_never_overwrites(self):
        path=self.root/'rules.iss'
        write_rules(path,self.new_dir,self.new,self.old_dir,self.old)
        text=path.read_text(encoding='utf-8-sig');self.assertIn("舊版''授權.txt",text)
        self.assertIn(plan(self.new,self.old)['previous_catalog_sha256'],text)
        before=path.read_bytes()
        with self.assertRaises(FileExistsError):write_rules(path,self.new_dir,self.new,self.old_dir,self.old)
        self.assertEqual(path.read_bytes(),before)

    def test_tampered_build_or_catalog_cannot_generate_deletion_rules(self):
        (self.old_dir/ENTRY).write_bytes(b'tampered')
        with self.assertRaises(RuntimeError):write_rules(self.root/'rules.iss',self.new_dir,self.new,self.old_dir,self.old)
        self.assertFalse((self.root/'rules.iss').exists())
        (self.new_dir/CATALOG).write_text('{}')
        with self.assertRaises(ValueError):write_rules(self.root/'rules.iss',self.new_dir,self.new)

    def test_previous_catalog_and_source_directory_must_be_paired(self):
        with self.assertRaises(ValueError):write_rules(self.root/'rules.iss',self.new_dir,self.new,previous=self.old)
        with self.assertRaises(ValueError):write_rules(self.root/'rules.iss',self.new_dir,self.new,self.old_dir)

    def test_same_version_and_case_only_rename_are_rejected(self):
        with self.assertRaises(ValueError):plan(self.new,self.new)
        changed=deepcopy(self.new)
        changed['files'][next(i for i,p in enumerate(changed['files']) if p['path']==ENTRY)]['path']=ENTRY.lower()
        with self.assertRaises(ValueError):plan(changed,self.old)

    def test_windows_version_precision_and_initial_install_without_previous(self):
        self.assertEqual(plan(self.new)['obsolete_files'],[])
        self.assertEqual(plan(self.new)['previous_version'],'')
        changed=deepcopy(self.new);changed['app_version']='0.65536.0'
        with self.assertRaises(ValueError):plan(changed,self.old)

    @unittest.skipIf(sys.platform=='win32','Linux platform refusal')
    def test_platform_guard_precedes_every_registry_child_and_filesystem_change(self):
        with patch.object(upgrade.subprocess,'run') as child,patch.object(upgrade,'registration') as registry:
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):
                upgrade.check(self.new_dir,self.old_dir,ROOT,self.root/'setup.exe',self.root/'work',self.root/'reports')
        child.assert_not_called();registry.assert_not_called()
        self.assertFalse((self.root/'work').exists());self.assertFalse((self.root/'reports').exists())

    def test_failure_annotation_does_not_mask_upgrade_with_installer_success(self):
        records={'windows-build.json':dict(validation_accepted=True,installer_accepted=True,upgrade_accepted=False,overall_accepted=False),
                 'upgrade/upgrade-lifecycle.json':dict(accepted=False,error='CalledProcessError: compiler',
                    commands=[dict(label='compile-previous-compatible')])}
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as stream:
            publish_annotation(records,{'upgrade/driver-error.log':'wrapper',
                                       'upgrade/compile-previous-compatible.log':'actual Pascal compiler failure'})
        self.assertTrue(stream.getvalue().startswith('::error'))
        self.assertIn('actual Pascal compiler failure',stream.getvalue())
        self.assertIn('"upgrade_accepted":false',stream.getvalue())

    def test_success_summary_retains_partial_acceptance_and_actual_versions(self):
        records={'windows-build.json':dict(validation_accepted=True,installer_accepted=True,upgrade_accepted=True,overall_accepted=True),
                 'upgrade/upgrade-lifecycle.json':dict(accepted=True,source_version='0.16.0',previous_version='0.15.0',
                    full_c11_complete=False,all_profiles_accepted=False,automatic_failure_rollback=False,checks_passed=8)}
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as stream:
            publish_annotation(records,{})
        self.assertTrue(stream.getvalue().startswith('::notice'))
        payload=json.loads(stream.getvalue().split('::')[-1])
        self.assertEqual(payload['upgrade']['previous_version'],'0.15.0')
        self.assertFalse(payload['upgrade']['all_profiles_accepted'])
        self.assertFalse(payload['upgrade']['automatic_failure_rollback'])


if __name__=='__main__':unittest.main()

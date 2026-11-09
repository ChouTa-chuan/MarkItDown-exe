"""安裝清單與資料保留契約；合成檔案不冒充 Windows／Inno 安裝。"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import base_install_catalog as catalog
import check_windows_base_installer as installer
from publish_windows_ci_summary import publish_annotation


class BaseInstallerTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.bundle=self.root/'中文 bundle';self.bundle.mkdir()
        profile=self.bundle/'_internal/desktop_app/data/build-profile.json'
        profile.parent.mkdir(parents=True)
        profile.write_text(json.dumps(dict(id='base',platform='windows',source_version='0.15.0',native_ocr_integrated=True)))
        (self.bundle/catalog.ENTRY).write_bytes(b'synthetic executable, never run')
        model=self.bundle/'_internal/eng.traineddata';model.write_bytes(b'synthetic model')

    def document(self):return catalog.create(self.bundle,'0.15.0')

    def test_actual_files_roundtrip_and_no_overwrite(self):
        expected=self.document()
        self.assertEqual(catalog.verify(self.bundle,expected),3)
        with self.assertRaises(FileExistsError):self.document()

    def test_missing_changed_and_extra_files_are_rejected(self):
        expected=self.document();entry=self.bundle/catalog.ENTRY;raw=entry.read_bytes()
        entry.unlink()
        with self.assertRaises(OSError):catalog.verify(self.bundle,expected)
        entry.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):catalog.verify(self.bundle,expected)
        entry.write_bytes(raw);(self.bundle/'untracked.dll').write_bytes(b'x')
        with self.assertRaises(ValueError):catalog.verify(self.bundle,expected)

    def test_modified_installed_catalog_is_not_a_new_trust_root(self):
        expected=self.document()
        forged=deepcopy(expected);forged['files'][0]['sha256']='0'*64
        (self.bundle/catalog.CATALOG).write_bytes(catalog.encoded(forged))
        with self.assertRaisesRegex(ValueError,'清單遭變更'):catalog.verify(self.bundle,expected)

    def test_case_alias_escape_and_reserved_metadata_are_rejected(self):
        expected=self.document()
        for name in ['../escape','C:/drive','folder\\name','CON.txt',catalog.CATALOG,'unins000.exe']:
            document=deepcopy(expected);document['files'][0]['path']=name
            with self.subTest(name=name),self.assertRaises(ValueError):catalog.validate(document)
        document=deepcopy(expected);document['files'][1]['path']=document['files'][0]['path'].upper()
        with self.assertRaises(ValueError):catalog.validate(document)

    def test_links_and_replacement_parent_are_rejected(self):
        target=self.root/'elsewhere';target.write_bytes(b'not owned')
        (self.bundle/'linked').symlink_to(target)
        with self.assertRaises(RuntimeError):self.document()

    def test_installer_metadata_exception_is_explicit(self):
        expected=self.document();unins=self.bundle/'unins000.exe';unins.write_bytes(b'synthetic uninstaller, never run')
        with self.assertRaises(ValueError):catalog.verify(self.bundle,expected)
        catalog.verify(self.bundle,expected,installed=True)
        (self.bundle/'unins001.dll').write_bytes(b'not an allowed installer sidecar')
        with self.assertRaises(ValueError):catalog.verify(self.bundle,expected,installed=True)

    def test_unknown_user_file_is_preserved_and_cannot_override_owned_file(self):
        expected=self.document();note=self.bundle/'使用者文件.txt';note.write_bytes(b'KEEP')
        extra={note.name:catalog.file_hash(note)}
        catalog.verify(self.bundle,expected,allowed_extras=extra)
        for item in expected['files']:(self.bundle/item['path']).unlink()
        (self.bundle/catalog.CATALOG).unlink()
        self.assertTrue(catalog.assert_managed_removed(self.bundle,expected))
        self.assertEqual(note.read_bytes(),b'KEEP')

    def test_uninstall_must_remove_every_owned_file(self):
        expected=self.document()
        with self.assertRaises(ValueError):catalog.assert_managed_removed(self.bundle,expected)

    def test_profile_and_package_versions_cannot_diverge(self):
        with self.assertRaises(ValueError):catalog.create(self.bundle,'0.15.1')

    def test_new_inno_identity_is_separate_and_has_no_recursive_deletion(self):
        spec=(ROOT/'packaging/base-installer.iss').read_text(encoding='utf-8-sig')
        self.assertIn('AppId={'+catalog.APP_ID,spec)
        self.assertNotIn(catalog.APP_ID,(ROOT/'packaging/windows-installer.iss').read_text(encoding='utf-8-sig'))
        self.assertNotIn('[InstallDelete]',spec);self.assertNotIn('[UninstallDelete]',spec)
        self.assertIn('PrivilegesRequired=lowest',spec)
        self.assertIn('Filename: "{app}\\'+catalog.ENTRY+'"',spec)

    @unittest.skipIf(sys.platform=='win32','Linux refusal guard')
    def test_linux_guard_never_installs_queries_registry_or_creates_reports(self):
        with patch.object(installer.subprocess,'run') as child,patch.object(installer,'registration') as registry:
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):
                installer.check(self.bundle,self.root/'work',self.root/'reports')
        child.assert_not_called();registry.assert_not_called()
        self.assertFalse((self.root/'work').exists());self.assertFalse((self.root/'reports').exists())

    def test_installer_failure_cannot_be_hidden_by_successful_folder_validation(self):
        import io,os
        records={'windows-build.json':dict(validation_accepted=True,overall_accepted=False,installer_accepted=False),
                 'installer/installer-lifecycle.json':dict(accepted=False,error='real installer failure')}
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as output:
            publish_annotation(records,{'installer/driver-error.log':'specific failure'})
        self.assertTrue(output.getvalue().startswith('::error'))
        self.assertIn('specific failure',output.getvalue())
        records['installer/installer-lifecycle.json'].update(error='CalledProcessError: compiler failed',
                                                           commands=[dict(label='compile-installer')])
        with patch.dict(os.environ,{'GITHUB_ACTIONS':'true'}),patch('sys.stdout',new_callable=io.StringIO) as output:
            publish_annotation(records,{'installer/driver-error.log':'generic wrapper',
                                       'installer/compile-installer.log':'actual compiler reason'})
        self.assertIn('actual compiler reason',output.getvalue())

    def test_real_utf16_inno_log_is_readable_in_summary(self):
        import os
        import publish_windows_ci_summary as publisher
        reports=self.root/'reports';reports.mkdir()
        (reports/'install.log').write_text('安裝／日本語／한국어\n正常完成',encoding='utf-16')
        summary=self.root/'summary.md'
        with patch.object(sys,'argv',['publisher','--reports',str(reports),'--summary',str(summary)]), \
             patch.dict(os.environ,{'GITHUB_ACTIONS':'false'}):publisher.main()
        value=json.loads(summary.read_text().split('```json\n')[1].split('\n```')[0])
        self.assertEqual(value['log_tails']['install.log'],'安裝／日本語／한국어\n正常完成')


if __name__=='__main__':unittest.main()

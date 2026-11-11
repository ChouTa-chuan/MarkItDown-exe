"""候選逐檔快照的內容、來源對照及重驗反例；僅使用合成檔案。"""
import base64
import json
import os
from pathlib import Path
import sys
import tempfile
import subprocess
import shutil
import zipfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from build_provenance import sha256
import candidate_inventory as subject


class InventoryTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.write('.hidden',b'hidden')
        self.write('_internal/module/data.txt',b'original data')

    def write(self,name,body):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body);return path

    def snapshot(self):
        return dict(files=subject.snapshot(self.root))

    def test_all_regular_files_including_hidden_and_empty_have_hashes(self):
        self.write('empty',b'');rows=subject.snapshot(self.root)
        self.assertEqual([p['path'] for p in rows],['.hidden','_internal/module/data.txt','empty'])
        for row in rows:
            self.assertEqual(row['bytes'],(self.root/row['path']).stat().st_size)
            self.assertEqual(row['sha256'],sha256(self.root/row['path']))
        self.assertTrue(subject.verify_inventory(self.root,dict(files=rows)))

    def test_changed_bytes_are_rejected_even_with_same_size(self):
        report=self.snapshot();self.write('.hidden',b'HIDDEN')
        with self.assertRaisesRegex(ValueError,'differs'):subject.verify_inventory(self.root,report)

    def test_added_file_is_rejected(self):
        report=self.snapshot();self.write('new',b'extra')
        with self.assertRaisesRegex(ValueError,'differs'):subject.verify_inventory(self.root,report)

    def test_missing_file_is_rejected(self):
        report=self.snapshot();(self.root/'.hidden').unlink()
        with self.assertRaisesRegex(ValueError,'differs'):subject.verify_inventory(self.root,report)

    def test_renamed_file_is_rejected(self):
        report=self.snapshot();(self.root/'.hidden').rename(self.root/'renamed')
        with self.assertRaisesRegex(ValueError,'differs'):subject.verify_inventory(self.root,report)

    def test_duplicate_entries_and_case_aliases_are_rejected(self):
        report=self.snapshot();report['files'].append(report['files'][0])
        with self.assertRaisesRegex(ValueError,'duplicate'):subject.verify_inventory(self.root,report)
        self.write('NAME',b'1');self.write('name',b'2')
        with self.assertRaisesRegex(ValueError,'case alias'):subject.snapshot(self.root)

    def test_links_to_file_and_directory_are_rejected(self):
        for target in (self.root/'.hidden',self.root/'_internal'):
            link=self.root/'link';link.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'link or reparse'):subject.snapshot(self.root)
            link.unlink()

    def test_special_file_is_rejected_without_reading(self):
        # Linux直接建立FIFO；Windows以lstat模式測同一拒絕分支，無需管理員權限。
        if not hasattr(os,'mkfifo'):
            import stat
            original=Path.lstat
            target=self.write('fifo',b'fixture')
            def mode(path,*args,**kwargs):
                if path==target:return SimpleNamespace(st_mode=stat.S_IFIFO)
                return original(path,*args,**kwargs)
            with patch.object(Path,'lstat',mode),self.assertRaisesRegex(ValueError,'special file'):subject.snapshot(self.root)
            return
        os.mkfifo(self.root/'fifo')
        with self.assertRaisesRegex(ValueError,'special file'):subject.snapshot(self.root)

    def test_junction_branch_is_rejected(self):
        (self.root/'junction').mkdir()
        with patch.object(Path,'is_junction',lambda path:path.name=='junction'),self.assertRaisesRegex(ValueError,'link or reparse'):
            subject.snapshot(self.root)

    def test_file_and_byte_limits_are_enforced(self):
        for name in ('MAX_FILES','MAX_BYTES'):
            with patch.object(subject,name,1),self.assertRaisesRegex(ValueError,'bounded'):subject.snapshot(self.root)

    def test_unreadable_directory_cannot_be_silently_omitted(self):
        with patch.object(subject.os,'scandir',side_effect=PermissionError('fixture denied')),self.assertRaises(PermissionError):
            subject.snapshot(self.root)

    def test_concurrent_file_change_is_rejected(self):
        def changing(path):
            digest=sha256(path);path.write_bytes(b'changed while hashing');return digest
        with patch.object(subject,'sha256',side_effect=changing),self.assertRaisesRegex(ValueError,'changed while reading'):
            subject.snapshot(self.root)

    def test_record_owner_requires_exact_path_and_bytes(self):
        class Entry:
            hash=SimpleNamespace(mode='sha256',value=base64.urlsafe_b64encode(bytes.fromhex(sha256(self.root/'_internal/module/data.txt'))).decode().rstrip('='))
            def __str__(self):return 'module/data.txt'
        dist=SimpleNamespace(metadata={'Name':'Example_Package'},version='2',files=[Entry()])
        rows={r['path'].casefold():r for r in subject.snapshot(self.root)}
        with patch.object(subject.metadata,'distributions',return_value=[dist]):
            owners=subject.record_owners(rows)
            self.assertEqual(owners['_internal/module/data.txt'][0]['name'],'example-package')
            rows['_internal/module/data.txt']['sha256']='0'*64
            self.assertEqual(subject.record_owners(rows),{})

    def complete(self):
        self.write('App.exe',b'entry');meta=self.write('_internal/assets/METADATA',b'metadata')
        notice=self.write('_internal/assets/LICENSE.txt',b'original')
        self.write('_internal/assets/bootloader/COPYING.txt',b'bootloader')
        self.write('_internal/assets/python/LICENSE.txt',b'python')
        packages=[dict(name='markitdown-desktop',version='0.19.1',metadata_path='_internal/assets/METADATA',
            metadata_sha256=sha256(meta),notices=[dict(path='_internal/assets/LICENSE.txt',sha256=sha256(notice))])]
        loader=dict(prefix='bootloader',version='6.22.3',files={'COPYING.txt':sha256(self.root/'_internal/assets/bootloader/COPYING.txt')})
        return packages,loader

    def run_inventory(self,packages,loader,native=()):
        with patch.object(subject,'record_owners',return_value={}):
            return subject.inventory(self.root,packages,native,loader,'_internal/assets','python/LICENSE.txt','App.exe')

    def test_complete_file_list_keeps_unresolved_source_and_archives_pending(self):
        packages,loader=self.complete();self.write('_internal/base_library.zip',b'archive fixture')
        report=self.run_inventory(packages,loader)
        self.assertEqual(report['summary']['files'],len(subject.snapshot(self.root)))
        self.assertTrue(report['summary']['file_inventory_complete'])
        self.assertFalse(report['summary']['runtime_sbom_complete']);self.assertFalse(report['summary']['redistribution_approved'])
        self.assertFalse(report['summary']['release_ready'])
        archive=next(r for r in report['files'] if r['role']=='archive')
        self.assertIn('archive-members-not-enumerated',archive['review_reasons'])
        self.assertTrue(report['summary']['unresolved_files'])

    def test_original_notice_mapping_has_package_version_and_hash(self):
        packages,loader=self.complete();report=self.run_inventory(packages,loader)
        notice=next(r for r in report['files'] if r['path']=='_internal/assets/LICENSE.txt')
        self.assertEqual(notice['role'],'original-notice');self.assertEqual(notice['owners'][0]['version'],'0.19.1')
        self.assertEqual(notice['sha256'],packages[0]['notices'][0]['sha256'])

    def test_missing_or_changed_package_reference_is_rejected(self):
        packages,loader=self.complete();packages[0]['metadata_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'reference mismatch'):self.run_inventory(packages,loader)

    def test_microsoft_dll_is_not_cleared_by_python_license_location(self):
        packages,loader=self.complete();self.write('_internal/VCRUNTIME140.dll',b'fixture')
        native=[dict(file='VCRUNTIME140.dll',distributions=[],origin='python-runtime',bytes_changed=False)]
        report=self.run_inventory(packages,loader,native)
        row=next(r for r in report['files'] if r['path']=='_internal/VCRUNTIME140.dll')
        self.assertNotIn('_internal/assets/python/LICENSE.txt',row['notice_paths'])
        self.assertIn('microsoft-native-redistribution-review',row['review_reasons'])

    def test_cli_reverification_and_public_summary_are_bounded(self):
        # 重用已有fixture，不把TestCase匯入模組全域以免discover重複計數。
        from test_bundle_provenance import ProvenanceTests
        fixture=ProvenanceTests();fixture.setUp();self.addCleanup(fixture.doCleanups)
        script=Path(__file__).resolve().parents[1]/'scripts/check_bundle_provenance.py'
        report=self.root/'first.json'
        output=self.package(fixture.bundle)
        argv=[sys.executable,str(script),'--profile','cpu','--bundle',str(fixture.bundle),'--package-directory',str(output)]
        env={**os.environ,'GITHUB_ACTIONS':'true','GITHUB_SHA':'1'*40}
        result=subprocess.run([*argv,'--report',str(report)],capture_output=True,text=True,env=env,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        self.assertLess(len(result.stdout.encode()),4000)
        brief=json.loads(result.stdout.removeprefix('::notice::'))
        self.assertTrue(brief['inventory']['file_inventory_complete'])
        self.assertFalse(brief['inventory']['runtime_sbom_complete'])
        self.assertTrue(brief['package_inventory']['archive_verified'])
        self.assertEqual(brief['package_inventory']['files'],brief['inventory']['files']+1)
        self.assertEqual(brief['report_sha256'],sha256(report))
        args=[*argv,'--verify-inventory',str(report)]
        result=subprocess.run([*args,'--report',str(self.root/'second.json')],capture_output=True,text=True,env=env,timeout=30)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        (fixture.bundle/'extra').write_bytes(b'extra')
        result=subprocess.run([*args,'--report',str(self.root/'third.json')],capture_output=True,text=True,env=env,timeout=30)
        self.assertEqual(result.returncode,1)
        self.assertIn('Candidate inventory differs',result.stdout)

    def package(self,bundle=None):
        from package_cpu_worker import package
        output=Path(tempfile.mkdtemp());output.rmdir()
        self.addCleanup(shutil.rmtree,output,ignore_errors=True)
        package(bundle or self.root,output)
        return output

    def refresh_descriptor_archive_hash(self,output):
        archive=output/'onnx-cpu-ocr-development.zip';path=output/'component.json'
        record=json.loads(path.read_text());record.update(package_sha256=sha256(archive),download_bytes=archive.stat().st_size)
        path.write_text(json.dumps(record))

    def test_actual_zip_inventory_includes_generated_notice(self):
        contents=self.snapshot();output=self.package();report=subject.component_inventory(output,contents)
        self.assertEqual(report['summary']['files'],len(contents['files'])+1)
        self.assertIn('NOTICE.txt',[row['path'] for row in report['files']])
        self.assertTrue(report['summary']['archive_verified']);self.assertFalse(report['summary']['redistribution_approved'])
        (output/'NOTICE.txt').write_bytes(b'changed notice')
        with self.assertRaisesRegex(ValueError,'descriptor differs'):subject.component_inventory(output,contents)

    def test_changed_zip_archive_is_rejected(self):
        contents=self.snapshot();output=self.package()
        with (output/'onnx-cpu-ocr-development.zip').open('ab') as file:file.write(b'changed')
        with self.assertRaisesRegex(ValueError,'archive fingerprint mismatch'):subject.component_inventory(output,contents)

    def test_extra_zip_entry_is_rejected_even_if_archive_hash_matches(self):
        contents=self.snapshot();output=self.package()
        with zipfile.ZipFile(output/'onnx-cpu-ocr-development.zip','a') as archive:archive.writestr('extra',b'extra')
        self.refresh_descriptor_archive_hash(output)
        with self.assertRaisesRegex(ValueError,'Unexpected'):subject.component_inventory(output,contents)

    def test_missing_zip_entry_is_rejected_even_if_archive_hash_matches(self):
        contents=self.snapshot();output=self.package();path=output/'onnx-cpu-ocr-development.zip'
        with zipfile.ZipFile(path) as archive:files={p:archive.read(p) for p in archive.namelist() if p!='NOTICE.txt'}
        with zipfile.ZipFile(path,'w') as archive:
            for name,data in files.items():archive.writestr(name,data)
        self.refresh_descriptor_archive_hash(output)
        with self.assertRaisesRegex(ValueError,'missing inventory entry'):subject.component_inventory(output,contents)


if __name__=='__main__':unittest.main()

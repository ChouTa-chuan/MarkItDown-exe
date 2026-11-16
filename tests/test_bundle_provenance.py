"""以合成包驗證指紋與拒絕條件，不把 fixture 當作 Windows 原生執行。"""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_provenance import bootloader_notices, distribution_sources, sha256
from check_bundle_provenance import audit, contained_file
from prepare_worker_assets import native_notices


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.bundle=self.root/'bundle';self.assets=self.bundle/'_internal/worker-assets'
        self.assets.mkdir(parents=True)
        self.write(self.bundle/'MarkItDownOCRWorker.exe', b'fixture entry')
        self.write(self.bundle/'_internal/runtime.dll', b'collected binary')
        self.write(self.assets/'python-runtime/LICENSE.txt', b'original Python fixture')
        notice='installed/markitdown-desktop/original/LICENSE.txt'
        meta='installed/markitdown-desktop/METADATA'
        self.write(self.assets/notice, b'original fixture notice')
        self.write(self.assets/meta, b'Name: markitdown-desktop\nVersion: 0.19.1\n')
        self.installed=dict(packages=[dict(name='markitdown-desktop',version='0.19.1',notice_files=[notice])],
                            files={p:sha256(self.assets/p) for p in (notice,meta)})
        self.save(self.assets/'installed-manifest.json',self.installed)
        self.write(self.assets/'bootloader/original/COPYING.txt', b'original bootloader fixture')
        self.save(self.assets/'bootloader/manifest.json',dict(name='pyinstaller',version='6.22.3',
                  files={'original/COPYING.txt':sha256(self.assets/'bootloader/original/COPYING.txt')}))
        self.native=dict(schema_version=2,files=[dict(file='runtime.dll',source_sha256='0'*64,
                         source_bytes=12,origin='system-native',distributions=[])])
        self.save(self.assets/'native/manifest.json',self.native)

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(value)

    def save(self,path,value):
        self.write(path,json.dumps(value).encode())

    def check(self):
        return audit(self.bundle,'cpu','0.19.1')

    def test_distinct_source_and_collected_bytes_are_explicit(self):
        report=self.check()
        self.assertTrue(report['accepted']);self.assertEqual(report['transformed_binaries'],1)
        self.assertFalse(report['redistribution_approved']);self.assertFalse(report['release_ready'])
        self.assertFalse(report['native_execution_performed'])

    def test_excluded_binary_in_bundle_is_rejected_and_identity_fields_are_carried(self):
        self.native['files'][0].update(source_directory='C:/Windows/System32', signature_status='Valid',
                                       signer='CN=Fixture')
        self.save(self.assets/'native/manifest.json', self.native)
        report = self.check()
        self.assertTrue(report['excluded_binaries_absent'])
        self.assertEqual((report['native_files'][0]['source_directory'], report['native_files'][0]['signer']),
                         ('C:/Windows/System32', 'CN=Fixture'))
        self.assertNotIn('company', report['native_files'][0])
        self.write(self.bundle/'_internal/cv2/opencv_videoio_ffmpeg500_64.dll', b'should have been excluded')
        with self.assertRaisesRegex(ValueError, 'Excluded binaries present'):
            self.check()

    def test_changed_original_is_rejected(self):
        (self.assets/'installed/markitdown-desktop/original/LICENSE.txt').write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'Fingerprint mismatch'):self.check()

    def test_metadata_version_conflict_is_rejected_even_with_matching_file_hash(self):
        key='installed/markitdown-desktop/METADATA'
        (self.assets/key).write_text('Name: markitdown-desktop\nVersion: 9.0\n')
        self.installed['files'][key]=sha256(self.assets/key)
        self.save(self.assets/'installed-manifest.json',self.installed)
        with self.assertRaisesRegex(ValueError,'METADATA mismatch'):self.check()

    def test_stale_application_version_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Application version mismatch'):
            audit(self.bundle,'cpu','0.20.0')

    def test_bootloader_original_is_required(self):
        (self.assets/'bootloader/original/COPYING.txt').unlink()
        with self.assertRaisesRegex(ValueError,'Missing or linked'):self.check()

    def test_source_digest_missing_or_malformed_is_rejected(self):
        for value in ('', 'z'*64):
            self.native['files'][0]['source_sha256']=value
            self.save(self.assets/'native/manifest.json',self.native)
            with self.assertRaisesRegex(ValueError,'Invalid native source'):self.check()

    def test_missing_collected_binary_is_rejected(self):
        (self.bundle/'_internal/runtime.dll').unlink()
        with self.assertRaisesRegex(ValueError,'Missing or linked'):self.check()

    def base_fixture(self):
        import shutil
        assets=self.bundle/'_internal/desktop_app/data';assets.mkdir(parents=True)
        shutil.copytree(self.assets/'installed',assets/'licenses/installed')
        shutil.copytree(self.assets/'bootloader',assets/'licenses/bootloader')
        shutil.copytree(self.assets/'python-runtime',assets/'licenses/python-runtime')
        shutil.copytree(self.assets/'native',assets/'licenses/native')
        installed=json.loads(json.dumps(self.installed))
        installed['packages'][0]['notice_files']=['licenses/'+p for p in installed['packages'][0]['notice_files']]
        self.save(assets/'licenses/installed/manifest.json',installed)
        profile=dict(source_version='0.19.1',runtime_packages={},local_packages={'markitdown-desktop':'0.19.1'},
                     assets={p.relative_to(assets).as_posix():sha256(p) for p in assets.rglob('*') if p.is_file()})
        self.save(assets/'build-profile.json',profile)
        self.write(self.bundle/'MarkItDownBase.exe',b'base fixture entry')
        return assets,profile

    def test_base_runtime_and_original_metadata_are_checked(self):
        assets,profile=self.base_fixture()
        self.assertTrue(audit(self.bundle,'base','0.19.1')['accepted'])
        profile['local_packages']['extra']='1';self.save(assets/'build-profile.json',profile)
        with self.assertRaisesRegex(ValueError,'Runtime package list mismatch'):audit(self.bundle,'base','0.19.1')

    def test_final_base_inventory_includes_generated_installer_catalog(self):
        from base_install_catalog import create, CATALOG
        from candidate_inventory import verify_inventory
        assets,profile=self.base_fixture()
        profile.update(id='base',platform='windows',native_ocr_integrated=True)
        self.save(assets/'build-profile.json',profile)
        before=audit(self.bundle,'base','0.19.1')['candidate_inventory']
        create(self.bundle,'0.19.1')
        with self.assertRaisesRegex(ValueError,'differs'):verify_inventory(self.bundle,before)
        after=audit(self.bundle,'base','0.19.1')['candidate_inventory']
        self.assertEqual(after['summary']['files'],before['summary']['files']+1)
        self.assertIn(CATALOG,[row['path'] for row in after['files']])
        self.assertTrue(verify_inventory(self.bundle,after))

    def test_old_native_manifest_and_duplicate_destinations_are_rejected(self):
        self.native['schema_version']=1;self.save(self.assets/'native/manifest.json',self.native)
        with self.assertRaisesRegex(ValueError,'fingerprints missing'):self.check()
        self.native['schema_version']=2;self.native['files']*=2
        self.save(self.assets/'native/manifest.json',self.native)
        with self.assertRaisesRegex(ValueError,'Duplicate native destination'):self.check()

    def test_packages_without_original_notice_remain_pending(self):
        self.installed['packages'][0]['notice_files']=[]
        self.save(self.assets/'installed-manifest.json',self.installed)
        report=self.check()
        self.assertEqual(report['packages_without_wheel_notice'],['markitdown-desktop'])
        self.assertFalse(report['redistribution_approved'])

    def test_manifest_path_escape_is_rejected(self):
        for name in ('../outside','/absolute','C:/windows','dir\\file','a/./b'):
            with self.assertRaisesRegex(ValueError,'Unsafe manifest'):contained_file(self.bundle,name)

    def test_symlinks_and_case_aliases_are_rejected(self):
        self.write(self.bundle/'NAME',b'one');self.write(self.bundle/'name',b'two')
        with self.assertRaisesRegex(ValueError,'case alias'):self.check()
        (self.bundle/'name').unlink();(self.bundle/'NAME').unlink()
        (self.bundle/'link').symlink_to(self.bundle/'MarkItDownOCRWorker.exe')
        with self.assertRaisesRegex(ValueError,'Bundle link'):self.check()

    def test_bootloader_directory_named_notice_preserves_exact_bytes(self):
        source=self.root/'source';key='pkg.dist-info/licenses/Apache-2.0.txt'
        self.write(source/key,b'original\r\nbytes\xff')
        distribution=SimpleNamespace(version='1',files=[key],locate_file=lambda entry:source/entry)
        report=bootloader_notices(self.root/'notices',distribution)
        self.assertEqual((self.root/'notices/original'/key).read_bytes(),b'original\r\nbytes\xff')
        self.assertEqual(report['files']['original/'+key],sha256(source/key))
        with self.assertRaises(FileExistsError):bootloader_notices(self.root/'notices',distribution)

    def test_empty_bootloader_notice_inventory_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'original notice missing'):
            bootloader_notices(self.root/'empty',SimpleNamespace(files=[],version='1'))

    def test_native_source_digest_and_distribution_owner_are_captured(self):
        source=self.root/'runtime.dll';self.write(source,b'actual source fixture')
        dist=SimpleNamespace(metadata={'Name':'Example'},version='2',files=['runtime.dll'],
                             locate_file=lambda entry:self.root/entry)
        with patch('build_provenance.metadata.distributions',return_value=[dist]):
            owners=distribution_sources()
        with patch('prepare_worker_assets.distribution_sources',return_value=owners),patch('prepare_worker_assets.subprocess.run',return_value=SimpleNamespace(returncode=1)):
            report=native_notices([('runtime.dll',str(source),'BINARY')],self.root/'native')
        self.assertEqual(report['schema_version'],2)
        self.assertEqual(report['files'][0]['source_sha256'],sha256(source))
        self.assertEqual(report['files'][0]['distributions'],[dict(name='Example',version='2')])

    def test_windows_analysis_destination_is_normalized_before_audit(self):
        source=self.root/'runtime.dll';self.write(source,b'fixture source')
        with patch('prepare_worker_assets.distribution_sources',return_value={}),patch('prepare_worker_assets.subprocess.run',return_value=SimpleNamespace(returncode=1)):
            report=native_notices([('package.libs\\runtime.dll',str(source),'BINARY')],self.root/'native-windows')
        self.assertEqual(report['files'][0]['file'],'package.libs/runtime.dll')


if __name__=='__main__':unittest.main()

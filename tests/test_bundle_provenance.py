"""以合成包驗證指紋與拒絕條件，不把 fixture 當作 Windows 原生執行。"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_provenance import bootloader_notices, distribution_sources, sha256
from check_bundle_provenance import audit, contained_file
from prepare_worker_assets import native_notices


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.bundle=self.root/'bundle'
        self.assets=self.bundle/'_internal/worker-assets'
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
        # 跨平台合成 fixture 也提供新清單，讓 Windows 的強制檢核不被舊 fixture 繞過。
        from cpython_components import write_inventory, REPORT
        path = self.assets/'native'/REPORT
        write_inventory(self.native['files'], path, target=sys.platform, version='3.12.10',
                        license_path=self.assets/'python-runtime/LICENSE.txt', probe=dict(versions={}, files={}))
        self.native.update(cpython_components=REPORT, cpython_components_sha256=sha256(path))
        self.save(self.assets/'native/manifest.json', self.native)
        self.modules=[dict(name='json',kind='PYMODULE',origin='stdlib',source_sha256='1'*64,source_bytes=5),
                      dict(name='mystery',kind='PYMODULE',origin='unknown',source_sha256=None,source_bytes=None,
                           reason='source-unreadable:FileNotFoundError')]
        self.save(self.assets/'native/python-modules.json',dict(schema_version=1,modules=self.modules))
        with zipfile.ZipFile(self.bundle/'_internal/base_library.zip','w') as archive:
            archive.writestr('os.pyc',b'compiled fixture')

    def write(self,path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value)

    def save(self,path,value):
        self.write(path,json.dumps(value).encode())

    def check(self):
        return audit(self.bundle,'cpu','0.19.1')

    def test_distinct_source_and_collected_bytes_are_explicit(self):
        report=self.check()
        self.assertTrue(report['accepted'])
        self.assertEqual(report['transformed_binaries'],1)
        self.assertFalse(report['redistribution_approved'])
        self.assertFalse(report['release_ready'])
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

    def test_python_archive_inventory_is_reported_and_summarized(self):
        report=self.check()
        archives=report['python_archives']
        self.assertEqual([row['name'] for row in archives['pure_modules']],['json','mystery'])
        self.assertEqual([m['name'] for m in archives['base_library']['members']],['os.pyc'])
        self.assertEqual(archives['base_library']['sha256'],sha256(self.bundle/'_internal/base_library.zip'))
        self.assertEqual(archives['summary']['by_origin']['stdlib'],1)
        self.assertEqual(archives['summary']['unknown_names'],['mystery'])
        self.assertEqual(archives['summary']['base_library_members'],1)
        library=next(r for r in report['candidate_inventory']['files'] if r['path']=='_internal/base_library.zip')
        self.assertNotIn('archive-members-not-enumerated',library['review_reasons'])
        self.assertFalse(report['candidate_inventory']['summary']['runtime_sbom_complete'])

    def test_missing_python_module_manifest_or_base_library_is_rejected(self):
        (self.assets/'native/python-modules.json').unlink()
        with self.assertRaisesRegex(ValueError,'Missing or linked'):
            self.check()
        self.save(self.assets/'native/python-modules.json',dict(schema_version=1,modules=self.modules))
        (self.bundle/'_internal/base_library.zip').unlink()
        with self.assertRaisesRegex(ValueError,'Missing or linked'):
            self.check()

    def test_python_module_manifest_that_is_empty_is_rejected(self):
        self.save(self.assets/'native/python-modules.json',dict(schema_version=1,modules=[]))
        with self.assertRaisesRegex(ValueError,'Invalid or empty'):
            self.check()

    def test_missing_manifest_makes_cli_report_not_accepted(self):
        (self.assets/'native/python-modules.json').unlink()
        script=Path(__file__).resolve().parents[1]/'scripts/check_bundle_provenance.py'
        report=self.root/'report.json'
        result=subprocess.run([sys.executable,str(script),'--profile','cpu','--bundle',str(self.bundle),'--report',str(report)],
                              capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,1)
        self.assertFalse(json.loads(report.read_text())['accepted'])

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

    def test_cpython_sidecar_is_verified_by_the_bundle_auditor(self):
        from cpython_components import REPORT
        path = self.assets/'native'/REPORT
        # 只驗合成清單的檢核接線，applicable 依平台，不把 fixture 當作 Windows 實證。
        report = self.check()
        self.assertEqual(report['cpython_components']['applicable'], sys.platform == 'win32')
        path.write_text('{}')
        with self.assertRaisesRegex(ValueError, 'inventory fingerprint mismatch'):
            self.check()

    def base_fixture(self):
        import shutil
        assets=self.bundle/'_internal/desktop_app/data'
        assets.mkdir(parents=True)
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
        profile['local_packages']['extra']='1'
        self.save(assets/'build-profile.json',profile)
        with self.assertRaisesRegex(ValueError,'Runtime package list mismatch'):audit(self.bundle,'base','0.19.1')

    def test_base_requires_python_module_manifest_in_asset_fingerprints(self):
        assets,profile=self.base_fixture()
        del profile['assets']['licenses/native/python-modules.json']
        self.save(assets/'build-profile.json',profile)
        with self.assertRaisesRegex(ValueError,'not covered by asset fingerprints'):
            audit(self.bundle,'base','0.19.1')

    def test_base_rejects_setuptools_even_with_valid_asset_hash_but_cpu_is_unchanged(self):
        # 排除檢查需真的接到建置後 audit；即使有人重算資產 hash 也不能放回建置工具。
        self.modules.append(dict(name='setuptools._vendor', kind='PYMODULE', origin='unknown',
                                 source_sha256=None, source_bytes=None, reason='namespace-package'))
        self.save(self.assets/'native/python-modules.json', dict(schema_version=1, modules=self.modules))
        self.assertTrue(self.check()['accepted'])
        assets, profile = self.base_fixture()
        with self.assertRaisesRegex(ValueError, 'Build-only modules present'):
            audit(self.bundle, 'base', '0.19.1')
        path = assets/'licenses/native/python-modules.json'
        self.save(path, dict(schema_version=1, modules=self.modules[:-1]))
        profile['assets']['licenses/native/python-modules.json'] = sha256(path)
        self.save(assets/'build-profile.json', profile)
        result = audit(self.bundle, 'base', '0.19.1')
        self.assertTrue(result['python_archives']['summary']['build_only_modules_absent'])

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
        self.native['schema_version']=1
        self.save(self.assets/'native/manifest.json',self.native)
        with self.assertRaisesRegex(ValueError,'fingerprints missing'):self.check()
        self.native['schema_version']=2
        self.native['files']*=2
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
        self.write(self.bundle/'NAME',b'one')
        self.write(self.bundle/'name',b'two')
        with self.assertRaisesRegex(ValueError,'case alias'):self.check()
        (self.bundle/'name').unlink()
        (self.bundle/'NAME').unlink()
        (self.bundle/'link').symlink_to(self.bundle/'MarkItDownOCRWorker.exe')
        with self.assertRaisesRegex(ValueError,'Bundle link'):self.check()

    def test_bootloader_directory_named_notice_preserves_exact_bytes(self):
        source=self.root/'source'
        key='pkg.dist-info/licenses/Apache-2.0.txt'
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
        source=self.root/'runtime.dll'
        self.write(source,b'actual source fixture')
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
        source=self.root/'runtime.dll'
        self.write(source,b'fixture source')
        with patch('prepare_worker_assets.distribution_sources',return_value={}),patch('prepare_worker_assets.subprocess.run',return_value=SimpleNamespace(returncode=1)):
            report=native_notices([('package.libs\\runtime.dll',str(source),'BINARY')],self.root/'native-windows')
        self.assertEqual(report['files'][0]['file'],'package.libs/runtime.dll')


if __name__=='__main__':unittest.main()

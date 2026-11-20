"""以合成目錄與 zip 驗證 Python 程式封存成員清單；不依賴 Windows 或真正的 PyInstaller。"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_provenance import sha256
import cpu_build_tools_audit as audit
from cpu_build_tools_runtime import tool_imports
import python_archive_inventory as subject


class PureModuleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name).resolve()
        # site-packages 刻意放在標準庫目錄之下，與一般 Windows／Linux 安裝相同。
        self.stdlib, self.application = root/'lib', root/'src'
        self.site = self.stdlib/'site-packages'
        self.root = root
        self.files = {}
        for key, path, body in (('std', self.stdlib/'json/__init__.py', b'stdlib'),
                                ('dist', self.site/'demo/__init__.py', b'demo'),
                                ('orphan', self.site/'orphan.py', b'orphan'),
                                ('app', self.application/'desktop_app/__init__.py', b'app'),
                                ('elsewhere', root/'other/stray.py', b'stray')):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            self.files[key] = path

    def run_modules(self, toc, owners=None):
        return {row['name']: row for row in subject.pure_modules(
            toc, [self.stdlib], [self.site], [self.application], owners)}

    def test_four_origins_are_decided_from_roots_and_record_owner(self):
        owners = {self.files['dist'].resolve(): [dict(name='Demo_Pkg', version='1.2')]}
        rows = self.run_modules([('json', str(self.files['std']), 'PYMODULE'),
                                 ('demo', str(self.files['dist']), 'PYMODULE'),
                                 ('desktop_app', str(self.files['app']), 'PYMODULE'),
                                 ('stray', str(self.files['elsewhere']), 'PYMODULE')], owners)
        self.assertEqual(rows['json']['origin'], 'stdlib')
        self.assertEqual(rows['json']['source_sha256'], sha256(self.files['std']))
        self.assertEqual(rows['json']['source_bytes'], 6)
        self.assertEqual((rows['demo']['origin'], rows['demo']['distribution'], rows['demo']['version']),
                         ('distribution', 'demo-pkg', '1.2'))
        self.assertEqual(rows['desktop_app']['origin'], 'application')
        self.assertEqual((rows['stray']['origin'], rows['stray']['reason']), ('unknown', 'outside-known-roots'))
        self.assertNotIn('distribution', rows['stray'])

    def test_site_module_without_unique_record_owner_is_unknown_not_guessed(self):
        path = self.files['orphan']
        rows = self.run_modules([('orphan', str(path), 'PYMODULE')])
        self.assertEqual((rows['orphan']['origin'], rows['orphan']['reason']), ('unknown', 'no-record-owner'))
        self.assertNotIn('distribution', rows['orphan'])
        owners = {path.resolve(): [dict(name='a', version='1'), dict(name='b', version='1')]}
        rows = self.run_modules([('orphan', str(path), 'PYMODULE')], owners)
        self.assertEqual(rows['orphan']['reason'], 'ambiguous-record-owner')

    def test_missing_or_absent_source_is_unknown_with_reason_and_does_not_fail(self):
        rows = self.run_modules([('gone', str(self.stdlib/'gone.py'), 'PYMODULE'), ('empty', '', 'PYMODULE')])
        self.assertEqual((rows['gone']['origin'], rows['gone']['reason']),
                         ('unknown', 'source-unreadable:FileNotFoundError'))
        self.assertIsNone(rows['gone']['source_sha256'])
        self.assertEqual(rows['empty']['reason'], 'no-source-path')

    def test_namespace_package_marker_is_not_resolved_as_a_file(self):
        import os
        self.addCleanup(os.chdir, os.getcwd())
        os.chdir(self.root)
        (self.root/'-').write_bytes(b'stray file named dash')
        rows = self.run_modules([('nspkg', '-', 'PYMODULE')])
        self.assertEqual((rows['nspkg']['origin'], rows['nspkg']['reason']), ('unknown', 'namespace-package'))
        self.assertIsNone(rows['nspkg']['source_sha256'])

    def test_manifest_roundtrip_rejects_malformed_entries(self):
        path = self.root/'python-modules.json'
        modules = [dict(name='json', origin='stdlib', source_sha256='1'*64, source_bytes=3),
                   dict(name='x', origin='unknown', source_sha256=None, source_bytes=None, reason='no-source-path')]
        path.write_text(json.dumps(dict(schema_version=1, modules=modules)))
        self.assertEqual(len(subject.load_manifest(path)), 2)
        path.write_text(json.dumps(dict(schema_version=2, modules=modules)))
        with self.assertRaises(ValueError):
            subject.load_manifest(path)
        for bad in ([modules[0], modules[0]],
                    [dict(modules[0], source_sha256='zz')],
                    [dict(modules[0], origin='distribution')],
                    [dict(modules[1], reason='')],
                    [dict(modules[0], origin='made-up')],
                    [dict(modules[0], source_bytes='3')]):
            path.write_text(json.dumps(dict(schema_version=1, modules=bad)))
            with self.assertRaises(ValueError):
                subject.load_manifest(path)

    def test_write_manifest_uses_injected_owners(self):
        output = self.root/'out.json'
        modules = subject.write_pure_manifest([('stray', str(self.files['elsewhere']), 'PYMODULE')], output, [], owners={})
        self.assertEqual(modules[0]['origin'], 'unknown')
        self.assertEqual(subject.load_manifest(output)[0]['name'], 'stray')


class BaseRuntimeModuleTests(unittest.TestCase):
    def test_build_tools_and_namespace_children_are_rejected_regardless_of_origin(self):
        # 不能靠改 origin 或把 namespace 標成已知套件來掩蓋排除失效。
        for name in ('setuptools', 'setuptools._vendor', 'setuptools._vendor.jaraco',
                     'setuptools._distutils.compilers', 'setuptools._distutils.compilers.C',
                     'setuptools._distutils.compilers.platform'):
            for origin in ('unknown', 'distribution'):
                with self.subTest(name=name, origin=origin):
                    with self.assertRaisesRegex(ValueError, 'Build-only modules present'):
                        subject.verify_base_runtime_modules([dict(name=name, origin=origin)])

    def test_runtime_modules_and_similar_names_are_preserved(self):
        subject.verify_base_runtime_modules([dict(name=name) for name in
                                            ('desktop_app', 'urllib3', 'onnxruntime', 'setuptools_extra',
                                             'another.setuptools')])


class ZipMemberTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name)/'base_library.zip'

    def make(self, *names):
        with zipfile.ZipFile(self.path, 'w') as archive:
            for name in names:
                archive.writestr(zipfile.ZipInfo(name), b'body')

    def test_members_report_name_size_and_crc(self):
        self.make('b.pyc', 'a/c.pyc')
        members = subject.zip_members(self.path)
        self.assertEqual([m['name'] for m in members], ['a/c.pyc', 'b.pyc'])
        self.assertEqual(members[0]['bytes'], 4)
        self.assertRegex(members[0]['crc32'], '^[0-9a-f]{8}$')

    def test_duplicate_absolute_and_parent_members_are_rejected(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore')
            self.make('a.pyc', 'a.pyc')
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            subject.zip_members(self.path)
        for name in ('/abs.pyc', 'C:/abs.pyc', 'x/../y.pyc', 'x\\..\\y.pyc'):
            self.make(name)
            with self.assertRaisesRegex(ValueError, 'Absolute|escapes'):
                subject.zip_members(self.path)


class SummaryTests(unittest.TestCase):
    def test_summary_counts_origins_and_bounds_unknown_names(self):
        modules = [dict(name='m%02d' % index, origin='unknown') for index in range(15)]
        modules += [dict(name='json', origin='stdlib'), dict(name='x'*200, origin='unknown')]
        summary = subject.summarize(modules, [dict(name='os.pyc')])
        self.assertEqual(summary['by_origin'], dict(stdlib=1, distribution=0, application=0, unknown=16))
        self.assertEqual(summary['unknown_modules'], 16)
        self.assertEqual(len(summary['unknown_names']), 10)
        self.assertEqual(summary['base_library_members'], 1)
        self.assertEqual(summary['pure_modules'], 17)
        self.assertTrue(all(len(name) <= subject.MAX_NAME_LENGTH for name in summary['unknown_names']))


class FixedCPUBuildToolEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.inventory = dict(files=[
            dict(path='_internal/pip-25.0.1.dist-info/METADATA', bytes=3, sha256='1'*64,
                 role='package-metadata', owners=[dict(name='pip', version='25.0.1')]),
            dict(path='_internal/PIL/__init__.py', bytes=7, sha256='2'*64, role='data', owners=[]),
        ])
        self.modules = [dict(name='setuptools._vendor.sample', distribution='setuptools'),
                        dict(name='setuptools_extra'), dict(name='pdf.pip'), dict(name='PIL.Image')]
        self.library = dict(members=[dict(name='ensurepip/__init__.pyc'), dict(name='collections.pyc')])
        self.report = dict(profile='cpu', source_commit='a'*40, accepted=True, inventory_reverified=True,
                           host_platform='win32', candidate_inventory=self.inventory, packages=[],
                           python_archives=dict(pure_modules=self.modules, base_library=self.library))
        self.review = dict(profile='cpu', selection=dict(source_commit='a'*40, run_id='123'),
                           candidate=dict(sha256='b'*64),
                           inventory_sha256=audit.sha(audit.canonical(self.inventory)),
                           pure_modules_sha256=audit.sha(audit.canonical(self.modules)),
                           classification_input=dict(report=dict(python_archives=dict(
                               base_library=json.loads(json.dumps(self.library))))))
        self.raw = audit.canonical(self.report)
        self.review['provenance_report_sha256'] = audit.sha(self.raw)

    def repin_outer_report(self):
        raw = audit.canonical(self.report)
        self.review['provenance_report_sha256'] = audit.sha(raw)
        return raw

    def test_scopes_packages_without_confusing_similarly_named_files_or_modules(self):
        result = audit.extract(self.raw, self.review)
        self.assertEqual([row['path'] for row in result['physical_files']],
                         ['_internal/pip-25.0.1.dist-info/METADATA'])
        self.assertEqual([row['name'] for row in result['pyz_sources']], ['setuptools._vendor.sample'])
        self.assertEqual([row['name'] for row in result['base_library_members']], ['ensurepip/__init__.pyc'])

    def test_raw_provenance_with_one_changed_byte_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'provenance fingerprint'):
            audit.extract(self.raw + b'\n', self.review)

    def test_repinning_outer_report_cannot_hide_a_missing_physical_file(self):
        self.inventory['files'].pop()
        with self.assertRaisesRegex(ValueError, 'physical inventory fingerprint'):
            audit.extract(self.repin_outer_report(), self.review)

    def test_repinning_outer_report_cannot_hide_a_misbound_pyz_module(self):
        self.modules[0]['distribution'] = 'pip'
        with self.assertRaisesRegex(ValueError, 'pure module fingerprint'):
            audit.extract(self.repin_outer_report(), self.review)

    def test_changed_base_library_index_is_rejected(self):
        self.library['members'].pop()
        with self.assertRaisesRegex(ValueError, 'base_library inventory'):
            audit.extract(self.repin_outer_report(), self.review)

    def test_report_for_wrong_candidate_commit_is_rejected(self):
        self.report['source_commit'] = 'c'*40
        with self.assertRaisesRegex(ValueError, 'accepted Windows CPU candidate'):
            audit.extract(self.repin_outer_report(), self.review)

    def repo_notice_fixture(self, root):
        key = 'setuptools/wheel/LICENSE'
        path = root/key
        path.parent.mkdir(parents=True)
        path.write_bytes(b'notice')
        digest = audit.sha(b'notice')
        row = dict(path=audit.REPO_COPIES[0]+key, sha256=digest, bytes=6, owners=[])
        index = dict(files={key: digest}, packages=[
            dict(name='setuptools', version='84.2.1', wheel='setuptools.whl', wheel_sha256='c'*64)])
        return dict(physical_files=[row]), index, path

    def test_license_copy_resolves_to_wheel_by_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, inventory, _ = self.repo_notice_fixture(root)
            binding, = audit.repo_notice_sources(report, inventory, root)
            self.assertEqual(binding['distribution'], 'setuptools')
            self.assertEqual(binding['version'], '84.2.1')
            self.assertEqual(binding['sha256'], report['physical_files'][0]['sha256'])

    def test_license_copy_with_wrong_bytes_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, inventory, path = self.repo_notice_fixture(root)
            path.write_bytes(b'change')
            with self.assertRaisesRegex(ValueError, 'notice bytes differ'):
                audit.repo_notice_sources(report, inventory, root)

    def test_license_copy_without_expected_inventory_binding_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            report, inventory, _ = self.repo_notice_fixture(root)
            inventory['files'].clear()
            with self.assertRaisesRegex(ValueError, 'no matching wheel inventory'):
                audit.repo_notice_sources(report, inventory, root)

    def test_archive_scans_nested_imports_without_executing_them(self):
        code = compile('import PIL\nimport pyimod02_importers\n'
                       'def startup():\n    import setuptools.build_meta\n    import library.pip\n',
                       '<synthetic-startup>', 'exec')
        self.assertEqual(tool_imports(code), {'pyimod02_importers', 'setuptools.build_meta'})


if __name__ == '__main__':
    unittest.main()

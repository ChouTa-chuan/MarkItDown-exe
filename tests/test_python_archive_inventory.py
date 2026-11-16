"""以合成目錄與 zip 驗證 Python 程式封存成員清單；不依賴 Windows 或真正的 PyInstaller。"""
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from build_provenance import sha256
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


if __name__ == '__main__':
    unittest.main()

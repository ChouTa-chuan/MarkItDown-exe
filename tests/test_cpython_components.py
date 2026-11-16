"""CPython 逐檔原文／版本證據的反例；合成 DLL 指紋不代表 Windows 實機驗證。"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import cpython_components as subject
import candidate_inventory


class ComponentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        source = subject.ROOT/'packaging/cpython/windows-3.12.10'
        self.profile_root = self.root/'packaging/cpython/windows-3.12.10'
        shutil.copytree(source, self.profile_root)
        self.profile = json.loads((source/'profile.json').read_text())
        self.license = self.root/'LICENSE.txt'
        self.license.write_bytes(b'Synthetic CPython runtime notice\r\n')
        self.output = self.root/'native'/subject.REPORT
        self.output.parent.mkdir()
        self.native = []
        for component, config in self.profile['components'].items():
            for name, role in config['files'].items():
                digest = hashlib.sha256(name.encode()).hexdigest()
                pe_version = None if component == 'libffi' else ('3.12.10.0' if role == 'cpython-extension'
                                                               else config['declared_version'])
                self.native.append(dict(file=name, source_basename=name, origin='python-runtime',
                                        source_sha256=digest, source_bytes=100, file_version=pe_version))
        self.probe = dict(versions={'openssl': '3.0.16', 'sqlite': '3.49.1'},
                          files={r['source_basename']: dict(sha256=r['source_sha256']) for r in self.native})

    def write(self, **kwargs):
        args = dict(root=self.root, target='win32', version='3.12.10', license_path=self.license,
                    probe=self.probe)
        args.update(kwargs)
        return subject.write_inventory(self.native, self.output, **args)

    def verify(self):
        return subject.verify_inventory(self.output, self.native, self.license, root=self.root, target='win32')

    def save(self, report):
        self.output.write_text(json.dumps(report))

    def test_original_fingerprints_and_patch_version_must_match(self):
        subject.load_profile('3.12.10', self.root)
        with self.assertRaisesRegex(ValueError, 'Missing pinned'):
            subject.load_profile('3.12.11', self.root)
        (self.profile_root/'original/openssl.txt').write_bytes(b'tampered notice')
        with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
            subject.load_profile('3.12.10', self.root)

    def test_profile_cannot_relabel_versions_without_the_original_build_declaration(self):
        self.profile['components']['libffi']['declared_version'] = '8.0'
        (self.profile_root/'profile.json').write_text(json.dumps(self.profile))
        with self.assertRaisesRegex(ValueError, 'declaration mismatch'):
            subject.load_profile('3.12.10', self.root)

    def test_renaming_a_profile_cannot_substitute_another_patch_release(self):
        new = self.root/'packaging/cpython/windows-3.12.11'
        self.profile_root.rename(new)
        self.profile['cpython_version'] = '3.12.11'
        (new/'profile.json').write_text(json.dumps(self.profile))
        with self.assertRaisesRegex(ValueError, 'source version mismatch'):
            subject.load_profile('3.12.11', self.root)

    def test_x64_sources_are_not_applied_to_another_architecture(self):
        with patch.object(subject.platform, 'machine', return_value='ARM64'):
            with self.assertRaisesRegex(ValueError, 'Windows x64'):
                self.write()

    def test_windows_manifest_keeps_distinct_pe_runtime_and_declared_versions(self):
        report = self.write()
        self.assertEqual(self.verify(), report)
        rows = {r['file']: r for r in report['files']}
        self.assertEqual(rows['_ssl.pyd']['file_version'], '3.12.10.0')
        self.assertEqual(rows['_ssl.pyd']['declared_version'], '3.0.16')
        self.assertEqual(rows['_ssl.pyd']['observed_version'], '3.0.16')
        self.assertIsNone(rows['libffi-8.dll']['file_version'])
        self.assertIsNone(rows['libffi-8.dll']['observed_version'])
        self.assertEqual(rows['libffi-8.dll']['declared_version'], '3.4.4')
        self.assertEqual(rows['libffi-8.dll']['version_status'], 'build-declaration-only')
        for notice in report['notices']:
            original = self.profile_root/self.profile['components'][notice['component']]['notice']
            self.assertEqual(original.read_bytes(), (self.output.parent/notice['path']).read_bytes())
        self.assertFalse(report['redistribution_approved'])

    def test_same_name_from_a_wheel_is_not_claimed_as_cpython(self):
        self.native[0]['origin'] = 'installed-wheel'
        report = self.write()
        self.assertNotIn(self.native[0]['file'], [r['file'] for r in report['files']])
        self.verify()

    def test_an_unmatched_loaded_library_cannot_supply_the_observed_version(self):
        self.probe['files']['libssl-3.dll']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'CPython runtime probe required'):
            self.write()
        report = json.loads(self.output.read_text())
        row = next(r for r in report['files'] if r['file'] == 'libssl-3.dll')
        self.assertIsNone(row['observed_version'])
        self.assertFalse(row['loaded_source_matched'])
        with self.assertRaisesRegex(ValueError, 'CPython runtime probe required'):
            self.verify()
        row.update(observed_version='3.0.16', version_status='matched-runtime-probe')
        self.save(report)
        with self.assertRaisesRegex(ValueError, 'Unmatched'):
            self.verify()

    def test_actual_runtime_version_conflict_is_not_silently_overridden(self):
        self.probe['versions']['sqlite'] = '3.50.0'
        with self.assertRaisesRegex(ValueError, 'differs from pinned'):
            self.write()

    def test_probe_failure_is_an_explicit_gap(self):
        with patch.object(subject, 'runtime_probe', side_effect=RuntimeError('fixture failure')):
            with self.assertRaisesRegex(ValueError, 'CPython runtime probe failed'):
                self.write(probe=None)
        report = json.loads(self.output.read_text())
        self.assertIn('fixture failure', report['probe_error'])
        self.assertTrue(all(r['observed_version'] is None for r in report['files']))
        with self.assertRaisesRegex(ValueError, 'CPython runtime probe failed'):
            self.verify()

    def test_rehashing_a_modified_notice_cannot_replace_the_pinned_original(self):
        report = self.write()
        notice = report['notices'][0]
        path = self.output.parent/notice['path']
        path.write_bytes(b'changed notice')
        notice.update(sha256=subject.sha256(path), bytes=path.stat().st_size)
        self.save(report)
        with self.assertRaisesRegex(ValueError, 'original notice mismatch'):
            self.verify()

    def test_deleted_bundled_openssl_original_is_rejected(self):
        self.write()
        (self.output.parent/'cpython-original/openssl.txt').unlink()
        with self.assertRaisesRegex(ValueError, 'Missing or linked CPython evidence'):
            self.verify()

    def test_each_openssl_and_sqlite_file_requires_a_matched_observation(self):
        report = self.write()
        for original in report['files']:
            if original['component'] not in ('openssl', 'sqlite'):
                continue
            with self.subTest(file=original['file']):
                modified = copy.deepcopy(report)
                row = next(r for r in modified['files'] if r['file'] == original['file'])
                row.update(observed_version=None, version_status='build-declaration-only')
                self.save(modified)
                with self.assertRaisesRegex(ValueError, 'CPython runtime probe required'):
                    self.verify()

    def test_probe_error_key_is_rejected_even_when_rows_are_matched(self):
        report = self.write()
        for error in ('fixture failure', ''):
            with self.subTest(error=error):
                self.save(dict(report, probe_error=error))
                with self.assertRaisesRegex(ValueError, 'CPython runtime probe failed'):
                    self.verify()

    def test_missing_or_duplicated_rows_and_source_hash_changes_are_rejected(self):
        report = self.write()
        for rows in (report['files'][1:], report['files'] + [report['files'][0]]):
            self.save(dict(report, files=rows))
            with self.assertRaisesRegex(ValueError, 'coverage differs'):
                self.verify()
        modified = copy.deepcopy(report)
        modified['files'][0]['source_sha256'] = '0'*64
        self.save(modified)
        with self.assertRaisesRegex(ValueError, 'file mismatch'):
            self.verify()

    def test_changing_the_installed_python_notice_is_detected(self):
        self.write()
        self.license.write_bytes(b'different installed interpreter')
        with self.assertRaisesRegex(ValueError, 'runtime notice mismatch'):
            self.verify()

    def test_no_libffi_runtime_probe_can_be_invented(self):
        report = self.write()
        row = next(r for r in report['files'] if r['file'] == 'libffi-8.dll')
        row.update(observed_version='3.4.4', version_status='matched-runtime-probe')
        self.save(report)
        with self.assertRaisesRegex(ValueError, 'no supported'):
            self.verify()

    def test_linux_is_not_windows_evidence(self):
        report = self.write(target='linux', version='3.12.3')
        self.assertFalse(report['applicable'])
        self.assertEqual(report['files'], [])
        self.assertFalse((self.output.parent/'cpython-original').exists())
        subject.verify_inventory(self.output, self.native, self.license, target='linux')
        with self.assertRaisesRegex(ValueError, 'Invalid CPython'):
            self.verify()

    def test_public_summary_is_bounded_and_contains_each_collected_file(self):
        report = self.write()
        brief = subject.public_summary(report)
        self.assertEqual({r['file'] for r in brief['files']}, {r['file'] for r in report['files']})
        self.assertLessEqual(len(json.dumps(brief, ensure_ascii=False, separators=(',', ':')).encode()), 3900)

    def test_candidate_links_to_component_notice_without_granting_an_owner(self):
        report = self.write()
        notice = report['notices'][0]['path']
        bundle = self.output.parent
        (bundle/'_internal').mkdir()
        (bundle/'_internal/libssl-3.dll').write_bytes(b'fixture dll')
        (bundle/'assets').mkdir()
        (bundle/'assets/python.txt').write_bytes(b'fixture interpreter notice')
        native = [dict(file='libssl-3.dll', origin='python-runtime', distributions=[], bytes_changed=False,
                       component_notice_paths=[notice])]
        with patch.object(candidate_inventory, 'record_owners', return_value={}):
            inventory = candidate_inventory.inventory(bundle, [], native,
                dict(prefix='unused', version='1', files={}), 'assets', 'python.txt', 'unused-entry')
        dll = next(r for r in inventory['files'] if r['path'] == '_internal/libssl-3.dll')
        self.assertIn(notice, dll['notice_paths'])
        self.assertEqual(dll['owners'], [])
        self.assertIn('source-owner-unresolved', dll['review_reasons'])


if __name__ == '__main__':
    unittest.main()

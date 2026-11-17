"""Qt 來源／原文與替換驗收的反例；合成資料不當成 Windows 接受證據。"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import qt_components as qt
import qt_sources
import check_qt_replacement as replacement


class QtComponentTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        shutil.copytree(ROOT/'packaging/qt', self.root/'packaging/qt')
        target = self.root/'src/desktop_app/data/licenses/windows'
        target.mkdir(parents=True)
        shutil.copyfile(ROOT/'src/desktop_app/data/licenses/windows/inventory.json', target/'inventory.json')

    def save(self, value):
        (self.root/qt.CATALOG).write_text(json.dumps(value), encoding='utf-8')

    def test_missing_and_tampered_source_originals_are_rejected(self):
        catalog = qt.load_catalog(self.root)
        original = self.root/qt.CATALOG
        original = original.parent/catalog['evidence_files'][0]['path']
        saved = original.read_bytes()
        original.unlink()
        with self.assertRaisesRegex(ValueError, 'original missing'):
            qt.load_catalog(self.root)
        original.write_bytes(saved+b'changed')
        with self.assertRaisesRegex(ValueError, 'fingerprint differs'):
            qt.load_catalog(self.root)

    def test_version_and_compiled_status_cannot_be_upgraded_from_source_declaration(self):
        catalog = qt.load_catalog(self.root)
        for field, changed in [('version', '999'), ('version_basis', 'wheel-declared'),
                               ('compiled_into_windows_wheel', 'verified')]:
            value = copy.deepcopy(catalog)
            value['components'][0][field] = changed
            self.save(value)
            with self.assertRaisesRegex(ValueError, 'relabelled'):
                qt.load_catalog(self.root)

    def test_incomplete_attribution_or_other_release_is_rejected(self):
        catalog = qt.load_catalog(self.root)
        changed = copy.deepcopy(catalog)
        changed['components'].pop()
        self.save(changed)
        with self.assertRaisesRegex(ValueError, 'coverage differs'):
            qt.load_catalog(self.root)
        changed = copy.deepcopy(catalog)
        changed['evidence_files'][0]['commit'] = '0'*40
        self.save(changed)
        with self.assertRaisesRegex(ValueError, 'source binding'):
            qt.load_catalog(self.root)

    def test_bundled_notices_require_original_bytes_and_catalog_even_after_manifest_rehash(self):
        assets = self.root/'assets'
        qt.stage(self.root, assets)
        value = qt.verify(assets, self.root)
        path = assets/qt.STAGED/value['evidence_files'][0]['path']
        saved = path.read_bytes()
        path.unlink()
        with self.assertRaisesRegex(ValueError, 'original missing'):
            qt.verify(assets, self.root)
        path.write_bytes(saved+b'changed')
        with self.assertRaisesRegex(ValueError, 'original differs'):
            qt.verify(assets, self.root)
        path.write_bytes(saved)
        (assets/qt.STAGED/'catalog.json').write_text('{}')
        with self.assertRaisesRegex(ValueError, 'catalog differs'):
            qt.verify(assets, self.root)

    def test_native_mapping_and_a13_binding_are_checked_without_changing_counts(self):
        catalog = qt.load_catalog(self.root)
        registry = json.loads((ROOT/'packaging/redistribution/obligations.json').read_text())
        entry = next(e for e in registry['profiles']['base']['entries'] if e['id'] == 'base-qt')
        report = json.loads((ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json').read_text())
        result = qt.check_profile(catalog, entry=entry, report=report, root=self.root)
        self.assertFalse(result['thirdparty_runtime_closure_verified'])
        entry['requires_user_decision'] = False
        with self.assertRaisesRegex(ValueError, 'A13'):
            qt.check_profile(catalog, entry=entry, report=report, root=self.root)
        entry['requires_user_decision'] = True
        altered = copy.deepcopy(report)
        altered['classification_input']['report']['native_files'] = [
            dict(r, bundled_sha256='0'*64) if r['file'] == 'PySide6/Qt6Core.dll' else r
            for r in altered['classification_input']['report']['native_files']]
        with self.assertRaisesRegex(ValueError, 'fingerprint differs'):
            qt.check_profile(catalog, entry=entry, report=altered, root=self.root)

    def test_qlibraryinfo_observation_keeps_build_and_platform_distinct(self):
        observed = qt_sources.observe()
        self.assertIn('Qt 6.12.0', observed['qt_build'])
        self.assertEqual(observed['library_version'], observed['qt_version'])
        self.assertIsInstance(observed['shared_build'], bool)
        self.assertIsInstance(observed['debug_build'], bool)


class QtReplacementTests(unittest.TestCase):
    def test_only_pinned_wheel_and_member_bytes_are_extracted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            wheel = root/'input.whl'
            with zipfile.ZipFile(wheel, 'w') as archive:
                archive.writestr('bin/Qt6Core.dll', b'synthetic DLL, not executed')
                archive.writestr('bin/not-needed.dll', b'not extracted')
            data = b'synthetic DLL, not executed'
            record = dict(bytes=wheel.stat().st_size, sha256=hashlib.sha256(wheel.read_bytes()).hexdigest(),
                member='bin/Qt6Core.dll', member_bytes=len(data), member_sha256=hashlib.sha256(data).hexdigest())
            target = root/'core.dll'
            replacement.extract_replacement(wheel, target, record)
            self.assertEqual(target.read_bytes(), data)
            self.assertFalse((root/'bin').exists())
            record['member_sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'DLL fingerprint'):
                replacement.extract_replacement(wheel, target, record)
            wheel.write_bytes(wheel.read_bytes()+b'changed')
            with self.assertRaisesRegex(ValueError, 'wheel fingerprint'):
                replacement.extract_replacement(wheel, target, record)

    def test_missing_core_must_fail_for_the_expected_loader_reason(self):
        replacement.validate_missing(1, 'ImportError: DLL load failed while importing QtCore')
        for code, log in [(0, 'ImportError: QtCore'), (1, 'Unrelated converter failure'),
                          (1, 'QtCore window did not close'), (1, 'ImportError: another_module')]:
            with self.assertRaisesRegex(ValueError, 'expected loader'):
                replacement.validate_missing(code, log)

    def test_success_requires_actual_replacement_path_and_hash(self):
        path = Path('/tmp/synthetic/Qt6Core.dll')
        value = dict(opened=True, normal_exit=True, returncode=0, qt_core=dict(path=str(path), sha256='1'*64))
        replacement.validate_success(value, path, '1'*64)
        for changed in [dict(value, opened=False), dict(value, returncode=1),
                        dict(value, qt_core=dict(path=str(path), sha256='0'*64)),
                        dict(value, qt_core=dict(path='/tmp/host/Qt6Core.dll', sha256='1'*64))]:
            with self.assertRaisesRegex(ValueError, 'expected Qt6Core'):
                replacement.validate_success(changed, path, '1'*64)

    def test_non_windows_execution_is_recorded_as_unaccepted(self):
        with tempfile.TemporaryDirectory() as temporary, patch.object(replacement.sys, 'platform', 'linux'):
            root = Path(temporary)
            report = replacement.check(root/'bundle', root/'work', root/'reports')
            self.assertFalse(report['accepted'])
            self.assertFalse(report['physical_machine_accepted'])
            self.assertFalse(report['release_ready'])
            self.assertIn('requires hosted Windows', report['error'])
            self.assertEqual(report, json.loads((root/'reports/qt-replacement.json').read_text()))


if __name__ == '__main__':
    unittest.main()

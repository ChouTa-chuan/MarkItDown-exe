"""內含四語資產、預設解析與故障保護；合成 ELF 不執行，也不當成 OCR 品質證據。"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from desktop_app import build_profile as bp, bundled_ocr as bundled, diagnostics
from desktop_app.onboarding.service import EngineObservation, RamAdvice, SetupReport, SetupSession, probe_engine
from threading import Event
from desktop_app.settings import Settings, save_settings

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from prepare_base_assets import attach_native
import prepare_bundled_ocr as prepare


class BundledOCRTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / 'data'
        self.native = self.data / 'native'
        self.native.mkdir(parents=True)
        header = bytearray(64)
        header[:6] = b'\x7fELF\x02\x01'
        header[18:20] = b'\x3e\x00'
        self.put('native/bin/tesseract', bytes(header))
        self.fixed = dict(commit='fixed-test-commit', files={})
        for name in ['chi_tra.traineddata', 'eng.traineddata', 'jpn.traineddata', 'kor.traineddata', 'LICENSE']:
            value = ('Synthetic ' + name).encode()
            self.put('native/tessdata/' + name, value)
            self.fixed['files'][name] = hashlib.sha256(value).hexdigest()
        self.put('native/notices/LICENSE.txt', b'Synthetic license')
        self.put('native/source.json', b'{"scope":"synthetic fixture only"}')
        self.spec = dict(schema_version=1, id='bundled-tesseract', platform='linux', entrypoint='bin/tesseract',
                         languages=list(bundled.LANGUAGES), model_commit=self.fixed['commit'],
                         development_only=True, redistribution_approved=False, files={})
        for p in self.native.rglob('*'):
            if p.is_file():
                self.spec['files'][p.relative_to(self.native).as_posix()] = dict(
                    sha256=hashlib.sha256(p.read_bytes()).hexdigest(), bytes=p.stat().st_size)
        self.save_native()
        for name in ['user-guide.md', 'third-party.md', 'base-runtime-lock.txt',
                     'licenses/python-runtime/LICENSE.txt', 'licenses/installed/manifest.json']:
            self.put(name, b'Synthetic core metadata')
        self.put('ocr-four-languages.json', json.dumps(self.fixed).encode())
        self.profile = dict(schema_version=2, id='base', source_version='test', runtime_packages={'psutil':'test'},
                            local_packages={'markitdown':'test','markitdown-desktop':'test'}, notice_packages=3,
                            native_ocr_required=True, native_ocr_integrated=True, native_ocr_manifest='native/manifest.json',
                            release_ready=False, assets={})
        self.save_profile()
        self.patches = [patch.object(bp, 'data_root', return_value=self.data),
                        patch.object(bundled, 'model_manifest', return_value=self.fixed),
                        patch.object(prepare, 'model_manifest', return_value=self.fixed)]
        for item in self.patches:
            item.start()
            self.addCleanup(item.stop)

    def put(self, name, content):
        path = self.data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def save_native(self):
        (self.native / 'manifest.json').write_text(json.dumps(self.spec))

    def save_profile(self):
        self.profile['assets'] = {p.relative_to(self.data).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in self.data.rglob('*') if p.is_file() and p.name != 'build-profile.json'}
        (self.data / 'build-profile.json').write_text(json.dumps(self.profile))

    def test_v2_profile_and_complete_payload_are_valid(self):
        profile = bp.load_profile()
        bp.verify_assets(profile)
        self.assertEqual(bundled.validate_payload(self.native, assets=profile['assets']), self.spec)

    def test_source_without_profile_keeps_legacy_resolution(self):
        (self.data / 'build-profile.json').unlink()
        self.assertEqual(bundled.bindings(None, '/custom/data'), (None, '/custom/data', None))

    def test_core_profile_cannot_borrow_external_engine(self):
        self.profile.update(schema_version=1, native_ocr_integrated=False)
        self.save_profile()
        with self.assertRaisesRegex(RuntimeError, 'PATH'):
            bundled.bindings()

    def test_explicit_external_engine_preserves_data_and_does_not_read_bundle(self):
        (self.native / 'manifest.json').write_text('broken')
        self.assertEqual(bundled.bindings('/custom/engine', None), ('/custom/engine', None, None))

    def test_explicit_model_path_is_preserved_with_auto_bundled_engine(self):
        engine, data, origin = bundled.bindings(None, '/custom/models')
        self.assertEqual(engine, str(self.native / 'bin/tesseract'))
        self.assertEqual(data, '/custom/models')
        self.assertEqual(origin, bundled.ORIGIN)

    def test_auto_paths_follow_bundle_after_directory_move(self):
        moved = self.root / 'moved'
        self.data.rename(moved)
        with patch.object(bp, 'data_root', return_value=moved):
            engine, data, _ = bundled.bindings()
        self.assertEqual(engine, str(moved / 'native/bin/tesseract'))
        self.assertEqual(data, str(moved / 'native/tessdata'))

    def test_missing_model_fails_without_path_fallback(self):
        (self.native / 'tessdata/jpn.traineddata').unlink()
        with self.assertRaises(ValueError):
            bundled.bindings()

    def test_changed_model_is_rejected(self):
        (self.native / 'tessdata/kor.traineddata').write_bytes(b'tampered')
        with self.assertRaises(ValueError):
            bundled.bindings()

    def test_replaced_executable_is_rejected(self):
        (self.native / 'bin/tesseract').write_bytes(b'other')
        with self.assertRaises(ValueError):
            bundled.bindings()

    def test_linked_model_parent_is_rejected(self):
        actual = self.native / 'tessdata'
        actual.rename(self.root / 'models')
        actual.symlink_to(self.root / 'models', target_is_directory=True)
        with self.assertRaises(ValueError):
            bundled.bindings()

    def test_unlisted_dll_is_rejected(self):
        self.put('native/bin/unlisted.dll', b'unknown')
        with self.assertRaisesRegex(ValueError, '未列出'):
            bundled.bindings()

    def test_changed_fixed_model_manifest_is_rejected(self):
        self.put('ocr-four-languages.json', b'{}')
        with self.assertRaisesRegex(ValueError, '模型清單'):
            bundled.bindings()

    def test_platform_mismatch_prevents_execution(self):
        with patch.object(bundled.sys, 'platform', 'win32'):
            with self.assertRaisesRegex(ValueError, '平台'):
                bundled.bindings()

    def test_declared_platform_must_match_real_binary_format(self):
        self.spec.update(platform='windows', entrypoint='bin/tesseract.exe')
        path = self.native / 'bin/tesseract'
        path.rename(path.with_suffix('.exe'))
        self.spec['files']['bin/tesseract.exe'] = self.spec['files'].pop('bin/tesseract')
        self.save_native()
        with self.assertRaises(ValueError):
            bundled.validate_payload(self.native, expected_platform='windows')

    def test_data_flags_cannot_approve_redistribution(self):
        self.spec['redistribution_approved'] = True
        self.save_native()
        with self.assertRaises(ValueError):
            bundled.validate_payload(self.native)

    def test_payload_parent_paths_are_rejected(self):
        self.spec['files']['../outside'] = dict(sha256='0'*64, bytes=1)
        self.save_native()
        with self.assertRaises(ValueError):
            bundled.validate_payload(self.native)

    def test_missing_language_contract_is_rejected(self):
        self.spec['languages'].remove('kor')
        self.save_native()
        with self.assertRaises(ValueError):
            bundled.validate_payload(self.native)

    def test_native_manifest_hash_is_bound_to_profile(self):
        self.spec['extra'] = 'changed'
        self.save_native()
        with self.assertRaisesRegex(ValueError, '清單'):
            bundled.bindings()

    def diagnostic_report(self, *, failure=False, scope='full'):
        def convert(source, destination, backend='tesseract', **kwargs):
            if source.suffix == '.txt':
                destination.write_bytes(source.read_bytes())
            return 'INSTALLATION PDF CHECK 12345 route: native'
        with patch.object(bp, 'verify_runtime', return_value='synthetic runtime check'), \
             patch.object(diagnostics, '_convert', side_effect=convert), \
             patch.object(diagnostics, 'bundled_native_check', side_effect=RuntimeError('synthetic failure') if failure else None,
                          return_value={'scope':'synthetic check only'}):
            return diagnostics.collect_report(scope=scope)

    def test_full_diagnostics_separate_ocr_verification_and_release(self):
        full = self.diagnostic_report()
        self.assertTrue(full['complete'])
        self.assertTrue(full['native_ocr_verified'])
        self.assertFalse(full['release_ready'])
        core = self.diagnostic_report(scope='core')
        self.assertTrue(core['complete'])
        self.assertFalse(core['native_ocr_verified'])

    def test_full_ocr_failure_preserves_core_and_cannot_claim_verified(self):
        result = self.diagnostic_report(failure=True)
        self.assertTrue(result['core_complete'])
        self.assertFalse(result['complete'])
        self.assertFalse(result['native_ocr_verified'])

    def test_setup_does_not_persist_absolute_auto_bundle_paths(self):
        session = SetupSession(self.root / 'settings.json')
        report = SetupReport(RamAdvice(8192, 4096, 2048, 1024),
            EngineObservation(True, str(self.native/'bin/tesseract'), str(self.native/'tessdata'),
                              bundled.ORIGIN, 'synthetic', bundled.LANGUAGES, (), 'synthetic'), False)
        result = session.complete(report, apply_engine=True)
        self.assertIsNone(result.ocr_executable)
        self.assertIsNone(result.ocr_data_dir)

    def test_setup_keeps_existing_explicit_user_paths(self):
        path = self.root / 'settings.json'
        saved = Settings(ocr_executable='/custom/engine', ocr_data_dir='/custom/models')
        save_settings(saved, path)
        session = SetupSession(path)
        report = SetupReport(RamAdvice(8192, 4096, 2048, 1024),
            EngineObservation(True, '/other/engine', '/other/models', bundled.ORIGIN,
                              'synthetic', bundled.LANGUAGES, (), 'synthetic'), True)
        self.assertEqual(session.complete(report, apply_engine=True), replace(saved, onboarding_version=1))

    def test_bundled_engine_with_custom_models_respects_selected_language(self):
        settings = Settings(ocr_data_dir=str(self.native/'tessdata'), ocr_languages=('eng',))
        def command(argv, cancel, **kwargs):
            if '--version' in argv:
                return 'tesseract synthetic'
            if '--list-langs' in argv:
                return 'List of available languages:\neng\n'
            return 'WORKER HEALTH CHECK 12345'
        with patch('desktop_app.onboarding.service.native_command', side_effect=command):
            result = probe_engine(settings, self.root, Event())
        self.assertTrue(result.ready, result.message)
        self.assertEqual(len(result.samples), 1)
        self.assertEqual(result.languages, ('eng',))

    def test_wrong_platform_cannot_attach_to_base_build(self):
        with self.assertRaises(ValueError):
            attach_native(self.root / 'stage', self.native, 'windows')
        self.assertFalse((self.root / 'stage').exists())

    def test_windows_assembly_rejects_unpinned_candidate(self):
        candidate = self.root / 'candidate'
        candidate.mkdir()
        (candidate / 'tesseract.exe').write_bytes(b'unpinned')
        with self.assertRaises(ValueError):
            prepare.prepare(self.root / 'output', self.native / 'tessdata', windows_candidate=candidate)
        self.assertFalse((self.root / 'output').exists())

    def test_existing_output_is_never_overwritten(self):
        output = self.root / 'output'
        output.mkdir()
        (output / 'keep').write_bytes(b'user data')
        with self.assertRaises(FileExistsError):
            prepare.prepare(output, self.native / 'tessdata', linux_development=True)
        self.assertEqual((output / 'keep').read_bytes(), b'user data')

    def test_assembly_requires_explicit_target_mode(self):
        with self.assertRaises(ValueError):
            prepare.prepare(self.root / 'output', self.native / 'tessdata')


if __name__ == '__main__':
    unittest.main()

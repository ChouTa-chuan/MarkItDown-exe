"""GEOS 使用者替換只接受固定邊界，既有協定在未替換時維持原樣。"""
from copy import deepcopy
from contextlib import ExitStack, nullcontext
from ctypes import wintypes
import hashlib
import io
import json
import os
from pathlib import Path, PureWindowsPath
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, call, patch

from desktop_app.component_workers import binding, geos_replacement as geos, protocol as wire, server
from desktop_app.settings import Settings, load_settings


class GEOSPathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.managed = self.root/'component-state'
        self.managed.mkdir()
        self.directory = self.root/geos.DIRECTORY

    def fill(self):
        self.directory.mkdir()
        files = tuple(self.directory/name for name in geos.NAMES)
        for file in files:
            file.write_bytes(file.name.encode('ascii'))
        return files

    def test_absent_and_empty_are_not_detected(self):
        self.assertFalse(geos.has_replacement_files(self.directory))
        self.assertEqual(geos.replacement_files(self.directory, self.managed), ())
        self.directory.mkdir()
        self.assertFalse(geos.has_replacement_files(self.directory))
        self.assertEqual(geos.replacement_files(self.directory, self.managed), ())

    def test_exact_pair_returns_core_before_capi(self):
        self.assertEqual(geos.replacement_files(self.root/geos.DIRECTORY, self.managed), ())
        files = self.fill()
        self.assertTrue(geos.has_replacement_files(self.directory))
        self.assertEqual(geos.replacement_files(self.directory, self.managed), files)

    def test_rejects_relative_paths(self):
        with self.assertRaisesRegex(geos.GeosReplacementError, '絕對路徑'):
            geos.replacement_files(Path(geos.DIRECTORY), self.managed)

    def test_rejects_a_parent_reference_and_managed_descendant(self):
        for folder in (self.managed/geos.DIRECTORY, self.root/'child'/'..'/geos.DIRECTORY):
            with self.subTest(folder=folder), self.assertRaisesRegex(geos.GeosReplacementError, '受管目錄之外'):
                geos.replacement_files(folder, self.managed)

    def test_rejects_incomplete_pair(self):
        self.directory.mkdir()
        (self.directory/geos.NAMES[0]).touch()
        with self.assertRaisesRegex(geos.GeosReplacementError, '兩個指定'):
            geos.replacement_files(self.directory, self.managed)

    def test_rejects_unexpected_filename_even_with_the_complete_pair(self):
        self.fill()
        (self.directory/'unexpected.dll').touch()
        with self.assertRaisesRegex(geos.GeosReplacementError, '兩個指定'):
            geos.replacement_files(self.directory, self.managed)

    def test_rejects_directory_symlink_even_if_the_target_is_empty(self):
        target = self.root/'empty'
        target.mkdir()
        self.directory.symlink_to(target, target_is_directory=True)
        self.assertFalse(geos.has_replacement_files(self.directory))
        with self.assertRaisesRegex(geos.GeosReplacementError, '連結'):
            geos.replacement_files(self.directory, self.managed)

    def test_rejects_a_file_symlink(self):
        self.directory.mkdir()
        target = self.root/'other.dll'
        target.touch()
        (self.directory/geos.NAMES[0]).symlink_to(target)
        (self.directory/geos.NAMES[1]).touch()
        with self.assertRaisesRegex(geos.GeosReplacementError, '連結'):
            geos.replacement_files(self.directory, self.managed)

    def test_rejects_a_file_hardlink(self):
        files = self.fill()
        os.link(files[0], self.managed/'alias.dll')
        with self.assertRaisesRegex(geos.GeosReplacementError, '獨立的一般檔案'):
            geos.replacement_files(self.directory, self.managed)

    def test_rejects_a_directory_masquerading_as_a_dll(self):
        self.directory.mkdir()
        (self.directory/geos.NAMES[0]).mkdir()
        (self.directory/geos.NAMES[1]).touch()
        with self.assertRaisesRegex(geos.GeosReplacementError, '一般檔案'):
            geos.replacement_files(self.directory, self.managed)

    def test_refuses_loading_after_shapely_has_already_imported(self):
        with patch.object(geos.sys, 'platform', 'win32'), patch.dict(sys.modules, {'shapely': object()}):
            with self.assertRaisesRegex(geos.GeosReplacementError, '匯入 Shapely 前'):
                geos.load_replacement(self.directory, self.managed)

    def test_failed_replacement_has_explicit_pre_handshake_status(self):
        control = io.BytesIO()
        with patch.object(server, 'load_replacement', side_effect=geos.GeosReplacementError('broken')):
            result = server.serve(self.root, self.root/'guard', control, io.BytesIO(),
                                  geos_directory=self.directory)
        self.assertEqual(result, 1)
        event = wire.event(wire.decode(control.getvalue()))
        self.assertEqual((event['type'], event['job_id'], event['code']), ('failed', None, geos.FAILURE))

    def test_worker_without_launch_argument_does_not_read_user_settings_or_load(self):
        self.fill()
        (self.root/'settings.json').write_text('{"geos_replacement_enabled":true}', encoding='utf-8')
        with patch.object(server, 'file_lock', return_value=nullcontext()), \
                patch.object(server, 'load_replacement') as load, \
                patch.object(Path, 'open', side_effect=AssertionError('worker tried to open a file')) as opened, \
                patch.object(server, 'preload_windows_runtime', side_effect=RuntimeError('end before protocol')) as managed:
            server.serve(self.root, self.managed/'.locks/worker-use.lock', io.BytesIO(), io.BytesIO())
        load.assert_not_called()
        opened.assert_not_called()
        managed.assert_called_once()

    def mock_windows_loader(self, kernel=None):
        stack = ExitStack()
        self.addCleanup(stack.close)
        stack.enter_context(patch.object(geos.sys, 'platform', 'win32'))
        modules = stack.enter_context(patch.dict(sys.modules))
        modules.pop('shapely', None)
        fake = SimpleNamespace(geos_version=(3, 14, 1), geos_capi_version=(1, 20, 5), box=Mock())
        fake.box.return_value.intersection.return_value.area = 4

        def win_dll(name, **kwargs):
            if name == 'kernel32':
                return kernel
            modules['shapely'] = fake
            return name

        load = stack.enter_context(patch.object(geos.ctypes, 'WinDLL', side_effect=win_dll, create=True))
        stack.enter_context(patch.object(geos, '_pin_file', side_effect=lambda path, _kernel: path.open('rb')))
        return load

    def test_enabled_loads_core_then_capi_and_records_fingerprints(self):
        paths = self.fill()
        load = self.mock_windows_loader()
        with patch.object(geos, '_loaded_paths', side_effect=[[], list(paths)]):
            record, handles = geos.load_replacement(self.directory, self.managed)
        self.assertEqual(load.call_args_list, [call('kernel32', use_last_error=True)] +
                         [call(str(path), winmode=0x1100) for path in paths])
        self.assertEqual(handles, tuple(map(str, paths)))
        self.assertEqual(record['files'], [
            dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths
        ])

    def test_rejects_loaded_module_from_a_different_directory(self):
        core, capi = self.fill()
        self.mock_windows_loader()
        with patch.object(geos, '_loaded_paths', side_effect=[[], [self.managed/core.name, capi]]):
            with self.assertRaisesRegex(geos.GeosReplacementError, '指定目錄'):
                geos.load_replacement(self.directory, self.managed)

    def test_rejects_duplicate_loaded_modules(self):
        core, capi = self.fill()
        self.mock_windows_loader()
        with patch.object(geos, '_loaded_paths', side_effect=[[], [core, capi, core]]):
            with self.assertRaisesRegex(geos.GeosReplacementError, '指定目錄'):
                geos.load_replacement(self.directory, self.managed)

    def test_rejects_more_than_1024_loaded_modules(self):
        self.fill()
        kernel = Mock()
        self.mock_windows_loader(kernel)
        sizes = iter((0, 1025))

        def enum(_process, modules, buffer_bytes, needed):
            self.assertEqual(len(modules), 1024)
            self.assertEqual(buffer_bytes, 1024 * geos.ctypes.sizeof(wintypes.HMODULE))
            needed._obj.value = next(sizes) * geos.ctypes.sizeof(wintypes.HMODULE)
            return True

        kernel.K32EnumProcessModules.side_effect = enum
        with self.assertRaisesRegex(geos.GeosReplacementError, '超過 1024'):
            geos.load_replacement(self.directory, self.managed)
        kernel.GetModuleFileNameW.assert_not_called()

    def test_enabled_without_files_fails_before_loading(self):
        with patch.object(geos.sys, 'platform', 'win32'), patch.dict(sys.modules):
            sys.modules.pop('shapely', None)
            with patch.object(geos.ctypes, 'WinDLL', create=True) as load:
                for directory_exists in (False, True):
                    if directory_exists:
                        self.directory.mkdir()
                    with self.subTest(directory_exists=directory_exists), \
                            self.assertRaisesRegex(geos.GeosReplacementError, '請放入兩個'):
                        geos.load_replacement(self.directory, self.managed)
        load.assert_not_called()

    def test_parent_sends_replacement_path_only_when_enabled(self):
        self.fill()
        spec = SimpleNamespace(component_id=wire.COMPONENT_ID, version=wire.COMPONENT_VERSION,
                               worker_protocols=SimpleNamespace(contains=lambda _: True),
                               files=[SimpleNamespace(path='MarkItDownOCRWorker.exe')],
                               resources=SimpleNamespace(ram_mib=768))
        installed = self.managed/'versions/ocr'
        installed.mkdir(parents=True)
        executable = installed/'MarkItDownOCRWorker.exe'
        executable.touch()
        guard = self.managed/'.locks/worker-use.lock'
        with patch.object(binding, 'os', SimpleNamespace(name='nt')):
            for enabled in (None, False, True, False, 1):
                with self.subTest(enabled=enabled):
                    kwargs = {} if enabled is None else {'geos_replacement_enabled': enabled}
                    runner = binding.CPUWorkerBinding(guard, data_directory=self.root, **kwargs).runner(spec, installed)
                    suffix = ('--geos-replacement-dir', str(self.directory)) if enabled is True else ()
                    self.assertEqual(runner.command, (str(executable), *suffix))
                    self.assertEqual(runner.geos_notice, None if enabled is True else geos.NOT_ENABLED)

    def test_geos_setting_accepts_only_json_true_and_keeps_other_values(self):
        path = self.root/'settings.json'
        self.assertFalse(Settings().geos_replacement_enabled)
        for option, expected in (({}, False), ({'geos_replacement_enabled': True}, True),
                                 ({'geos_replacement_enabled': False}, False),
                                 *[({'geos_replacement_enabled': value}, False)
                                   for value in (1, 0, 'true', None, [], {'enabled': True})]):
            with self.subTest(option=option):
                path.write_text(json.dumps(dict(schema_version=7, cpu_threads=3, **option)), encoding='utf-8')
                result = load_settings(path)
                self.assertIs(result.geos_replacement_enabled, expected)
                self.assertEqual(result.cpu_threads, 3)


class GEOSProtocolTests(unittest.TestCase):
    def setUp(self):
        folder = PureWindowsPath(r'C:\Users\Sample\AppData\Local')/geos.DIRECTORY
        self.evidence = dict(status=geos.STATUS, files=[
            dict(path=str(folder/name), sha256=str(index)*64)
            for index, name in enumerate(geos.NAMES)
        ])
        self.job = 'a'*32
        self.payload = dict(schema_version=1, protocol=wire.PROTOCOL, component_id=wire.COMPONENT_ID,
                            component_version=wire.COMPONENT_VERSION, job_id=self.job, actual_device='cpu',
                            providers=['CPUExecutionProvider']*3, text='text', warning='', input_sha256='0'*64,
                            health_passed=True, runtime=dict(python='3.12', rapidocr='1.4.4', onnxruntime='1',
                                                             numpy='2', opencv='5', frozen=True))

    def test_legacy_result_and_verified_shape_of_replacement_are_accepted(self):
        self.assertEqual(wire.result(self.payload, self.job), self.payload)
        self.payload['runtime']['geos_replacement'] = self.evidence
        self.assertEqual(wire.result(self.payload, self.job), self.payload)
        self.assertIn(geos.LABEL, geos.record_detail(self.evidence))
        for item in self.evidence['files']:
            self.assertIn(item['sha256'], geos.record_detail(self.evidence))

    def test_invalid_replacement_result_is_rejected(self):
        for changes in ({'path': geos.NAMES[0]}, {'sha256': 'wrong'},
                        {'path': str(PureWindowsPath(r'D:\Different')/geos.DIRECTORY/geos.NAMES[0])},
                        {'path': str(PureWindowsPath(r'C:\Other')/geos.DIRECTORY/'wrong.dll')}):
            with self.subTest(changes=changes), self.assertRaisesRegex(wire.ProtocolError, 'GEOS 替換'):
                record = deepcopy(self.evidence)
                record['files'][0].update(changes)
                self.payload['runtime']['geos_replacement'] = record
                wire.result(self.payload, self.job)


if __name__ == '__main__':
    unittest.main()

"""GEOS 使用者替換只接受固定邊界，既有協定在未替換時維持原樣。"""
from copy import deepcopy
import io
import os
from pathlib import Path, PureWindowsPath
import sys
import tempfile
import unittest
from unittest.mock import patch

from desktop_app.component_workers import geos_replacement as geos, protocol as wire, server


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

    def test_absent_and_empty_restore_managed_mode(self):
        self.assertFalse(geos.requested(self.directory))
        self.assertEqual(geos.replacement_files(self.directory, self.managed), ())
        self.directory.mkdir()
        self.assertFalse(geos.requested(self.directory))
        self.assertEqual(geos.replacement_files(self.directory, self.managed), ())

    def test_exact_pair_returns_core_before_capi(self):
        self.assertEqual(geos.replacement_files(self.root/geos.DIRECTORY, self.managed), ())
        files = self.fill()
        self.assertTrue(geos.requested(self.directory))
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
        self.assertTrue(geos.requested(self.directory))
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

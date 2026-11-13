"""原生檔身分紀錄：逐檔容錯、簽章查詢失敗不冒充通過、公開摘要分組；不依賴 Windows。"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bundle_filters
import native_identity as subject


class DescribeTests(unittest.TestCase):
    def test_version_and_signature_are_merged_per_file(self):
        paths = [Path('/sys/ucrtbase.dll'), Path('/py/python312.dll')]
        result = subject.describe(
            paths, sign=lambda items: {items[0]: ('Valid', 'CN=Microsoft Windows')},
            version=lambda path: dict(company='Microsoft Corporation', file_version='10.0') if path.name == 'ucrtbase.dll' else {})
        self.assertEqual(result[paths[0]], dict(source_directory='/sys', company='Microsoft Corporation',
                                                file_version='10.0', signature_status='Valid',
                                                signer='CN=Microsoft Windows'))
        # 沒有查到的欄位不補造。
        self.assertEqual(result[paths[1]], dict(source_directory='/py'))

    def test_failures_are_recorded_and_never_look_like_a_valid_signature(self):
        def broken_sign(items):
            raise RuntimeError('powershell unavailable')

        def broken_version(path):
            raise ValueError('not a PE file')

        row = subject.describe([Path('/sys/a.dll')], sign=broken_sign, version=lambda path: {})[Path('/sys/a.dll')]
        self.assertIn('powershell unavailable', row['identity_error'])
        self.assertNotIn('signature_status', row)
        row = subject.describe([Path('/sys/a.dll')], sign=lambda items: {}, version=broken_version)[Path('/sys/a.dll')]
        self.assertIn('not a PE file', row['identity_error'])

    def test_signature_query_is_skipped_off_windows_or_without_paths(self):
        calls = []
        self.assertEqual(subject.signatures([], runner=lambda *a, **k: calls.append(a)), {})
        if sys.platform != 'win32':
            self.assertEqual(subject.signatures(['/x.dll'], runner=lambda *a, **k: calls.append(a)), {})
        self.assertEqual(calls, [])


class SummaryTests(unittest.TestCase):
    def test_only_non_wheel_files_are_grouped_by_origin_directory_and_signer(self):
        files = [dict(origin='system-native', source_directory='C:/Windows/System32', company='Microsoft Corporation',
                      signature_status='Valid', signer='CN=Microsoft Windows'),
                 dict(origin='system-native', source_directory='C:/Windows/System32', company='Microsoft Corporation',
                      signature_status='Valid', signer='CN=Microsoft Windows'),
                 dict(origin='system-native', source_directory='C:/tools'),
                 dict(origin='python-runtime', source_directory='C:/Python'),
                 dict(origin='installed-wheel', source_directory='ignored')]
        summary = subject.summarize(files)
        self.assertEqual([(row['origin'], row['source_directory'], row['signature_status'], row['files'])
                          for row in summary],
                         [('python-runtime', 'C:/Python', '', 1), ('system-native', 'C:/Windows/System32', 'Valid', 2),
                          ('system-native', 'C:/tools', '', 1)])


class ExcludedNameTests(unittest.TestCase):
    def test_excluded_names_match_both_filters_and_nothing_else(self):
        for name in ('qopensslbackend.dll', 'LIBSSL-3-X64.DLL', 'libcrypto-3-x64.dll', 'opencv_videoio_ffmpeg500_64.dll'):
            self.assertTrue(bundle_filters.is_excluded_name(name), name)
        for name in ('libssl-3.dll', 'qschannelbackend.dll', 'opencv_videoio_ffmpeg500_64.dll.txt', 'cv2.pyd'):
            self.assertFalse(bundle_filters.is_excluded_name(name), name)


if __name__ == '__main__':
    unittest.main()

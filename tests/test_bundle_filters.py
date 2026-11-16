"""隨包原生檔排除規則：只排除明確列出的三個檔名，其餘保持原順序。"""
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import bundle_filters as subject


class OpenSslFilterTests(unittest.TestCase):
    def test_only_named_files_are_dropped_on_either_separator(self):
        entries = [('PySide6\\plugins\\tls\\qopensslbackend.dll', 'C:\\site\\qopensslbackend.dll', 'BINARY'),
                   ('PySide6/plugins/tls/qschannelbackend.dll', '/site/qschannelbackend.dll', 'BINARY'),
                   ('libssl-3-x64.dll', 'C:\\Windows\\System32\\libssl-3-x64.dll', 'BINARY'),
                   ('LIBCRYPTO-3-X64.DLL', 'C:\\somewhere\\libcrypto-3-x64.dll', 'BINARY'),
                   ('libssl-3.dll', 'C:\\Python\\DLLs\\libssl-3.dll', 'BINARY'),
                   ('libcrypto-3.dll', 'C:\\Python\\DLLs\\libcrypto-3.dll', 'BINARY'),
                   ('pkg/libcrypto-3-x64.dll.txt', '/notice', 'DATA')]
        kept, dropped = subject.drop_untracked_openssl(entries)
        self.assertEqual(dropped, ['LIBCRYPTO-3-X64.DLL', 'PySide6/plugins/tls/qopensslbackend.dll',
                                   'libssl-3-x64.dll'])
        self.assertEqual([entry[0] for entry in kept],
                         ['PySide6/plugins/tls/qschannelbackend.dll', 'libssl-3.dll', 'libcrypto-3.dll',
                          'pkg/libcrypto-3-x64.dll.txt'])
        self.assertTrue(all(entry in entries for entry in kept))

    def test_nothing_to_drop_returns_entries_unchanged(self):
        entries = [('a.dll', '/a.dll', 'BINARY'), ('b.pyd', '/b.pyd', 'EXTENSION')]
        self.assertEqual(subject.drop_untracked_openssl(entries), (entries, []))


class OpenCvFfmpegFilterTests(unittest.TestCase):
    def test_only_the_bundled_ffmpeg_plugin_is_dropped(self):
        entries = [('cv2\\opencv_videoio_ffmpeg500_64.dll', 'C:\\site\\cv2\\opencv_videoio_ffmpeg500_64.dll', 'BINARY'),
                   ('cv2/OPENCV_VIDEOIO_FFMPEG4110.DLL', '/site/x.dll', 'BINARY'),
                   ('cv2/cv2.pyd', '/site/cv2/cv2.pyd', 'EXTENSION'),
                   ('cv2/opencv_videoio_msmf500_64.dll', '/site/msmf.dll', 'BINARY'),
                   ('licenses/opencv_videoio_ffmpeg500_64.dll.txt', '/notice', 'DATA'),
                   ('ffmpeg.exe', '/elsewhere/ffmpeg.exe', 'BINARY')]
        kept, dropped = subject.drop_opencv_ffmpeg(entries)
        self.assertEqual(dropped, ['cv2/OPENCV_VIDEOIO_FFMPEG4110.DLL', 'cv2/opencv_videoio_ffmpeg500_64.dll'])
        self.assertEqual([entry[0] for entry in kept],
                         ['cv2/cv2.pyd', 'cv2/opencv_videoio_msmf500_64.dll',
                          'licenses/opencv_videoio_ffmpeg500_64.dll.txt', 'ffmpeg.exe'])

    def test_no_match_returns_entries_unchanged(self):
        entries = [('cv2/cv2.pyd', '/site/cv2/cv2.pyd', 'EXTENSION')]
        self.assertEqual(subject.drop_opencv_ffmpeg(entries), (entries, []))


class MicrosoftRuntimeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.python = self.root / 'python'
        self.site = self.root / 'site'
        self.elsewhere = self.root / 'jdk' / 'bin'
        self.redist = self.root / 'redist'
        for directory in (self.python, self.site / 'pkg', self.elsewhere, self.redist):
            directory.mkdir(parents=True)
        for path in (self.python / 'vcruntime140.dll', self.site / 'pkg' / 'msvcp140.dll',
                     self.elsewhere / 'msvcp140.dll', self.elsewhere / 'MSVCP140_1.dll',
                     self.redist / 'msvcp140.dll', self.redist / 'msvcp140_1.dll'):
            path.write_bytes(b'x')

    def test_universal_crt_is_dropped_by_exact_name_family(self):
        entries = [('api-ms-win-crt-runtime-l1-1-0.dll', 'a', 'BINARY'), ('UCRTBASE.DLL', 'b', 'BINARY'),
                   ('ucrtbased.dll', 'c', 'BINARY'), ('msvcp140.dll', 'd', 'BINARY'),
                   ('notices/api-ms-win-core.dll.txt', 'e', 'DATA')]
        kept, dropped = subject.drop_os_ucrt(entries)
        self.assertEqual(dropped, ['UCRTBASE.DLL', 'api-ms-win-crt-runtime-l1-1-0.dll'])
        self.assertEqual([entry[0] for entry in kept], ['ucrtbased.dll', 'msvcp140.dll', 'notices/api-ms-win-core.dll.txt'])

    def test_only_untrusted_vc_runtime_is_replaced_from_the_redistributable_directory(self):
        entries = [('vcruntime140.dll', str(self.python / 'vcruntime140.dll'), 'BINARY'),
                   ('pkg/msvcp140.dll', str(self.site / 'pkg' / 'msvcp140.dll'), 'BINARY'),
                   ('msvcp140.dll', str(self.elsewhere / 'msvcp140.dll'), 'BINARY'),
                   ('MSVCP140_1.dll', str(self.elsewhere / 'MSVCP140_1.dll'), 'BINARY'),
                   ('other.dll', str(self.elsewhere / 'other.dll'), 'BINARY')]
        result, replaced = subject.official_vc_runtime(entries, self.redist, (self.python, self.site))
        self.assertEqual(result[:2], entries[:2])
        self.assertEqual(result[4], entries[4])
        self.assertEqual(result[2], ('msvcp140.dll', str(self.redist / 'msvcp140.dll'), 'BINARY'))
        self.assertEqual(result[3], ('MSVCP140_1.dll', str(self.redist / 'msvcp140_1.dll'), 'BINARY'))
        self.assertEqual([row[0] for row in replaced], ['msvcp140.dll', 'MSVCP140_1.dll'])

    def test_missing_official_file_or_directory_is_an_error_not_a_silent_fallback(self):
        entries = [('concrt140.dll', str(self.elsewhere / 'concrt140.dll'), 'BINARY')]
        with self.assertRaisesRegex(RuntimeError, 'Official VC runtime not found'):
            subject.official_vc_runtime(entries, self.redist, (self.python, self.site))
        with self.assertRaisesRegex(RuntimeError, 'Official VC runtime not found'):
            subject.official_vc_runtime([('msvcp140.dll', str(self.elsewhere / 'msvcp140.dll'), 'BINARY')],
                                        None, (self.python, self.site))
        # 沒有需要替換的檔案時，不要求可再散布目錄存在。
        trusted = [('vcruntime140.dll', str(self.python / 'vcruntime140.dll'), 'BINARY')]
        self.assertEqual(subject.official_vc_runtime(trusted, None, (self.python, self.site)), (trusted, []))

    def test_newest_redistributable_directory_is_selected(self):
        studio = self.root / 'vs'
        for version in ('14.9.1', '14.44.35112', '14.40.33807'):
            (studio / 'VC' / 'Redist' / 'MSVC' / version / 'x64' / 'Microsoft.VC143.CRT').mkdir(parents=True)
        (studio / 'VC' / 'Redist' / 'MSVC' / '14.99.0' / 'x64' / 'Microsoft.VC143.DebugCRT').mkdir(parents=True)
        vswhere = self.root / 'vswhere.exe'
        vswhere.write_bytes(b'')
        runner = lambda *a, **k: SimpleNamespace(returncode=0, stdout=str(studio) + '\n')
        self.assertEqual(subject.find_vc_redist(runner=runner, vswhere=vswhere).parts[-3], '14.44.35112')
        self.assertIsNone(subject.find_vc_redist(runner=runner, vswhere=self.root / 'missing.exe'))
        failed = lambda *a, **k: SimpleNamespace(returncode=1, stdout='')
        self.assertIsNone(subject.find_vc_redist(runner=failed, vswhere=vswhere))


if __name__ == '__main__':
    unittest.main()

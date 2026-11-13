"""隨包原生檔排除規則：只排除明確列出的三個檔名，其餘保持原順序。"""
from pathlib import Path
import sys
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


if __name__ == '__main__':
    unittest.main()

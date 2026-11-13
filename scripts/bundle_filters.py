"""打包前排除不該隨包的原生檔；供 PyInstaller spec 與測試共用。

背景：Qt 的 OpenSSL TLS 外掛（plugins/tls/qopensslbackend.dll）依賴 libssl-3-x64／
libcrypto-3-x64.dll。PyInstaller 做相依分析時會從建置機的系統路徑把這兩個檔案收進來，
版本與來源隨 runner 映像而變、無法追溯。應用程式不使用 Qt 的網路 TLS；Windows 上 Qt
另有系統內建的 Schannel 後端（qschannelbackend.dll）保留不動。

限制：只比對下列明確檔名，不用萬用字元。CPython 自己的 libssl-3.dll／libcrypto-3.dll
（沒有 -x64 字尾，供 Python 的 ssl 模組使用）不在排除範圍。若日後有其他模組真的
需要這份 OpenSSL，應改為固定來源後再納入，而不是恢復從系統路徑收集。
"""
import re
from pathlib import PurePosixPath

UNTRACKED_OPENSSL = frozenset(('qopensslbackend.dll', 'libssl-3-x64.dll', 'libcrypto-3-x64.dll'))
# opencv-python 的 wheel 內附 FFmpeg 影片讀寫外掛（LGPL）。OCR worker 只處理圖片，用不到影片 I/O；
# cv2 在需要 FFmpeg 後端時才載入它，缺少時其餘功能不受影響。影音轉換日後另做獨立選配元件，
# 屆時使用固定來源的 FFmpeg 並一併處理其授權義務，不沿用這份順帶進來的檔案。
OPENCV_FFMPEG = re.compile(r'^opencv_videoio_ffmpeg\d*(_64)?\.dll$', re.IGNORECASE)


def drop_untracked_openssl(entries):
    """回傳 (保留的 TOC 條目, 被排除的目的路徑)；條目格式為 (目的路徑, 來源路徑, 類型)。"""
    kept, dropped = [], []
    for entry in entries:
        destination = str(entry[0]).replace('\\', '/')
        if PurePosixPath(destination).name.lower() in UNTRACKED_OPENSSL:
            dropped.append(destination)
        else:
            kept.append(entry)
    return kept, sorted(dropped)


def drop_opencv_ffmpeg(entries):
    """回傳 (保留的 TOC 條目, 被排除的目的路徑)；只排除 OpenCV 內附的 FFmpeg 影片外掛。"""
    kept, dropped = [], []
    for entry in entries:
        destination = str(entry[0]).replace('\\', '/')
        if OPENCV_FFMPEG.match(PurePosixPath(destination).name):
            dropped.append(destination)
        else:
            kept.append(entry)
    return kept, sorted(dropped)

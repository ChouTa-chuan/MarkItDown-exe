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
import subprocess
from pathlib import Path, PurePosixPath

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


def is_excluded_name(name):
    """檔名是否屬於已決定不隨包的原生檔；供建置後的檢核確認排除確實生效。"""
    return name.lower() in UNTRACKED_OPENSSL or bool(OPENCV_FFMPEG.match(name))


# ---- Microsoft 執行期 ----
# 2026-11-13 的 Windows CI 顯示：隨包的 api-ms-win-*.dll、ucrtbase.dll 與 msvcp140.dll 並非來自
# Windows 系統目錄，而是 PyInstaller 沿 PATH 從 runner 上某個 Java JDK 的 bin 目錄收進來的複本。
# 那不是 Microsoft 指定的散布來源，內容也隨 runner 映像變動。處理方式分兩類：
# - Universal CRT（api-ms-win-*、ucrtbase）是 Windows 10 以後內建的系統元件，本專案目標為
#   Windows 10／11，因此不隨包，由作業系統提供。
# - Visual C++ runtime（msvcp140*.dll 等）改從 Visual Studio 的可再散布目錄取得；
#   CPython 安裝與 wheel 自帶的複本各有其散布依據，維持原樣。
OS_UCRT = re.compile(r'^(api-ms-win-[a-z0-9-]+|ucrtbase)\.dll$', re.IGNORECASE)
VC_RUNTIME = re.compile(r'^(msvcp140(_\d|_atomic_wait|_codecvt_ids)?|vcruntime140(_1|_threads)?|concrt140|vccorlib140)\.dll$',
                        re.IGNORECASE)
VSWHERE = Path(r'C:\Program Files (x86)\Microsoft Visual Studio\Installer\vswhere.exe')


def drop_os_ucrt(entries):
    """回傳 (保留的條目, 被排除的目的路徑)；排除由 Windows 10 以後作業系統提供的 Universal CRT。"""
    kept, dropped = [], []
    for entry in entries:
        destination = str(entry[0]).replace('\\', '/')
        if OS_UCRT.match(PurePosixPath(destination).name):
            dropped.append(destination)
        else:
            kept.append(entry)
    return kept, sorted(dropped)


def find_vc_redist(runner=subprocess.run, vswhere=VSWHERE):
    """回傳 Visual Studio x64 CRT 可再散布目錄；找不到時回傳 None，由呼叫端決定是否中止。"""
    if not Path(vswhere).is_file():
        return None
    done = runner([str(vswhere), '-latest', '-products', '*', '-property', 'installationPath'],
                  capture_output=True, text=True, timeout=60)
    root = Path(done.stdout.strip().splitlines()[0]) if done.returncode == 0 and done.stdout.strip() else None
    if root is None:
        return None
    # 版本目錄以數字排序取最新；只接受正式的 Microsoft.VC*.CRT，不取 debug 或 onecore 目錄。
    candidates = sorted((root / 'VC' / 'Redist' / 'MSVC').glob('*/x64/Microsoft.VC*.CRT'),
                        key=lambda path: [int(part) if part.isdigit() else 0 for part in path.parts[-3].split('.')])
    return candidates[-1] if candidates else None


def official_vc_runtime(entries, redist, trusted_roots):
    """把不是來自受信任位置的 VC runtime 換成可再散布目錄中的同名檔。

    trusted_roots：CPython 安裝目錄與 site-packages；位於其下的複本不更動。
    需要替換卻找不到可再散布目錄或同名檔時直接丟出錯誤，避免默默沿用來源不明的檔案。
    回傳 (新的條目, [(目的路徑, 原來源, 新來源)])。
    """
    trusted = [Path(root).resolve() for root in trusted_roots]
    available = {path.name.lower(): path for path in Path(redist).iterdir()} if redist else {}
    result, replaced = [], []
    for entry in entries:
        destination = str(entry[0]).replace('\\', '/')
        name = PurePosixPath(destination).name
        source = Path(entry[1])
        if not VC_RUNTIME.match(name) or any(source.resolve().is_relative_to(root) for root in trusted):
            result.append(entry)
            continue
        official = available.get(name.lower())
        if official is None:
            raise RuntimeError(f'Official VC runtime not found for {name}; refusing untracked source {source}')
        result.append((entry[0], str(official), *entry[2:]))
        replaced.append((destination, str(source), str(official)))
    return result, replaced

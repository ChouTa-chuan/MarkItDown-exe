"""Windows GEOS：只從使用者資料下的獨立目錄預載完整的一組替換 DLL。"""
from contextlib import ExitStack, contextmanager
import ctypes
from ctypes import wintypes
import hashlib
import os
from pathlib import Path, PureWindowsPath
import stat
import sys

from ..components.registry import IntegrityError, _chain, _plain

DIRECTORY = 'geos-replacement'
NAMES = ('geos-bf067cd6ff74ee0ad5f3ff52c7ef08c9.dll',
         'geos_c-6dd9fd915eef8a7928285416bef1e666.dll')
STATUS = 'user-replacement-unverified'
LABEL = 'GEOS 使用者替換、未驗證'
FAILURE = 'geos_replacement_failed'
ERROR = 'GEOS 使用者替換失敗。請核對兩檔的名稱、版本與相容性，或移除全部替換檔後重試。'


class GeosReplacementError(ValueError):
    """選用了替換，但無法安全確認來源路徑或啟動該組程式庫。"""


def requested(directory):
    """舊 worker 在空目錄下仍使用原命令。可疑路徑交給新 worker 明確拒絕。"""
    try:
        directory.lstat()
        _chain(directory)
        return not directory.is_dir() or next(directory.iterdir(), None) is not None
    except FileNotFoundError:
        return False
    except (OSError, IntegrityError):
        return True


def replacement_files(directory, managed):
    """名稱、連結及目錄邊界在解析路徑之前驗證，空目錄代表沿用受管 DLL。"""
    if (not directory.is_absolute() or '..' in directory.parts or directory.name != DIRECTORY
            or directory.is_relative_to(managed)):
        raise GeosReplacementError('替換目錄須為受管目錄之外的固定絕對路徑。')
    try:
        _chain(directory)
        try:
            mode = _plain(directory).st_mode
        except FileNotFoundError:
            return ()
        if not stat.S_ISDIR(mode):
            raise GeosReplacementError('替換路徑須為資料夾。')
        names = {item.name for item in directory.iterdir()}
        if not names:
            return ()
        if names != set(NAMES):
            raise GeosReplacementError('替換目錄須剛好包含兩個指定的 GEOS DLL。')
        paths = tuple(directory/name for name in NAMES)
        for path in paths:
            info = _plain(path)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise GeosReplacementError('替換檔須為獨立的一般檔案。')
        return paths
    except (OSError, IntegrityError) as exc:
        raise GeosReplacementError('替換路徑不可含連結或無法讀取的檔案。') from exc


def record_detail(record):
    if record is None:
        return ''
    parts = [f"{file['path']}（SHA-256 {file['sha256']}）" for file in record['files']]
    return LABEL + '：' + '；'.join(parts)


def valid_record(value):
    """同一個固定使用者目錄的兩個絕對路徑，每個都必須有完整的指紋。"""
    if not isinstance(value, dict) or set(value) != {'status', 'files'} or value['status'] != STATUS:
        return False
    files = value['files']
    if not isinstance(files, list) or len(files) != len(NAMES):
        return False
    parents = set()
    for row, name in zip(files, NAMES):
        if not isinstance(row, dict) or set(row) != {'path', 'sha256'}:
            return False
        path, digest = row['path'], row['sha256']
        if (not isinstance(path, str) or '\x00' in path or not isinstance(digest, str)
                or len(digest) != 64 or any(char not in '0123456789abcdef' for char in digest)):
            return False
        parsed = PureWindowsPath(path)
        if not parsed.is_absolute() or '..' in parsed.parts or parsed.name != name or parsed.parent.name != DIRECTORY:
            return False
        parents.add(parsed.parent)
    return len(parents) == 1


@contextmanager
def _pin_file(path, kernel):
    """允許 Windows loader 讀取，但載入與取指紋期間拒絕改寫或刪除檔案。"""
    import msvcrt

    open_file = kernel.CreateFileW
    open_file.argtypes = (wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.c_void_p,
                          wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE)
    open_file.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = (wintypes.HANDLE,)
    close.restype = wintypes.BOOL
    # GENERIC_READ、FILE_SHARE_READ、OPEN_EXISTING、FILE_FLAG_OPEN_REPARSE_POINT。
    handle = open_file(str(path), 0x80000000, 1, None, 3, 0x00200000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        fd = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
    except OSError:
        close(handle)
        raise
    with os.fdopen(fd, 'rb') as stream:
        _chain(path)
        info = os.fstat(fd)
        stored = _plain(path)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or not os.path.samestat(info, stored):
            raise GeosReplacementError('開啟後的替換檔身分不符。')
        yield stream


def _loaded_paths(kernel):
    """以實際程序模組清單核對路徑及同名模組是否重複。"""
    process = kernel.GetCurrentProcess
    process.restype = wintypes.HANDLE
    enum = kernel.K32EnumProcessModules
    enum.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE), wintypes.DWORD,
                     ctypes.POINTER(wintypes.DWORD))
    enum.restype = wintypes.BOOL
    name = kernel.GetModuleFileNameW
    name.argtypes = (wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD)
    name.restype = wintypes.DWORD
    modules = (wintypes.HMODULE * 1024)()
    needed = wintypes.DWORD()
    if not enum(process(), modules, ctypes.sizeof(modules), ctypes.byref(needed)) or needed.value > ctypes.sizeof(modules):
        raise ctypes.WinError(ctypes.get_last_error())
    paths = []
    for module in modules[:needed.value // ctypes.sizeof(wintypes.HMODULE)]:
        buffer = ctypes.create_unicode_buffer(32768)
        if not 0 < name(module, buffer, len(buffer)) < len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        path = Path(buffer.value)
        if path.name.lower() in NAMES:
            paths.append(path)
    return paths


def load_replacement(directory, managed):
    """在匯入 Shapely 前載入 core/C API，失敗交呼叫端停止此 worker。"""
    if directory is None:
        return None, ()
    if sys.platform != 'win32' or 'shapely' in sys.modules:
        raise GeosReplacementError('GEOS 替換須在 Windows worker 匯入 Shapely 前執行。')
    paths = replacement_files(directory, managed)
    if not paths:
        return None, ()
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    try:
        if _loaded_paths(kernel):
            raise GeosReplacementError('程序內已有 GEOS，無法保證替換來源。')
        with ExitStack() as stack:
            files = []
            for path in paths:
                stream = stack.enter_context(_pin_file(path, kernel))
                files.append(dict(path=str(path), sha256=hashlib.file_digest(stream, 'sha256').hexdigest()))
            # 搜尋僅含明確載入路徑及 Windows 安全搜尋目錄。先載入 core 再載入 C API。
            handles = tuple(ctypes.WinDLL(str(path), winmode=0x1100) for path in paths)
            import shapely
            if (shapely.geos_version != (3, 14, 1) or shapely.geos_capi_version != (1, 20, 5)
                    or shapely.box(0, 0, 3, 3).intersection(shapely.box(1, 1, 4, 4)).area != 4):
                raise GeosReplacementError('替換 GEOS 的版本、ABI 或幾何運算不相容。')
            loaded = _loaded_paths(kernel)
            if len(loaded) != len(paths) or {path.resolve() for path in loaded} != {path.resolve() for path in paths}:
                raise GeosReplacementError('程序未從指定目錄載入兩個 GEOS 替換檔。')
            return dict(status=STATUS, files=files), handles
    except (OSError, ImportError, IntegrityError) as exc:
        raise GeosReplacementError('無法載入或核對 GEOS 替換檔。') from exc

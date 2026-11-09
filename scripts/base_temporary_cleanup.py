"""只供可拋棄 Windows CI 清理自己建立的安裝中斷產物；不讀外部收據授權刪除。"""
from contextlib import ExitStack
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys

from desktop_app.components.contracts import relative_path
from desktop_app.components.registry import _chain

TEMPORARY_NAME = re.compile(r'is-[a-z0-9]{6,16}\.tmp', re.I)
MAX_BYTES = 128 * 1024**2


@dataclass(frozen=True)
class CapturedTemporary:
    root: str
    path: str
    sha256: str
    bytes: int
    identity: tuple
    pid: int
    stage: str
    setup_sha256: str


def _snapshot(source):
    if os.name != 'nt':
        info = os.fstat(source.fileno())
        return (stat.S_ISREG(info.st_mode), info.st_nlink,
                getattr(info, 'st_file_attributes', 0),
                (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns))
    # Windows CPython 的 CRT fstat 不可靠地提供 file index／link count；
    # 身分及連結數必須直接從同一個 Win32 handle 取得，不退回可遭替換的路徑查詢。
    import ctypes
    from ctypes import wintypes
    import msvcrt
    class Information(ctypes.Structure):
        _fields_ = [('attributes', wintypes.DWORD), ('created', wintypes.FILETIME),
                    ('accessed', wintypes.FILETIME), ('written', wintypes.FILETIME),
                    ('volume', wintypes.DWORD), ('size_high', wintypes.DWORD),
                    ('size_low', wintypes.DWORD), ('links', wintypes.DWORD),
                    ('index_high', wintypes.DWORD), ('index_low', wintypes.DWORD)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    method = kernel.GetFileInformationByHandle
    method.argtypes = [wintypes.HANDLE, ctypes.POINTER(Information)]; method.restype = wintypes.BOOL
    handle = msvcrt.get_osfhandle(source.fileno()); info = Information()
    if not method(handle, ctypes.byref(info)):
        raise ctypes.WinError(ctypes.get_last_error())
    file_type = kernel.GetFileType
    file_type.argtypes = [wintypes.HANDLE]; file_type.restype = wintypes.DWORD
    def packed(high, low): return (high << 32) | low
    identity = (info.volume, packed(info.index_high, info.index_low), packed(info.size_high, info.size_low),
                packed(info.written.dwHighDateTime, info.written.dwLowDateTime),
                packed(info.created.dwHighDateTime, info.created.dwLowDateTime))
    return (file_type(handle) == 1 and not info.attributes & 0x10, info.links, info.attributes, identity)


def fingerprint(source):
    """從同一 handle 核對類型、單一連結、檔案身分及內容，避免驗A檔卻刪B檔。"""
    before = _snapshot(source)
    regular, links, attributes, identity = before
    if (not regular or links != 1 or identity[2] > MAX_BYTES
            or not identity[1] or attributes & 0x400):
        raise ValueError('Temporary must be a bounded, unlinked regular file with one owner')
    digest = hashlib.sha256(); size = 0
    for block in iter(lambda: source.read(65536), b''):
        size += len(block)
        if size > MAX_BYTES:
            raise ValueError('Temporary exceeds the size limit')
        digest.update(block)
    after = _snapshot(source)
    if before != after or size != identity[2]:
        raise ValueError('Temporary changed during verification')
    return digest.hexdigest(), size, after[3]


def _windows_reader(path):
    """獨占寫入／刪除分享，拒絕reparse，之後以同一handle標記刪除，不用Path.unlink。"""
    import ctypes
    from ctypes import wintypes
    import msvcrt
    import ntpath
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    create = kernel.CreateFileW
    create.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, wintypes.LPVOID,
                       wintypes.DWORD, wintypes.DWORD, wintypes.HANDLE]
    create.restype = wintypes.HANDLE
    close = kernel.CloseHandle
    close.argtypes = [wintypes.HANDLE]; close.restype = wintypes.BOOL
    handle = create(str(path), 0x80000000 | 0x10000, 1, None, 3, 0x00200000 | 0x08000000, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        final = kernel.GetFinalPathNameByHandleW
        final.argtypes = [wintypes.HANDLE, wintypes.LPWSTR, wintypes.DWORD, wintypes.DWORD]
        final.restype = wintypes.DWORD
        name = ctypes.create_unicode_buffer(32768)
        length = final(handle, name, len(name), 0)
        if not 0 < length < len(name):
            raise ctypes.WinError(ctypes.get_last_error())
        actual = name.value
        if actual.startswith('\\\\?\\UNC\\'): actual = '\\\\' + actual[8:]
        elif actual.startswith('\\\\?\\'): actual = actual[4:]
        if ntpath.normcase(ntpath.normpath(actual)) != ntpath.normcase(ntpath.normpath(str(path))):
            raise ValueError('Opened temporary resolved outside its exact owned path')
        descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
        handle = None  # ownership now belongs to the Python descriptor
        return os.fdopen(descriptor, 'rb')
    finally:
        if handle is not None: close(handle)


def _reader(path):
    if sys.platform == 'win32':
        return _windows_reader(path)
    # Linux 僅供讀取／契約測試；真正刪除仍由下方 Windows 門檻限制。
    return os.fdopen(os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)
                            | getattr(os, 'O_NONBLOCK', 0)), 'rb')


def capture(directory, before, observed, *, pid, stage, setup_sha256, parents, protected):
    """只由本次控制端操作前快照＋自身停點觀察產生記憶體收據，不能從JSON匯入。"""
    directory = Path(directory).absolute(); _chain(directory)
    if type(pid) is not int or pid < 1 or stage not in ('intent', 'first-file', 'payload-written'):
        raise ValueError('Missing owned process/checkpoint')
    if not re.fullmatch(r'[0-9a-f]{64}', setup_sha256):
        raise ValueError('Missing exact test installer hash')
    protected = {name.casefold() for name in protected}
    existing = {name.casefold() for name in before}
    receipts = []
    for name in sorted(observed):
        relative_path(name)
        path = PurePosixPath(name)
        if name.casefold() in existing:
            continue
        if (not TEMPORARY_NAME.fullmatch(path.name) or str(path.parent) not in parents
                or name.casefold() in protected):
            raise ValueError('Temporary is outside the observed maintenance scope')
        target = directory/name; _chain(target)
        with _reader(target) as source:
            digest, size, identity = fingerprint(source)
        receipts.append(CapturedTemporary(str(directory), name, digest, size, identity, pid, stage, setup_sha256))
    return receipts


def validate_receipts(directory, receipts):
    """預檢全部收據；任何缺檔、改名、同bytes替換、連結或重複，皆先停止，不刪部分檔。"""
    directory = Path(directory).absolute(); _chain(directory)
    seen = set()
    for receipt in receipts:
        if type(receipt) is not CapturedTemporary or receipt.root != str(directory):
            raise ValueError('Only in-memory receipts for this exact test directory are accepted')
        relative_path(receipt.path)
        if not TEMPORARY_NAME.fullmatch(PurePosixPath(receipt.path).name) or receipt.path.casefold() in seen:
            raise ValueError('Invalid or duplicate temporary receipt')
        seen.add(receipt.path.casefold())
        path = directory/receipt.path; _chain(path)
        with _reader(path) as source:
            actual = fingerprint(source)
        if actual != (receipt.sha256, receipt.bytes, receipt.identity):
            raise ValueError('Captured temporary was modified or replaced: '+receipt.path)
    return True


def _mark_deleted(source):
    import ctypes
    from ctypes import wintypes
    import msvcrt
    class Disposition(ctypes.Structure):
        _fields_ = [('DeleteFile', ctypes.c_ubyte)]
    method = ctypes.WinDLL('kernel32', use_last_error=True).SetFileInformationByHandle
    method.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD]
    method.restype = wintypes.BOOL
    flag = Disposition(1)
    if not method(msvcrt.get_osfhandle(source.fileno()), 4, ctypes.byref(flag), ctypes.sizeof(flag)):
        raise ctypes.WinError(ctypes.get_last_error())


def cleanup(directory, receipts, *, quiescent):
    """不掃描通配、不刪目錄、不終止程序；鎖住全部原檔並重驗後，才逐一標記delete-on-close。"""
    if (sys.platform != 'win32' or os.environ.get('GITHUB_ACTIONS') != 'true'
            or os.environ.get('RUNNER_OS') != 'Windows'):
        raise RuntimeError('Cleanup requires a disposable actual Windows CI account')
    receipts = tuple(receipts)
    if not quiescent(): raise RuntimeError('Owned installer processes have not exited')
    validate_receipts(directory, receipts)
    records = []
    with ExitStack() as stack:
        opened = []
        for receipt in receipts:
            path = Path(directory).absolute()/receipt.path; _chain(path)
            source = stack.enter_context(_windows_reader(path))
            if fingerprint(source) != (receipt.sha256, receipt.bytes, receipt.identity):
                raise ValueError('Temporary changed before acquiring deletion handles')
            opened.append((receipt, source))
        # 全部handle已拒絕寫入／rename／delete分享，預檢失敗不會先刪第一個檔案。
        if not quiescent(): raise RuntimeError('Owned process state changed before cleanup')
        for receipt, source in opened:
            _mark_deleted(source)
            records.append(dict(path=receipt.path, sha256=receipt.sha256, bytes=receipt.bytes,
                                stage=receipt.stage, pid=receipt.pid, deletion_marked=True))
    for receipt in receipts:
        if (Path(directory)/receipt.path).exists():
            raise RuntimeError('Marked temporary still exists after closing its handle')
    return records

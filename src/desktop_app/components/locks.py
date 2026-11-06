"""程序生命週期鎖：固定鎖檔不刪除，核心鎖會在程序結束時自動釋放。"""
from contextlib import contextmanager
import os
from pathlib import Path
import stat

from .registry import _chain, _plain


class ComponentBusy(RuntimeError):
    """元件仍在使用或維護中，呼叫端可取消、稍後重試，不強制解鎖。"""


@contextmanager
def file_lock(path, *, exclusive):
    """Linux flock／Windows LockFileEx；非阻塞，不用 PID 或時間猜測鎖已失效。"""
    path = Path(path).absolute()
    _chain(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | getattr(os, 'O_NOFOLLOW', 0), 0o600)
    locked = False
    try:
        info = os.fstat(descriptor)
        current = _plain(path)
        if (not stat.S_ISREG(info.st_mode) or info.st_size != 0
                or (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino)):
            raise ValueError('鎖檔不是本服務使用的空白一般檔案。')
        if os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            import msvcrt
            class Overlapped(ctypes.Structure):
                _fields_ = [('Internal', ctypes.c_size_t), ('InternalHigh', ctypes.c_size_t),
                            ('Offset', wintypes.DWORD), ('OffsetHigh', wintypes.DWORD), ('hEvent', wintypes.HANDLE)]
            kernel = ctypes.WinDLL('kernel32', use_last_error=True)
            kernel.LockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                         wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(Overlapped)]
            kernel.LockFileEx.restype = wintypes.BOOL
            kernel.UnlockFileEx.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.DWORD,
                                           wintypes.DWORD, ctypes.POINTER(Overlapped)]
            kernel.UnlockFileEx.restype = wintypes.BOOL
            overlap = Overlapped()
            handle = msvcrt.get_osfhandle(descriptor)
            if not kernel.LockFileEx(handle, 1 | (2 if exclusive else 0), 0, 1, 0, ctypes.byref(overlap)):
                code = ctypes.get_last_error()
                if code in (32, 33):
                    raise ComponentBusy('元件仍在使用或維護中。')
                raise ctypes.WinError(code)
        else:
            import fcntl
            try:
                fcntl.flock(descriptor, (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise ComponentBusy('元件仍在使用或維護中。') from exc
        locked = True
        yield
    finally:
        if locked:
            if os.name == 'nt':
                kernel.UnlockFileEx(handle, 0, 1, 0, ctypes.byref(overlap))
            else:
                fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
        # 不刪鎖檔：其他程序可能已持有相同 inode／handle，刪檔會產生兩把不同的鎖。

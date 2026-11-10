"""Windows控制管道直接用ReadFile，避免CRT阻塞讀取與原生模組初始化的標準輸入鎖互等。"""
from .protocol import MAX_FRAME


class PipeInput:
    """只保留一個有界frame；分段／合併讀取、CRLF及EOF片段仍交原協定檢查。"""
    def __init__(self, read_chunk):
        self.read_chunk=read_chunk;self.buffer=bytearray();self.eof=False

    def readline(self, limit=MAX_FRAME+1):
        if type(limit) is not int or not 1<=limit<=MAX_FRAME+1:
            raise ValueError('Invalid control pipe line bound')
        while True:
            end=self.buffer.find(b'\n')+1
            if end or len(self.buffer)>=limit or self.eof:
                count=min(end or len(self.buffer),limit)
                value=bytes(self.buffer[:count]);del self.buffer[:count]
                return value
            count=min(4096,limit-len(self.buffer))
            data=self.read_chunk(count)
            if not isinstance(data,bytes) or len(data)>count:
                raise ValueError('Invalid control pipe read')
            if not data:self.eof=True
            else:self.buffer.extend(data)


def windows_pipe_input(descriptor):
    """借用stdin的Win32 HANDLE，不由CRT _read持有fd鎖；所有權仍屬原Python標準輸入。"""
    import ctypes
    from ctypes import wintypes
    import msvcrt
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    handle=msvcrt.get_osfhandle(descriptor)
    file_type=kernel.GetFileType;file_type.argtypes=[wintypes.HANDLE];file_type.restype=wintypes.DWORD
    if file_type(handle)!=3:raise ValueError('Worker control input must be a Windows pipe')
    read=kernel.ReadFile
    read.argtypes=[wintypes.HANDLE,wintypes.LPVOID,wintypes.DWORD,ctypes.POINTER(wintypes.DWORD),wintypes.LPVOID]
    read.restype=wintypes.BOOL
    def read_chunk(count):
        target=ctypes.create_string_buffer(count);received=wintypes.DWORD()
        # ctypes外部呼叫釋放GIL，背景reader可持續接收pause／cancel及父程序EOF。
        if not read(handle,target,count,ctypes.byref(received),None):
            code=ctypes.get_last_error()
            if code in (109,232):return b''
            raise ctypes.WinError(code)
        return target.raw[:received.value]
    return PipeInput(read_chunk)

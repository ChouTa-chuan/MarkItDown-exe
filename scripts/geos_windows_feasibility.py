"""B3-3 hosted Windows 可行性實驗，只測 Windows 載入與 Shapely 綁定。"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import json
from pathlib import Path
import sys
import sysconfig

NAMES = ('geos-bf067cd6ff74ee0ad5f3ff52c7ef08c9.dll',
         'geos_c-6dd9fd915eef8a7928285416bef1e666.dll')


def loaded_modules():
    """以實際程序模組清單查出同名 DLL 是否重複載入。"""
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
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
        length = name(module, buffer, len(buffer))
        if not 0 < length < len(buffer):
            raise ctypes.WinError(ctypes.get_last_error())
        paths.append(Path(buffer.value))
    return paths


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def observe(replacement):
    if sys.platform != 'win32' or 'shapely' in sys.modules:
        raise ValueError('Use a fresh Windows process before importing Shapely')
    bundled = Path(sysconfig.get_path('platlib'))/'shapely.libs'
    expected = (replacement or bundled).resolve(strict=True)
    handles = []
    if replacement is not None:
        for name in NAMES:
            source = expected/name
            if sha(source) == sha(bundled/name):
                raise ValueError('Replacement equals wheel bytes: '+name)
            handles.append(ctypes.WinDLL(str(source), winmode=0x1100))
    import shapely
    if shapely.geos_version != (3, 14, 1) or shapely.geos_capi_version != (1, 20, 5):
        raise ValueError('Unexpected GEOS CAPI: '+shapely.geos_capi_version_string)
    area = shapely.box(0, 0, 3, 3).intersection(shapely.box(1, 1, 4, 4)).area
    if area != 4:
        raise ValueError('Shapely geometric intersection failed')
    paths = loaded_modules()
    files = []
    for name in NAMES:
        matches = [p for p in paths if p.name.casefold() == name.casefold()]
        if len(matches) != 1 or matches[0].resolve() != (expected/name).resolve():
            raise ValueError('Unexpected process module binding: '+name+' '+repr(matches))
        files.append(dict(name=name, loaded_path=str(matches[0]), sha256=sha(matches[0]), wheel_sha256=sha(bundled/name)))
    return dict(check='geos-windows-feasibility', mode='replacement' if replacement else 'wheel',
                geos=shapely.geos_capi_version_string, intersection_area=area, files=files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replacement', type=Path)
    args = parser.parse_args()
    try:
        print('::notice title=B3-3 GEOS feasibility::'+json.dumps(observe(args.replacement), separators=(',', ':')))
    except (OSError, ValueError, ImportError) as error:
        print('::error title=B3-3 GEOS experiment::'+str(error).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A'))
        raise SystemExit(1) from error

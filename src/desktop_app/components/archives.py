"""僅展開受信任描述列出的 ZIP 檔案；拒絕逃逸、連結、額外項目與解壓超量。"""
import os
from pathlib import Path, PurePosixPath
import stat
import struct
import zipfile

from ..core import Cancelled
from .contracts import relative_path
from .registry import IntegrityError, _chain, _plain, verify_file


def sync_directory(path):
    """POSIX 持久化目錄項目；Windows 原生持久化仍須實機驗收。"""
    if os.name != 'nt':
        descriptor = os.open(path,os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
        try:os.fsync(descriptor)
        finally:os.close(descriptor)


def durable_mkdir(path, *, exist_ok=True):
    """新建父目錄也須持久化，不能只同步最後一次 rename 的直接父目錄。"""
    path=Path(path);_chain(path)
    missing=[]
    for item in (path,*path.parents):
        if item.exists():break
        missing.append(item)
    path.mkdir(parents=True,exist_ok=exist_ok)
    for item in missing:
        sync_directory(item);sync_directory(item.parent)


def durable_rename(source, target):
    _chain(source);_chain(target)
    os.rename(source,target)
    sync_directory(Path(source).parent)
    if Path(source).parent != Path(target).parent:sync_directory(Path(target).parent)


def expected_directories(spec):
    result = set()
    for item in spec.files:
        for parent in PurePosixPath(item.path).parents:
            if parent.as_posix() != '.':result.add(parent.as_posix())
            if len(result)+len(spec.files)>8192:
                raise IntegrityError('元件宣告的目錄數量超過上限。')
    return result


def inventory(directory, spec):
    directory = Path(directory)
    _chain(directory)
    if not stat.S_ISDIR(_plain(directory).st_mode):
        raise IntegrityError('元件目錄不是一般目錄。')
    expected = {item.path for item in spec.files}
    allowed_dirs = expected_directories(spec)
    present = set()
    entries = 0
    def error(exc):
        raise exc
    for parent, dirs, names in os.walk(directory, followlinks=False, onerror=error):
        for name in (*dirs, *names):
            entries += 1
            if entries > 8192:
                raise IntegrityError('元件目錄超過列舉上限。')
            path = Path(parent)/name
            info = _plain(path)
            relative = path.relative_to(directory).as_posix()
            if stat.S_ISDIR(info.st_mode):
                if relative not in allowed_dirs:
                    raise IntegrityError('元件含未知目錄，未接管或刪除。')
            elif stat.S_ISREG(info.st_mode) and relative in expected:
                present.add(relative)
            else:
                raise IntegrityError('元件含未知檔案或特殊檔案，未接管或刪除。')
    return present


def verify_tree(directory, spec, checkpoint=lambda:None):
    if inventory(directory, spec) != {item.path for item in spec.files}:
        raise IntegrityError('元件檔案不完整。')
    for item in spec.files:
        verify_file(Path(directory)/item.path, item.size, item.sha256, checkpoint)


def delete_owned_tree(directory, spec, *, modified=False):
    """只刪描述中的已知檔案與空目錄；未知項目阻擋清理，不使用 rmtree。"""
    directory = Path(directory)
    if not directory.exists() and not directory.is_symlink():
        return
    present = inventory(directory, spec)
    if not modified:
        for item in spec.files:
            if item.path in present:
                verify_file(directory/item.path, item.size, item.sha256)
    for name in sorted(present):
        _chain(directory/name)
        (directory/name).unlink()
    for name in sorted(expected_directories(spec), key=lambda value:(value.count('/'),value), reverse=True):
        path = directory/name
        if path.exists():
            _plain(path);path.rmdir()
    directory.rmdir()


def _preflight(source):
    """先限制中央目錄大小與數量，再讓 zipfile 解析，避免 metadata 消耗無界 RAM。"""
    source.seek(0, 2)
    size = source.tell()
    source.seek(max(0, size-65557))
    tail = source.read(65557)
    index = tail.rfind(b'PK\x05\x06')
    if index < 0 or len(tail)-index < 22:
        raise IntegrityError('元件包不是支援的 ZIP 格式。')
    fields = struct.unpack_from('<4s4H2IH', tail, index)
    _, disk, central_disk, disk_entries, entries, central_size, central_start, comment = fields
    if (disk or central_disk or disk_entries != entries or not 0 < entries <= 8192
            or central_size > 4*1024**2 or central_start == 0xffffffff
            or tail[max(0,index-20):index].startswith(b'PK\x06\x07')
            or central_start+central_size > size-len(tail)+index
            or index+22+comment != len(tail)):
        raise IntegrityError('拒絕分卷、ZIP64、過量或不完整 ZIP 中央目錄。')
    source.seek(0)
    if source.read(4) != b'PK\x03\x04':
        raise IntegrityError('拒絕自解壓或附加執行檔的 ZIP。')
    source.seek(0)


def extract_archive(archive, destination, spec, checkpoint=lambda:None):
    destination = Path(destination)
    _chain(destination)
    destination.mkdir(parents=True, exist_ok=False)
    expected = {item.path:item for item in spec.files}
    directories = expected_directories(spec)
    if len(expected) + len(directories) > 8192:
        raise IntegrityError('ZIP 展開目錄數量超過上限。')
    try:
        with Path(archive).open('rb') as source:
            _preflight(source)
            with zipfile.ZipFile(source) as package:
                entries = package.infolist()
                seen = set();prefixes = {};files = {}
                for entry in entries:
                    checkpoint()
                    name = entry.filename[:-1] if entry.is_dir() else entry.filename
                    relative_path(name)
                    folded = name.casefold()
                    if folded in seen:
                        raise IntegrityError('ZIP 含重複或大小寫衝突的路徑。')
                    seen.add(folded)
                    for prefix in (*PurePosixPath(name).parents, PurePosixPath(name)):
                        value = prefix.as_posix()
                        if value == '.':continue
                        if value.casefold() in prefixes and prefixes[value.casefold()] != value:
                            raise IntegrityError('ZIP 父目錄大小寫不一致。')
                        prefixes[value.casefold()] = value
                    mode = entry.external_attr >> 16
                    kind = stat.S_IFMT(mode)
                    if (kind not in (0, stat.S_IFDIR if entry.is_dir() else stat.S_IFREG) or entry.extract_version >= 45
                            or entry.flag_bits & 1 or entry.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)):
                        raise IntegrityError('ZIP 含連結、特殊檔案、加密或不支援壓縮格式。')
                    if entry.is_dir():
                        if name not in directories or entry.file_size:
                            raise IntegrityError('ZIP 含未知或非空目錄項目。')
                    else:
                        if name not in expected or entry.file_size != expected[name].size:
                            raise IntegrityError('ZIP 檔案或大小與可信描述不符。')
                        files[name] = entry
                if set(files) != set(expected) or sum(item.file_size for item in files.values()) > spec.unpacked_bytes:
                    raise IntegrityError('ZIP 檔案不完整或超出展開上限。')
                for name, entry in files.items():
                    checkpoint()
                    target = destination/name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    _chain(target)
                    with package.open(entry) as data, target.open('xb') as output:
                        count = 0
                        while True:
                            checkpoint()
                            block = data.read(min(65536, expected[name].size-count+1))
                            if not block:break
                            count += len(block)
                            if count > expected[name].size:
                                raise IntegrityError('ZIP 實際展開超出上限。')
                            output.write(block)
                        output.flush();os.fsync(output.fileno())
                    target.chmod(0o755 if (entry.external_attr >> 16) & 0o111 else 0o644)
        verify_tree(destination, spec, checkpoint)
        for name in sorted(expected_directories(spec),key=lambda value:value.count('/'),reverse=True):
            sync_directory(destination/name)
        sync_directory(destination)
        sync_directory(destination.parent)
    except Cancelled:
        raise
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
        if isinstance(exc, IntegrityError):raise
        raise IntegrityError('ZIP 內容或校驗失敗。') from exc

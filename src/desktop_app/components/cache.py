"""可確認所有權的下載快取與配額；只回收未使用且內容未修改的完整包檔。"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import stat
import tempfile

from .locks import file_lock
from .registry import IntegrityError, _chain, _plain, verify_file
from .archives import sync_directory


class CacheQuotaError(RuntimeError):
    """沒有足夠可安全回收的空間，不刪未知或正在使用的資料。"""


class CacheStore:
    def __init__(self, directory, quota_bytes=8*1024**3):
        if type(quota_bytes) is not int or quota_bytes <= 0:
            raise ValueError('快取配額須為正整數。')
        self.directory = Path(directory).absolute()
        self.quota_bytes = quota_bytes
        _chain(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _identity(digest,size):
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest) or type(size) is not int or not 0 < size <= 2**40:
            raise ValueError('快取內容識別或大小無效。')

    def lock_path(self, digest):
        if not re.fullmatch('[0-9a-f]{64}', digest):raise ValueError('快取識別無效。')
        return self.directory/'.locks'/(digest+'.lock')

    @contextmanager
    def lock(self, digest=None, *, exclusive):
        with file_lock(self.directory/'.locks/cache.lock', exclusive=exclusive):
            if digest is None:
                yield
            else:
                with file_lock(self.lock_path(digest), exclusive=exclusive):
                    yield

    def receipt(self, digest, size):
        return dict(schema_version=1, purpose='markitdown-download-cache',
                    directory=str(self.directory), sha256=digest, size=size)

    def record(self, path, digest, size):
        """僅在本服務確實發布新檔時呼叫；已有來源不明快取不因重用而被認領。"""
        path = Path(path)
        self._identity(digest,size)
        if path != self.directory/(digest+'.archive'):
            raise ValueError('不是本服務的快取檔案。')
        verify_file(path, size, digest)
        self._write_receipt(digest,size)

    def reserve(self, digest, size):
        """新檔發布前先持久化所有權意圖；已有未知完整檔時不能認領。"""
        self._identity(digest,size)
        target = self.directory/(digest+'.archive')
        if target.exists() or target.is_symlink():raise IntegrityError('已有完整檔案，未認領。')
        self._write_receipt(digest,size)

    def _write_receipt(self, digest, size):
        receipt = self.directory/(digest+'.receipt.json')
        if receipt.exists() or receipt.is_symlink():
            if not self.has_receipt(self.directory/(digest+'.archive'),size):
                raise IntegrityError('已有不同的快取收據，未覆寫。')
            return
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=self.directory, prefix='.cache-receipt-', delete=False) as output:
                temporary = Path(output.name)
                json.dump(self.receipt(digest,size), output, sort_keys=True)
                output.flush();os.fsync(output.fileno())
            os.link(temporary, receipt)
            sync_directory(self.directory)
        finally:
            if temporary is not None:temporary.unlink(missing_ok=True)

    def _files(self):
        files = []
        for index,path in enumerate(self.directory.iterdir()):
            if index >= 4096:raise CacheQuotaError('快取項目超過列舉上限。')
            if re.fullmatch('[0-9a-f]{64}\\.(archive|part)',path.name):
                info = _plain(path)
                if not stat.S_ISREG(info.st_mode):raise CacheQuotaError('快取含非一般檔案。')
                files.append((path,info.st_size,info.st_mtime_ns))
        return files

    def has_receipt(self, path, size):
        path = Path(path).absolute()
        if path.parent != self.directory or not re.fullmatch('[0-9a-f]{64}\\.archive',path.name):return False
        digest = path.stem
        receipt = self.directory/(digest+'.receipt.json')
        try:
            _plain(receipt)
            if not receipt.is_file() or receipt.stat().st_size > 8192:
                return False
            if json.loads(receipt.read_bytes()) != self.receipt(digest,size):return False
            return True
        except (OSError,ValueError,IntegrityError,RecursionError):
            return False

    def _owned(self, path, size, checkpoint=lambda:None):
        if not self.has_receipt(path,size):return False
        try:
            verify_file(path,size,path.stem,checkpoint)
            return True
        except (OSError,IntegrityError):return False

    def make_room(self, required=0, protected=(), checkpoint=lambda:None):
        """呼叫端必須已持有 cache exclusive 鎖；下載准入時與寫入同一鎖範圍。"""
        files = self._files()
        total = sum(size for _,size,_ in files)
        removed = []
        candidates = sorted(files,key=lambda item:item[2])
        for path,size,_ in candidates:
            checkpoint()
            if total+required <= self.quota_bytes:break
            legacy = self.directory/(path.stem+'.lock')
            if legacy.exists() or legacy.is_symlink():continue
            if path.suffix != '.archive' or path.stem in protected or not self._owned(path,size,checkpoint):continue
            path.unlink()
            (self.directory/(path.stem+'.receipt.json')).unlink()
            total -= size;removed.append(path.name)
        if total+required > self.quota_bytes:
            raise CacheQuotaError('快取配額不足，沒有足夠可安全回收的完整包檔；片段與未知資料保留。')
        return tuple(removed)

    def prune(self, *, protected=(), checkpoint=lambda:None):
        with self.lock(exclusive=True):
            return self.make_room(protected=protected,checkpoint=checkpoint)

    @contextmanager
    def archive_lease(self, path):
        """安裝讀取受管 archive 時持有 shared 鎖，下載與配額清理皆不得修改。"""
        path = Path(path).absolute()
        if path.parent != self.directory or not re.fullmatch('[0-9a-f]{64}\\.archive',path.name):
            raise ValueError('快取租約位置無效。')
        with self.lock(path.stem, exclusive=False):
            yield

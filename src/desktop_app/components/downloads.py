"""C05 受信任元件下載快取：有界重試／ETag 續傳／離線匯入，不解壓或執行。"""
from contextlib import contextmanager
from dataclasses import dataclass
import http.client
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile
from threading import Event
import urllib.error
import urllib.request

from ..core import Cancelled
from .contracts import ComponentState
from .registry import IntegrityError, _chain, _plain, verify_file
from .network import opener_for


class DownloadError(RuntimeError):
    """傳輸、續傳或快取未通過；不可把檔案交給安裝服務。"""


class DownloadBusy(DownloadError):
    """同包檔已有下載工作；不自動移除可能仍在使用的鎖。"""


class RestartDownload(DownloadError):
    """伺服器續傳條件失效，捨棄舊片段後使用剩餘重試額度重來。"""


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    source: str
    attempts: int
    resumed_from: int
    size: int


def _regular(path):
    if path.exists() or path.is_symlink():
        if not stat.S_ISREG(_plain(path).st_mode):
            raise DownloadError('下載快取路徑不是一般檔案。')


def _etag(value):
    if isinstance(value, str) and re.fullmatch(r'"[\x21\x23-\x7e]{0,254}"', value):
        return value
    return None


class DownloadService:
    def __init__(self, directory, verifier, registry=None, *, opener=None, attempts=3, reserve_bytes=64*1024**2):
        if type(attempts) is not int or not 1 <= attempts <= 5:
            raise ValueError('下載重試次數須為 1 至 5。')
        if type(reserve_bytes) is not int or reserve_bytes < 0:
            raise ValueError('下載磁碟保留量無效。')
        self.directory = Path(directory).absolute()
        _chain(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.verifier = verifier
        self.registry = registry
        self.opener = opener or opener_for(verifier.policy)
        self.attempts = attempts
        self.reserve_bytes = reserve_bytes

    def _paths(self, spec):
        return tuple(self.directory / (spec.package_sha256 + suffix)
                     for suffix in ('.archive', '.part', '.resume.json', '.lock'))

    @contextmanager
    def _lock(self, spec):
        _chain(self.directory)
        final, part, meta, lock = self._paths(spec)
        for path in (final, part, meta):
            _regular(path)
        try:
            descriptor = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        except FileExistsError as exc:
            raise DownloadBusy('此包檔已有下載鎖；請待原工作結束，崩潰後由維護流程處理。') from exc
        try:
            os.close(descriptor)
            yield final, part, meta
        finally:
            lock.unlink(missing_ok=True)

    @staticmethod
    def _checkpoint(cancel, checkpoint):
        if cancel.is_set():
            raise Cancelled('元件下載已取消；可續傳片段保留。')
        checkpoint()

    @staticmethod
    def _discard(part, meta):
        # 只清理由 SHA-256 衍生的受管片段，不掃描或刪除其他快取／外部資料。
        for path in (part, meta):
            _regular(path)
            path.unlink(missing_ok=True)

    def _metadata(self, spec, meta, etag):
        value = dict(schema_version=1, url=spec.source_url, sha256=spec.package_sha256,
                     size=spec.download_bytes, etag=etag)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile('w', encoding='utf-8', dir=self.directory, prefix='.resume-', delete=False) as output:
                temporary = Path(output.name)
                json.dump(value, output, sort_keys=True)
                output.flush();os.fsync(output.fileno())
            _regular(meta)
            os.replace(temporary, meta)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def _resume(self, spec, part, meta):
        if not part.exists():
            return 0, None
        size = part.stat().st_size
        if size == spec.download_bytes:
            return size, None
        try:
            if not 0 < size < spec.download_bytes or not meta.exists() or meta.stat().st_size > 8192:
                raise ValueError('invalid fragment')
            value = json.loads(meta.read_bytes())
            expected = dict(schema_version=1, url=spec.source_url, sha256=spec.package_sha256,
                            size=spec.download_bytes, etag=value.get('etag'))
            if value != expected or _etag(value['etag']) is None:
                raise ValueError('invalid validator')
            return size, value['etag']
        except (OSError, ValueError, AttributeError, TypeError):
            self._discard(part, meta)
            return 0, None

    def _space(self, required):
        if shutil.disk_usage(self.directory).free < required + self.reserve_bytes:
            raise DownloadError('磁碟可用空間不足，尚未啟動或繼續下載。')

    def _record(self, spec, path, checkpoint):
        if self.registry is not None:
            record = self.registry.register(spec)
            if not record.installed:
                self.registry.record_download(spec, path)
                if self.registry.verify_download(spec, checkpoint).state != ComponentState.VERIFIED:
                    raise DownloadError('下載檔無法登錄為已驗證。')

    def _finish(self, spec, final, part, meta, checkpoint, authorize, source, attempts, resumed):
        try:
            verify_file(part, spec.download_bytes, spec.package_sha256, checkpoint)
        except (OSError, IntegrityError):
            self._discard(part, meta)
            raise
        checkpoint()
        authorize()
        # 排他發布，不以 replace 覆寫已有包檔；完整性通過仍僅是 verified。
        os.link(part, final)
        self._discard(part, meta)
        self._record(spec, final, checkpoint)
        return DownloadResult(final, source, attempts, resumed, spec.download_bytes)

    def _cached(self, spec, final, checkpoint, authorize):
        if final.exists():
            verify_file(final, spec.download_bytes, spec.package_sha256, checkpoint)
            authorize()
            self._record(spec, final, checkpoint)
            return DownloadResult(final, 'cache', 0, 0, spec.download_bytes)
        return None

    def download(self, catalog, component_id, version, *, cancel=None, checkpoint=lambda: None,
                 progress=lambda received, total: None, wait=None):
        spec = self.verifier.load(catalog).component(component_id, version)
        cancel = cancel if cancel is not None else Event()
        check = lambda: self._checkpoint(cancel, checkpoint)
        authorize = lambda: self.verifier.load(catalog)
        wait = wait or cancel.wait
        check()
        with self._lock(spec) as (final, part, meta):
            cached = self._cached(spec, final, check, authorize)
            if cached is not None:
                return cached
            resumed = 0
            for attempt in range(1, self.attempts + 1):
                check()
                # 每次請求也重驗到期／撤銷；取消與資源 checkpoint 例外不重試。
                self.verifier.load(catalog)
                offset, validator = self._resume(spec, part, meta)
                if offset == spec.download_bytes:
                    return self._finish(spec, final, part, meta, check, authorize, 'partial-cache', attempt-1, offset)
                self._space(spec.download_bytes - offset)
                headers = {'Accept-Encoding': 'identity'}
                if offset:
                    headers.update({'Range': f'bytes={offset}-', 'If-Range': validator})
                request = urllib.request.Request(spec.source_url, headers=headers)
                try:
                    with self.opener(request, timeout=10) as response:
                        self.verifier.policy.check_url(response.geturl())
                        status = response.status
                        if response.headers.get('Content-Encoding', 'identity') != 'identity':
                            raise DownloadError('包檔回應不能使用未核准的傳輸編碼。')
                        if status == 206:
                            expected_range = f'bytes {offset}-{spec.download_bytes-1}/{spec.download_bytes}'
                            if (not offset or response.headers.get('Content-Range') != expected_range
                                    or _etag(response.headers.get('ETag')) != validator):
                                raise RestartDownload('續傳範圍或 ETag 已失效。')
                            resumed = max(resumed, offset)
                        elif status == 200:
                            offset = 0
                            resumed = 0
                            self._space(spec.download_bytes)
                        else:
                            raise DownloadError('包檔 HTTP 狀態不符合完整或續傳回應。')
                        length = response.headers.get('Content-Length')
                        if length is not None and (not re.fullmatch('[0-9]{1,13}', length)
                                                   or int(length) != spec.download_bytes-offset):
                            raise RestartDownload('回應長度與可信目錄不符。')
                        self._metadata(spec, meta, _etag(response.headers.get('ETag')))
                        with part.open('ab' if offset else 'wb') as output:
                            received = offset
                            while True:
                                check()
                                block = response.read(min(65536, spec.download_bytes-received+1))
                                if not block:
                                    break
                                received += len(block)
                                if received > spec.download_bytes:
                                    raise RestartDownload('包檔超過宣告上限。')
                                output.write(block)
                                progress(received, spec.download_bytes)
                            output.flush();os.fsync(output.fileno())
                        if received != spec.download_bytes:
                            raise http.client.IncompleteRead(b'', spec.download_bytes-received)
                    check()
                    return self._finish(spec, final, part, meta, check, authorize, 'network', attempt, resumed)
                except urllib.error.HTTPError as exc:
                    code = exc.code
                    exc.close()
                    if code == 416:
                        self._discard(part, meta)
                    elif code not in (408, 429, 500, 502, 503, 504):
                        raise DownloadError(f'下載 HTTP {code}，未繼續重試。') from exc
                except RestartDownload:
                    self._discard(part, meta)
                except (urllib.error.URLError, TimeoutError, ConnectionError, http.client.IncompleteRead):
                    pass
                if attempt < self.attempts:
                    if wait(min(2**(attempt-1), 4)):
                        raise Cancelled('元件下載等待已取消。')
            raise DownloadError('已達下載重試上限；可續傳片段保留，未產生可安裝包檔。')

    def import_offline(self, catalog, component_id, version, archive, *, cancel=None, checkpoint=lambda: None):
        spec = self.verifier.load(catalog).component(component_id, version)
        cancel = cancel if cancel is not None else Event()
        check = lambda: self._checkpoint(cancel, checkpoint)
        authorize = lambda: self.verifier.load(catalog)
        source = Path(archive).absolute()
        check()
        verify_file(source, spec.download_bytes, spec.package_sha256, check)
        with self._lock(spec) as (final, part, meta):
            cached = self._cached(spec, final, check, authorize)
            if cached is not None:
                return cached
            if source in (part, meta):
                raise DownloadError('離線來源不可是同一下載工作的片段。')
            self._space(spec.download_bytes)
            self._discard(part, meta)
            with source.open('rb') as input_file, part.open('xb') as output:
                total = 0
                while True:
                    check()
                    block = input_file.read(65536)
                    if not block:
                        break
                    total += len(block)
                    if total > spec.download_bytes:
                        raise DownloadError('離線來源於複製時變大。')
                    output.write(block)
                output.flush();os.fsync(output.fileno())
            return self._finish(spec, final, part, meta, check, authorize, 'offline', 0, 0)

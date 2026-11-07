"""C08 桌面用服務：固定信任來源、背景操作、可重驗狀態與既有交易 API 的橋接。"""
from dataclasses import dataclass
from importlib import metadata
import os
from pathlib import Path
import platform
import stat
import tempfile
from threading import Event

from ..capabilities import HostContext, incompatibility
from ..component_workers.binding import CPUWorkerBinding
from ..core import Cancelled
from ..settings import Settings
from .archives import sync_directory
from .catalog import CatalogError, CatalogVerifier, MAX_CATALOG_BYTES, TrustPolicy
from .contracts import ComponentState, ComponentSpec, Version
from .downloads import DownloadService
from .lifecycle import ComponentManager
from .locks import file_lock
from .network import fetch_catalog
from .registry import ComponentRegistry, _chain, _plain, verify_file


@dataclass(frozen=True)
class TrustedSource:
    """只由可信應用程式／發行設定提供；使用者匯入的目錄不能新增金鑰或 URL。"""
    policy: TrustPolicy
    catalog_url: str | None = None

    def __post_init__(self):
        if not isinstance(self.policy, TrustPolicy):
            raise ValueError('目錄來源缺少可信政策。')
        if self.catalog_url is not None:
            self.policy.check_url(self.catalog_url)


@dataclass(frozen=True)
class ComponentRow:
    spec: ComponentSpec
    state: str
    reason: str
    owned: bool
    approved: bool
    compatible: bool
    active: bool
    previous: bool


@dataclass(frozen=True)
class ManagementResult:
    rows: tuple[ComponentRow, ...]
    state: str
    message: str
    document: str | None = None


def local_host():
    architecture = platform.machine().lower()
    architecture = {'amd64':'x86_64', 'aarch64':'arm64'}.get(architecture, architecture)
    return HostContext(platform.system().lower(), architecture,
                       Version.parse(metadata.version('markitdown-desktop')), Version.parse('1.0.0'))


class ComponentManagement:
    """每次操作重驗目錄；只讀列表不執行健康探針，也不把過去 ready 當成現在可用。"""
    def __init__(self, directory, *, source=None, settings=None, host=None, health_checks=None, opener=None):
        self.directory = Path(directory).absolute()
        self.source = source
        if source is not None and not isinstance(source, TrustedSource):
            raise ValueError('不接受未驗證的元件來源設定。')
        self.settings = settings or Settings()
        self.host = host or local_host()
        self.verifier = CatalogVerifier(source.policy) if source else None
        # 測試／可信程式可注入固定探針；目錄檔不能決定要執行的 Python／shell。
        self.health_checks = dict(health_checks or {})
        self.opener = opener
        self.catalog_path = self.directory/'component-catalog.json'
        self.registry_path = self.directory/'component-state'

    def _read_catalog_file(self, path):
        path = Path(path).absolute(); _chain(path); info = _plain(path)
        # 拒絕 FIFO／裝置，避免選入特殊檔後阻塞讀取與取消。
        if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_CATALOG_BYTES:
            raise CatalogError('目錄須為大小受限的一般檔案。')
        with path.open('rb') as source:
            raw = source.read(MAX_CATALOG_BYTES+1)
        if not 0 < len(raw) <= MAX_CATALOG_BYTES:
            raise CatalogError('目錄檔超過大小限制或為空。')
        return raw

    def _catalog(self):
        if self.verifier is None:
            raise CatalogError('正式選配元件目錄尚未提供；基本轉換與原模型管理仍可使用。')
        if not self.catalog_path.exists():
            raise CatalogError('請先匯入受信任簽章目錄，或明確更新目錄。')
        return self.verifier.load(self._read_catalog_file(self.catalog_path))

    def _save_catalog(self, catalog, check):
        check(); self.verifier.load(catalog)
        _chain(self.catalog_path)
        if self.catalog_path.exists(): _plain(self.catalog_path)
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=self.directory, prefix='.catalog-', delete=False) as output:
                temporary = Path(output.name); output.write(catalog.envelope); output.flush(); os.fsync(output.fileno())
            check(); self.verifier.load(catalog)
            os.replace(temporary, self.catalog_path); sync_directory(self.directory)
        finally:
            if temporary is not None: temporary.unlink(missing_ok=True)

    def _services(self, cancel, check):
        registry = ComponentRegistry(self.registry_path)
        binding = CPUWorkerBinding(registry.directory/'.locks/worker-use.lock', self.settings.policy(),
                                   cpu_threads=self.settings.cpu_threads, cancel=cancel)
        health = {'onnx.cpu.health':binding.health, **self.health_checks}
        manager = ComponentManager(registry, self.verifier, self.host, health, checkpoint=check)
        return registry, manager

    def _snapshot(self, registry, manager):
        # 不能在另一個 C06 交易搬移／提交的中間狀態產生可操作列表。
        with file_lock(manager.lock_path, exclusive=False):
            return self._snapshot_locked(registry, manager)

    def _snapshot_locked(self, registry, manager):
        approved = {}; note = ''
        try:
            approved = {spec.key:spec for spec in self._catalog().components}
        except (OSError, ValueError) as exc:
            note = str(exc)
        active = manager.store.active(); specs = dict(approved)
        # 目錄撤回／到期仍列出受管舊版本，允許安全移除，不授予執行或修復權。
        for key in manager.store.owned_keys():
            record = registry.get(*key)
            if record is not None: specs.setdefault(key, record.spec)
        rows = []
        for key, spec in sorted(specs.items(), key=lambda item:(item[0][0], item[1].version), reverse=True):
            record = registry.get(*key); owned = manager.store.owned(spec) is not None
            allowed = key in approved and approved[key] == spec
            reason = incompatibility(spec, self.host)
            state = record.state.value if record else 'missing'
            detail = record.reason if record else '尚未安裝。'
            if not allowed: state, detail = 'unapproved', note or '目前簽章目錄未核准此版本。'
            elif reason: state, detail = 'incompatible', reason
            elif record is not None and record.spec != spec: state, detail = 'corrupt', '登錄描述與目錄不符。'
            elif state == 'ready': state, detail = 'unchecked', '上次健康通過；使用前仍須重新驗證。'
            current, previous = active.get(spec.component_id, (None, None))
            rows.append(ComponentRow(spec, state, detail, owned, allowed, reason is None,
                                     str(spec.version)==current, str(spec.version)==previous))
        return tuple(rows), note

    def _license(self, registry, manager, spec, check):
        with file_lock(manager.lock_path, exclusive=False):
            if manager.store.journals(): raise RuntimeError('有未完成維護，請先恢復。')
            manager._owned_spec(*spec.key)
            declared = next(item for item in spec.files if item.path==spec.license_path)
            path = registry.installation_path(spec)/spec.license_path
            verify_file(path, declared.size, declared.sha256, check)
            with path.open('rb') as source: raw = source.read(256*1024+1)
            truncated = len(raw)>256*1024
            return raw[:256*1024].decode('utf-8', errors='replace') + ('\n\n〔畫面僅顯示前 256 KiB，完整原文隨元件保存〕' if truncated else '')

    def run(self, operation, key=None, path=None, *, cancel=None, status=lambda message:None,
            progress=lambda received,total:None):
        """只在背景呼叫。相同資料根的視窗以核心鎖互斥；失敗後仍重讀真實登錄。"""
        cancel = cancel if cancel is not None else Event()
        def check():
            if cancel.is_set(): raise Cancelled('元件操作已取消；基本功能不受影響。')
        try:
            with file_lock(self.registry_path/'.locks/management.lock', exclusive=True):
                registry, manager = self._services(cancel, check)
                state, message, document = 'completed', '已更新本機狀態；未執行健康檢查。', None
                try:
                    check()
                    if operation == 'refresh': pass
                    elif operation in ('catalog_file','catalog_online'):
                        if self.verifier is None: self._catalog()
                        # 同一服務先讀已保存目錄，保留 C05 的版次／同版摘要檢查。
                        if self.catalog_path.exists():
                            try: self._catalog()
                            except CatalogError: pass  # 到期不能阻擋明確取得新的有效目錄。
                        status('正在驗證簽章目錄…')
                        if operation=='catalog_file': catalog=self.verifier.load(self._read_catalog_file(path))
                        else:
                            if not self.source.catalog_url: raise CatalogError('此發行設定未提供線上目錄。')
                            catalog=fetch_catalog(self.source.catalog_url,self.verifier,opener=self.opener,checkpoint=check)
                        self._save_catalog(catalog,check); message='簽章目錄已驗證；尚未下載或安裝元件。'
                    elif operation == 'recover':
                        status('正在恢復未完成的維護…'); manager.recover(); message='維護恢復檢查完成。'
                    else:
                        if not isinstance(key, tuple) or len(key)!=2: raise ValueError('請先選擇元件版本。')
                        if operation in ('remove','license'):
                            spec=manager._owned_spec(*key)
                        else: spec=self._catalog().component(*key)
                        if operation in ('install','repair','offline'):
                            if incompatibility(spec,self.host): raise ValueError(incompatibility(spec,self.host))
                            if spec.health_check not in manager.health_checks: raise ValueError('此版本尚無可信健康探針，未下載。')
                            download=DownloadService(self.directory/'component-cache',self.verifier,registry,opener=self.opener)
                            status('正在取得並驗證元件包檔…')
                            if operation=='offline': cached=download.import_offline(self._catalog(),*key,path,cancel=cancel,checkpoint=check)
                            else: cached=download.download(self._catalog(),*key,cancel=cancel,checkpoint=check,progress=progress)
                            check(); status('正在交易安裝與健康檢查；大型元件可能需要較久…')
                            manager.install(self._catalog(),*key,cached.path,repair=operation=='repair',cancel=cancel)
                            message='元件已驗證並啟用；文件自動路由尚待接入。'
                        elif operation=='health':
                            status('正在重驗檔案與健康…'); manager.check_health(self._catalog(),*key,cancel=cancel)
                            message='健康檢查通過；使用時仍會重新驗證。'
                        elif operation=='activate':
                            manager.activate(self._catalog(),*key,cancel=cancel); message='所選版本已驗證並啟用。'
                        elif operation=='rollback':
                            manager.rollback(self._catalog(),spec.component_id,cancel=cancel); message='已驗證並回復前一版本。'
                        elif operation=='remove':
                            manager.remove(*key,cancel=cancel); message='所選受管版本已移除，其他資料保留。'
                        elif operation=='license':
                            document=self._license(registry,manager,spec,check); message='已驗證授權檔，以下顯示原文。'
                        else: raise ValueError('不支援的元件管理操作。')
                except Cancelled as exc: state, message='cancelled',str(exc)
                except Exception as exc: state, message='failed',f'{type(exc).__name__}: {exc}'
                try: rows, note=self._snapshot(registry,manager)
                except Exception as exc: rows, note=(),f'狀態讀取失敗：{type(exc).__name__}: {exc}'
                if operation=='refresh' and note: message=note
                if note and not rows and state=='completed' and operation!='refresh': message+=' '+note
                return ManagementResult(rows,state,message,document)
        except Exception as exc:
            return ManagementResult((),'failed',f'{type(exc).__name__}: {exc}')

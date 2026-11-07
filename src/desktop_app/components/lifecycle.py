"""交易式元件維護：日誌協調檔案系統／登錄，active 在驗證成功後才原子切換。"""
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from pathlib import Path
import shutil
from threading import Event
import uuid

from ..capabilities import CapabilityResolver, HealthResult, incompatibility
from ..core import Cancelled
from .archives import delete_owned_tree, durable_mkdir, durable_rename, expected_directories, extract_archive, inventory, sync_directory, verify_tree
from .cache import CacheStore
from .contracts import ComponentSpec, ComponentState
from .lifecycle_store import LifecycleError, LifecycleStore
from .locks import file_lock
from .registry import IntegrityError, _chain, _plain, verify_file


@dataclass(frozen=True)
class MaintenanceResult:
    component_id: str
    version: str
    state: str
    previous_version: str | None = None


@dataclass(frozen=True)
class ComponentLease:
    """呼叫端須在整個使用期間保持 context；worker 接入時也須自行持有租約。"""
    spec: ComponentSpec
    directory: Path


class ComponentManager:
    def __init__(self, registry, verifier, host, health_checks, *, reserve_bytes=64*1024**2,
                 checkpoint=lambda:None, fault=lambda stage:None):
        if type(reserve_bytes) is not int or reserve_bytes < 0:
            raise ValueError('安裝磁碟保留量無效。')
        self.registry = registry
        self.verifier = verifier
        self.host = host
        self.health_checks = dict(health_checks)
        self.reserve_bytes = reserve_bytes
        self.checkpoint = checkpoint
        self.fault = fault
        self.store = LifecycleStore(registry.directory)
        self.staging = registry.directory/'lifecycle-staging'
        self.lock_path = registry.directory/'.locks/lifecycle.lock'
        self.worker_guard_path = registry.directory/'.locks/worker-use.lock'

    def _workers_idle(self):
        # worker 自己持有 shared guard；控制端死亡後也不能刪改仍在讀取的元件。
        return file_lock(self.worker_guard_path,exclusive=True)

    def _check(self, cancel):
        if cancel.is_set():raise Cancelled('元件維護已取消，原版本保留。')
        self.checkpoint()

    def _owned_spec(self, component_id, version):
        record = self.registry.get(component_id,version)
        if record is None or self.store.owned(record.spec) is None:
            raise LifecycleError('找不到受管元件，不接管外部或原有目錄。')
        return record.spec

    def _active_catalog(self, catalog, candidate=None):
        active = self.store.active()
        result = []
        for spec in catalog.components:
            if candidate is not None and spec.component_id == candidate.component_id:continue
            if active.get(spec.component_id,(None,))[0] == str(spec.version):
                if self.store.owned(spec) is None:raise LifecycleError('active 元件缺少所有權紀錄。')
                result.append(spec)
        if candidate is not None:result.append(candidate)
        return tuple(result)

    def _dependents_allow(self, candidate):
        """切換共用 runtime 前反向檢查現有 active 使用者，避免更新破壞另一元件。"""
        for component_id,(version,_) in self.store.active().items():
            if component_id==candidate.component_id:continue
            dependent = self._owned_spec(component_id,version)
            if any(item.component_id==candidate.component_id and not item.versions.contains(candidate.version)
                   for item in dependent.dependencies):
                raise LifecycleError(f'已啟用元件 {dependent.component_id} 不相容此版本，未切換。')

    def _stage_health(self, spec, path, catalog, check):
        reason = incompatibility(spec,self.host)
        if reason:raise LifecycleError(reason)
        approved = self._active_catalog(catalog)
        resolver = CapabilityResolver(self.registry,approved,self.host,self.health_checks,check)
        for dependency in spec.dependencies:
            candidates = [item for item in approved if item.component_id==dependency.component_id
                          and dependency.versions.contains(item.version)]
            if not candidates or not resolver.assess(candidates[0]).ready:
                raise LifecycleError(f'依賴 {dependency.component_id} 尚未就緒。')
        probe = self.health_checks.get(spec.health_check)
        if probe is None:raise LifecycleError('沒有已註冊的可信健康檢查。')
        check()
        result = probe(spec,path,self.host)
        check()
        if not isinstance(result,HealthResult) or not result.passed:
            raise LifecycleError('元件健康檢查未通過。')
        verify_tree(path,spec,check)

    def _ready(self, spec, catalog, check):
        verify_tree(self.registry.installation_path(spec),spec,check)
        approved = self._active_catalog(catalog,spec)
        result = CapabilityResolver(self.registry,approved,self.host,self.health_checks,check).assess(spec)
        if not result.ready:raise LifecycleError(result.reason)
        verify_tree(self.registry.installation_path(spec),spec,check)

    def _begin(self, spec, operation, had_payload):
        record = self.registry.get(*spec.key)
        old = None if record is None else dict(state=record.state.value,installed=record.installed,reason=record.reason)
        value = dict(schema_version=1, token=uuid.uuid4().hex, operation=operation,
                     spec=spec.to_dict(), previous_record=old, had_payload=had_payload, phase='preparing')
        base = self._base(value)
        if base.exists() or base.is_symlink():raise LifecycleError('事務目錄已存在，未接管未知資料。')
        self.store.begin(value)
        return value

    def _base(self, value):
        path = self.staging/value['token']
        _chain(path)
        return path

    def _restore_record(self, spec, old):
        current = self.registry.get(*spec.key)
        if current is None:
            if old is not None:raise LifecycleError('原登錄資料遺失，未自行重建。')
            return
        if current.spec != spec:raise LifecycleError('原登錄描述不符，未覆寫。')
        self.registry._update(current,ComponentState.MISSING if old is None else ComponentState(old['state']),
                              '' if old is None else old['reason'],installed=False if old is None else old['installed'])

    def _clean_base(self, value, spec):
        base = self._base(value)
        if not base.exists():return
        _plain(base)
        delete_owned_tree(base/'payload',spec,modified=True)
        delete_owned_tree(base/'previous',spec,modified=value['operation']=='repair')
        base.rmdir()  # 額外檔案會阻擋清理，沒有遞迴刪除未知內容。
        sync_directory(base.parent)

    def _recover_one(self, value):
        with self._workers_idle():
            return self._recover_one_locked(value)

    def _recover_one_locked(self, value):
        spec = self.store.validate_journal(value)
        base = self._base(value)
        target = self.registry.installation_path(spec)
        previous = base/'previous'
        payload = base/'payload'
        _chain(target)
        if value['phase']=='committed':
            if value['operation']!='remove':
                owner = self.store.owned(spec)
                if owner is None or owner['token']!=value['token']:
                    raise LifecycleError('已提交事務的所有權不符，停止清理。')
                verify_tree(target,spec)
            elif self.store.owned(spec) is not None:
                raise LifecycleError('移除事務與所有權紀錄衝突，未清理。')
        else:
            owner = self.store.owned(spec)
            if (value['operation']=='install' and owner is not None) or (value['operation']!='install' and owner is None):
                raise LifecycleError('未提交事務的所有權不符，未刪檔。')
            if previous.exists() or previous.is_symlink():
                inventory(previous,spec)
                if target.exists() or target.is_symlink():
                    verify_tree(target,spec)
                    delete_owned_tree(target,spec)
                durable_mkdir(target.parent)
                durable_rename(previous,target)
            elif value['had_payload']:
                inventory(target,spec)  # 尚未搬走的舊版本，可能正是待修復的已知檔案。
            elif target.exists() or target.is_symlink():
                if payload.exists():raise LifecycleError('出現來源不明的目標目錄，未刪除。')
                verify_tree(target,spec)
                delete_owned_tree(target,spec)
            self._restore_record(spec,value['previous_record'])
        self._clean_base(value,spec)
        self.store.finish(value['token'])

    def _recover_all(self):
        recovered = []
        for value in self.store.journals():
            self._recover_one(value)
            recovered.append(value['token'])
        return tuple(recovered)

    def recover(self):
        with file_lock(self.lock_path,exclusive=True):
            return self._recover_all()

    def _on_failure(self, value):
        matches = [item for item in self.store.journals() if item['token']==value['token']]
        if matches:self._recover_one(matches[0])

    @staticmethod
    def _archive_lease(archive, spec):
        archive = Path(archive).absolute()
        receipt = archive.parent/(spec.package_sha256+'.receipt.json')
        if archive.name == spec.package_sha256+'.archive' and receipt.exists():
            cache = CacheStore(archive.parent)
            if cache.has_receipt(archive,spec.download_bytes):return cache.archive_lease(archive)
        return nullcontext()

    def install(self, catalog, component_id, version, archive, *, repair=False, cancel=None):
        cancel = cancel if cancel is not None else Event()
        check = lambda:self._check(cancel)
        check()
        with file_lock(self.lock_path,exclusive=True):
            self._recover_all()
            with self._workers_idle():pass
            catalog = self.verifier.load(catalog)
            spec = catalog.component(component_id,version)
            reason = incompatibility(spec,self.host)
            if reason:raise LifecycleError(reason)
            expected_directories(spec)
            self._dependents_allow(spec)
            target = self.registry.installation_path(spec)
            _chain(target)
            owner = self.store.owned(spec)
            existed = target.exists()
            if existed and owner is None:raise LifecycleError('目標已有未知資料，未接管。')
            if repair and owner is None:raise LifecycleError('不修復未受管的外部資料。')
            if owner is not None and not repair:
                self._ready(spec,catalog,check)
                self.verifier.load(catalog)
                with self._workers_idle():self.store.activate(spec)
                return MaintenanceResult(*spec.key,'ready',self.store.active()[spec.component_id][1])
            if existed:inventory(target,spec)
            archive = Path(archive).absolute()
            with self._archive_lease(archive,spec):
                verify_file(archive,spec.download_bytes,spec.package_sha256,check)
                needed = max(sum(item.size for item in spec.files),spec.resources.disk_mib*1024**2)
                if shutil.disk_usage(self.registry.directory).free < needed+self.reserve_bytes:
                    raise LifecycleError('安裝暫存與保留空間不足，未更動原版本。')
                value = self._begin(spec,'repair' if repair else 'install',existed)
                try:
                    self.fault('journaled')
                    base = self._base(value)
                    durable_mkdir(base,exist_ok=False)
                    extract_archive(archive,base/'payload',spec,check)
                    self._stage_health(spec,base/'payload',catalog,check)
                    self.fault('staged')
                    check();self.verifier.load(catalog)
                    with self._workers_idle():
                        durable_mkdir(target.parent)
                        if existed:
                            durable_rename(target,base/'previous')
                            self.fault('old_moved')
                        if target.exists() or target.is_symlink():raise LifecycleError('目標目錄已變更，未覆寫。')
                        durable_rename(base/'payload',target)
                    self.fault('published')
                    record = self.registry.register(spec)
                    if not record.installed:
                        self.registry.record_download(spec,archive)
                        if self.registry.verify_download(spec,check).state!=ComponentState.VERIFIED:
                            raise LifecycleError('包檔完整性失效。')
                        self.registry.record_installation(spec,check)
                    else:
                        verify_tree(target,spec,check)
                        self.registry._update(record,ComponentState.INSTALLED,installed=True,archive_path=str(archive))
                    self._ready(spec,catalog,check)
                    self.fault('registered')
                    check();self.verifier.load(catalog)
                    with self._workers_idle():self.store.commit(value)
                    self.fault('committed')
                    self._recover_one({**value,'phase':'committed'})
                    self.fault('cleaned')
                except Exception:
                    self._on_failure(value)
                    raise
            return MaintenanceResult(*spec.key,'ready',self.store.active()[spec.component_id][1])

    def repair(self, catalog, component_id, version, archive, *, cancel=None):
        return self.install(catalog,component_id,version,archive,repair=True,cancel=cancel)

    def activate(self, catalog, component_id, version, *, cancel=None):
        cancel = cancel if cancel is not None else Event()
        check = lambda:self._check(cancel)
        check()
        with file_lock(self.lock_path,exclusive=True):
            self._recover_all()
            return self._activate_locked(catalog,component_id,version,check)

    def check_health(self, catalog, component_id, version, *, cancel=None):
        """重驗指定受管版本，不切換 active；C08 背景健康操作使用共享維護租約。"""
        cancel = cancel if cancel is not None else Event()
        check = lambda:self._check(cancel)
        with file_lock(self.lock_path,exclusive=False):
            check()
            if self.store.journals(): raise LifecycleError('有未完成事務，請先執行恢復。')
            catalog = self.verifier.load(catalog)
            spec = catalog.component(component_id,version)
            self._owned_spec(*spec.key)
            self._ready(spec,catalog,check)
            check();self.verifier.load(catalog)
            return MaintenanceResult(*spec.key,'ready')

    def _activate_locked(self, catalog, component_id, version,check):
        with self._workers_idle():pass
        catalog = self.verifier.load(catalog)
        spec = catalog.component(component_id,version)
        self._owned_spec(*spec.key)
        self._dependents_allow(spec)
        self._ready(spec,catalog,check)
        check()
        self.verifier.load(catalog)
        with self._workers_idle():self.store.activate(spec)
        return MaintenanceResult(*spec.key,'ready',self.store.active()[spec.component_id][1])

    def rollback(self, catalog, component_id, *, cancel=None):
        cancel = cancel if cancel is not None else Event()
        check = lambda:self._check(cancel)
        check()
        with file_lock(self.lock_path,exclusive=True):
            self._recover_all()
            previous = self.store.active().get(component_id,(None,None))[1]
            if previous is None:raise LifecycleError('沒有可回復的前一版本。')
            return self._activate_locked(catalog,component_id,previous,check)

    @contextmanager
    def lease(self, catalog, component_id):
        with file_lock(self.lock_path,exclusive=False):
            if self.store.journals():raise LifecycleError('有未完成事務，請先執行恢復。')
            catalog = self.verifier.load(catalog)
            active = self.store.active().get(component_id)
            if active is None:raise LifecycleError('沒有已啟用的元件版本。')
            spec = catalog.component(component_id,active[0])
            self._owned_spec(*spec.key)
            self._ready(spec,catalog,self.checkpoint)
            self.verifier.load(catalog)
            yield ComponentLease(spec,self.registry.installation_path(spec))

    def remove(self, component_id, version, *, cancel=None):
        cancel = cancel if cancel is not None else Event()
        check = lambda:self._check(cancel)
        check()
        with file_lock(self.lock_path,exclusive=True):
            self._recover_all()
            with self._workers_idle():pass
            spec = self._owned_spec(component_id,version)
            if spec.required:raise LifecycleError('必要基本元件不提供單獨移除。')
            for key in self.store.owned_keys():
                if key==spec.key:continue
                other = self._owned_spec(*key)
                if any(dep.component_id==spec.component_id and dep.versions.contains(spec.version) for dep in other.dependencies):
                    raise LifecycleError(f'仍有元件 {other.component_id} 依賴此版本，未移除。')
            target = self.registry.installation_path(spec)
            existed = target.exists()
            if existed:
                present = inventory(target,spec)
                for item in spec.files:
                    if item.path in present:verify_file(target/item.path,item.size,item.sha256,check)
            value = self._begin(spec,'remove',existed)
            try:
                self.fault('journaled')
                check()
                base = self._base(value);durable_mkdir(base,exist_ok=False)
                if existed:
                    with self._workers_idle():durable_rename(target,base/'previous')
                    self.fault('old_moved')
                record = self.registry.get(*spec.key)
                self.registry._update(record,ComponentState.MISSING,'已移除受管元件。',installed=False)
                self.fault('registered')
                check()
                with self._workers_idle():self.store.commit(value)
                self.fault('committed')
                self._recover_one({**value,'phase':'committed'})
            except Exception:
                self._on_failure(value)
                raise
            return MaintenanceResult(*spec.key,'missing')

"""元件能力解析：以應用程式核准描述、實檔與當次健康檢查決定可用性。"""
from dataclasses import dataclass

from .core import Cancelled
from .components.contracts import ComponentSpec, ComponentState, Version, VersionRange, _name, _require
from .components.registry import ConcurrentChange, IntegrityError, RegistryError


@dataclass(frozen=True)
class HostContext:
    """平台資料由呼叫端提供，方便跨平台驗證；此資料不代表 GPU 推論成功。"""
    platform: str
    architecture: str
    app_version: Version
    worker_protocol: Version

    def __post_init__(self):
        _require(self.platform in ('windows', 'linux') and self.architecture in ('x86_64', 'arm64'), '主程式平台無效。')
        _require(isinstance(self.app_version, Version) and isinstance(self.worker_protocol, Version), '主程式版本無效。')


@dataclass(frozen=True)
class HealthResult:
    passed: bool
    detail: str = ''

    def __post_init__(self):
        _require(type(self.passed) is bool and isinstance(self.detail, str) and len(self.detail) <= 2048,
                 '健康檢查結果格式無效。')


@dataclass(frozen=True)
class Assessment:
    component_id: str
    version: Version
    state: ComponentState
    reason: str

    @property
    def ready(self):
        return self.state == ComponentState.READY


@dataclass(frozen=True)
class Resolution:
    capability: str
    selected: ComponentSpec | None
    assessments: tuple[Assessment, ...]

    @property
    def available(self):
        return self.selected is not None


def incompatibility(spec, host):
    if host.platform not in spec.platforms:
        return '元件不支援目前作業系統。'
    if host.architecture not in spec.architectures:
        return '元件不支援目前處理器架構。'
    if not spec.app_versions.contains(host.app_version):
        return '元件與目前主程式版本不相容。'
    if not spec.worker_protocols.contains(host.worker_protocol):
        return '元件與目前 worker 協定不相容。'
    return None


class CapabilityResolver:
    """catalog 與 health_checks 由可信應用程式提供，不能直接信任下載的 JSON。"""

    def __init__(self, registry, catalog, host, health_checks, checkpoint=lambda: None):
        if not isinstance(catalog, (list, tuple)) or not all(isinstance(spec, ComponentSpec) for spec in catalog) or len(catalog) > 256 or len({spec.key for spec in catalog}) != len(catalog):
            raise RegistryError('核准元件描述過多或有重複版本。')
        self.registry = registry
        self.catalog = {spec.key: spec for spec in catalog}
        self.host = host
        self.health_checks = dict(health_checks)
        self.checkpoint = checkpoint

    def assess(self, spec):
        # 每次查詢重新建立快取，不沿用先前 ready 或舊版健康結果。
        return self._assess(spec, (), {})

    def _assess(self, spec, stack, cache):
        self.checkpoint()
        def result(state, reason):
            return Assessment(spec.component_id, spec.version, state, reason)
        if self.catalog.get(spec.key) != spec:
            return result(ComponentState.INCOMPATIBLE, '描述未經目前應用程式核准。')
        if spec.key in stack or len(stack) >= 32:
            return result(ComponentState.INCOMPATIBLE, '元件依賴循環或深度超過上限。')
        if spec.key in cache:
            return cache[spec.key]
        try:
            record = self.registry.get(*spec.key)
        except RegistryError as exc:
            return result(ComponentState.CORRUPT, str(exc))
        if record is None:
            return result(ComponentState.MISSING, '尚未登錄元件。')
        if record.spec != spec:
            return result(ComponentState.CORRUPT, '登錄描述與核准目錄不符。')
        if not record.installed:
            return result(record.state if record.state != ComponentState.READY else ComponentState.MISSING,
                          '下載或包檔驗證不能取代安裝與健康檢查。')
        state = ComponentState.INSTALLED
        reason = incompatibility(spec, self.host)
        if reason:
            state = ComponentState.INCOMPATIBLE
        else:
            try:
                self.registry.verify_installation(spec, self.checkpoint)
            except (OSError, IntegrityError) as exc:
                state, reason = ComponentState.CORRUPT, str(exc)
        if reason is None:
            for dependency in spec.dependencies:
                candidates = sorted((item for item in self.catalog.values()
                                     if item.component_id == dependency.component_id and dependency.versions.contains(item.version)),
                                    key=lambda item: item.version, reverse=True)
                observations = []
                for item in candidates:
                    observation = self._assess(item, (*stack, spec.key), cache)
                    observations.append(observation)
                    if observation.ready:
                        break
                if not any(item.ready for item in observations):
                    state = ComponentState.INSTALLED
                    detail = observations[0].reason if observations else '沒有相符版本。'
                    reason = f'依賴 {dependency.component_id} 尚未可用：{detail}'
                    break
        if reason is None:
            probe = self.health_checks.get(spec.health_check)
            if probe is None:
                state, reason = ComponentState.UNHEALTHY, '尚未註冊可信的健康檢查。'
            else:
                try:
                    self.checkpoint()
                    health = probe(spec, self.registry.installation_path(spec), self.host)
                    if not isinstance(health, HealthResult) or not health.passed:
                        state, reason = ComponentState.UNHEALTHY, health.detail if isinstance(health, HealthResult) else '健康檢查回傳格式無效。'
                    else:
                        # 健康檢查若改動了 payload，不能寫入 ready。
                        self.registry.verify_installation(spec, self.checkpoint)
                        state, reason = ComponentState.READY, health.detail
                except Cancelled:
                    raise
                except (OSError, IntegrityError) as exc:
                    state, reason = ComponentState.CORRUPT, str(exc)
                except Exception as exc:
                    state, reason = ComponentState.UNHEALTHY, f'健康檢查失敗：{type(exc).__name__}'
        try:
            self.registry._update(record, state, reason)
        except ConcurrentChange:
            return result(ComponentState.INSTALLED, '檢查期間登錄已變更，未採用過期健康結果。')
        except RegistryError as exc:
            return result(ComponentState.CORRUPT, str(exc))
        assessment = result(state, reason)
        cache[spec.key] = assessment
        return assessment

    def resolve(self, capability, *, component_id=None, versions=None):
        """優先必要元件、同 ID 最新相容版本；明確指定 ID 時不改用別的引擎。"""
        _name(capability)
        _require(versions is None or isinstance(versions, VersionRange), '能力請求版本範圍無效。')
        if component_id is not None:
            _name(component_id)
        candidates = [spec for spec in self.catalog.values() if capability in spec.capabilities and
                      (component_id is None or spec.component_id == component_id) and
                      (versions is None or versions.contains(spec.version))]
        candidates.sort(key=lambda spec: spec.version, reverse=True)
        candidates.sort(key=lambda spec: (not spec.required, spec.component_id))
        observations = []
        for spec in candidates:
            observation = self.assess(spec)
            observations.append(observation)
            if observation.ready:
                return Resolution(capability, spec, tuple(observations))
        return Resolution(capability, None, tuple(observations))

"""元件描述契約：只解析資料，不執行清單中的指令，也不代表簽章已驗證。"""
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
import base64
from pathlib import PurePosixPath
import re
from urllib.parse import urlsplit


class ContractError(ValueError):
    """描述格式、版本或路徑不符合目前支援的契約。"""


def _require(condition, message):
    if not condition:
        raise ContractError(message)


def _integer(value, minimum=0):
    _require(type(value) is int and minimum <= value <= 2**40, '容量或版本欄位須為範圍內整數。')


def _name(value):
    _require(isinstance(value, str) and len(value) <= 96 and
             re.fullmatch(r'[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*', value), '元件／能力識別名稱無效。')


def _text(value):
    _require(isinstance(value, str) and 0 < len(value) <= 2048 and
             not any(ord(char) < 32 for char in value), '文字欄位須非空且不可含控制字元。')
    try:
        value.encode('utf-8')
    except UnicodeEncodeError as exc:
        raise ContractError('文字欄位不是有效 UTF-8 字元。') from exc


def relative_path(value):
    """接受跨平台相對檔案名稱，排除 Windows 裝置名稱、ADS 與路徑別名。"""
    _text(value)
    _require(len(value) <= 240 and '\\' not in value and ':' not in value and
             not PurePosixPath(value).is_absolute(), '元件檔案須使用安全的相對路徑。')
    for part in value.split('/'):
        _require(part not in ('', '.', '..') and not part.endswith(('.', ' ')) and
                 not any(char in part for char in '<>"|?*') and
                 not re.fullmatch(r'(con|prn|aux|nul|com[1-9¹²³]|lpt[1-9¹²³])', part.split('.')[0], re.I),
                 '元件檔案路徑有逃逸或跨平台名稱衝突。')
    return value


@dataclass(frozen=True, order=True)
class Version:
    """C01 支援三段穩定版號；以數字比較，1.10.0 大於 1.9.0。"""
    major: int
    minor: int
    patch: int

    def __post_init__(self):
        for value in (self.major, self.minor, self.patch):
            _integer(value)

    @classmethod
    def parse(cls, value):
        _require(isinstance(value, str) and len(value) <= 48 and re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value),
                 '版本須為三段穩定版號，例如 0.2.0。')
        return cls(*(int(part) for part in value.split('.')))

    def __str__(self):
        return f'{self.major}.{self.minor}.{self.patch}'


@dataclass(frozen=True)
class VersionRange:
    minimum: Version
    maximum_exclusive: Version

    def __post_init__(self):
        _require(isinstance(self.minimum, Version) and isinstance(self.maximum_exclusive, Version) and
                 self.minimum < self.maximum_exclusive, '版本範圍須為有效的左閉右開區間。')

    def contains(self, version):
        return self.minimum <= version < self.maximum_exclusive


@dataclass(frozen=True)
class FileSpec:
    path: str
    sha256: str
    size: int

    def __post_init__(self):
        relative_path(self.path)
        _require(isinstance(self.sha256, str) and re.fullmatch('[0-9a-f]{64}', self.sha256), 'SHA-256 格式無效。')
        _integer(self.size)


@dataclass(frozen=True)
class Dependency:
    component_id: str
    versions: VersionRange

    def __post_init__(self):
        _name(self.component_id)
        relative_path(self.component_id)
        _require(isinstance(self.versions, VersionRange), '依賴版本範圍無效。')


@dataclass(frozen=True)
class ResourceRequirements:
    ram_mib: int
    vram_mib: int
    disk_mib: int

    def __post_init__(self):
        for value in (self.ram_mib, self.vram_mib, self.disk_mib):
            _integer(value)


@dataclass(frozen=True)
class Signature:
    """只保存簽章資料；可信目錄與金鑰驗證屬 C05，不由此結構宣稱通過。"""
    key_id: str
    algorithm: str
    value: str

    def __post_init__(self):
        _name(self.key_id)
        _require(self.algorithm == 'ed25519' and isinstance(self.value, str), '不支援的簽章描述。')
        try:
            decoded = base64.b64decode(self.value, validate=True)
        except (ValueError, TypeError) as exc:
            raise ContractError('簽章編碼無效。') from exc
        _require(len(decoded) == 64, 'Ed25519 簽章長度無效。')


class ComponentKind(str, Enum):
    ENGINE = 'engine'
    MODEL = 'model'
    RUNTIME = 'runtime'


class ComponentState(str, Enum):
    MISSING = 'missing'
    DOWNLOADED = 'downloaded'
    VERIFIED = 'verified'
    INSTALLED = 'installed'
    READY = 'ready'
    UNHEALTHY = 'unhealthy'
    INCOMPATIBLE = 'incompatible'
    CORRUPT = 'corrupt'


@dataclass(frozen=True)
class ComponentSpec:
    schema_version: int
    component_id: str
    version: Version
    kind: ComponentKind
    display_name: str
    source_url: str
    license_id: str
    license_path: str
    package_sha256: str
    download_bytes: int
    unpacked_bytes: int
    files: tuple[FileSpec, ...]
    capabilities: tuple[str, ...]
    platforms: tuple[str, ...]
    architectures: tuple[str, ...]
    app_versions: VersionRange
    worker_protocols: VersionRange
    dependencies: tuple[Dependency, ...]
    resources: ResourceRequirements
    health_check: str
    required: bool = False
    signature: Signature | None = None

    def __post_init__(self):
        _require(type(self.schema_version) is int and self.schema_version == 1, '不支援的元件描述版本。')
        _name(self.component_id)
        relative_path(self.component_id)
        _require(isinstance(self.version, Version) and isinstance(self.kind, ComponentKind), '元件版本或種類無效。')
        for value in (self.display_name, self.license_id):
            _text(value)
        _text(self.source_url)
        try:
            url = urlsplit(self.source_url)
            _require(not any(char.isspace() for char in self.source_url) and url.scheme == 'https' and bool(url.hostname) and url.username is None and
                     url.password is None and not url.fragment, '來源須為不含帳密的 HTTPS URL。')
            url.port
        except ValueError as exc:
            raise ContractError('來源 URL 無效。') from exc
        relative_path(self.license_path)
        _require(isinstance(self.package_sha256, str) and re.fullmatch('[0-9a-f]{64}', self.package_sha256), '包檔 SHA-256 無效。')
        _integer(self.download_bytes, 1)
        _integer(self.unpacked_bytes, 1)
        _require(isinstance(self.files, tuple) and 0 < len(self.files) <= 4096 and
                 all(isinstance(item, FileSpec) for item in self.files), '元件檔案清單無效。')
        names = [item.path.casefold() for item in self.files]
        _require(len(names) == len(set(names)), '元件檔案有重複的跨平台名稱。')
        _require(any(item.path == self.license_path and item.size > 0 for item in self.files), '缺少可驗證的授權檔案。')
        _require(sum(item.size for item in self.files) <= self.unpacked_bytes, '檔案大小超出宣告解壓上限。')
        for values in (self.capabilities, self.platforms, self.architectures, self.dependencies):
            _require(isinstance(values, tuple) and len(values) <= 64, '過多或可變的元件屬性。')
        for values in (self.capabilities, self.platforms, self.architectures):
            _require(all(isinstance(value, str) for value in values) and len(set(values)) == len(values), '元件屬性格式無效或重複。')
        _require(bool(self.capabilities) and bool(self.platforms) and bool(self.architectures), '能力與平台不可空白。')
        for capability in self.capabilities:
            _name(capability)
        _require(set(self.platforms) <= {'windows', 'linux'}, '不支援的平台。')
        _require(set(self.architectures) <= {'x86_64', 'arm64'}, '不支援的處理器架構。')
        _require(isinstance(self.app_versions, VersionRange) and isinstance(self.worker_protocols, VersionRange), '相容版本範圍無效。')
        _require(all(isinstance(item, Dependency) and item.component_id != self.component_id for item in self.dependencies), '依賴內容或自我依賴無效。')
        _require(len({item.component_id for item in self.dependencies}) == len(self.dependencies), '依賴元件重複。')
        _require(isinstance(self.resources, ResourceRequirements) and type(self.required) is bool and
                 (self.signature is None or isinstance(self.signature, Signature)), '資源或簽章資料無效。')
        _name(self.health_check)

    @property
    def key(self):
        return self.component_id, str(self.version)

    def to_dict(self):
        return _encode(self)

    @classmethod
    def from_dict(cls, raw):
        try:
            return cls._decode(raw)
        except (ValueError, TypeError, KeyError, RecursionError) as exc:
            if isinstance(exc, ContractError):
                raise
            raise ContractError('元件描述的欄位或值無效。') from exc

    @classmethod
    def _decode(cls, raw):
        data = _object(raw, cls, optional={'required', 'signature'})
        data['version'] = Version.parse(data['version'])
        data['kind'] = ComponentKind(data['kind'])
        data['files'] = tuple(FileSpec(**_object(item, FileSpec)) for item in _array(data['files']))
        for name in ('capabilities', 'platforms', 'architectures'):
            data[name] = tuple(_array(data[name]))
        for name in ('app_versions', 'worker_protocols'):
            data[name] = _bounds(data[name])
        data['dependencies'] = tuple(Dependency(item['component_id'], _bounds(item['versions']))
                                     for raw_item in _array(data['dependencies'])
                                     for item in [_object(raw_item, Dependency)])
        data['resources'] = ResourceRequirements(**_object(data['resources'], ResourceRequirements))
        if data.get('signature') is not None:
            data['signature'] = Signature(**_object(data['signature'], Signature))
        return cls(**data)


def _object(raw, kind, optional=frozenset()):
    names = {field.name for field in fields(kind)}
    _require(isinstance(raw, dict) and set(raw) <= names and names - optional <= set(raw), '描述欄位缺漏或含未知欄位。')
    return dict(raw)


def _array(value):
    _require(isinstance(value, list) and len(value) <= 4096, '描述陣列格式或長度無效。')
    return value


def _bounds(raw):
    data = _object(raw, VersionRange)
    return VersionRange(Version.parse(data['minimum']), Version.parse(data['maximum_exclusive']))


def _encode(value):
    if isinstance(value, Version):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _encode(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple):
        return [_encode(item) for item in value]
    return value

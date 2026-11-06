"""驗證受信任 Ed25519 目錄；信任根由應用程式提供，網路資料不能新增金鑰。"""
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import base64
import hashlib
import json
from types import MappingProxyType
from urllib.parse import urlsplit

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from .contracts import ComponentSpec, ContractError, Signature, _name

MAX_CATALOG_BYTES = 1024 * 1024


class CatalogError(ValueError):
    """目錄來源、簽章、時間或契約未通過，不得提供給下載／執行服務。"""


def canonical_json(value):
    """簽署格式固定為 UTF-8／排序鍵／無空白；拒絕非 JSON 浮點常數。"""
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise CatalogError('目錄包含重複 JSON 欄位。')
        result[key] = value
    return result


def source_origin(url):
    if not isinstance(url, str) or len(url) > 4096 or any(char.isspace() or ord(char) < 32 for char in url):
        raise CatalogError('元件來源 URL 無效。')
    try:
        parsed = urlsplit(url)
        if (parsed.scheme != 'https' or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.fragment or parsed.port not in (None, 443)):
            raise CatalogError('元件來源須為不含帳密的 HTTPS 預設連接埠。')
        return 'https://' + parsed.hostname.lower()
    except ValueError as exc:
        raise CatalogError('元件來源 URL 無效。') from exc


@dataclass(frozen=True)
class TrustPolicy:
    """應用程式固定信任根及來源；輪替由新版政策加入金鑰，撤銷立即優先。"""
    policy_version: int
    catalog_id: str
    minimum_revision: int
    keys: object
    revoked_keys: frozenset[str]
    allowed_origins: tuple[str, ...]
    max_download_bytes: int = 4 * 1024**3
    max_unpacked_bytes: int = 64 * 1024**3

    def __post_init__(self):
        _name(self.catalog_id)
        if (type(self.policy_version) is not int or self.policy_version < 1 or
                type(self.minimum_revision) is not int or self.minimum_revision < 1):
            raise CatalogError('信任政策版本無效。')
        keys = dict(self.keys)
        if not 0 < len(keys) <= 16 or not isinstance(self.revoked_keys, frozenset):
            raise CatalogError('信任金鑰清單無效。')
        for key_id, value in keys.items():
            _name(key_id)
            if not isinstance(value, bytes) or len(value) != 32:
                raise CatalogError('Ed25519 公鑰須為 32 bytes。')
        for key_id in self.revoked_keys:
            _name(key_id)
        if (not isinstance(self.allowed_origins, tuple) or not 0 < len(self.allowed_origins) <= 16
                or any(source_origin(value) != value or urlsplit(value).path for value in self.allowed_origins)):
            raise CatalogError('來源白名單須為固定 HTTPS origin。')
        for value in (self.max_download_bytes, self.max_unpacked_bytes):
            if type(value) is not int or not 0 < value <= 2**40:
                raise CatalogError('信任政策容量上限無效。')
        object.__setattr__(self, 'keys', MappingProxyType(keys))

    def check_url(self, url):
        if source_origin(url) not in self.allowed_origins:
            raise CatalogError('來源或重新導向不在應用程式核准的 HTTPS 白名單。')


def _time(value):
    if not isinstance(value, str) or len(value) != 20 or not value.endswith('Z'):
        raise CatalogError('目錄時間須為 UTC YYYY-MM-DDTHH:MM:SSZ。')
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise CatalogError('目錄時間無效。') from exc


@dataclass(frozen=True)
class VerifiedCatalog:
    catalog_id: str
    revision: int
    digest: str
    components: tuple[ComponentSpec, ...]
    envelope: bytes

    def component(self, component_id, version):
        matches = [item for item in self.components if item.key == (component_id, str(version))]
        if not matches:
            raise CatalogError('可信目錄內沒有指定的元件版本。')
        return matches[0]


class CatalogVerifier:
    def __init__(self, policy, clock=lambda: datetime.now(timezone.utc)):
        self.policy = policy
        self.clock = clock
        self._highest_revision = policy.minimum_revision
        self._highest_payload_hash = None

    def load(self, envelope):
        """每次重新驗證；不信任呼叫端自行建立的 VerifiedCatalog 物件。"""
        if isinstance(envelope, VerifiedCatalog):
            envelope = envelope.envelope
        if not isinstance(envelope, bytes) or not 0 < len(envelope) <= MAX_CATALOG_BYTES:
            raise CatalogError('目錄超過大小限制或格式無效。')
        try:
            raw = json.loads(envelope, object_pairs_hook=unique_object)
            if not isinstance(raw, dict) or set(raw) != {'payload', 'signature'}:
                raise CatalogError('目錄封套欄位無效。')
            signature = Signature(**raw['signature'])
            if signature.key_id in self.policy.revoked_keys or signature.key_id not in self.policy.keys:
                raise CatalogError('目錄簽章金鑰未受信任或已撤銷。')
            payload = raw['payload']
            public = Ed25519PublicKey.from_public_bytes(self.policy.keys[signature.key_id])
            public.verify(base64.b64decode(signature.value, validate=True), canonical_json(payload))
            if not isinstance(payload, dict) or set(payload) != {
                    'schema_version', 'catalog_id', 'revision', 'trust_policy_version', 'issued_at', 'expires_at', 'components'}:
                raise CatalogError('目錄 payload 欄位無效。')
            if (type(payload['schema_version']) is not int or payload['schema_version'] != 1
                    or payload['catalog_id'] != self.policy.catalog_id
                    or type(payload['trust_policy_version']) is not int
                    or payload['trust_policy_version'] != self.policy.policy_version):
                raise CatalogError('目錄 schema、識別或信任政策版本不符。')
            revision = payload['revision']
            if type(revision) is not int or revision < self._highest_revision:
                raise CatalogError('拒絕低於最低版本或本次已見版本的目錄。')
            issued, expires = _time(payload['issued_at']), _time(payload['expires_at'])
            now = self.clock()
            if now.tzinfo is None or issued > now + timedelta(minutes=5) or expires <= now or not issued < expires:
                raise CatalogError('目錄已過期、尚未生效或有效期間無效。')
            items = payload['components']
            if not isinstance(items, list) or not 0 < len(items) <= 256:
                raise CatalogError('元件目錄數量無效。')
            specs = tuple(ComponentSpec.from_dict(item) for item in items)
            if len({item.key for item in specs}) != len(specs):
                raise CatalogError('目錄含重複元件版本。')
            for spec in specs:
                self.policy.check_url(spec.source_url)
                if spec.download_bytes > self.policy.max_download_bytes or spec.unpacked_bytes > self.policy.max_unpacked_bytes:
                    raise CatalogError('元件容量超過信任政策上限。')
            payload_hash = hashlib.sha256(canonical_json(payload)).hexdigest()
            if revision == self._highest_revision and self._highest_payload_hash not in (None, payload_hash):
                raise CatalogError('相同目錄版本不能替換成不同內容。')
            self._highest_revision = revision
            self._highest_payload_hash = payload_hash
            return VerifiedCatalog(payload['catalog_id'], revision, hashlib.sha256(envelope).hexdigest(), specs, envelope)
        except CatalogError:
            raise
        except (ValueError, TypeError, KeyError, RecursionError, InvalidSignature) as exc:
            raise CatalogError('目錄簽章或內容驗證失敗。') from exc

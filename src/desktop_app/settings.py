"""桌面與 CLI 共用的版本化設定，保留舊 schema 遷移及安全儲存。"""
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile

from .resources import MIB, Policy
from .components.contracts import Version, _name
from .languages import validate_languages


@dataclass(frozen=True)
class ComponentPreference:
    """只保存選擇，不保存 ready 等健康狀態；指定版本不代表已安裝。"""
    capability: str
    component_id: str
    version: str | None = None

    def __post_init__(self):
        _name(self.capability)
        _name(self.component_id)
        if self.version is not None:
            Version.parse(self.version)


@dataclass(frozen=True)
class Settings:
    schema_version: int = 7
    ram_budget_mib: int | None = None
    reserve_mib: int = 2048
    resource_wait_seconds: float = 30.0
    ocr_executable: str | None = None
    ocr_data_dir: str | None = None
    device: str = "auto"
    cpu_threads: int = 1
    ocr_backend: str = "tesseract"
    vram_budget_mib: int = 768
    quality: str = 'precise'
    onboarding_version: int = 0
    component_preferences: tuple[ComponentPreference, ...] = ()
    update_channel: str = 'stable'
    allow_optional_downloads: bool = False
    ocr_languages: tuple[str, ...] | None = None

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 7:
            raise ValueError("不支援的設定版本，請勿以舊版程式覆寫。")
        if self.ram_budget_mib is not None and (
                type(self.ram_budget_mib) is not int or self.ram_budget_mib <= 0):
            raise ValueError("RAM 預算須為正整數 MiB 或 null（自動）。")
        if type(self.reserve_mib) is not int or self.reserve_mib < 0:
            raise ValueError("系統保留容量須為非負整數 MiB。")
        wait = self.resource_wait_seconds
        if type(wait) not in (int, float) or not math.isfinite(wait) or wait < 0:
            raise ValueError("等待時間須為有限的非負秒數。")
        for value in (self.ocr_executable, self.ocr_data_dir):
            if value is not None and (not isinstance(value, str) or not value.strip() or "\x00" in value):
                raise ValueError("OCR 路徑須為非空字串或 null。")
        if self.device not in ("auto", "cpu", "gpu"):
            raise ValueError("運算裝置須為 auto、cpu 或 gpu。")
        if type(self.cpu_threads) is not int or not 1 <= self.cpu_threads <= 256:
            raise ValueError("CPU 執行緒上限須為 1 至 256 的整數。")
        if self.ocr_backend not in ("tesseract", "onnx", "onnx_verify", "managed_cpu"):
            raise ValueError("不支援的 OCR 後端。")
        if type(self.vram_budget_mib) is not int or self.vram_budget_mib < 192:
            raise ValueError("GPU 記憶體預算須為至少 192 MiB 的整數。")
        if self.quality not in ('precise', 'fast') or self.update_channel not in ('stable', 'preview'):
            raise ValueError('轉換品質或更新頻道無效。')
        if type(self.onboarding_version) is not int or not 0 <= self.onboarding_version <= 1000:
            raise ValueError('首次精靈版本無效。')
        if type(self.allow_optional_downloads) is not bool:
            raise ValueError('元件下載選項須為布林值。')
        if (not isinstance(self.component_preferences, tuple) or len(self.component_preferences) > 64
                or not all(isinstance(item, ComponentPreference) for item in self.component_preferences)
                or len({item.capability for item in self.component_preferences}) != len(self.component_preferences)):
            raise ValueError('元件偏好無效、重複或超過限制。')
        validate_languages(self.ocr_languages)

    def policy(self) -> Policy:
        return Policy(budget=None if self.ram_budget_mib is None else self.ram_budget_mib*MIB,
                      reserve=self.reserve_mib*MIB)


def _read(path):
    with path.open("rb") as source:
        raw = source.read(65537)
    if len(raw) > 65536:
        raise ValueError("設定檔超過 64 KiB。")
    return raw


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('設定含有重複欄位。')
        result[key] = value
    return result


def _decode(raw):
    try:
        content = json.loads(raw, object_pairs_hook=_unique_object)
    except RecursionError as exc:
        raise ValueError('設定結構過深，原檔未變更。') from exc
    if not isinstance(content, dict):
        raise ValueError("設定檔須為 JSON 物件。")
    unknown = content.keys() - Settings.__dataclass_fields__.keys()
    if unknown:
        raise ValueError("設定包含不支援的欄位：" + ", ".join(sorted(unknown)))
    if "schema_version" not in content:
        raise ValueError("設定檔缺少 schema_version。")
    original_version = content['schema_version']
    if type(original_version) is not int or original_version not in (1, 2, 3, 4, 5, 6, 7):
        raise ValueError('不支援的設定版本，原檔未變更。')
    preferences = content.get('component_preferences', [])
    if not isinstance(preferences, list) or len(preferences) > 64:
        raise ValueError('元件偏好須為有限的清單。')
    try:
        preferences = tuple(ComponentPreference(**item) for item in preferences)
    except TypeError as exc:
        raise ValueError('元件偏好欄位無效。') from exc
    languages=content.get('ocr_languages')
    if languages is not None and not isinstance(languages,list):raise ValueError('OCR 語言須為 JSON 清單或 null。')
    return Settings(**{**content, 'schema_version': 7, 'component_preferences': preferences,
                       'ocr_languages':None if languages is None else tuple(languages)}), original_version


def load_settings(path: Path) -> Settings:
    """v1–v6 只在記憶體遷移；讀取不寫檔、不下載、不更動外部資料。"""
    return _decode(_read(Path(path)))[0]


def _backup(raw, path, version):
    """遷移前保存完整原始位元組；內容雜湊命名且不覆寫既有備份。"""
    backup = path.with_name(path.name + f'.pre-v{version}-' + hashlib.sha256(raw).hexdigest()[:16] + '.bak')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.settings-backup-', delete=False) as output:
            temporary = Path(output.name)
            output.write(raw)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, backup)
        except FileExistsError:
            if backup.is_symlink() or not backup.is_file() or _read(backup) != raw:
                raise ValueError('既有設定備份不符，未覆寫設定或備份。')
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


_UNSPECIFIED = object()


def save_settings(settings: Settings, path: Path, *, expected_raw=_UNSPECIFIED):
    """明確儲存才備份／升級；拒絕覆蓋損毀或未來設定，失敗保留原檔。"""
    encoded = json.dumps(asdict(settings), ensure_ascii=False, indent=2, allow_nan=False) + '\n'
    if len(encoded.encode('utf-8')) > 65536:
        raise ValueError('設定檔超過 64 KiB，未儲存。')
    path = Path(path)
    if path.is_symlink():
        raise ValueError('不覆寫符號連結設定檔。')
    previous = _read(path) if path.exists() else None
    # 首次設定可能在背景檢查數十秒；拒絕以過期畫面覆寫這段期間的新偏好。
    if expected_raw is not _UNSPECIFIED and previous != expected_raw:
        raise ValueError('設定已變更，請重新開啟首次設定；原檔未覆寫。')
    if previous is not None:
        _, original_version = _decode(previous)
        if original_version < 7:
            _backup(previous, path, original_version)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".settings-", delete=False) as output:
            temporary = Path(output.name)
            output.write(encoded)
            output.flush()
            os.fsync(output.fileno())
        # 偵測明顯並行變更，不能在載入後以過期畫面覆寫新 schema。
        current = _read(path) if path.exists() else None
        if path.is_symlink() or current != previous:
            raise ValueError('儲存期間設定已變更，請重新載入。')
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

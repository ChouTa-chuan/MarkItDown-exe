"""Versioned resource preferences shared by the CLI and future desktop UI."""
from dataclasses import asdict, dataclass
import json
import math
import os
from pathlib import Path
import tempfile

from .resources import MIB, Policy


@dataclass(frozen=True)
class Settings:
    schema_version: int = 2
    ram_budget_mib: int | None = None
    reserve_mib: int = 2048
    resource_wait_seconds: float = 30.0
    ocr_executable: str | None = None
    ocr_data_dir: str | None = None

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 2:
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

    def policy(self) -> Policy:
        return Policy(budget=None if self.ram_budget_mib is None else self.ram_budget_mib*MIB,
                      reserve=self.reserve_mib*MIB)


def load_settings(path: Path) -> Settings:
    # An explicitly selected missing file is an error, never a silent reset.
    with path.open("rb") as source:
        raw = source.read(65537)
    if len(raw) > 65536:
        raise ValueError("設定檔超過 64 KiB。")
    content = json.loads(raw)
    if not isinstance(content, dict):
        raise ValueError("設定檔須為 JSON 物件。")
    unknown = content.keys() - Settings.__dataclass_fields__.keys()
    if unknown:
        raise ValueError("設定包含不支援的欄位：" + ", ".join(sorted(unknown)))
    if "schema_version" not in content:
        raise ValueError("設定檔缺少 schema_version。")
    if type(content["schema_version"]) is int and content["schema_version"] == 1:
        content = {**content, "schema_version": 2}
    return Settings(**content)


def save_settings(settings: Settings, path: Path):
    """Explicit save; same-directory atomic replacement preserves prior on error."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=".settings-", delete=False) as output:
            temporary = Path(output.name)
            json.dump(asdict(settings), output, ensure_ascii=False, indent=2, allow_nan=False)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

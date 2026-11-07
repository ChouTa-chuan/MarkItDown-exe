"""核心契約：轉換品質、任務狀態、請求、計畫及可辨識的錯誤類型。"""
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class Quality(str, Enum):
    FAST = "fast"
    PRECISE = "precise"


class State(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class Request:
    """不可變的單次轉換請求；路徑、品質與資源偏好一併傳入隔離程序。"""
    source: Path
    destination: Path
    quality: Quality = Quality.PRECISE
    ocr_executable: str | None = None
    ocr_data_dir: str | None = None
    device: str = "auto"
    cpu_threads: int = 1
    ocr_backend: str = "tesseract"
    vram_budget_mib: int = 768
    component_id: str | None = None
    component_version: str | None = None
    ocr_languages: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Plan:
    """轉換步驟與額外 RAM 估算；估算用於准入，並非記憶體硬上限。"""
    steps: tuple[str, ...]
    additional_bytes: int
    explanation: str


class UnsupportedFormat(ValueError):
    pass


class Cancelled(RuntimeError):
    pass


class ResourceDeferred(RuntimeError):
    pass

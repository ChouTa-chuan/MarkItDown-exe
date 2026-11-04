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
    source: Path
    destination: Path
    quality: Quality = Quality.PRECISE
    ocr_executable: str | None = None
    ocr_data_dir: str | None = None
    device: str = "auto"
    cpu_threads: int = 1


@dataclass(frozen=True)
class Plan:
    steps: tuple[str, ...]
    additional_bytes: int
    explanation: str


class UnsupportedFormat(ValueError):
    pass


class Cancelled(RuntimeError):
    pass


class ResourceDeferred(RuntimeError):
    pass

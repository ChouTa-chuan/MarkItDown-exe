"""Native text analysis; PDF/OCR analysis must be added with tested engines."""
from .core import Plan, Request, UnsupportedFormat
from .resources import MIB


def analyze(request: Request) -> Plan:
    if not request.source.is_file():
        raise FileNotFoundError(request.source)
    suffix = request.source.suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise UnsupportedFormat(f"尚未整合 {suffix or '無副檔名'} 格式；目前支援 UTF-8 txt/md。")
    if request.source.resolve() == request.destination.resolve():
        raise ValueError("輸出不得覆蓋來源。")
    if request.destination.exists():
        raise FileExistsError(request.destination)
    return Plan(("stream_utf8", "atomic_export"), 8*MIB,
                "純文字使用原生解析，不需 OCR 或 GPU；以固定區塊處理。")

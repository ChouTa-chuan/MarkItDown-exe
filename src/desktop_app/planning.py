"""Native text analysis; PDF/OCR analysis must be added with tested engines."""
from .core import Plan, Request, UnsupportedFormat, Quality
from .resources import MIB


def analyze(request: Request) -> Plan:
    if not request.source.is_file():
        raise FileNotFoundError(request.source)
    suffix = request.source.suffix.lower()
    if suffix not in {".txt", ".md", ".docx", ".pptx", ".xlsx", ".pdf", ".html", ".htm"}:
        raise UnsupportedFormat(f"尚未整合 {suffix or '無副檔名'} 格式。")
    if request.source.resolve() == request.destination.resolve():
        raise ValueError("輸出不得覆蓋來源。")
    if request.destination.exists():
        raise FileExistsError(request.destination)
    if suffix in {".txt", ".md"}:
        return Plan(("stream_utf8", "atomic_export"), 8*MIB,
                    "純文字使用原生解析，不需 OCR 或 GPU；以固定區塊處理。")
    # Initial conservative estimate, not a hard allocation guarantee. Office
    # archives can expand far beyond on-disk size; monitor the worker too.
    estimate = max(256*MIB, request.source.stat().st_size*12)
    if suffix == ".pdf" and request.quality == Quality.PRECISE:
        return Plan(("analyze_pages", "native_or_ocr", "atomic_export"), estimate,
                    "PDF 逐頁自動選擇原生解析或本機 OCR，必要時提供品質提醒。")
    return Plan(("markitdown_local", "atomic_export"), estimate,
                "使用本機 MarkItDown 解析；尚未加入掃描 OCR 與精準版面重試。")

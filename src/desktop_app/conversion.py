import os
from pathlib import Path
import tempfile

from .core import Request, Quality


def convert_text(request: Request, checkpoint, progress=lambda stage: None):
    """Checkpoint may pause or cancel at bounded text-processing boundaries."""
    with request.source.open(encoding="utf-8-sig", newline="") as source:
        def chunks():
            while True:
                block = source.read(64*1024)
                if not block:
                    break
                yield block
        _write_chunks(request, chunks(), checkpoint, progress)


def convert_document(request: Request, checkpoint, progress=lambda stage: None):
    if request.source.suffix.lower() in {".txt", ".md"}:
        return convert_text(request, checkpoint, progress)
    if request.source.suffix.lower() == ".pdf" and request.quality == Quality.PRECISE:
        from .devices import ocr_backend
        progress("運算裝置：" + ocr_backend(request.device))
        from .pdf_pipeline import pdf_chunks
        reports = []
        _write_chunks(request, pdf_chunks(request.source, checkpoint, progress, reports,
                                         request.ocr_executable, request.ocr_data_dir), checkpoint, progress)
        warnings = sum(len(report["warnings"]) for report in reports)
        return f"逐頁分析 {len(reports)} 頁，OCR {sum(r['route'] == 'ocr' for r in reports)} 頁，品質提醒 {warnings} 項。"
    checkpoint()
    progress("載入本機轉換器")
    from markitdown import MarkItDown
    converter = MarkItDown(enable_plugins=False)
    checkpoint()
    progress("解析文件（原生套件可能無法立即暫停）")
    result = converter.convert_local(str(request.source.resolve()))
    checkpoint()
    markdown = result.text_content
    _write_chunks(request, (markdown[i:i+64*1024] for i in range(0, len(markdown), 64*1024)),
                  checkpoint, progress)


def _write_chunks(request, chunks, checkpoint, progress):
    destination = request.destination.resolve()
    checkpoint()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                dir=destination.parent, prefix=".conversion-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            progress("寫入 Markdown")
            for block in chunks:
                checkpoint()
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
        checkpoint()
        progress("提交輸出")
        # Same-volume exclusive publication. Unsupported filesystems fail
        # explicitly instead of falling back to overwriting existing output.
        os.link(temporary, destination)
    finally:
        if hasattr(chunks, "close"):
            chunks.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)

"""格式轉換與輸出保護：串流寫入暫存，完成後以排他方式提交結果。"""
import os
from pathlib import Path
import tempfile

from .core import Request, Quality


def convert_text(request: Request, checkpoint, progress=lambda stage: None):
    """在固定大小的文字處理邊界接受暫停或取消。"""
    with request.source.open(encoding="utf-8-sig", newline="") as source:
        def chunks():
            while True:
                block = source.read(64*1024)
                if not block:
                    break
                yield block
        _write_chunks(request, chunks(), checkpoint, progress)


def convert_document(request: Request, checkpoint, progress=lambda stage: None, *, component_context=None,
                     policy=None,cancel=None,permit=None,owner_pid=None,resource_wait=30,record_component=lambda evidence:None,
                     resource_event=None):
    if request.source.suffix.lower() in {".txt", ".md"}:
        return convert_text(request, checkpoint, progress)
    if request.source.suffix.lower() == ".pdf" and request.quality == Quality.PRECISE:
        from .devices import ocr_backend
        progress("運算裝置：" + ocr_backend(request.device, request.ocr_backend))
        from .pdf_pipeline import pdf_chunks
        reports = []
        from contextlib import nullcontext
        session=nullcontext(None)
        if request.ocr_backend=='managed_cpu':
            from .component_workers.managed import ManagedOCRSession
            session=ManagedOCRSession(component_context,request,checkpoint,progress,policy=policy,cancel=cancel,
                                      permit=permit,owner_pid=owner_pid,resource_wait=resource_wait,record_component=record_component,
                                      resource_event=resource_event)
        with session as managed:
            def output_progress(stage):
                progress(stage)
                if stage=='提交輸出' and managed is not None: managed.validate(for_commit=True)
            _write_chunks(request, pdf_chunks(request.source, checkpoint, progress, reports,
                                             request.ocr_executable, request.ocr_data_dir,
                                             request.ocr_backend, request.device, request.cpu_threads,
                                             request.vram_budget_mib,managed=managed,
                                             languages=request.ocr_languages), checkpoint, output_progress)
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
    # 保留最後檔名，不 resolve 懸空連結到其他路徑；既有連結也是既有輸出。
    destination = request.destination.absolute()
    if destination.exists() or destination.is_symlink(): raise FileExistsError(destination)
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
        # 同磁碟硬連結以排他方式提交；目的地已存在或不支援時直接失敗，避免覆寫既有輸出。
        os.link(temporary, destination)
    finally:
        if hasattr(chunks, "close"):
            chunks.close()
        if temporary is not None:
            temporary.unlink(missing_ok=True)

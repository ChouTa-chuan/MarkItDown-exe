"""Page-wise PDF analysis with bounded local OCR and explicit quality warnings."""
from dataclasses import dataclass
import math
import os
from statistics import median
from pathlib import Path
import shutil
import subprocess
import tempfile
import time


@dataclass(frozen=True)
class PageDecision:
    number: int
    route: str
    warnings: tuple[str, ...] = ()


def decide_page(number, text, image_coverage):
    meaningful = sum(char.isalnum() for char in text)
    if meaningful == 0 and image_coverage == 0:
        return PageDecision(number, "blank")
    if meaningful < 24 and image_coverage >= 0.25:
        return PageDecision(number, "ocr")
    warnings = []
    if "\ufffd" in text or "(cid:" in text:
        return PageDecision(number, "ocr", ("原生文字含無法解碼字元，改用 OCR。",))
    if image_coverage >= 0.25:
        warnings.append("文字與圖片混合，圖片內的文字可能尚未完整擷取。")
    return PageDecision(number, "native", tuple(warnings))


def _run_ocr(image, checkpoint, progress, dpi, executable=None, data_dir=None):
    executable = executable or shutil.which("tesseract")
    if not executable:
        raise RuntimeError("本頁需要 OCR，但找不到 Tesseract；請安裝 OCR 元件後重試。")
    data_args = ["--tessdata-dir", data_dir] if data_dir else []
    languages = subprocess.run([executable, "--list-langs", *data_args], capture_output=True,
                               text=True, timeout=10, check=True).stdout.splitlines()[1:]
    languages = {name.strip() for name in languages}
    selected = "+".join(name for name in ("chi_tra", "eng") if name in languages)
    if not selected:
        raise RuntimeError("OCR 缺少 chi_tra 或 eng 語言模型，無法辨識。")
    warning = None if "chi_tra" in languages else "未安裝繁體中文 OCR 模型；本頁僅以英文模型處理，中文結果需檢查。"
    with tempfile.TemporaryDirectory(prefix="markitdown-ocr-") as directory:
        source = Path(directory) / "page.png"
        prepared, dpi = _normalize_ocr_image(image, dpi)
        try:
            mode = _segmentation_mode(prepared)
            prepared.save(source)
        finally:
            prepared.close()
        target = Path(directory) / "recognized"
        command = [executable, str(source), str(target), "-l", selected,
                   "--dpi", str(dpi), "--psm", str(mode), *data_args]
        # Redirect to files so verbose native output cannot fill a PIPE and
        # deadlock cancellation. Do not record the recognized document in logs.
        with (Path(directory) / "stderr.txt").open("w+b") as errors:
            child = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=errors,
                                     env={**os.environ, "OMP_THREAD_LIMIT": os.environ.get("OMP_THREAD_LIMIT", "1")})
            started = time.monotonic()
            try:
                while child.poll() is None:
                    checkpoint()
                    if time.monotonic() - started > 90:
                        raise RuntimeError("單頁 OCR 超過 90 秒，已停止；可調整文件後重試。")
                    time.sleep(0.1)
                if child.returncode:
                    raise RuntimeError(f"OCR 執行失敗，exitcode={child.returncode}。")
                return target.with_suffix(".txt").read_text(encoding="utf-8"), warning
            finally:
                if child.poll() is None:
                    child.terminate()
                    try:
                        child.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        child.kill()
                        child.wait(timeout=3)


def _normalize_ocr_image(image, dpi):
    """Normalize oversized glyphs, which can hurt Tesseract recognition.

    Projection estimates line heights without allocating a Python pixel list.
    This is a heuristic; heterogeneous layouts still require quality review.
    """
    from PIL import ImageOps, Image
    gray = ImageOps.grayscale(image)
    with ImageOps.invert(gray) as inverted:
        with inverted.point(lambda value: 255 if value > 100 else 0) as mask:
            _, rows = mask.getprojection()
    runs = []
    start = None
    for index, ink in enumerate([*rows, 0]):
        if ink and start is None:
            start = index
        elif not ink and start is not None:
            if index-start >= 8:
                runs.append(index-start)
            start = None
    height = median(runs) if runs else 0
    if height > 40:
        scale = 28/height
        resized = gray.resize((max(1, round(gray.width*scale)), max(1, round(gray.height*scale))),
                              Image.Resampling.LANCZOS)
        gray.close()
        return resized, max(70, round(dpi*scale))
    return gray, dpi


def _segmentation_mode(image):
    """Sparse short blocks need a different layout mode than dense pages."""
    from PIL import ImageOps
    with ImageOps.grayscale(image) as gray, ImageOps.invert(gray) as inverted:
        with inverted.point(lambda value: 255 if value > 100 else 0) as mask:
            density = mask.histogram()[255] / max(1, image.width*image.height)
            _, rows = mask.getprojection()
    runs, length = 0, 0
    for ink in [*rows, 0]:
        if ink:
            length += 1
        else:
            if length >= 4:
                runs += 1
            length = 0
    return 11 if 1 <= runs <= 6 and density < 0.08 else 3


def _render(pdfium, index, dpi):
    page = pdfium[index]
    try:
        width, height = page.get_size()
        scale = min(dpi / 72, math.sqrt(12_000_000 / max(width*height, 1)))
        bitmap = page.render(scale=scale)
        try:
            return bitmap.to_pil().copy(), max(1, round(scale*72))
        finally:
            bitmap.close()
    finally:
        page.close()


def _table_markdown(table):
    rows = [[str(cell or "").replace("|", "\\|").replace("\n", "<br>") for cell in row] for row in table]
    if not rows:
        return ""
    width = max(map(len, rows))
    normalized = [row + [""]*(width-len(row)) for row in rows]
    output = ["| " + " | ".join(normalized[0]) + " |", "| " + " | ".join(["---"]*width) + " |"]
    output.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
    return "\n".join(output)


def _native_columns(page, text):
    words = page.extract_words()
    middle = page.width/2
    gutter = page.width*0.025
    left = [word for word in words if word["x1"] < middle-gutter]
    right = [word for word in words if word["x0"] > middle+gutter]
    # Conservative two-column heuristic; full-width titles/footers or objects
    # crossing the gutter defer to the original order and quality review.
    if len(left) >= 12 and len(right) >= 12 and len(left)+len(right) == len(words):
        top = min(word["top"] for word in words)
        bottom = max(word["bottom"] for word in words)
        left_text = page.crop((0, top, middle, bottom)).extract_text() or ""
        right_text = page.crop((middle, top, page.width, bottom)).extract_text() or ""
        return left_text + "\n\n" + right_text, "偵測到中央留白，按左欄再右欄排列；請核對閱讀順序。"
    return text, None


def pdf_chunks(source, checkpoint, progress, reports, executable=None, data_dir=None,
               backend="tesseract", device="auto", threads=1, vram_budget_mib=768):
    import pdfplumber
    import pypdfium2
    renderer = None
    onnx = None
    try:
        with pdfplumber.open(source) as document:
            for index, page in enumerate(document.pages):
                checkpoint()
                try:
                    text = page.extract_text() or ""
                    area = max(page.width*page.height, 1)
                    coverage = min(1, sum(max(0, im["x1"]-im["x0"])*max(0, im["bottom"]-im["top"])
                                          for im in page.images)/area)
                    decision = decide_page(index+1, text, coverage)
                    warnings = list(decision.warnings)
                    route = decision.route
                    progress(f"第 {index+1}/{len(document.pages)} 頁：{'OCR' if route == 'ocr' else '原生分析'}")
                    if route == "ocr":
                        if backend in ("onnx", "onnx_verify") and onnx is None:
                            from .onnx_ocr import OnnxOCR
                            onnx = OnnxOCR(device, threads, vram_budget_mib, checkpoint, progress)
                        warnings.append("OCR 結果需核對；圖表、公式與原始版面尚未完整還原。")
                        if renderer is None:
                            renderer = pypdfium2.PdfDocument(str(source))
                        text = ""
                        comparison = None
                        for dpi in (200, 300):
                            checkpoint()
                            image, actual_dpi = _render(renderer, index, dpi)
                            try:
                                if onnx is not None:
                                    recognized, warning = onnx.recognize(image)
                                    current_comparison = None
                                    if backend == "onnx_verify":
                                        from .quality import compare_ocr
                                        checkpoint()
                                        primary, primary_warning = _run_ocr(image, checkpoint, progress,
                                                                           actual_dpi, executable, data_dir)
                                        current_comparison = compare_ocr(primary, recognized)
                                        recognized = primary
                                        warning = current_comparison.warning
                                        if primary_warning:
                                            warning += " " + primary_warning
                                else:
                                    recognized, warning = _run_ocr(image, checkpoint, progress, actual_dpi,
                                                                   executable, data_dir)
                            finally:
                                image.close()
                            if warning and warning not in warnings:
                                warnings.append(warning)
                            if len(recognized.strip()) > len(text.strip()):
                                text = recognized
                                if backend == "onnx_verify":
                                    comparison = current_comparison
                            elif backend == "onnx_verify" and comparison is None:
                                comparison = current_comparison
                            if len(text.strip()) >= 24:
                                break
                            progress(f"第 {index+1} 頁 OCR 文字不足，嘗試較高解析度（最多兩次）。")
                        if not text.strip():
                            warnings.append("OCR 未辨識出文字；可能為純圖片或辨識失敗，請核對原頁。")
                        if comparison is not None:
                            text += comparison.evidence_markdown()
                    elif route == "native":
                        tables = page.find_tables()
                        if tables:
                            # Keep text around tables; exclude their cells from
                            # prose to avoid duplicate content, then order blocks.
                            blocks = []
                            filtered = page
                            for table in tables:
                                x0, top, x1, bottom = table.bbox
                                filtered = filtered.filter(lambda obj, box=(x0, top, x1, bottom): not (
                                    obj.get("object_type") == "char" and box[0] <= obj.get("x0", -1) <= box[2]
                                    and box[1] <= obj.get("top", -1) <= box[3]))
                                blocks.append((top, _table_markdown(table.extract())))
                            # Remaining lines retain their vertical position.
                            for line in filtered.extract_text_lines():
                                blocks.append((line["top"], line["text"]))
                            text = "\n\n".join(value for _, value in sorted(blocks, key=lambda item:item[0]))
                            warnings.append("表格已自動擷取；合併儲存格與複雜版面請核對。")
                        else:
                            text, column_warning = _native_columns(page, text)
                            if column_warning:
                                warnings.append(column_warning)
                    reports.append({"page": index+1, "route": route, "warnings": warnings})
                    checkpoint()
                    yield f"<!-- source-page: {index+1}; route: {route} -->\n\n"
                    for warning in warnings:
                        yield f"> ⚠ 第 {index+1} 頁：{warning}\n\n"
                    yield text.strip() + "\n\n"
                finally:
                    page.close()
    finally:
        if onnx is not None:
            onnx.close()
        if renderer is not None:
            renderer.close()

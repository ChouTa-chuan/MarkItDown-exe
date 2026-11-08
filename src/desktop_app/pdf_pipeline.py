"""逐頁 PDF 分析：原生文字／OCR 路由、有界重試、表格與品質提醒。"""
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


def _run_ocr(image, checkpoint, progress, dpi, executable=None, data_dir=None, *, languages=None):
    from .languages import validate_languages
    validate_languages(languages)
    from .bundled_ocr import bindings
    executable, data_dir, _ = bindings(executable, data_dir)
    executable = executable or shutil.which("tesseract")
    if not executable:
        raise RuntimeError("本頁需要 OCR，但找不到 Tesseract；請安裝 OCR 元件後重試。")
    data_args = ["--tessdata-dir", data_dir] if data_dir else []
    available = subprocess.run([executable, "--list-langs", *data_args], capture_output=True,
                               text=True, timeout=10, check=True).stdout.splitlines()[1:]
    available = {name.strip() for name in available}
    if languages is not None and not set(languages)<=available:
        raise RuntimeError('缺少所選 OCR 語言模型：'+'、'.join(name for name in languages if name not in available)+'；未改用其他語言。')
    selected = "+".join(languages) if languages is not None else "+".join(name for name in ("chi_tra", "eng") if name in available)
    if not selected:
        raise RuntimeError("OCR 缺少 chi_tra 或 eng 語言模型，無法辨識。")
    warning = None if languages is not None or "chi_tra" in available else "未安裝繁體中文 OCR 模型；本頁僅以英文模型處理，中文結果需檢查。"
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
        # 原生錯誤輸出導向暫存檔，避免 PIPE 滿載卡住取消；日誌不記錄辨識全文。
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
    """以投影估算行高並縮放過大字形，避免額外建立逐像素 Python 串列。

    此為啟發式前處理，混合版面仍須依原頁核對品質。
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
    """稀疏短文字與密集文件採不同分頁模式，降低短行漏字風險。"""
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


def _native_columns(page, text, words=None, checkpoint=lambda:None):
    words = page.extract_words() if words is None else words
    middle = page.width/2
    gutter = page.width*0.025
    # 以跨欄標題切分水平區域，再各區先左後右，避免標題被切半或上下兩區混讀。
    crossing=sorted((w['top'],w['bottom']) for w in words
                    if not (w['x1']<middle-gutter or w['x0']>middle+gutter))
    separators=[]
    for top,bottom in crossing:
        if separators and top<=separators[-1][1]+2:
            separators[-1]=(separators[-1][0],max(bottom,separators[-1][1]))
        else:separators.append((top,bottom))
    if len(separators)>64:
        return text, '跨欄分區超過 64 區，保留原生閱讀順序，請核對版面。'
    def extract(top,bottom,left=0,right=None):
        right=page.width if right is None else right
        return page.filter(lambda obj: obj.get('object_type')!='char' or
                           (top<=(obj['top']+obj['bottom'])/2<bottom and
                            left<=(obj['x0']+obj['x1'])/2<right)).extract_text() or ''
    parts=[];reordered=False;start=0
    for top,bottom in [*separators,(page.height,page.height)]:
        checkpoint()
        band=[w for w in words if start<=(w['top']+w['bottom'])/2<top]
        left=[w for w in band if w['x1']<middle-gutter]
        right=[w for w in band if w['x0']>middle+gutter]
        # 兩側都需有足夠文字且垂直範圍重疊；零星左右標籤不足以證明雙欄。
        overlap=(min(max(w['bottom'] for w in left),max(w['bottom'] for w in right))-
                 max(min(w['top'] for w in left),min(w['top'] for w in right))) if left and right else 0
        span=max((w['bottom'] for w in band),default=0)-min((w['top'] for w in band),default=0)
        if len(left)>=12 and len(right)>=12 and len(left)+len(right)==len(band) and overlap>=span*0.5:
            parts.extend([(start,top,0,middle),(start,top,middle,page.width)])
            reordered=True
        else:parts.append((start,top,0,page.width))
        if bottom>top:parts.append((top,bottom,0,page.width))
        start=bottom
    if reordered:
        output=[]
        for part in parts:
            checkpoint();output.append(extract(*part))
        return '\n\n'.join(part for part in output if part), "偵測到中央留白，分區按左欄再右欄排列；跨欄標題與頁尾保留，請核對閱讀順序。"
    return text, None


def pdf_chunks(source, checkpoint, progress, reports, executable=None, data_dir=None,
               backend="tesseract", device="auto", threads=1, vram_budget_mib=768, *, managed=None,languages=None):
    """逐頁產出內容與核對提醒；頁面、渲染器及引擎在取消或例外時仍需釋放。"""
    import pdfplumber
    import pypdfium2
    from .languages import validate_languages
    validate_languages(languages)
    renderer = None
    onnx = None
    previous_tail = None
    try:
        with pdfplumber.open(source) as document:
            for index, page in enumerate(document.pages):
                checkpoint()
                next_tail = None
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
                        if backend!='tesseract' and set(languages or ()) & {'jpn','kor'}:
                            raise RuntimeError('日文／韓文目前僅驗證 Tesseract；請明確選擇 Tesseract 後重試，未更換後端。')
                        if backend=='managed_cpu' and managed is None:
                            raise RuntimeError('受管 OCR 尚未接入此呼叫；未改用其他引擎。')
                        if backend in ("onnx", "onnx_verify") and onnx is None:
                            from .onnx_ocr import OnnxOCR
                            onnx = OnnxOCR(device, threads, vram_budget_mib, checkpoint, progress)
                        warnings.append("OCR 結果需核對；圖表、公式與原始版面尚未完整還原。")
                        if backend=='tesseract' and len(languages or ())>1 and set(languages)&{'jpn','kor'}:
                            warnings.append('多語混合解碼可能混淆相近字形；若已知文件語言，請選對應語言並核對原文。')
                        if renderer is None:
                            renderer = pypdfium2.PdfDocument(str(source))
                        text = ""
                        comparison = None
                        for dpi in (200, 300):
                            checkpoint()
                            image, actual_dpi = _render(renderer, index, dpi)
                            try:
                                if backend=='managed_cpu':
                                    recognized,warning=managed.recognize(image)
                                    current_comparison=None
                                elif onnx is not None:
                                    recognized, warning = onnx.recognize(image)
                                    current_comparison = None
                                    if backend == "onnx_verify":
                                        from .quality import compare_ocr
                                        checkpoint()
                                        primary, primary_warning = _run_ocr(image, checkpoint, progress,
                                                                           actual_dpi, executable, data_dir,languages=languages)
                                        current_comparison = compare_ocr(primary, recognized)
                                        recognized = primary
                                        warning = current_comparison.warning
                                        if primary_warning:
                                            warning += " " + primary_warning
                                else:
                                    recognized, warning = _run_ocr(image, checkpoint, progress, actual_dpi,
                                                                   executable, data_dir,languages=languages)
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
                        from .tables import render_table
                        from .borderless import infer_tables
                        from .table_continuation import TableFragment, boundary_text, possible_continuation
                        tables = page.find_tables()
                        entries=[];filtered=page
                        for number,table in enumerate(sorted(tables,key=lambda table:(table.bbox[1],table.bbox[0])),1):
                            rendered=render_table(page,table,checkpoint)
                            filtered=filtered.filter(lambda obj,claimed=rendered.claimed_char_ids:id(obj) not in claimed)
                            warnings.append(rendered.warning)
                            if rendered.text:
                                entries.append((f'p{index+1}-t{number}','source-table',table.bbox,rendered))
                        analysis=infer_tables(filtered,checkpoint)
                        warnings.extend(analysis.warnings)
                        for number,table in enumerate(analysis.tables,1):
                            entries.append((f'p{index+1}-b{number}','inferred-borderless-table',table.bbox,table))
                            filtered=filtered.filter(lambda obj,claimed=table.claimed_char_ids:id(obj) not in claimed)
                        # 有框線與無框線共用保守頁界規則；多個候選或幾何不明時不自動關聯。
                        top_candidates=sum(bbox[1]<=page.height*0.12 for _,_,bbox,_ in entries)
                        tail_candidates=sum(bbox[3]>=page.height*0.9 for _,_,bbox,_ in entries)
                        blocks=[]
                        for identifier,kind,bbox,rendered in entries:
                            comment=f'<!-- {kind}: {identifier} -->\n\n'
                            if rendered.column_edges:
                                fragment=TableFragment(index+1,identifier,page.width,page.height,bbox,
                                                       rendered.column_edges,rendered.first_row,rendered.row_count,
                                                       boundary_text(page,bbox,False))
                                if top_candidates==1 and possible_continuation(previous_tail,fragment):
                                    comment+=f'<!-- possible-table-continuation: {previous_tail.identifier} -> {identifier} -->\n\n'
                                    warnings.append(f'本表可能接續第 {previous_tail.page} 頁表格：欄位與表頭吻合。各頁原文與重複表頭保留，未自動合併。')
                                if tail_candidates==1 and bbox[3]>=page.height*0.9:
                                    next_tail=TableFragment(index+1,identifier,page.width,page.height,bbox,
                                                           rendered.column_edges,rendered.first_row,rendered.row_count,
                                                           boundary_text(page,bbox,True))
                            blocks.append((bbox[1],comment+rendered.text))
                        if entries or tables:
                            blocks.extend((line['top'],line['text']) for line in filtered.extract_text_lines())
                            text='\n\n'.join(value for _,value in sorted(blocks,key=lambda item:item[0]))
                        elif analysis.words is not None:
                            text,column_warning=_native_columns(page,text,analysis.words,checkpoint)
                            if column_warning:warnings.append(column_warning)
                    reports.append({"page": index+1, "route": route, "warnings": warnings})
                    component=managed.provenance if route=='ocr' and managed is not None else None
                    if component: reports[-1]['component']=component
                    checkpoint()
                    yield f"<!-- source-page: {index+1}; route: {route} -->\n\n"
                    if route=='ocr' and backend=='tesseract' and languages is not None:
                        yield '<!-- source-ocr-languages: '+'+'.join(languages)+' -->\n\n'
                    if component:
                        yield (f"<!-- source-component: {component['component_id']}; version: {component['version']}; "
                               f"protocol: {component['protocol']}; device: {component['device']} -->\n\n")
                    for warning in warnings:
                        yield f"> ⚠ 第 {index+1} 頁：{warning}\n\n"
                    yield text.strip() + "\n\n"
                finally:
                    previous_tail=next_tail
                    page.close()
    finally:
        if onnx is not None:
            onnx.close()
        if renderer is not None:
            renderer.close()

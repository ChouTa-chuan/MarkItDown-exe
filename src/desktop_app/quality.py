"""回報 OCR 差異並保留兩引擎原文；不自行補字、修字或繁簡轉換。"""
from dataclasses import dataclass
from difflib import SequenceMatcher
from html import escape


@dataclass(frozen=True)
class OCRComparison:
    primary: str
    candidate: str
    agrees: bool
    changed_regions: int | None

    @property
    def warning(self):
        if not self.primary.strip() or not self.candidate.strip():
            return "至少一個引擎未辨識出文字，交叉核對未完成；請核對原頁。"
        if self.agrees:
            return "兩引擎文字一致（忽略空白）；一致不代表正確，仍需核對原頁。"
        difference = f"{self.changed_regions} 處文字差異" if self.changed_regions is not None else "文字不一致（長頁未逐區對齊）"
        return f"兩引擎有{difference}；採 Tesseract 原始結果，保留 ONNX 候選供核對，未自動修字。"

    def evidence_markdown(self):
        if self.agrees and self.primary.strip():
            return ""
        return ("\n\n<details><summary>交叉核對：兩引擎原始文字</summary>\n\n"
                "<p>Tesseract（主要結果）</p><pre>" + escape(self.primary) +
                "</pre><p>ONNX（候選結果）</p><pre>" + escape(self.candidate) +
                "</pre></details>\n")


def compare_ocr(primary, candidate):
    left, right = ("".join(text.split()) for text in (primary, candidate))
    if left == right:
        return OCRComparison(primary, candidate, True, 0)
    # 長篇或重複文字只限制差異對齊成本；即使不列出逐區差異，仍保留完整兩份原文。
    regions = None if max(len(left),len(right)) > 10000 else sum(
        tag != "equal" for tag, *_ in SequenceMatcher(None,left,right,autojunk=True).get_opcodes())
    return OCRComparison(primary, candidate, left == right, regions)

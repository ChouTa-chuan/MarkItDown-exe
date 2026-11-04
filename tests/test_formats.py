"""Integration fixtures are generated locally, never downloaded user documents."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

from desktop_app.application import Runner
from desktop_app.core import Request, State
from desktop_app.resources import MIB, Policy, Snapshot


@unittest.skipUnless(importlib.util.find_spec("markitdown"), "Install the vendored MarkItDown first")
class FormatTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)

    def convert(self, source):
        destination = self.root / (source.name + ".md")
        runner = Runner(Policy(budget=2048*MIB, reserve=0),
                        read_snapshot=lambda: Snapshot(8192*MIB, 4096*MIB, 200*MIB))
        outcome = runner.run(Request(source, destination))
        self.assertEqual(outcome.state, State.COMPLETED, outcome.message)
        return destination.read_text(encoding="utf-8")

    def test_docx_heading_and_table(self):
        from docx import Document
        document = Document()
        document.add_heading("繁體中文標題", level=1)
        document.add_paragraph("文件內容測試")
        table = document.add_table(rows=2, cols=2)
        for row, values in zip(table.rows, [("項目", "金額"), ("測試", "123")]):
            for cell, value in zip(row.cells, values):
                cell.text = value
        source = self.root / "中文.docx"
        document.save(source)
        markdown = self.convert(source)
        for expected in ["# 繁體中文標題", "文件內容測試", "項目", "123"]:
            self.assertIn(expected, markdown)

    def test_pptx_title_and_content(self):
        from pptx import Presentation
        presentation = Presentation()
        slide = presentation.slides.add_slide(presentation.slide_layouts[1])
        slide.shapes.title.text = "簡報標題"
        slide.placeholders[1].text = "簡報內容"
        source = self.root / "簡報.pptx"
        presentation.save(source)
        markdown = self.convert(source)
        self.assertIn("簡報標題", markdown)
        self.assertIn("簡報內容", markdown)

    def test_xlsx_sheet_and_values(self):
        from openpyxl import Workbook
        book = Workbook()
        sheet = book.active
        sheet.title = "工作表"
        sheet.append(["名稱", "數量"])
        sheet.append(["產品", 42])
        source = self.root / "資料.xlsx"
        book.save(source)
        markdown = self.convert(source)
        for expected in ["工作表", "名稱", "產品", "42"]:
            self.assertIn(expected, markdown)

    def test_html_structure(self):
        source = self.root / "網頁.html"
        source.write_text('<html><meta charset="utf-8"><h1>測試標題</h1><p>內文</p><ul><li>項目</li></ul></html>', encoding="utf-8")
        markdown = self.convert(source)
        self.assertIn("# 測試標題", markdown)
        self.assertIn("項目", markdown)

    def test_text_pdf(self):
        from reportlab.pdfgen import canvas
        source = self.root / "文件.pdf"
        document = canvas.Canvas(str(source))
        document.drawString(72, 750, "Document conversion smoke test")
        document.drawString(72, 720, "Invoice total 12345")
        document.save()
        markdown = self.convert(source)
        self.assertIn("Document conversion smoke test", markdown)
        self.assertIn("12345", markdown)

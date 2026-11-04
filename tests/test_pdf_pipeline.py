import importlib.util
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from desktop_app.conversion import convert_document
from desktop_app.core import Request
from desktop_app.core import Cancelled
from desktop_app.pdf_pipeline import decide_page


class PageDecisionTests(unittest.TestCase):
    def test_scan_routes_to_ocr(self):
        self.assertEqual(decide_page(1, "", 0.9).route, "ocr")

    def test_short_native_title_does_not_require_ocr(self):
        self.assertEqual(decide_page(1, "目錄", 0).route, "native")

    def test_blank_page(self):
        self.assertEqual(decide_page(1, "", 0).route, "blank")

    def test_bad_encoding_requests_ocr(self):
        self.assertEqual(decide_page(1, "(cid:123)"*10, 0).route, "ocr")

    def test_mixed_content_has_warning(self):
        self.assertTrue(decide_page(1, "good text "*20, 0.5).warnings)


@unittest.skipUnless(importlib.util.find_spec("pdfplumber"), "Install precise PDF dependencies")
class PdfPipelineTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.source = self.root / "測試.pdf"
        self.destination = self.root / "結果.md"

    def convert(self):
        summary = convert_document(Request(self.source, self.destination), lambda: None)
        return summary, self.destination.read_text(encoding="utf-8")

    def make_scan(self, chinese=False, mixed=False):
        from PIL import Image, ImageDraw, ImageFont
        from reportlab.pdfgen import canvas
        image = Image.new("RGB", (1600, 600), "white")
        draw = ImageDraw.Draw(image)
        if chinese:
            font_path = os.environ.get("TEST_CJK_FONT", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc")
            if not Path(font_path).exists():
                self.skipTest("CJK sample font not configured")
            font = ImageFont.truetype(font_path, 72)
            text = "繁體中文文件測試\n會議紀錄與資料轉換"
        else:
            font_path = os.environ.get("TEST_LATIN_FONT", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
            if not Path(font_path).exists():
                self.skipTest("Latin sample font not configured")
            font = ImageFont.truetype(font_path, 72)
            text = "DOCUMENT SCAN TEST\nInvoice total 12345"
        draw.multiline_text((80, 100), text, fill="black", font=font, spacing=30)
        bitmap = self.root / "scan.png"
        image.save(bitmap)
        image.close()
        document = canvas.Canvas(str(self.source), pagesize=(800, 600))
        if mixed:
            document.drawString(40, 500, "Native first page with useful text content")
            document.showPage()
        # Preserve aspect ratio; stretching glyphs to twice their natural
        # height is a different distortion benchmark, not a clean scan fixture.
        document.drawImage(str(bitmap), 0, 150, width=800, height=300)
        document.save()

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract not installed")
    def test_english_scan_and_native_page_are_routed_separately(self):
        self.make_scan(mixed=True)
        summary, markdown = self.convert()
        self.assertIn("分析 2 頁，OCR 1 頁", summary)
        self.assertIn("Native first page", markdown)
        self.assertIn("DOCUMENT SCAN TEST", markdown)
        self.assertIn("12345", markdown)
        self.assertEqual(markdown.count("DOCUMENT SCAN TEST"), 1)

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract not installed")
    def test_traditional_chinese_scan(self):
        import subprocess
        if "chi_tra" not in subprocess.run(["tesseract", "--list-langs"], capture_output=True, text=True).stdout:
            self.skipTest("Traditional Chinese OCR model not installed")
        self.make_scan(chinese=True)
        summary, markdown = self.convert()
        compact = "".join(markdown.split())
        self.assertIn("繁體中文", compact)
        self.assertIn("會議紀錄", compact)
        self.assertIn("OCR 1 頁", summary)

    @unittest.skipUnless(shutil.which("tesseract"), "Tesseract not installed")
    def test_explicit_paths_work_without_environment_variable(self):
        data_dir = os.environ.get("TESSDATA_PREFIX")
        if not data_dir:
            self.skipTest("Explicit model directory not configured for integration test")
        self.make_scan()
        with patch.dict(os.environ):
            os.environ.pop("TESSDATA_PREFIX", None)
            request = Request(self.source, self.destination, ocr_executable=shutil.which("tesseract"),
                              ocr_data_dir=data_dir)
            convert_document(request, lambda: None)
        self.assertIn("DOCUMENT SCAN TEST", self.destination.read_text(encoding="utf-8"))

    def test_missing_ocr_engine_fails_without_partial_output(self):
        self.make_scan()
        with patch("desktop_app.pdf_pipeline.shutil.which", return_value=None):
            with self.assertRaisesRegex(RuntimeError, "找不到 Tesseract"):
                self.convert()
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    def test_native_table_extracted_without_duplicate_cells(self):
        from reportlab.pdfgen import canvas
        document = canvas.Canvas(str(self.source))
        for y in (700, 730, 760):
            document.line(50, y, 350, y)
        for x in (50, 200, 350):
            document.line(x, 700, x, 760)
        document.drawString(60, 740, "Item")
        document.drawString(210, 740, "Amount")
        document.drawString(60, 710, "Product")
        document.drawString(210, 710, "12345")
        document.save()
        _, markdown = self.convert()
        self.assertIn("| Item | Amount |", markdown)
        self.assertEqual(markdown.count("Product"), 1)

    def test_ocr_retry_is_bounded_and_warns(self):
        self.make_scan()
        with patch("desktop_app.pdf_pipeline._run_ocr", return_value=("", None)) as engine:
            _, markdown = self.convert()
        self.assertEqual(engine.call_count, 2)
        self.assertIn("OCR 未辨識出文字", markdown)

    def test_two_columns_read_left_then_right(self):
        from reportlab.pdfgen import canvas
        document = canvas.Canvas(str(self.source), pagesize=(600, 800))
        for index in range(6):
            document.drawString(40, 700-index*30, f"Left column line {index}")
            document.drawString(360, 700-index*30, f"Right column line {index}")
        document.save()
        _, markdown = self.convert()
        self.assertLess(markdown.index("Left column line 5"), markdown.index("Right column line 0"))
        self.assertIn("左欄再右欄", markdown)

    def test_cancel_during_pdf_export_cleans_output(self):
        from reportlab.pdfgen import canvas
        document = canvas.Canvas(str(self.source))
        document.drawString(72, 700, "Cancel this PDF conversion")
        document.save()
        calls = 0
        def checkpoint():
            nonlocal calls
            calls += 1
            if calls == 4:
                raise Cancelled()
        with self.assertRaises(Cancelled):
            convert_document(Request(self.source, self.destination), checkpoint)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    @unittest.skipUnless(shutil.which("tesseract") and importlib.util.find_spec("markitdown"),
                         "Tesseract and MarkItDown are required")
    def test_scan_improves_over_native_baseline(self):
        from markitdown import MarkItDown
        self.make_scan()
        baseline = MarkItDown(enable_plugins=False).convert_local(str(self.source)).text_content
        _, improved = self.convert()
        self.assertNotIn("DOCUMENT SCAN TEST", baseline)
        self.assertIn("DOCUMENT SCAN TEST", improved)

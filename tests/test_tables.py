import importlib.util
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from desktop_app.core import Request, Cancelled
from desktop_app.conversion import convert_document
from desktop_app.tables import render_table


@unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
class TableGeometryTests(unittest.TestCase):
    def test_overlap_does_not_discard_source(self):
        table=SimpleNamespace(cells=[(0,0,20,20),(10,0,30,20)])
        result=render_table(SimpleNamespace(chars=[]),table)
        self.assertEqual(result.text,'')
        self.assertFalse(result.claimed_char_ids)
        self.assertIn('保留原生文字',result.warning)

    def test_large_sparse_grid_is_bounded(self):
        table=SimpleNamespace(cells=[(i*20,i*20,i*20+10,i*20+10) for i in range(200)])
        result=render_table(SimpleNamespace(chars=[]),table)
        self.assertEqual(result.text,'')
        self.assertFalse(result.claimed_char_ids)

    def test_cancel_during_geometry_processing(self):
        with self.assertRaises(Cancelled):
            render_table(SimpleNamespace(chars=[]),SimpleNamespace(cells=[(0,0,20,20)]),
                         lambda:(_ for _ in ()).throw(Cancelled()))

    def test_invalid_coordinates_keep_source_text(self):
        for box in [(0,0,float('nan'),20),(20,0,0,20)]:
            result=render_table(SimpleNamespace(chars=[]),SimpleNamespace(cells=[box]))
            self.assertFalse(result.claimed_char_ids)
            self.assertEqual(result.text,'')


@unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
class TablePDFTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.source=self.root/'table.pdf';self.output=self.root/'table.md'

    def convert(self):
        convert_document(Request(self.source,self.output),lambda:None)
        return self.output.read_text(encoding='utf-8')

    def merged(self,header='MergedHeader'):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source))
        pdf.drawString(50,810,'INTRO_BEFORE')
        for x in (50,350):pdf.line(x,660,x,780)
        pdf.line(200,660,200,740)
        for y in (660,740,780):pdf.line(50,y,350,y)
        pdf.line(200,700,350,700)
        pdf.drawString(60,755,header)
        pdf.drawString(60,715,'RowSpanText')
        pdf.drawString(210,715,'RightTop')
        pdf.drawString(210,675,'RightBottom')
        pdf.drawString(50,630,'AFTER_FOOTNOTE')
        pdf.save()

    def test_row_and_column_spans_and_order(self):
        self.merged();markdown=self.convert()
        self.assertIn('colspan="2"',markdown)
        self.assertIn('rowspan="2"',markdown)
        for text in ['MergedHeader','RowSpanText','RightTop','RightBottom']:
            self.assertEqual(markdown.count(text),1,text)
        self.assertLess(markdown.index('INTRO_BEFORE'),markdown.index('<table>'))
        self.assertLess(markdown.index('</table>'),markdown.index('AFTER_FOOTNOTE'))

    def test_html_content_is_escaped(self):
        self.merged('<script>x</script>');markdown=self.convert()
        self.assertNotIn('<script>',markdown)
        self.assertIn('&lt;script&gt;x&lt;/script&gt;',markdown)

    def test_text_in_non_cell_gap_is_preserved(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source))
        for x in (50,200):pdf.line(x,700,x,780)
        pdf.line(350,700,350,740)
        pdf.line(50,780,200,780)
        for y in (700,740):pdf.line(50,y,350,y)
        pdf.drawString(60,755,'Header')
        pdf.drawString(60,715,'LeftCell')
        pdf.drawString(210,715,'RightCell')
        pdf.drawString(220,755,'KEEP_GAP')
        pdf.save();markdown=self.convert()
        for text in ['Header','LeftCell','RightCell','KEEP_GAP']:
            self.assertEqual(markdown.count(text),1,text)

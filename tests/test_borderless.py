import importlib.util
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from desktop_app.borderless import numeric,infer_tables
from desktop_app.conversion import convert_document
from desktop_app.core import Request,Cancelled


class NumericEvidenceTests(unittest.TestCase):
    def test_numeric_cell_does_not_accept_prose_or_unbalanced_parentheses(self):
        for value in ['123.45','(200)','$1,250','30%']:
            self.assertTrue(numeric(value),value)
        for value in ['Invoice 123','(123','123)','1A','Total']:
            self.assertFalse(numeric(value),value)

    def test_word_limit_skips_further_layout_analysis(self):
        page=SimpleNamespace(extract_words=lambda:[{}]*20001)
        result=infer_tables(page)
        self.assertFalse(result.tables)
        self.assertIsNone(result.words)
        self.assertIn('上限',result.warnings[0])

    def test_analysis_cancelled_at_checkpoint(self):
        page=SimpleNamespace(width=600,chars=[],extract_words=lambda:[{'top':50,'bottom':60,'x0':20,'x1':40,'text':'test'}])
        with self.assertRaises(Cancelled):
            infer_tables(page,lambda:(_ for _ in ()).throw(Cancelled()))

    def test_sparse_candidate_search_has_global_work_limit(self):
        words=[{'x0':x,'x1':x+20,'top':row*10,'bottom':row*10+8,'text':'Text'}
               for row in range(1100) for x in (20,200,400)]
        result=infer_tables(SimpleNamespace(width=600,chars=[],extract_words=lambda:words))
        self.assertFalse(result.tables)
        self.assertIn('詞比對上限',''.join(result.warnings))


@unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
class BorderlessPDFTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.source=self.root/'borderless.pdf';self.output=self.root/'out.md'

    def convert(self):
        convert_document(Request(self.source,self.output),lambda:None)
        return self.output.read_text(encoding='utf-8')

    def make_table(self,right_aligned=False,frame=False):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        pdf.drawString(50,760,'INTRO_TEXT')
        rows=[('Item','Qty','Amount'),('Alpha','2','123.45'),('Beta','5','9000')]
        for index,row in enumerate(rows):
            y=700-index*30
            pdf.drawString(50,y,row[0]);pdf.drawString(300,y,row[1])
            if right_aligned:pdf.drawRightString(550,y,row[2])
            else:pdf.drawString(450,y,row[2])
        pdf.drawString(50,600,'AFTER_TEXT')
        if frame:
            for x in (50,300,550):pdf.line(x,300,x,400)
            for y in (300,350,400):pdf.line(50,y,550,y)
            pdf.drawString(60,370,'Framed');pdf.drawString(310,370,'Value')
            pdf.drawString(60,320,'Cell');pdf.drawString(310,320,'42')
        pdf.save()

    def test_three_columns_numeric_data_and_prose(self):
        self.make_table();text=self.convert()
        self.assertIn('inferred-borderless-table: p1-b1',text)
        self.assertIn('| Item | Qty | Amount |',text)
        self.assertIn('| Alpha | 2 | 123.45 |',text)
        for value in ['Alpha','Beta','123.45','9000']:
            self.assertEqual(text.count(value),1)
        self.assertLess(text.index('INTRO_TEXT'),text.index('| Item'))
        self.assertLess(text.index('9000'),text.index('AFTER_TEXT'))

    def test_right_aligned_numeric_column(self):
        self.make_table(right_aligned=True);text=self.convert()
        self.assertIn('| Beta | 5 | 9000 |',text)

    def test_framed_and_borderless_on_same_page(self):
        self.make_table(frame=True);text=self.convert()
        self.assertIn('source-table: p1-t1',text)
        self.assertIn('inferred-borderless-table: p1-b1',text)
        self.assertEqual(text.count('Alpha'),1)
        self.assertEqual(text.count('Framed'),1)

    def test_two_column_article_is_not_a_table(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        for i in range(6):
            pdf.drawString(40,700-i*30,f'Left article line {i}')
            pdf.drawString(360,700-i*30,f'Right article line {i}')
        pdf.save();text=self.convert()
        self.assertNotIn('inferred-borderless-table:',text)
        self.assertIn('Left article line 5',text);self.assertIn('Right article line 0',text)

    def test_numeric_first_row_is_not_assumed_header(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        for i in range(3):
            pdf.drawString(50,700-i*30,str(2024+i));pdf.drawString(400,700-i*30,str(500+i))
        pdf.save();text=self.convert()
        self.assertNotIn('inferred-borderless-table:',text)
        self.assertIn('2024',text);self.assertIn('502',text)

    def test_short_or_misaligned_data_keeps_text(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        for i,(left,right) in enumerate([('Item','Amount'),('Alpha','100'),('Beta','200')]):
            pdf.drawString(50,700-i*30,left);pdf.drawString(400+i*10,700-i*30,right)
        pdf.save();text=self.convert()
        self.assertNotIn('inferred-borderless-table:',text)
        self.assertIn('Alpha',text);self.assertIn('200',text)

    def test_two_column_numeric_table(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        for i,(left,right) in enumerate([('Item','Amount'),('Alpha','100'),('Beta','200')]):
            pdf.drawString(50,700-i*30,left);pdf.drawString(400,700-i*30,right)
        pdf.save();text=self.convert()
        self.assertIn('| Item | Amount |',text)
        self.assertIn('| Beta | 200 |',text)

    def test_upstream_sparse_fixture_preserves_data_without_fake_single_column(self):
        self.source=Path(__file__).parent/'fixtures/upstream-sparse.pdf'
        text=self.convert()
        for value in ['INVENTORY RECONCILIATION REPORT','SKU-8847','SKU-9201','Electronics','Hardware',
                      'Variance Analysis:','Recommendations:']:
            self.assertIn(value,text)
        self.assertNotIn('| Product Code Location Expected Actual Variance Status |',text)
        self.assertEqual(text.count('Variance Analysis:'),1)

    def test_upstream_sparse_table_exact_cells_and_empty_positions(self):
        self.source=Path(__file__).parent/'fixtures/upstream-sparse.pdf'
        text=self.convert()
        rows=[[cell.strip() for cell in line.strip().strip('|').split('|')]
              for line in text.splitlines() if line.strip().startswith('|')]
        expected=[
            ['Product Code','Location','Expected','Actual','Variance','Status'],
            ['SKU-8847','A-12','450','','',''],
            ['','B-07','','289','-23',''],
            ['SKU-9201','','780','778','','OK'],
            ['','C-15','','','+15',''],
            ['SKU-4563','D-22','','156','','CRITICAL'],
            ['','','180','','-24',''],
            ['SKU-7728','A-08','920','','',''],
            ['','','','935','+15','OK'],
        ]
        start=rows.index(expected[0])
        self.assertEqual(rows[start+2:start+10],expected[1:])
        self.assertEqual(sum(row[0]=='SKU-8847' for row in rows),2) # one per source table
        self.assertLess(text.index('935'),text.index('Variance Analysis:'))

    def test_sparse_text_columns_without_numeric_evidence_remain_prose(self):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        for index,row in enumerate([('Name','Region','Status'),('Alice','','Ready'),('','West','Pending')]):
            for x,value in zip((50,250,450),row):
                if value:pdf.drawString(x,700-index*30,value)
        pdf.save();text=self.convert()
        self.assertNotIn('inferred-borderless-table:',text)
        for value in ('Alice','West','Pending'):self.assertIn(value,text)

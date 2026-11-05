from dataclasses import replace
import importlib.util
from pathlib import Path
import tempfile
import unittest

from desktop_app.table_continuation import TableFragment,possible_continuation,boundary_has_content
from desktop_app.core import Request
from desktop_app.conversion import convert_document

PREVIOUS=TableFragment(1,'p1-t1',600,800,(50,680,550,780),(50,300,550),('Item','Amount'),2,'1')
CURRENT=TableFragment(2,'p2-t1',600,800,(50,40,550,140),(50,300,550),('Item','Amount'),2,'Page 2 of 3')


class ContinuationRulesTests(unittest.TestCase):
    def test_matching_header_and_geometry(self):
        self.assertTrue(possible_continuation(PREVIOUS,CURRENT))

    def test_changed_header_is_not_linked(self):
        self.assertFalse(possible_continuation(PREVIOUS,replace(CURRENT,header=('Other','Amount'))))

    def test_changed_columns_are_not_linked(self):
        self.assertFalse(possible_continuation(PREVIOUS,replace(CURRENT,columns=(50,320,550))))

    def test_skipped_page_is_not_linked(self):
        self.assertFalse(possible_continuation(PREVIOUS,replace(CURRENT,page=3)))

    def test_table_away_from_boundary_is_not_linked(self):
        self.assertFalse(possible_continuation(replace(PREVIOUS,bbox=(50,300,550,500)),CURRENT))

    def test_intervening_prose_is_not_linked(self):
        self.assertFalse(possible_continuation(PREVIOUS,replace(CURRENT,boundary_text='New Section')))

    def test_numeric_first_row_is_not_assumed_to_be_header(self):
        self.assertFalse(possible_continuation(replace(PREVIOUS,header=('100','200')),replace(CURRENT,header=('100','200'))))

    def test_only_page_number_lines_are_ignored(self):
        self.assertFalse(boundary_has_content('第 2 頁\n2 / 3\nPage 2 of 3'))
        self.assertTrue(boundary_has_content('Total 200'))

    def test_header_without_body_is_not_linked(self):
        self.assertFalse(possible_continuation(PREVIOUS,replace(CURRENT,rows=1)))


@unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
class CrossPagePDFTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.source=self.root/'cross-page.pdf';self.output=self.root/'output.md'

    def make_document(self,header='Item',middle=300,prose=False,blank=False,multiple=False):
        from reportlab.pdfgen import canvas
        pdf=canvas.Canvas(str(self.source),pagesize=(600,800))
        def table(bottom,first,label,xs=(50,300,550)):
            for x in xs:pdf.line(x,bottom,x,bottom+100)
            for y in (bottom,bottom+50,bottom+100):pdf.line(xs[0],y,xs[-1],y)
            pdf.drawString(xs[0]+10,bottom+70,first);pdf.drawString(xs[1]+10,bottom+70,'Amount')
            # Fit labels within narrow cells; overflowing text is a different
            # ambiguity fixture, not evidence of dropped table content.
            pdf.setFont('Helvetica',8)
            pdf.drawString(xs[0]+10,bottom+20,label);pdf.drawString(xs[1]+10,bottom+20,'12345')
            pdf.setFont('Helvetica',12)
        table(20,'Item','DATA_PAGE_ONE');pdf.drawString(280,7,'1');pdf.showPage()
        if blank:pdf.showPage()
        if prose:pdf.drawString(50,785,'New Section')
        if multiple:
            table(660,header,'DATA_PAGE_TWO',(30,140,250))
            table(660,'Other','SEPARATE',(320,430,540))
        else:
            table(660,header,'DATA_PAGE_TWO',(50,middle,550))
        pdf.drawString(50,600,'AFTER_TABLE');pdf.save()

    def convert(self):
        convert_document(Request(self.source,self.output),lambda:None)
        return self.output.read_text(encoding='utf-8')

    def test_possible_continuation_preserves_both_headers_and_rows(self):
        self.make_document();text=self.convert()
        self.assertIn('possible-table-continuation: p1-t1 -> p2-t1',text)
        self.assertIn('可能接續第 1 頁',text)
        self.assertEqual(text.count('| Item | Amount |'),2)
        for value in ['DATA_PAGE_ONE','DATA_PAGE_TWO','AFTER_TABLE']:
            self.assertEqual(text.count(value),1)
        self.assertIn('source-page: 1',text);self.assertIn('source-page: 2',text)

    def test_different_header_not_linked(self):
        self.make_document(header='Different');self.assertNotIn('possible-table-continuation:',self.convert())

    def test_different_column_geometry_not_linked(self):
        self.make_document(middle=330);self.assertNotIn('possible-table-continuation:',self.convert())

    def test_new_section_blocks_link(self):
        self.make_document(prose=True);text=self.convert()
        self.assertNotIn('possible-table-continuation:',text)
        self.assertIn('New Section',text)

    def test_blank_page_resets_candidate(self):
        self.make_document(blank=True);text=self.convert()
        self.assertNotIn('possible-table-continuation:',text)
        self.assertIn('source-page: 3',text)

    def test_multiple_top_tables_not_linked(self):
        self.make_document(multiple=True);text=self.convert()
        self.assertNotIn('possible-table-continuation:',text)
        self.assertIn('DATA_PAGE_TWO',text);self.assertIn('SEPARATE',text)

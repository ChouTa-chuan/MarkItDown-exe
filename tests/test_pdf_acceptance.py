"""Fixed upstream fixtures: content conservation plus independent structural targets.

Character counts ignore whitespace/punctuation; they are an omission/duplication
alarm, not proof of reading order, linguistic accuracy or table correctness.
"""
from collections import Counter
from html.parser import HTMLParser
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unicodedata
import unittest

from desktop_app.conversion import convert_document
from desktop_app.core import Request

FIXTURES=Path(__file__).parent/'fixtures'


class PlainText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]

    def handle_data(self,data):
        self.parts.append(data)


def content_counts(markdown):
    # Remove only app-generated metadata/warnings, not arbitrary source text.
    content='\n'.join(line for line in markdown.splitlines()
                      if not line.startswith(('<!--','> ⚠')))
    parser=PlainText();parser.feed(content);parser.close()
    return Counter(char for char in unicodedata.normalize('NFKC',''.join(parser.parts)) if char.isalnum())


@unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
class PublicPDFAcceptanceTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.output=Path(temporary.name)/'output.md'

    def convert(self,name,pages,characters):
        import pdfplumber
        source=FIXTURES/name
        executable=os.environ.get('MARKITDOWN_ACCEPTANCE_EXECUTABLE')
        if executable:
            subprocess.run([executable,'--cli',str(source),str(self.output),'--reserve-mib','0',
                            '--ram-budget-mib','2048'],check=True,timeout=120,capture_output=True)
        else:convert_document(Request(source,self.output),lambda:None)
        text=self.output.read_text(encoding='utf-8')
        with pdfplumber.open(source) as document:
            self.assertEqual(len(document.pages),pages)
            reference=Counter(char for char in unicodedata.normalize('NFKC',
                              ''.join(c['text'] for page in document.pages for c in page.chars)) if char.isalnum())
        self.assertEqual(reference.total(),characters)
        self.assertEqual(content_counts(text),reference,'Alphanumeric content omitted or duplicated')
        self.assertEqual(text.count('route: native -->'),pages)
        self.assertEqual(text.count('<!-- source-page:'),pages)
        return text

    def assert_order(self,text,anchors):
        positions=[text.index(value) for value in anchors]
        self.assertEqual(positions,sorted(positions))

    def test_sparse_inventory_exact_structure_and_content(self):
        text=self.convert('upstream-sparse.pdf',2,1397)
        rows=[[cell.strip() for cell in line.strip().strip('|').split('|')]
              for line in text.splitlines() if line.startswith('|')]
        expected=[
            ['Product Code','Location','Expected','Actual','Variance','Status'],
            ['SKU-8847','A-12','450','','',''],['','B-07','','289','-23',''],
            ['SKU-9201','','780','778','','OK'],['','C-15','','','+15',''],
            ['SKU-4563','D-22','','156','','CRITICAL'],['','','180','','-24',''],
            ['SKU-7728','A-08','920','','',''],['','','','935','+15','OK'],
        ]
        start=rows.index(expected[0]);self.assertEqual(rows[start+2:start+10],expected[1:])
        second=['Product Code','Category','Unit Cost','Total Value','Last Audit','Notes']
        start=rows.index(second)
        expected_second=[
            ['SKU-8847','Electronics','$45.00','$13,005.00','2024-10-15',''],
            ['SKU-9201','Hardware','$32.50','$25,285.00','2024-10-22','Verified'],
            ['SKU-4563','Software','$120.00','$18,720.00','','Critical'],
            ['SKU-7728','Accessories','$15.75','$14,726.25','2024-11-01',''],
            ['SKU-3345','Electronics','$67.00','$22,445.00','2024-10-18',''],
            ['SKU-5512','Hardware','$89.00','$31,150.00','','Pending'],
            ['SKU-6678','Software','$200.00','$42,000.00','2024-10-25','High Value'],
            ['SKU-7789','Accessories','$8.50','$5,950.00','2024-11-05',''],
            ['SKU-2234','Electronics','$125.00','$35,000.00','',''],
            ['SKU-1123','Hardware','$55.00','$27,500.00','2024-10-30','Verified'],
        ]
        self.assertEqual(rows[start+2:start+12],expected_second)
        self.assert_order(text,['INVENTORY RECONCILIATION REPORT','| Product Code | Location',
                               'Variance Analysis:','source-page: 2','Extended Inventory Review:',
                               '| Product Code | Category','Recommendations:','Approval:'])
        self.assertNotIn('possible-table-continuation:',text)

    def test_multipage_repair_preserves_people_totals_and_disclaimer(self):
        text=self.convert('upstream-repair.pdf',3,2188)
        pages=text.split('<!-- source-page:')[1:]
        for page,name,total in [(pages[0],'Gabriel Diaz','5,738'),(pages[1],'Bruce Wayne','211,522')]:
            self.assertIn(name,page)
            self.assertIn('GRAND TOTAL '+total,page)
            self.assertIn('colspan="3"',page)
            self.assert_order(page,['Customer Information','Insured name','Estimate Totals','GRAND TOTAL'])
        self.assertNotIn('Bruce Wayne',pages[0]);self.assertNotIn('Gabriel Diaz',pages[1])
        self.assertIn('This is a preliminary estimate',pages[2])
        # Shared stationery is not evidence of a continued line-item table.
        self.assertNotIn('possible-table-continuation:',text)

    def test_receipt_preserves_money_signs_discount_order_and_payment(self):
        text=self.convert('upstream-receipt.pdf',1,905)
        self.assert_order(text,['TECHMART ELECTRONICS','AUDIO-5521 1 @ $349.99',
                               'Member Discount $-50.00','$299.99','ACC-8834 2 @ $79.99',
                               'Member Discount (15%)-$84.00','Sales Tax (8.5%) $66.23',
                               'Rewards Applied -$25.00','TOTAL $821.14','Visa Card ending in 4782','RETURN POLICY'])
        self.assertEqual(text.count('TOTAL $821.14'),1)
        self.assertNotIn('inferred-borderless-table:',text)

    def test_article_preserves_paragraph_and_list_order(self):
        text=self.convert('upstream-article.pdf',1,4254)
        self.assert_order(text,['1 Introduction','Our insight','While there is contemporaneous',
                               '1 Customizableandconversableagents.','2 Conversationprogramming.'])
        self.assertNotIn('inferred-borderless-table:',text)

    def test_added_fixture_provenance_matches_vendored_commit(self):
        metadata=json.loads((FIXTURES/'PUBLIC-PDFS.json').read_text())
        vendored=json.loads((FIXTURES.parents[1]/'vendor/markitdown/UPSTREAM.json').read_text())
        self.assertEqual(metadata['commit'],vendored['commit'])
        for name,item in metadata['files'].items():
            self.assertEqual(hashlib.sha256((FIXTURES/name).read_bytes()).hexdigest(),item['sha256'])

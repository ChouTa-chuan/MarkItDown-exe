import unittest
from desktop_app.quality import compare_ocr


class CrossCheckTests(unittest.TestCase):
    def test_ignores_whitespace_only(self):
        result=compare_ocr('繁體\n中文','繁體 中文')
        self.assertTrue(result.agrees)
        self.assertIn('一致不代表正確',result.warning)

    def test_does_not_repair_or_convert_characters(self):
        result=compare_ocr('不可批准 1000','可以批准 100O')
        self.assertFalse(result.agrees)
        self.assertEqual(result.primary,'不可批准 1000')
        self.assertEqual(result.candidate,'可以批准 100O')
        self.assertIn('未自動修字',result.warning)

    def test_preserves_traditional_variant_difference(self):
        self.assertFalse(compare_ocr('資料轉換','资料转换').agrees)

    def test_html_escaped_in_evidence(self):
        output=compare_ocr('<script>x</script>','<img src="x">').evidence_markdown()
        self.assertNotIn('<script>',output)
        self.assertNotIn('<img ',output)
        self.assertIn('&lt;script&gt;',output)

    def test_empty_output_not_called_verified(self):
        for left,right in [('', ''),('', 'candidate'),('primary','')]:
            result=compare_ocr(left,right)
            self.assertIn('未完成',result.warning)
            self.assertTrue(result.evidence_markdown())

    def test_long_page_alignment_bounded(self):
        result=compare_ocr('文'*20000,'文'*19999+'字')
        self.assertFalse(result.agrees)
        self.assertIsNone(result.changed_regions)
        self.assertEqual(len(result.primary),20000)

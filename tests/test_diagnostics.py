import importlib.util
from importlib import metadata
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desktop_app.diagnostics import collect_report,main,sample_pdf,write_report


class DiagnosticsTests(unittest.TestCase):
    def test_report_is_utf8_and_does_not_replace_existing_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'報告.json'
            report={'complete':False,'checks':[{'detail':'繁體測試'}]}
            write_report(report,path)
            self.assertEqual(json.loads(path.read_text(encoding='utf-8')),report)
            before=path.read_bytes()
            with self.assertRaises(FileExistsError):write_report({'complete':True},path)
            self.assertEqual(path.read_bytes(),before)
            self.assertEqual(list(Path(directory).iterdir()),[path])

    def test_existing_report_prevents_starting_any_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'result.json';path.write_text('{}')
            with patch('desktop_app.diagnostics.collect_report') as collect:
                with self.assertRaises(SystemExit):main(['--report',str(path)])
            collect.assert_not_called()

    def test_failure_report_does_not_claim_complete_or_stop_remaining_checks(self):
        with patch('desktop_app.diagnostics.verify_help',side_effect=RuntimeError('broken guide')), \
             patch('desktop_app.diagnostics._convert',side_effect=RuntimeError('broken worker')):
            report=collect_report()
        self.assertFalse(report['complete'])
        self.assertEqual(report['app_version'],metadata.version('markitdown-desktop'))
        self.assertEqual(len(report['checks']),5)
        self.assertEqual(report['checks'][0]['outcome'],'failed')
        self.assertEqual(report['checks'][-1]['outcome'],'failed')

    @unittest.skipUnless(importlib.util.find_spec('pdfplumber'),'Install PDF dependencies')
    def test_embedded_pdf_fixture_parses_with_correct_content(self):
        import pdfplumber
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'native.pdf';sample_pdf(path)
            with pdfplumber.open(path) as doc:
                self.assertEqual(len(doc.pages),1)
                self.assertEqual(doc.pages[0].extract_text(),'INSTALLATION PDF CHECK 12345')

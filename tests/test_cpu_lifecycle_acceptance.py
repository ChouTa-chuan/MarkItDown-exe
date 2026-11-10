"""驗收控制端以真ZIP／登錄驗證八案，失效時保留部分結果；非原生OCR證據。"""
from pathlib import Path
import json
import sys
import tempfile
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_component_lifecycle import bundle,manager_for,MODEL
from test_component_downloads import sign

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from cpu_lifecycle_acceptance import acceptance


class CPULifecycleAcceptanceTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.spec,self.archive=bundle(self.root/'packages')
        key=Ed25519PrivateKey.generate();self.catalog=sign(key,[self.spec])
        self.manager=manager_for(self.root,key.public_key().public_bytes_raw(),self.catalog)
        self.manager.install(self.catalog,*self.spec.key,self.archive)
        self.report=self.root/'report.json'

    def check(self):return acceptance(self.manager,self.catalog,self.spec,self.archive,self.root,self.report)

    def test_eight_cases_use_real_transactions_and_preserve_data(self):
        result=self.check()
        self.assertTrue(result['accepted']);self.assertEqual(result['checks_passed'],8)
        self.assertFalse(result['cross_version_executed']);self.assertFalse(result['process_termination_executed'])
        self.assertEqual(len(result['checks']),8)
        self.assertTrue((self.manager.registry.installation_path(self.spec)/MODEL).is_file())

    def test_silent_maintenance_success_is_rejected_and_partial_report_saved(self):
        original=self.manager.repair
        def incorrectly_accept(catalog,*args,**kwargs):
            if self.manager.host.architecture=='arm64':return None
            return original(catalog,*args,**kwargs)
        with patch.object(self.manager,'repair',side_effect=incorrectly_accept):
            with self.assertRaisesRegex(AssertionError,'unexpectedly succeeded'):self.check()
        result=json.loads(self.report.read_bytes())
        self.assertFalse(result['accepted']);self.assertEqual(result['checks_passed'],1)
        self.assertEqual(result['current_check'],'incompatible architecture rejected')

    def test_failure_is_not_converted_to_a_successful_rejection(self):
        with patch.object(self.manager,'install',side_effect=OSError('controlled test failure')):
            with self.assertRaisesRegex(OSError,'controlled test failure'):self.check()
        result=json.loads(self.report.read_bytes());self.assertFalse(result['accepted'])
        self.assertEqual(result['checks_passed'],0)

    def test_existing_report_and_synthetic_document_are_not_overwritten(self):
        self.report.write_bytes(b'previous evidence')
        with self.assertRaisesRegex(AssertionError,'fresh lifecycle report'):self.check()
        self.assertEqual(self.report.read_bytes(),b'previous evidence')
        self.report.unlink();document=self.root/'使用者合成文件.md';document.write_bytes(b'preexisting fixture')
        with self.assertRaises(FileExistsError):self.check()
        self.assertEqual(document.read_bytes(),b'preexisting fixture')

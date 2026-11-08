"""CI 固定輸入、建置 receipt 與真實平台門檻；不把 Linux guard 測試當 Windows 驗收。"""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from prepare_bundled_ocr import read_build_evidence, WINDOWS_EVIDENCE, prepare
from fetch_windows_ci_inputs import fetch, fetch_with_retry
import check_windows_base as windows
from publish_windows_ci_summary import publish_annotation


class WindowsCITests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.evidence = json.loads(WINDOWS_EVIDENCE.read_text())

    def evidence_file(self, value):
        path = self.root/'evidence.json'
        path.write_text(json.dumps(value))
        return path

    def test_existing_real_source_evidence_is_accepted(self):
        result = read_build_evidence(WINDOWS_EVIDENCE)
        self.assertTrue(result['cross_build_complete'])
        self.assertFalse(result['windows_executed'])

    def test_different_source_contract_hash_is_rejected(self):
        self.evidence['source_contract_sha256'] = '0'*64
        with self.assertRaises(ValueError): read_build_evidence(self.evidence_file(self.evidence))

    def test_changed_source_toolchain_or_notice_records_are_rejected(self):
        for name in ['source_archives','toolchain_archive','notices']:
            value = deepcopy(self.evidence)
            value[name] = []
            with self.subTest(name=name), self.assertRaises(ValueError):
                read_build_evidence(self.evidence_file(value))

    def test_receipt_cannot_forge_windows_gpu_or_release_acceptance(self):
        for flag in ['windows_executed','gpu_executed','native_ocr_bundled','full_c03_complete',
                     'redistribution_approved','release_ready']:
            value = deepcopy(self.evidence)
            value[flag] = True
            with self.subTest(flag=flag), self.assertRaises(ValueError):
                read_build_evidence(self.evidence_file(value))

    def test_incomplete_cross_build_is_rejected(self):
        for flag in ['cross_build_complete','source_evidence_prepared']:
            value = deepcopy(self.evidence)
            value[flag] = False
            with self.assertRaises(ValueError): read_build_evidence(self.evidence_file(value))

    def test_wrong_candidate_machine_and_dll_are_rejected(self):
        for field, value in [('machine','ARM64'),('is_dll',True),('file','other.exe')]:
            record = deepcopy(self.evidence)
            record['candidate'][field] = value
            with self.assertRaises(ValueError): read_build_evidence(self.evidence_file(record))

    def test_receipt_cannot_be_used_with_linux_development_mode(self):
        with self.assertRaises(ValueError):
            prepare(self.root/'out',self.root,linux_development=True,build_evidence=WINDOWS_EVIDENCE)

    def test_fetch_stream_matches_hash_and_exact_length(self):
        data = b'verified source'
        path = self.root/'input'
        result = fetch('https://example.test/fixed',path,hashlib.sha256(data).hexdigest(),len(data),
                       opener=lambda *a,**k:io.BytesIO(data))
        self.assertEqual(path.read_bytes(),data)
        self.assertEqual(result['bytes'],len(data))

    def test_fetch_hash_mismatch_leaves_no_output_or_temporary(self):
        with self.assertRaises(ValueError):
            fetch('https://example.test/fixed',self.root/'input','0'*64,
                  opener=lambda *a,**k:io.BytesIO(b'tampered'))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_fetch_short_length_is_rejected_even_when_hash_matches(self):
        data = b'short'
        with self.assertRaises(ValueError):
            fetch('https://example.test/fixed',self.root/'input',hashlib.sha256(data).hexdigest(),100,
                  opener=lambda *a,**k:io.BytesIO(data))

    def test_fetch_size_limit_stops_stream_and_cleans_output(self):
        with self.assertRaises(ValueError):
            fetch('https://example.test/fixed',self.root/'input','0'*64,limit=4,
                  opener=lambda *a,**k:io.BytesIO(b'too long'))
        self.assertEqual(list(self.root.iterdir()),[])

    def test_fetch_does_not_overwrite_existing_input(self):
        path = self.root/'input'
        path.write_bytes(b'keep')
        with self.assertRaises(FileExistsError), patch('urllib.request.urlopen') as network:
            fetch('https://example.test/fixed',path,'0'*64)
        self.assertEqual(path.read_bytes(),b'keep')
        network.assert_not_called()

    def test_fetch_rejects_linked_parent(self):
        target = self.root/'actual'
        target.mkdir()
        link = self.root/'linked'
        link.symlink_to(target,target_is_directory=True)
        with self.assertRaises(RuntimeError):
            fetch('https://example.test/fixed',link/'input','0'*64)

    def test_transient_gateway_error_retries_and_honors_retry_after(self):
        error = urllib.error.HTTPError('https://example.test',503,'temporary',{'Retry-After':'2'},None)
        operation = unittest.mock.Mock(side_effect=[error,{'verified':True}])
        wait = unittest.mock.Mock()
        self.assertEqual(fetch_with_retry(operation=operation,wait=wait),{'verified':True})
        self.assertEqual(operation.call_count,2)
        wait.assert_called_once_with(2)

    def test_integrity_failure_and_permanent_http_error_do_not_retry(self):
        for error in [ValueError('hash mismatch'),urllib.error.HTTPError('https://example.test',404,'missing',{},None)]:
            operation = unittest.mock.Mock(side_effect=error)
            with self.assertRaises(type(error)):fetch_with_retry(operation=operation,wait=lambda n:None)
            self.assertEqual(operation.call_count,1)

    def test_child_environment_keeps_system_root_but_removes_search_paths(self):
        with patch.dict(os.environ,{'SystemRoot':'C:/Windows','PATH':'host-tools','TESSDATA_PREFIX':'host-models'}):
            environment = windows.native_environment()
        self.assertEqual(environment['SystemRoot'],'C:/Windows')
        self.assertEqual(environment['PATH'],'')
        self.assertEqual(environment['TESSDATA_PREFIX'],'')

    def test_ci_annotation_escapes_commands_and_preserves_real_failure(self):
        report = {'windows-build.json': {'validation_accepted': False, 'error': 'actual failure'}}
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), patch('sys.stdout', new_callable=io.StringIO) as stream:
            publish_annotation(report, {'driver.log':'100%\n::notice::untrusted\r'})
        line = stream.getvalue()
        self.assertTrue(line.startswith('::error title=Windows CI actual report::'))
        self.assertEqual(len(line.splitlines()), 1)
        self.assertIn('actual failure', line)
        self.assertIn('100%25', line)
        self.assertNotIn('\n::notice', line)

    def test_large_ci_report_is_bounded_and_does_not_claim_success(self):
        reports = {'windows-build.json': {'validation_accepted':False,'commands':['x'*50000]}}
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), patch('sys.stdout', new_callable=io.StringIO) as stream:
            publish_annotation(reports, {str(i):'x'*6000 for i in range(50)})
        self.assertLess(len(stream.getvalue().encode()), 24000)
        self.assertTrue(stream.getvalue().startswith('::error'))
        self.assertIn('"validation_accepted":false',stream.getvalue())
        reports['windows-build.json']['error'] = '真'*50000
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), patch('sys.stdout', new_callable=io.StringIO) as stream:
            publish_annotation(reports,{})
        self.assertLess(len(stream.getvalue().encode()),24000)
        self.assertIn('"accepted":false',stream.getvalue())

    def test_local_summary_does_not_emit_workflow_commands(self):
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'false'}), patch('sys.stdout', new_callable=io.StringIO) as stream:
            publish_annotation({}, {})
        self.assertEqual(stream.getvalue(),'')

    def test_windows_style_checkout_preserves_fixed_input_bytes(self):
        # 真正執行 Git 的換行轉換，但只在暫存 repository；不依賴主工作區 .git。
        repository = self.root/'repository'
        repository.mkdir()
        paths = ['packaging/profiles/base-windows-build.txt', 'packaging/native/minimal-windows.json',
                 'packaging/native/minimal-notices/tesseract-LICENSE.txt',
                 'docs/development-records/runs/c03-minimal-source-2026-11-08/build-report.json',
                 'docs/architecture/versions/v0.4-windows-ci-preparation.md',
                 'src/desktop_app/data/licenses/windows/pypdfium2/METADATA',
                 'vendor/markitdown/src/markitdown/__init__.py']
        shutil.copyfile(ROOT/'.gitattributes', repository/'.gitattributes')
        for name in paths:
            target = repository/name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT/name, target)
        for argv in [['git','init','-q'], ['git','-c','core.autocrlf=false','add','.'],
                     ['git','-c','core.autocrlf=true','checkout-index','--all',
                      '--prefix='+str(self.root/'checkout')+'/']]:
            subprocess.run(argv,cwd=repository,check=True,capture_output=True,timeout=20)
        for name in paths:
            self.assertEqual((self.root/'checkout'/name).read_bytes(),(ROOT/name).read_bytes(),name)

    @unittest.skipIf(sys.platform=='win32','This test verifies the Linux refusal guard')
    def test_linux_cannot_claim_windows_execution_or_start_any_child(self):
        with patch.object(windows.subprocess,'run') as child:
            result = windows.check(self.root/'not-used.exe',self.root/'reports')
        child.assert_not_called()
        self.assertFalse(result['accepted'])
        self.assertFalse(result['windows_executed'])
        self.assertFalse(result['clean_machine_accepted'])


if __name__=='__main__':
    unittest.main()

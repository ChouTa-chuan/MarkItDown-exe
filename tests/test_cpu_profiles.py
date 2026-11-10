"""Windows CPU profile 閉包與建置控制端反例；不以Linux測試冒充Windows執行。"""
from pathlib import Path
import json
import io
import os
import subprocess
import shutil
import sys
import tempfile
import runpy
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cpu_worker_profiles as profiles
import run_windows_cpu_ci as ci
from cpu_fixture_diagnostics import FixtureStderr


class CPUProfileTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)
        shutil.copytree(ROOT/'packaging',self.root/'packaging')
        shutil.copytree(ROOT/'src/desktop_app/data/licenses/windows',self.root/'src/desktop_app/data/licenses/windows')
        shutil.copyfile(ROOT/'pyproject.toml',self.root/'pyproject.toml')

    def test_independent_worker_and_lean_controller_closures(self):
        result=profiles.verify_profiles(self.root)
        self.assertFalse(result['windows_executed']);self.assertFalse(result['release_ready'])
        build=result['profiles']['build'];controller=result['profiles']['controller']
        self.assertIn('rapidocr-onnxruntime',build['packages']);self.assertIn('opencv-python',build['packages'])
        self.assertIn('onnxruntime',build['packages']);self.assertIn('pywin32-ctypes',build['packages'])
        for name in ('pyside6-essentials','onnxruntime-gpu','magika','markitdown','reportlab'):
            self.assertNotIn(name,build['packages'])
        for name in ('rapidocr-onnxruntime','onnxruntime','numpy','pillow','opencv-python','pyinstaller'):
            self.assertNotIn(name,controller['packages'])
        self.assertEqual(len(controller['packages']),5)
        self.assertTrue(build['windows_notice_files'])

    def test_changed_subset_hash_is_rejected(self):
        path=self.root/'packaging/profiles/cpu-windows-build.txt'
        path.write_text(path.read_text().replace('--hash=sha256:','--hash=sha256:0',1))
        with self.assertRaisesRegex(ValueError,'changed or expired'):profiles.verify_profiles(self.root)

    def test_original_notice_tampering_is_rejected(self):
        path=self.root/'src/desktop_app/data/licenses/windows/rapidocr-onnxruntime/METADATA'
        path.write_text('changed')
        with self.assertRaises(ValueError):profiles.verify_profiles(self.root)

    def test_parent_version_or_metadata_cannot_be_silently_reselected(self):
        path=self.root/'packaging/profiles/metadata-windows.json';value=json.loads(path.read_text())
        value['packages']['rapidocr-onnxruntime']['version']='9.9.9';path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):profiles.verify_profiles(self.root)

    def test_release_claim_in_generated_report_is_rejected(self):
        path=self.root/'packaging/profiles/cpu-windows-closure.json';value=json.loads(path.read_text())
        value['release_ready']=True;path.write_text(json.dumps(value))
        with self.assertRaises(ValueError):profiles.verify_profiles(self.root)

    def test_changed_core_dependency_bounds_do_not_silently_use_old_pin(self):
        path=self.root/'pyproject.toml'
        path.write_text(path.read_text().replace('cryptography>=50.0.2,<51','cryptography>=51,<52'))
        with self.assertRaisesRegex(ValueError,'固定版本不符'):profiles.expected_files(self.root)

    def test_wrong_platform_cannot_start_build_or_create_output(self):
        target=self.root/'must-not-exist'
        with patch.object(ci.sys,'platform','linux'),patch.object(ci.subprocess,'run') as child:
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):ci.run(target)
            child.assert_not_called()
        self.assertFalse(target.exists())

    def test_child_failure_is_saved_and_never_counted_as_native_success(self):
        target=self.root/'failed-build'
        with patch.object(ci.sys,'platform','win32'), \
             patch.object(ci.subprocess,'run',side_effect=subprocess.CalledProcessError(9,['synthetic'])), \
             patch('sys.stdout',new_callable=io.StringIO):
            result=ci.run(target)
        self.assertFalse(result['accepted']);self.assertFalse(result['build_verified'])
        self.assertEqual(result['checks_passed'],0);self.assertEqual(result['failed_step'],'build-venv')
        self.assertTrue((target/'reports/driver-error.log').is_file())
        saved=json.loads((target/'reports/cpu-build.json').read_text())
        self.assertFalse(saved['accepted']);self.assertIn('CalledProcessError',saved['error'])

    def test_fixture_stderr_keeps_drain_and_bounds_recorded_bytes(self):
        raw=b'fixed fixture diagnostic\n'*1000
        source=io.BytesIO(raw);target=self.root/'stderr.log'
        stream=FixtureStderr(source,target,limit=100)
        self.assertEqual(stream.read(50),raw[:50])
        self.assertEqual(stream.read(),raw[50:])
        self.assertEqual(target.read_bytes(),raw[:100]);stream.close();self.assertTrue(source.closed)

    def test_fixture_stderr_never_overwrites_existing_record(self):
        target=self.root/'stderr.log';target.write_bytes(b'preserved')
        with self.assertRaises(FileExistsError):FixtureStderr(io.BytesIO(b'new'),target)
        self.assertEqual(target.read_bytes(),b'preserved')

    def test_fixture_pipe_lines_are_recorded_without_changing_frames(self):
        raw=b'{"frame":1}\r\n{"frame":2}\n';target=self.root/'stdout.log'
        stream=FixtureStderr(io.BytesIO(raw),target,limit=100)
        self.assertEqual(stream.readline(),b'{"frame":1}\r\n')
        self.assertEqual(stream.readline(),b'{"frame":2}\n');self.assertEqual(stream.readline(),b'')
        self.assertEqual(target.read_bytes(),raw)

    def test_fixed_fixture_watchdog_is_opt_in_and_cancelled(self):
        import faulthandler
        for enabled in ('0','1'):
            with patch.dict(os.environ,{'MARKITDOWN_FIXED_HEALTH_TRACE':enabled}), \
                 patch('multiprocessing.freeze_support'),patch('desktop_app.component_workers.server.main',return_value=0), \
                 patch.object(faulthandler,'enable'),patch.object(faulthandler,'dump_traceback_later') as dump, \
                 patch.object(faulthandler,'cancel_dump_traceback_later') as cancel:
                with self.assertRaises(SystemExit) as caught:
                    runpy.run_path(str(ROOT/'packaging/ocr_worker_entry.py'),run_name='__main__')
                self.assertEqual(caught.exception.code,0)
                if enabled=='1':dump.assert_called_once_with(7);cancel.assert_called_once()
                else:dump.assert_not_called();cancel.assert_not_called()

"""Windows原生庫先於輸入reader初始化；固定guard與無OCR的EOF生命週期仍可驗證。"""
from contextlib import contextmanager
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch,Mock
from desktop_app.component_workers import server,protocol as wire
from desktop_app.components.locks import file_lock

ROOT=Path(__file__).resolve().parents[1]


class CPUStartupTests(unittest.TestCase):
    def test_native_initialization_has_guard_and_precedes_any_input_reader(self):
        owned=[]
        @contextmanager
        def guard(*args,**kwargs):
            owned.append(True)
            try:yield
            finally:owned.pop()
        def preload():
            self.assertEqual(owned,[True])
            thread.assert_not_called()
            raise RuntimeError('controlled initialization failure')
        with tempfile.TemporaryDirectory() as temporary,patch.object(server,'file_lock',side_effect=guard), \
             patch.object(server.threading,'Thread') as thread,patch.object(server,'preload_windows_runtime',side_effect=preload):
            control=io.BytesIO();value=server.serve(Path(temporary),Path(temporary)/'guard',control,io.BytesIO())
        self.assertEqual(value,1);self.assertFalse(owned)
        event=wire.event(wire.decode(control.getvalue()));self.assertEqual(event['type'],'failed')

    def test_lean_windows_source_can_handle_protocol_without_importing_ocr(self):
        with patch.object(server,'os',SimpleNamespace(name='nt')),patch.object(server.util,'find_spec',return_value=None), \
             patch('builtins.__import__',side_effect=AssertionError('no native imports for lean source probe')):
            server.preload_windows_runtime()

    def test_real_parent_eof_stops_source_worker_and_releases_guard(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);guard=root/'worker-use.lock'
            result=subprocess.run([sys.executable,str(ROOT/'packaging/ocr_worker_entry.py'),
                '--job-directory',str(root),'--guard',str(guard)],input=b'',capture_output=True,timeout=10,
                env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'MARKITDOWN_FIXED_HEALTH_TRACE':'0'})
            self.assertEqual(result.returncode,72,result.stderr.decode(errors='replace'))
            self.assertEqual(wire.event(wire.decode(result.stdout))['type'],'hello')
            with file_lock(guard,exclusive=True):pass

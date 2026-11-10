"""控制管道的真實byte framing；Win32 API以測試double核對，Windows整合結果另驗。"""
import ctypes
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch

from desktop_app.component_workers.pipe_input import PipeInput,windows_pipe_input
from desktop_app.component_workers import protocol as wire
from desktop_app.components.locks import file_lock

ROOT=Path(__file__).resolve().parents[1]


class PipeInputTests(unittest.TestCase):
    def test_fragmented_unicode_and_multiple_frames_keep_exact_bytes(self):
        data='{"訊息":"健康"}\r\n{"next":true}\n'.encode()
        stream=io.BytesIO(data)
        reader=PipeInput(lambda count:stream.read(min(3,count)))
        self.assertEqual(reader.readline(),'{"訊息":"健康"}\r\n'.encode())
        self.assertEqual(reader.readline(),b'{"next":true}\n');self.assertEqual(reader.readline(),b'')

    def test_oversize_frame_is_bounded_and_still_rejected_by_protocol(self):
        stream=io.BytesIO(b'x'*(wire.MAX_FRAME*2));reader=PipeInput(stream.read)
        value=reader.readline(wire.MAX_FRAME+1)
        self.assertEqual(len(value),wire.MAX_FRAME+1)
        self.assertLessEqual(len(reader.buffer),wire.MAX_FRAME+1)
        self.assertEqual(stream.tell(),wire.MAX_FRAME+1)
        with self.assertRaises(wire.ProtocolError):wire.decode(value)

    def test_eof_partial_frame_is_not_forged_into_a_complete_frame(self):
        reader=PipeInput(io.BytesIO(b'{"partial":').read)
        value=reader.readline();self.assertEqual(value,b'{"partial":')
        with self.assertRaises(wire.ProtocolError):wire.decode(value)
        self.assertEqual(reader.readline(),b'')

    def test_invalid_reader_or_bound_is_rejected(self):
        for limit in (0,-1,True,wire.MAX_FRAME+2):
            with self.subTest(limit=limit),self.assertRaises(ValueError):PipeInput(lambda n:b'').readline(limit)
        with self.assertRaises(ValueError):PipeInput(lambda n:'not bytes').readline()

    def test_windows_handle_read_does_not_use_crt_read(self):
        stream=io.BytesIO(b'hello\n')
        def read(handle,target,count,received,overlap):
            data=stream.read(count)
            if not data:return 0
            ctypes.memmove(target,data,len(data));received._obj.value=len(data);return 1
        kernel=SimpleNamespace(GetFileType=Mock(return_value=3),ReadFile=Mock(side_effect=read))
        with patch('ctypes.WinDLL',create=True,return_value=kernel), \
             patch('ctypes.get_last_error',create=True,return_value=109), \
             patch.dict(sys.modules,{'msvcrt':SimpleNamespace(get_osfhandle=lambda fd:123)}), \
             patch('os.read',side_effect=AssertionError('must not call CRT read')):
            reader=windows_pipe_input(0)
            self.assertEqual(reader.readline(),b'hello\n');self.assertEqual(reader.readline(),b'')
        self.assertGreaterEqual(kernel.ReadFile.call_count,2)

    def test_real_parent_eof_terminates_worker_and_releases_guard_without_ocr(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);guard=root/'worker-use.lock'
            result=subprocess.run([sys.executable,str(ROOT/'packaging/ocr_worker_entry.py'),
                '--job-directory',str(root),'--guard',str(guard)],input=b'',capture_output=True,timeout=10,
                env={**os.environ,'PYTHONPATH':str(ROOT/'src'),'MARKITDOWN_FIXED_HEALTH_TRACE':'0'})
            self.assertEqual(result.returncode,72,result.stderr.decode(errors='replace'))
            value=wire.event(wire.decode(result.stdout));self.assertEqual(value['type'],'hello')
            with file_lock(guard,exclusive=True):pass

import os
from pathlib import Path
from queue import Queue
import subprocess
from threading import Event
import unittest
from unittest.mock import patch

from desktop_app.devices import parse_nvidia_csv, probe_devices, ocr_backend
from desktop_app.core import Request
from desktop_app.settings import Settings
from desktop_app.workers import worker


class DeviceTests(unittest.TestCase):
    def test_multiple_gpu_csv(self):
        cards = parse_nvidia_csv('GPU-1, "Test GPU, Large", 8192, 4096, 555.1\nGPU-2, Second, 4096, 0, 555.1\n')
        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].free_mib, 4096)

    def test_invalid_memory_rejected(self):
        for row in ['GPU-1, Test, 8192, 9999, x', 'GPU-1, Test, N/A, N/A, x', 'broken']:
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_nvidia_csv(row)

    def test_gpu_request_does_not_silently_use_cpu(self):
        with self.assertRaisesRegex(ValueError, "不支援 GPU"):
            ocr_backend("gpu")
        self.assertIn("CPU", ocr_backend("auto"))

    def test_query_timeout_does_not_claim_ready(self):
        with patch('desktop_app.devices.shutil.which', return_value='/test/nvidia-smi'), \
             patch('desktop_app.devices.subprocess.run', side_effect=subprocess.TimeoutExpired('query', 5)):
            result = probe_devices()
        self.assertEqual(result.gpus, ())
        self.assertTrue(any('查詢失敗' in note for note in result.notes))

    def test_missing_query_does_not_claim_no_hardware(self):
        with patch('desktop_app.devices.shutil.which', return_value=None):
            result = probe_devices()
        self.assertTrue(any('其他廠牌' in note for note in result.notes))

    def test_device_and_threads_validation(self):
        for options in [dict(cpu_threads=0), dict(cpu_threads=True), dict(cpu_threads=257), dict(device='invalid')]:
            with self.subTest(options=options), self.assertRaises(ValueError):
                Settings(**options)

    def test_worker_limits_native_threads(self):
        permit, cancel, messages = Event(), Event(), Queue()
        permit.set()
        observed = []
        def convert(*args,**kwargs):
            observed.append(os.environ['OMP_THREAD_LIMIT'])
            self.assertIs(kwargs['cancel'],cancel)
            self.assertIs(kwargs['permit'],permit)
        with patch.dict(os.environ), patch('desktop_app.workers.convert_document', side_effect=convert), \
             patch('desktop_app.workers.psutil.Process'):
            worker(Request(Path('test.txt'), Path('output.md'), cpu_threads=2), cancel, permit, messages)
        self.assertEqual(observed, ['2'])
        self.assertEqual(list(messages.queue)[-1][0], 'completed')

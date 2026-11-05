import importlib.util
import hashlib
import json
from pathlib import Path
import os
import shutil
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from desktop_app.core import Cancelled, Request
from desktop_app.devices import DeviceReport, GPU
from desktop_app.onnx_ocr import OnnxOCR, gpu_admission

READY = DeviceReport((GPU('test', 'test', 4096, 2048, 'test'),), ('CUDAExecutionProvider',), ())


class FixedQualityRasterTests(unittest.TestCase):
    def test_known_gap_uses_the_same_raster_and_reference_on_all_platforms(self):
        root=Path(__file__).parent/'fixtures'
        spec=json.loads((root/'ocr-traditional-meeting.json').read_text(encoding='utf-8'))
        self.assertEqual(hashlib.sha256((root/'ocr-traditional-meeting.png').read_bytes()).hexdigest(),spec['sha256'])
        self.assertEqual(spec['reference'],'繁體中文文件測試\n會議紀錄與資料轉換')


class BackendPolicyTests(unittest.TestCase):
    def test_gpu_memory_reserve(self):
        self.assertTrue(gpu_admission(READY, 768)[0])
        self.assertFalse(gpu_admission(READY, 2048)[0])

    def test_provider_alone_is_insufficient(self):
        self.assertFalse(gpu_admission(DeviceReport((), ('CUDAExecutionProvider',), ()), 768)[0])

    def test_no_provider_is_not_gpu_ready(self):
        self.assertFalse(gpu_admission(DeviceReport(READY.gpus, ('CPUExecutionProvider',), ()), 768)[0])

    def test_explicit_gpu_not_silently_downgraded(self):
        with patch('desktop_app.onnx_ocr.verify_models'), patch('desktop_app.devices.probe_devices',
              return_value=DeviceReport((), (), ())), patch.object(OnnxOCR, '_create') as create:
            with self.assertRaises(RuntimeError):
                OnnxOCR('gpu')
            create.assert_not_called()

    def test_registered_cuda_sessions_checked(self):
        sessions = [MagicMock() for _ in range(3)]
        for session in sessions: session.get_providers.return_value = ['CPUExecutionProvider']
        with patch('desktop_app.onnx_ocr.verify_models'), patch('desktop_app.devices.probe_devices', return_value=READY), \
             patch.object(OnnxOCR, '_create'), patch.object(OnnxOCR, 'sessions', return_value=sessions):
            with self.assertRaisesRegex(RuntimeError, '初始化失敗'):
                OnnxOCR('gpu')

    def test_auto_init_fallback_requires_checkpoint(self):
        events=[]
        sessions = [MagicMock()]
        sessions[0].set_providers.side_effect=RuntimeError('CUDA OOM')
        with patch('desktop_app.onnx_ocr.verify_models'), patch('desktop_app.devices.probe_devices', return_value=READY), \
             patch.object(OnnxOCR, '_create', side_effect=lambda threads:events.append('create')), \
             patch.object(OnnxOCR, 'sessions', return_value=sessions):
            engine=OnnxOCR('auto',checkpoint=lambda:events.append('checkpoint'))
        self.assertEqual(engine.actual_device,'cpu')
        self.assertEqual(events.count('create'),2)
        self.assertEqual(events[-2:],['checkpoint','create'])

    def test_cancel_never_falls_back(self):
        with patch('desktop_app.onnx_ocr.verify_models'), patch.object(OnnxOCR, '_create') as create:
            with self.assertRaises(Cancelled):
                OnnxOCR('cpu', checkpoint=lambda: (_ for _ in ()).throw(Cancelled()))
            create.assert_not_called()

    def test_auto_inference_retries_once_on_cpu(self):
        from PIL import Image
        engine = object.__new__(OnnxOCR)
        engine.actual_device='cuda';engine.requested_device='auto';engine.threads=1
        engine.notice='test';events=[]
        engine.checkpoint=lambda:events.append('checkpoint')
        engine.progress=lambda message:None
        engine.engine=MagicMock(side_effect=RuntimeError('CUDA OOM'))
        def create(threads):
            events.append('create')
            engine.engine=MagicMock(return_value=([[None,'Recovered',0.9]],None))
        with Image.new('RGB',(32,32)) as image, patch.object(engine,'_create',side_effect=create):
            text,_=engine.recognize(image)
        self.assertEqual(text,'Recovered')
        self.assertEqual(engine.actual_device,'cpu')
        self.assertEqual(events.count('create'),1)
        self.assertEqual(events[1:3],['checkpoint','create'])


@unittest.skipUnless(importlib.util.find_spec('rapidocr_onnxruntime'), 'Optional ONNX OCR package not installed')
class OnnxIntegrationTests(unittest.TestCase):
    def make_image(self, chinese=False):
        from PIL import Image,ImageDraw,ImageFont
        default='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc' if chinese else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        path=os.environ.get('TEST_CJK_FONT' if chinese else 'TEST_LATIN_FONT',default)
        if not Path(path).exists():self.skipTest('Sample font unavailable')
        image=Image.new('RGB',(1600,600),'white')
        draw=ImageDraw.Draw(image)
        text='繁體中文文件測試\n會議紀錄與資料轉換' if chinese else 'DOCUMENT SCAN TEST\nInvoice total 12345'
        draw.multiline_text((80,100),text,font=ImageFont.truetype(path,72),fill='black',spacing=30)
        return image

    @unittest.expectedFailure
    def test_traditional_chinese_quality_known_gap(self):
        # Tracked quality gap in the pinned optional model. Keep the strict
        # assertion so a future improvement requires removing this marker.
        engine=OnnxOCR('cpu',1)
        try:
            # This known gap is specific to a fixed raster, not the host's
            # selected CJK font. Keep the same target on Windows and Linux.
            from PIL import Image
            with Image.open(Path(__file__).parent/'fixtures/ocr-traditional-meeting.png') as image:
                text,_=engine.recognize(image)
            compact=''.join(text.split())
            self.assertIn('繁體中文',compact)
            self.assertIn('會議紀錄',compact)
            self.assertEqual(engine.actual_device,'cpu')
        finally:engine.close()

    def test_pdf_onnx_needs_no_tesseract(self):
        from reportlab.pdfgen import canvas
        from desktop_app.conversion import convert_document
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'scan.pdf';target=root/'result.md'
            with self.make_image() as image:image.save(root/'scan.png')
            document=canvas.Canvas(str(source),pagesize=(800,600))
            document.drawImage(str(root/'scan.png'),0,150,800,300);document.save()
            with patch('desktop_app.pdf_pipeline.shutil.which',return_value=None):
                convert_document(Request(source,target,device='cpu',ocr_backend='onnx'),lambda:None)
            self.assertIn('DOCUMENT SCAN TEST',target.read_text(encoding='utf-8'))

    @unittest.skipUnless(shutil.which('tesseract'), 'Cross-check requires Tesseract')
    def test_crosscheck_keeps_primary_and_candidate(self):
        import subprocess
        from reportlab.pdfgen import canvas
        from desktop_app.conversion import convert_document
        if 'chi_tra' not in subprocess.run(['tesseract','--list-langs'],capture_output=True,text=True).stdout:
            self.skipTest('Traditional Chinese model unavailable')
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);source=root/'scan.pdf';target=root/'result.md'
            with self.make_image(True) as image:image.save(root/'scan.png')
            document=canvas.Canvas(str(source),pagesize=(800,600))
            document.drawImage(str(root/'scan.png'),0,150,800,300);document.save()
            request=Request(source,target,device='cpu',ocr_backend='onnx_verify')
            convert_document(request,lambda:None)
            text=target.read_text(encoding='utf-8')
            self.assertIn('會議紀錄與資料轉換',''.join(text.split()))
            self.assertIn('未自動修字',text)
            self.assertIn('ONNX（候選結果）',text)
            self.assertIn('<details>',text)
            target.unlink()
            with patch('desktop_app.pdf_pipeline.shutil.which',return_value=None):
                with self.assertRaisesRegex(RuntimeError,'找不到 Tesseract'):
                    convert_document(request,lambda:None)
            self.assertFalse(target.exists())

"""C10 路由／租約／版本／提交驗證；合成元件與 fake OCR 不作原生推論證據。"""
from dataclasses import replace
import importlib.util
from importlib import resources
import os
from pathlib import Path
import pickle
import tempfile
from threading import Event, Timer
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.application import Runner
from desktop_app.component_workers.client import WorkerOutcome, WorkerRunner
from desktop_app.component_workers.managed import ManagedContext, ManagedOCRSession, ManagedOCRUnavailable
from desktop_app.components.catalog import TrustPolicy
from desktop_app.components.management import ComponentManagement, TrustedSource
from desktop_app.conversion import convert_document
from desktop_app.core import Request, State, Cancelled, Quality
from desktop_app.planning import analyze
from desktop_app.resources import Policy, Snapshot, MIB
from desktop_app.settings import Settings, ComponentPreference, load_settings, save_settings
from test_component_downloads import NOW, sign
from test_component_lifecycle import bundle, health, HOST

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
ROOMY=Snapshot(8192*MIB,6144*MIB,64*MIB)
ROOT=Path(__file__).resolve().parents[1]


def make_pdf(path, *, scan=False, pages=1):
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    output=canvas.Canvas(str(path),pagesize=(800,500))
    for index in range(pages):
        if scan:
            image=resources.files('desktop_app').joinpath('data/worker-health.png')
            output.drawImage(ImageReader(str(image)),20,150,width=760,height=170)
        else:output.drawString(40,400,'NATIVE PAGE CONTENT PRESERVED 12345')
        output.showPage()
    output.save()


def nested_state_fixture(request,cancel,permit,messages,*args):
    """真 spawn／佇列的狀態 fixture，沒有文件轉換或 OCR。"""
    messages.put(('worker_state',('paused','fixture nested waiting')))
    messages.put(('progress','fixture still waiting'))
    messages.put(('worker_state',('running','fixture nested resumed')))
    messages.put(('completed','fixture complete'))


class ManagedContractTests(unittest.TestCase):
    def test_public_policy_roundtrip_immutable_and_validated_for_spawn(self):
        key=Ed25519PrivateKey.generate()
        policy=TrustPolicy(1,'test-catalog',1,{'key':key.public_key().public_bytes_raw()},frozenset(),('https://example.invalid',))
        restored=pickle.loads(pickle.dumps(ManagedContext('/tmp/managed-context',policy)))
        self.assertEqual(restored.policy,policy)
        with self.assertRaises(TypeError):restored.policy.keys['injected']=b'x'*32
        for directory,trust in (('relative',policy),('/tmp/root',{'keys':'untrusted'})):
            with self.assertRaises(ValueError):ManagedContext(directory,trust)

    def test_settings_managed_preference_roundtrip_and_default_retained(self):
        self.assertEqual(Settings().ocr_backend,'tesseract')
        settings=Settings(ocr_backend='managed_cpu',component_preferences=(ComponentPreference('ocr.onnx.cpu','onnx-cpu-ocr','1.0.0'),))
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'settings.json';save_settings(settings,path)
            self.assertEqual(load_settings(path),settings)

    def test_outer_permit_blocks_before_spawn_then_recovers(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.png';source.write_bytes(b'fixture');permit=Event();events=[]
            timer=Timer(0.1,permit.set);timer.start()
            try:
                runner=WorkerRunner((os.sys.executable,'-I',str(ROOT/'tests/fixtures/component-worker-fixture.py'),'--scenario','valid'),
                    root/'worker-use.lock',Policy(budget=1024*MIB,reserve=0),estimate_mib=8,read_snapshot=lambda:ROOMY,
                    permit=permit,require_frozen=False,resource_wait=1)
                result=runner.run(source,notify=lambda state,message:events.append(state))
            finally:timer.join()
            self.assertEqual(result.state,State.COMPLETED,result.message);self.assertIn(State.PAUSED,events)

    def test_outer_permit_pause_resume_during_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'input.png';source.write_bytes(b'fixture');permit=Event();permit.set();events=[];timers=[]
            def notify(state,message):
                events.append((state,message))
                if message.endswith('loading'):
                    permit.clear();timer=Timer(0.15,permit.set);timer.start();timers.append(timer)
            runner=WorkerRunner((os.sys.executable,'-I',str(ROOT/'tests/fixtures/component-worker-fixture.py'),'--scenario','slow'),
                root/'worker-use.lock',Policy(budget=1024*MIB,reserve=0),estimate_mib=8,read_snapshot=lambda:ROOMY,
                permit=permit,require_frozen=False,resource_wait=1)
            try:result=runner.run(source,notify=notify)
            finally:
                for timer in timers:timer.join()
            self.assertEqual(result.state,State.COMPLETED,result.message)
            self.assertTrue(any(state==State.PAUSED and '上層' in message for state,message in events))


@unittest.skipUnless(importlib.util.find_spec('reportlab'),'Install PDF fixtures')
class ManagedConversionTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.source=self.root/'source.pdf';make_pdf(self.source,scan=True,pages=2);self.target=self.root/'output.md'
        self.key=Ed25519PrivateKey.generate();self.policy=TrustPolicy(1,'test-catalog',1,
            {'test-key':self.key.public_key().public_bytes_raw()},frozenset(),('https://example.invalid',))
        self.spec,self.archive=bundle(self.root/'external',component_id='onnx-cpu-ocr',capabilities=['ocr.onnx.cpu'])
        self.new,self.new_archive=bundle(self.root/'external',component_id='onnx-cpu-ocr',version='2.0.0',capabilities=['ocr.onnx.cpu'])
        self.spec=replace(self.spec,health_check='onnx.cpu.health');self.new=replace(self.new,health_check='onnx.cpu.health')
        self.service=ComponentManagement(self.root/'app',source=TrustedSource(self.policy),host=HOST,health_checks={'onnx.cpu.health':health})
        self.service.verifier.clock=lambda:NOW
        path=self.root/'catalog.json';path.write_bytes(sign(self.key,[self.spec,self.new]))
        self.assertEqual(self.service.run('catalog_file',path=path).state,'completed')
        result=self.service.run('offline',self.spec.key,self.archive);self.assertEqual(result.state,'completed',result.message)
        self.request=Request(self.source,self.target,ocr_backend='managed_cpu',component_version='1.0.0')
        self.context=self.service.conversion_context();self.inference_calls=0;self.outcome=State.COMPLETED
        # 這些 fixture 只檢查接線，真 frozen session 另由實際驗收腳本執行。
        self.addCleanup(patch.stopall)
        patch('desktop_app.components.management.ComponentManagement',return_value=self.service).start()
        patch('desktop_app.component_workers.binding.CPUWorkerBinding.health',side_effect=health).start()
        owner=self
        class FakeRunner:
            def run(self,*args,**kwargs):
                owner.inference_calls+=1
                return WorkerOutcome(owner.outcome,'C10 fixture',dict(text='FAKE OCR CONTENT FOR PIPELINE TEST 12345',warning='Fixture only; not OCR proof'))
        patch('desktop_app.component_workers.binding.CPUWorkerBinding.runner',return_value=FakeRunner()).start()

    def convert(self,progress=lambda stage:None):
        return convert_document(self.request,lambda:None,progress,component_context=self.context,policy=Policy(budget=2048*MIB,reserve=0))

    def test_plan_defers_model_ram_and_rejects_gpu_or_invalid_version(self):
        self.assertEqual(analyze(self.request).additional_bytes,256*MIB)
        for request in (replace(self.request,device='gpu'),replace(self.request,component_version='bad'),
                        replace(self.request,ocr_backend='tesseract')):
            with self.assertRaises(ValueError):analyze(request)

    def test_two_ocr_pages_share_one_lease_through_output_commit(self):
        attempts=[]
        def progress(stage):
            if stage=='提交輸出':attempts.append(self.service.run('remove',self.spec.key).state)
        summary=self.convert(progress);text=self.target.read_text()
        self.assertIn('逐頁分析 2 頁',summary);self.assertEqual(self.inference_calls,2)
        self.assertEqual(text.count('source-component: onnx-cpu-ocr; version: 1.0.0'),2)
        self.assertEqual(text.count('Fixture only; not OCR proof'),2)
        self.assertEqual(attempts,['failed']);self.assertEqual(self.service.run('remove',self.spec.key).state,'completed')

    def test_pinned_version_mismatch_before_wrong_health(self):
        self.request=replace(self.request,component_version='2.0.0')
        with patch('desktop_app.component_workers.binding.CPUWorkerBinding.health',side_effect=AssertionError('wrong version health')):
            with self.assertRaisesRegex(RuntimeError,'指定版本未啟用'):self.convert()
        self.assertEqual(self.inference_calls,0);self.assertFalse(self.target.exists())

    def test_missing_capability_rejected_before_health(self):
        altered,archive=bundle(self.root/'other',component_id='unrelated',capabilities=['other.capability'])
        # 直接檢查 C06 租約能力閘，無需建立假的原生元件。
        from desktop_app.components.lifecycle import ComponentManager
        registry,manager=self.service._services(Event(),lambda:None)
        with patch.object(manager,'_ready',side_effect=AssertionError('must not health')):
            with self.assertRaisesRegex(RuntimeError,'沒有文件要求的能力'):
                with manager.lease(self.service._catalog(),'onnx-cpu-ocr',capability='other.capability'):pass

    def test_expiry_or_withdrawal_before_commit_rejects_partial_output(self):
        def progress(stage):
            if stage=='提交輸出':self.service.catalog_path.write_bytes(sign(self.key,[self.new],revision=2))
        with self.assertRaises(ValueError):self.convert(progress)
        self.assertFalse(self.target.exists());self.assertEqual(list(self.root.glob('.conversion-*')),[])

    def test_worker_failure_never_calls_other_ocr(self):
        self.outcome=State.FAILED
        with patch('desktop_app.pdf_pipeline._run_ocr',side_effect=AssertionError('no fallback')):
            with self.assertRaises(ManagedOCRUnavailable):self.convert()
        self.assertFalse(self.target.exists());self.assertEqual(self.service.run('remove',self.spec.key).state,'completed')

    def test_cancelled_worker_leaves_no_output_and_releases_lease(self):
        self.outcome=State.CANCELLED
        with self.assertRaises(Cancelled):self.convert()
        self.assertFalse(self.target.exists());self.assertEqual(self.service.run('remove',self.spec.key).state,'completed')

    def test_payload_tampering_before_commit_is_rejected(self):
        def progress(stage):
            if stage=='提交輸出':
                path=self.service.registry_path/'components'/self.spec.component_id/str(self.spec.version)/self.spec.license_path
                path.write_bytes(b'changed')
        with self.assertRaises(RuntimeError):self.convert(progress)
        self.assertFalse(self.target.exists())

    def test_existing_output_is_not_overwritten(self):
        self.target.write_text('user output')
        with self.assertRaises(FileExistsError):self.convert()
        self.assertEqual(self.target.read_text(),'user output')

    def test_dangling_output_link_is_not_followed(self):
        outside=self.root/'unrequested.md';self.target.symlink_to(outside)
        with self.assertRaises(FileExistsError):self.convert()
        self.assertTrue(self.target.is_symlink());self.assertFalse(outside.exists())

    def test_native_pages_do_not_touch_missing_optional_context(self):
        make_pdf(self.source,scan=False,pages=2)
        self.request=replace(self.request,component_version=None)
        with patch('desktop_app.component_workers.managed.ManagedOCRSession._start',side_effect=AssertionError('must not acquire')):
            convert_document(self.request,lambda:None,component_context=None)
        self.assertEqual(self.target.read_text().count('NATIVE PAGE CONTENT PRESERVED 12345'),2)
        self.assertNotIn('source-component',self.target.read_text())

    def test_missing_context_on_scan_is_explicit_and_no_partial_output(self):
        with self.assertRaisesRegex(ManagedOCRUnavailable,'選配元件管理'):
            convert_document(self.request,lambda:None)
        self.assertFalse(self.target.exists())


@unittest.skipUnless(importlib.util.find_spec('reportlab'),'Install PDF fixtures')
class ManagedSpawnTests(unittest.TestCase):
    def test_nested_resource_state_reaches_controller_without_becoming_running(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source.txt';source.write_text('fixture');events=[]
            with patch('desktop_app.application.worker',nested_state_fixture):
                outcome=Runner(Policy(budget=1024*MIB,reserve=0)).run(Request(source,root/'output.md'),
                    notify=lambda state,message:events.append((state,message)))
            self.assertEqual(outcome.state,State.COMPLETED)
            self.assertIn((State.PAUSED,'fixture still waiting'),events)
            self.assertIn((State.RUNNING,'fixture nested resumed'),events)

    def test_missing_optional_document_does_not_stop_native_or_text_batch(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);scan=root/'scan.pdf';native=root/'native.pdf';text=root/'source.txt'
            make_pdf(scan,scan=True);make_pdf(native);text.write_text('基本文字繼續')
            requests=[Request(path,root/(path.name+'.md'),ocr_backend='managed_cpu') for path in (scan,native,text)]
            result=list(Runner(Policy(budget=2048*MIB,reserve=0)).batch(requests))
            self.assertEqual([item.state for item in result],[State.FAILED,State.COMPLETED,State.COMPLETED])
            self.assertIn('選配元件管理',result[0].message);self.assertFalse(requests[0].destination.exists())
            self.assertEqual(requests[2].destination.read_text(),text.read_text())


@unittest.skipUnless(importlib.util.find_spec('PySide6'),'Install desktop dependencies')
class ManagedDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
        from qt_support import release_test_widgets
        cls.addClassCleanup(release_test_widgets, cls.app)

    def test_managed_preference_roundtrip_preserves_order_and_other_choices(self):
        from desktop_app.desktop import Window
        with tempfile.TemporaryDirectory() as temporary:
            path=Path(temporary)/'settings.json';prefs=(ComponentPreference('ocr.onnx.cpu','onnx-cpu-ocr','1.0.0'),ComponentPreference('other.capability','other-model'))
            settings=Settings(ocr_backend='managed_cpu',component_preferences=prefs);save_settings(settings,path)
            window=Window(settings_path=path)
            try:
                self.assertEqual(window.managed_version.text(),'1.0.0');window.save_preferences()
                self.assertEqual(load_settings(path),settings)
                window.set_running(True);self.assertFalse(window.managed_version.isEnabled())
                window.set_running(False);self.assertTrue(window.managed_version.isEnabled())
            finally:window.close()

    def test_bad_version_does_not_start_batch_or_overwrite_preferences(self):
        from desktop_app.desktop import Window
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'source.txt';source.write_text('text')
            window=Window(settings_path=root/'settings.json')
            try:
                window.backend.setCurrentIndex(window.backend.findData('managed_cpu'));window.managed_version.setText('bad')
                window.add_sources([source]);window.output.setText(str(root/'out'));window.start()
                self.assertIsNone(window.job);self.assertIn('轉換未開始',window.status.text())
                self.assertFalse(window.settings_path.exists())
            finally:window.close()

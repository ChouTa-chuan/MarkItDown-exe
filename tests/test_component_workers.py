"""C07 協定與資源測試；原生 CPU 子程序、frozen 獨立 runtime 的證據分開記錄。"""
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from threading import Event
import time
import unittest
from unittest.mock import patch

import psutil

from desktop_app.component_workers import protocol as wire
from desktop_app.component_workers.client import WorkerRunner
from desktop_app.components.locks import ComponentBusy,file_lock
from desktop_app.core import State
from desktop_app.resources import MIB,Policy,Snapshot

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'tests/fixtures/component-worker-fixture.py'
AVAILABLE=Snapshot(8192*MIB,6144*MIB,32*MIB)


class ProtocolTests(unittest.TestCase):
    def test_round_trip_valid_control(self):
        value=dict(protocol=wire.PROTOCOL,type='cancel',job_id='a'*32)
        self.assertEqual(wire.command(wire.decode(wire.encode(value))),value)

    def test_oversize_truncated_duplicate_future_and_nonfinite_frames_rejected(self):
        for raw in (b'x'*16385,b'{}',b'{"protocol":"1.0.0","protocol":"1.0.0"}\n',
                    b'{"protocol":"2.0.0"}\n',b'{"protocol":"1.0.0","value":NaN}\n',b'['*2000+b'\n'):
            with self.subTest(size=len(raw)),self.assertRaises(wire.ProtocolError):wire.decode(raw)

    def test_request_paths_limits_and_unknown_fields_rejected(self):
        good=dict(protocol=wire.PROTOCOL,type='run',job_id='a'*32,operation='ocr',input='input.png',input_bytes=5,
                  input_sha256='0'*64,output='result.json',limits=dict(cpu_threads=1,max_pixels=100,max_output_bytes=1024))
        self.assertEqual(wire.command(good),good)
        for changes in ({'input':'../private'},{'output':'/outside'},{'input_bytes':True},{'job_id':'bad'},
                        {'limits':dict(cpu_threads=0,max_pixels=100,max_output_bytes=1024)},{'execute':'shell'}):
            with self.subTest(changes=changes),self.assertRaises(wire.ProtocolError):wire.command({**good,**changes})

    def test_gpu_or_wrong_runtime_identity_is_not_a_cpu_handshake(self):
        hello=dict(protocol=wire.PROTOCOL,type='hello',component_id=wire.COMPONENT_ID,
                   component_version=wire.COMPONENT_VERSION,pid=1,frozen=True,device='cpu')
        for changes in ({'device':'gpu'},{'component_version':'2.0.0'},{'pid':True},{'frozen':'yes'}):
            with self.assertRaises(wire.ProtocolError):wire.event({**hello,**changes})


class ProcessTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.source=self.root/'來源.png';self.source.write_bytes(b'IPC fixture input')
        self.target=self.root/'結果.md'

    def runner(self, scenario='valid',**changes):
        return WorkerRunner((sys.executable,'-I',str(FIXTURE),'--scenario',scenario),self.root/'worker-use.lock',
            Policy(budget=1024*MIB,reserve=0),estimate_mib=8,read_snapshot=lambda:AVAILABLE,
            require_frozen=changes.pop('require_frozen',False),timeout=changes.pop('timeout',4),
            handshake_timeout=changes.pop('handshake_timeout',1),resource_wait=changes.pop('resource_wait',0.5),
            cancel_grace=changes.pop('cancel_grace',0.2),**changes)

    def assert_reaped(self,outcome):
        if outcome.pid is not None:self.assertFalse(psutil.pid_exists(outcome.pid))

    def test_real_process_protocol_and_atomic_output(self):
        outcome=self.runner().run(self.source,self.target)
        self.assertEqual(outcome.state,State.COMPLETED,outcome.message)
        self.assertIn('FAKE WORKER CONTENT',self.target.read_text());self.assert_reaped(outcome)

    def test_existing_destination_and_original_source_are_preserved(self):
        self.target.write_text('user data');original=self.source.read_bytes()
        outcome=self.runner().run(self.source,self.target)
        self.assertEqual(outcome.state,State.FAILED);self.assertIsNone(outcome.pid)
        self.assertEqual(self.target.read_text(),'user data');self.assertEqual(self.source.read_bytes(),original)

    def test_prestart_low_ram_does_not_spawn(self):
        runner=self.runner();runner.read_snapshot=lambda:Snapshot(8192*MIB,0,0)
        with patch('desktop_app.component_workers.client.subprocess.Popen',side_effect=AssertionError('must not spawn')):
            outcome=runner.run(self.source,self.target)
        self.assertEqual(outcome.state,State.FAILED);self.assertIsNone(outcome.pid);self.assertFalse(self.target.exists())

    def test_prestart_cancel_does_not_spawn(self):
        cancel=Event();cancel.set();outcome=self.runner().run(self.source,self.target,cancel=cancel)
        self.assertEqual(outcome.state,State.CANCELLED);self.assertIsNone(outcome.pid)

    def test_wrong_version_job_digest_escape_symlink_and_tail_are_rejected(self):
        for scenario in ('version','job','digest','escape','symlink','tail'):
            with self.subTest(scenario=scenario):
                outcome=self.runner(scenario).run(self.source,self.target)
                self.assertEqual(outcome.state,State.FAILED,outcome.message)
                self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_unfrozen_process_cannot_claim_independent_runtime(self):
        outcome=self.runner(require_frozen=True).run(self.source,self.target)
        self.assertEqual(outcome.state,State.FAILED);self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_handshake_timeout_and_premature_exit_are_bounded(self):
        for scenario in ('no_hello','crash'):
            before=time.monotonic();outcome=self.runner(scenario,handshake_timeout=0.3).run(self.source,self.target)
            self.assertEqual(outcome.state,State.FAILED);self.assertLess(time.monotonic()-before,5)
            self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_closed_child_pipe_during_cleanup_preserves_failure_and_cleans_workspace(self):
        # 真程序提前退出後，模擬 stdin.close 的最後緩衝 flush 回報 EPIPE。
        # 必須返回原工作失敗、回收程序與私有暫存，不能向批次呼叫端拋出收尾例外。
        real_popen=subprocess.Popen;real_temporary=tempfile.TemporaryDirectory
        workspaces=[]
        class ClosedPipe:
            def __init__(self, stream):self.stream=stream
            def __getattr__(self, name):return getattr(self.stream,name)
            def close(self):
                try:self.stream.close()
                finally:raise BrokenPipeError('fixture: child read end closed')
        def launch(*args,**kwargs):
            child=real_popen(*args,**kwargs);child.stdin=ClosedPipe(child.stdin)
            return child
        def workspace(*args,**kwargs):
            value=real_temporary(*args,**kwargs);workspaces.append(Path(value.name))
            return value
        with patch('desktop_app.component_workers.client.subprocess.Popen',side_effect=launch), \
             patch('desktop_app.component_workers.client.tempfile.TemporaryDirectory',side_effect=workspace):
            outcome=self.runner('crash').run(self.source,self.target)
        self.assertEqual(outcome.state,State.FAILED);self.assert_reaped(outcome)
        self.assertFalse(self.target.exists());self.assertTrue(workspaces)
        self.assertTrue(all(not path.exists() for path in workspaces))

    def test_total_timeout_and_completed_but_hanging_worker_fail(self):
        for scenario in ('hang','no_exit'):
            outcome=self.runner(scenario,timeout=1).run(self.source,self.target)
            self.assertEqual(outcome.state,State.FAILED);self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_cancel_cooperative_and_unresponsive_worker(self):
        for scenario in ('slow','ignore_cancel'):
            cancel=Event()
            def notify(state,message):
                if message.endswith('inference'):cancel.set()
            outcome=self.runner(scenario).run(self.source,self.target,cancel=cancel,notify=notify)
            self.assertEqual(outcome.state,State.CANCELLED,outcome.message)
            self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_backpressure_pauses_then_resumes(self):
        runner=self.runner('slow');pressure=[None];events=[]
        def notify(state,message):
            events.append((state,message))
            if message.endswith('loading') and pressure[0] is None:pressure[0]=time.monotonic()
        runner.read_snapshot=lambda:Snapshot(8192*MIB,0,2048*MIB) if pressure[0] is not None and time.monotonic()-pressure[0]<0.15 else AVAILABLE
        outcome=runner.run(self.source,self.target,notify=notify)
        self.assertEqual(outcome.state,State.COMPLETED,outcome.message)
        self.assertTrue(any(state==State.PAUSED for state,_ in events));self.assertTrue(any('資源恢復' in message for _,message in events))

    def test_runtime_pressure_expires_and_reaps_worker(self):
        runner=self.runner('ignore_cancel');pressure=[False]
        def notify(state,message):
            if message.endswith('loading'):pressure[0]=True
        runner.read_snapshot=lambda:Snapshot(8192*MIB,0,2048*MIB) if pressure[0] else AVAILABLE
        outcome=runner.run(self.source,self.target,notify=notify)
        self.assertEqual(outcome.state,State.FAILED);self.assertFalse(self.target.exists());self.assert_reaped(outcome)
        self.assertIn('資源等待逾時',outcome.message)

    def test_stdout_and_stderr_flood_are_bounded(self):
        for scenario in ('flood','oversize','stderr_flood'):
            outcome=self.runner(scenario).run(self.source,self.target)
            self.assertEqual(outcome.state,State.FAILED);self.assertFalse(self.target.exists());self.assert_reaped(outcome)

    def test_batch_failure_does_not_block_next_job(self):
        outcomes=list(self.runner().batch(((self.root/'missing.png',self.root/'missing.md'),(self.source,self.target))))
        self.assertEqual([item.state for item in outcomes],[State.FAILED,State.COMPLETED])

    def test_invalid_runtime_limits_are_rejected(self):
        for values in ({'timeout':float('nan')},{'cpu_threads':0},{'require_frozen':1},{'estimate_mib':0}):
            with self.assertRaises(ValueError):WorkerRunner((sys.executable,),self.root/'guard',Policy(),**values)


@unittest.skipUnless(importlib.util.find_spec('rapidocr_onnxruntime'),'Install native CPU OCR test dependencies')
class NativeCPUProcessTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)
        self.command=(sys.executable,'-I',str(ROOT/'packaging/ocr_worker_entry.py'))

    def runner(self):
        return WorkerRunner(self.command,self.root/'worker-use.lock',Policy(budget=2048*MIB,reserve=0),require_frozen=False,timeout=45)

    def test_actual_cpu_model_health_in_a_separate_process(self):
        outcome=self.runner().run(operation='health')
        self.assertEqual(outcome.state,State.COMPLETED,outcome.message)
        self.assertTrue(outcome.report['health_passed']);self.assertNotEqual(outcome.pid,os.getpid())
        self.assertEqual(outcome.report['providers'],['CPUExecutionProvider']*3)
        self.assertIn('WORKER HEALTH CHECK 12345',' '.join(outcome.report['text'].split()))
        self.assertFalse(outcome.report['runtime']['frozen'])  # 獨立 frozen runtime 由另外驗收腳本證明。

    def test_invalid_image_failure_leaves_no_output(self):
        source=self.root/'bad.png';source.write_bytes(b'not png');target=self.root/'bad.md'
        outcome=self.runner().run(source,target)
        self.assertEqual(outcome.state,State.FAILED);self.assertFalse(target.exists())

    def test_parent_channel_eof_stops_native_worker_and_releases_its_guard(self):
        process=subprocess.Popen([*self.command,'--job-directory',str(self.root),'--guard',str(self.root/'worker-use.lock')],
                                 stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        try:
            hello=wire.event(wire.decode(process.stdout.readline(wire.MAX_FRAME+1)))
            self.assertEqual(hello['type'],'hello')
            with self.assertRaises(ComponentBusy):
                with file_lock(self.root/'worker-use.lock',exclusive=True):pass
            request=dict(protocol=wire.PROTOCOL,type='run',job_id='a'*32,operation='health',input=None,input_bytes=0,
                         input_sha256=None,output='result.json',limits=dict(cpu_threads=1,max_pixels=wire.MAX_PIXELS,max_output_bytes=wire.MAX_RESULT))
            process.stdin.write(wire.encode(request));process.stdin.flush()
            value=wire.event(wire.decode(process.stdout.readline(wire.MAX_FRAME+1)));self.assertEqual(value.get('stage'),'loading')
            process.stdin.close();self.assertEqual(process.wait(timeout=5),72)
            with file_lock(self.root/'worker-use.lock',exclusive=True):pass
        finally:
            if process.poll() is None:process.kill();process.wait()
            process.stdout.close()

    def test_child_guard_blocks_lifecycle_even_without_parent_lease(self):
        from test_component_lifecycle import bundle,manager_for
        from test_component_downloads import sign
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        spec,archive=bundle(self.root/'source');key=Ed25519PrivateKey.generate();envelope=sign(key,[spec])
        manager=manager_for(self.root,key.public_key().public_bytes_raw(),envelope);manager.install(envelope,*spec.key,archive)
        with file_lock(manager.worker_guard_path,exclusive=False):
            with self.assertRaises(ComponentBusy):manager.remove(*spec.key)
            self.assertEqual(manager.store.journals(),())
        manager.remove(*spec.key)

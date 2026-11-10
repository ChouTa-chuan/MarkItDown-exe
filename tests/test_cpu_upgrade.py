"""精確版本協定、真子程序反例與合成ZIP跨版交易；Windows frozen另由CI驗收。"""
from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from desktop_app.component_workers import protocol as wire
from desktop_app.component_workers.binding import CPUWorkerBinding
from desktop_app.component_workers.client import WorkerRunner
from desktop_app.core import State
from desktop_app.resources import MIB,Policy,Snapshot
from test_components import descriptor
from test_component_lifecycle import bundle,manager_for,health
from test_component_downloads import sign

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from check_cpu_upgrade_acceptance import exercise,acceptance
from run_windows_cpu_ci import verify_previous_source,PREVIOUS_SOURCE


class CPUVersionTests(unittest.TestCase):
    def test_supported_handshake_still_requires_selected_version(self):
        for selected in ('1.0.0','1.0.1'):
            hello=dict(protocol=wire.PROTOCOL,type='hello',component_id=wire.COMPONENT_ID,
                component_version=selected,pid=1,frozen=True,device='cpu')
            self.assertEqual(wire.event(hello,expected_version=selected),hello)
            with self.assertRaises(wire.ProtocolError):wire.event(hello,expected_version='1.0.1' if selected=='1.0.0' else '1.0.0')

    def test_unknown_same_major_and_malformed_version_rejected_before_spawn(self):
        for version in ('1.0.2','1.1.0','2.0.0',True,None,[]):
            with self.subTest(version=version),self.assertRaises(wire.ProtocolError):
                WorkerRunner((sys.executable,),ROOT/'unused.lock',Policy(),component_version=version)

    def test_binding_passes_exact_descriptor_version(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);binding=CPUWorkerBinding(root/'.locks/worker-use.lock')
            folder=root/'engine';folder.mkdir();name='MarkItDownOCRWorker.exe' if os.name=='nt' else 'MarkItDownOCRWorker'
            executable=folder/name;executable.write_bytes(b'fixture');executable.chmod(0o755)
            files=[dict(path=name,size=7,sha256=hashlib.sha256(b'fixture').hexdigest()),
                dict(path='LICENSE.txt',size=1,sha256='a'*64)]
            for version in ('1.0.0','1.0.1'):
                spec=descriptor(wire.COMPONENT_ID,version,files=files,unpacked_bytes=8)
                self.assertEqual(binding.runner(spec,folder).component_version,version)
            with self.assertRaises(wire.ProtocolError):binding.runner(replace(spec,version=type(spec.version).parse('1.0.2')),folder)

    def process(self,hello_version,selected,result_version=None):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);source=root/'fixture.png';source.write_bytes(b'IPC input');destination=root/'output.md'
            command=(sys.executable,'-I',str(ROOT/'tests/fixtures/component-worker-fixture.py'),
                '--component-version',hello_version)
            if result_version:command+=('--result-version',result_version)
            runner=WorkerRunner(command,root/'guard',Policy(budget=1024*MIB,reserve=0),component_version=selected,
                estimate_mib=8,read_snapshot=lambda:Snapshot(8192*MIB,6144*MIB,32*MIB),require_frozen=False,timeout=5)
            result=runner.run(source,destination)
            return result,destination.exists()

    def test_actual_legacy_and_current_fixture_processes_accept_only_selected_identity(self):
        for version in ('1.0.0','1.0.1'):
            result,exists=self.process(version,version)
            self.assertEqual(result.state,State.COMPLETED,result.message);self.assertTrue(exists)
            self.assertEqual(result.report['component_version'],version)
        result,exists=self.process('1.0.0','1.0.1')
        self.assertEqual(result.state,State.FAILED);self.assertFalse(exists)

    def test_matching_hello_cannot_substitute_result_from_other_supported_version(self):
        result,exists=self.process('1.0.0','1.0.0','1.0.1')
        self.assertEqual(result.state,State.FAILED);self.assertFalse(exists)

    def test_previous_source_guard_rejects_dirty_and_other_commits(self):
        for outputs in ((PREVIOUS_SOURCE+'\n',' M src/file.py\n'),('a'*40+'\n','')):
            with patch('run_windows_cpu_ci.subprocess.check_output',side_effect=outputs):
                with self.assertRaisesRegex(ValueError,'clean pinned commit'):verify_previous_source(ROOT)

    def test_wrong_platform_cannot_create_native_report(self):
        with tempfile.TemporaryDirectory() as temporary,patch('check_cpu_upgrade_acceptance.sys.platform','linux'):
            report=Path(temporary)/'absent/report.json'
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):acceptance(Path(temporary),Path(temporary),report)
            self.assertFalse(report.parent.exists())


class CPUUpgradeTransactionTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.old,archive=bundle(self.root/'packages',version='1.0.0')
        self.new,new_archive=bundle(self.root/'packages',version='1.0.1')
        key=Ed25519PrivateKey.generate();self.catalog=sign(key,[self.old,self.new])
        self.manager=manager_for(self.root,key.public_key().public_bytes_raw(),self.catalog)
        self.archives={self.old.key:archive,self.new.key:new_archive};self.healths=[];self.versions=[]
        def probe(*args):self.healths.append(str(args[0].version));return health(*args)
        self.manager.health_checks={'fixture.health':probe};self.report=self.root/'report.json'

    def check(self):return exercise(self.manager,self.catalog,self.old,self.new,self.archives,self.root,
        self.report,lambda version,label:self.versions.append(version),self.healths)

    def test_eight_real_zip_transactions_with_explicit_rollback_and_retirement(self):
        result=self.check();self.assertTrue(result['transaction_checks_accepted']);self.assertEqual(result['checks_passed'],8)
        self.assertFalse(result['accepted']);self.assertFalse(result['windows_executed'])
        self.assertEqual(self.versions,['1.0.0','1.0.0','1.0.1','1.0.0','1.0.1'])
        self.assertEqual(self.manager.store.active(),{});self.assertEqual(self.manager.store.owned_keys(),())

    def test_bad_rollback_keeps_partial_failure_report(self):
        with patch.object(self.manager,'rollback',return_value=None):
            with self.assertRaisesRegex(AssertionError,'Wrong active component version'):self.check()
        value=json.loads(self.report.read_bytes());self.assertFalse(value['accepted'])
        self.assertEqual(value['checks_passed'],4)

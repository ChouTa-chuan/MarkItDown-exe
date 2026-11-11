"""真spawn／kill與獨立恢復程序的合成ZIP驗證；不當成Windows或原生OCR通過。"""
from pathlib import Path
import json
import multiprocessing
import os
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from desktop_app.components.archives import verify_tree
from desktop_app.components.lifecycle import ComponentManager
from test_component_lifecycle import bundle,manager_for
from test_component_downloads import sign

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from check_cpu_recovery_acceptance import exercise,receive,stopped,cleanup,acceptance


def synthetic_manager(root,public,catalog):return manager_for(root,public,catalog)


def synthetic_validate(manager,catalog,root,version):
    with manager.lease(catalog,'test-engine',expected_version=version) as lease:verify_tree(lease.directory,lease.spec)
    return dict(version=version,frozen=False,scope='synthetic ZIP only')


class BrokenRecoveryManager(ComponentManager):
    def recover(self):return ()


def broken_manager(root,public,catalog):
    manager=synthetic_manager(root,public,catalog)
    if multiprocessing.current_process().name=='cpu-recovery-probe':manager.__class__=BrokenRecoveryManager
    return manager


def exit_before_handshake(connection):
    connection.close();os._exit(23)


class CPURecoveryTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.old,old_archive=bundle(self.root/'packages',version='1.0.0')
        self.new,new_archive=bundle(self.root/'packages',version='1.0.1')
        key=Ed25519PrivateKey.generate();self.public=key.public_key().public_bytes_raw()
        self.catalog=sign(key,[self.old,self.new]);self.packages={self.old.key:old_archive,self.new.key:new_archive}
        self.report=self.root/'report.json'

    def run_cases(self,factory=synthetic_manager):
        return exercise(factory,synthetic_validate,self.public,self.catalog,self.old,self.new,self.packages,self.root,self.report)

    def test_six_actual_terminated_children_and_independent_recovery(self):
        result=self.run_cases()
        self.assertEqual(result['checks_passed'],6);self.assertTrue(result['transaction_checks_accepted'])
        self.assertTrue(result['process_termination_executed']);self.assertFalse(result['accepted'])
        self.assertFalse(result['windows_executed']);self.assertFalse(result['power_loss_accepted'])
        self.assertEqual([case['active_after_recover'] for case in result['cases']],['1.0.0','1.0.1','1.0.1','1.0.1','1.0.1',None])
        for case in result['cases']:
            self.assertNotEqual(case['termination_exitcode'],0)
            self.assertTrue(case['lock_rejected_while_alive'] and case['cache_unchanged'] and case['idempotent'])

    def test_recovery_noop_cannot_hide_unfinished_transaction(self):
        with self.assertRaisesRegex(AssertionError,'Recovery did not finish exactly one transaction'):
            self.run_cases(broken_manager)
        result=json.loads(self.report.read_bytes());self.assertFalse(result['accepted']);self.assertEqual(result['checks_passed'],0)
        self.assertEqual(result['current_check'],'upgrade/published')

    def test_stop_requires_exact_owned_pid_token_stage_and_operation(self):
        process=SimpleNamespace(pid=123,is_alive=lambda:True)
        good=dict(type='stopped',pid=123,token='token',operation='upgrade',stage='published')
        stopped(good,process,'token','upgrade','published')
        for change in ({'pid':124},{'token':'other'},{'operation':'remove'},{'stage':'committed'}):
            with self.assertRaisesRegex(AssertionError,'identity mismatch'):
                stopped({**good,**change},process,'token','upgrade','published')

    def test_actual_child_exit_before_stop_is_not_accepted(self):
        context=multiprocessing.get_context('spawn');receiver,sender=context.Pipe(duplex=False)
        process=context.Process(target=exit_before_handshake,args=(sender,))
        try:
            process.start();sender.close()
            with self.assertRaisesRegex(AssertionError,'before handshake'):receive(process,receiver,timeout=5)
        finally:cleanup(process);receiver.close();sender.close()

    def test_wrong_platform_cannot_create_report(self):
        report=self.root/'missing/report.json'
        with patch('check_cpu_recovery_acceptance.sys.platform','linux'):
            with self.assertRaisesRegex(RuntimeError,'actual Windows'):acceptance(self.root,self.root,report)
        self.assertFalse(report.parent.exists())

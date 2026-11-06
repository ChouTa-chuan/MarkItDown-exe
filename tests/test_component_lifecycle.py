"""C06：真實 ZIP／檔案／資料庫／跨程序核心鎖與強制退出恢復，不冒充 Windows／GPU。"""
from dataclasses import replace
import hashlib
import io
import json
import multiprocessing
import os
from pathlib import Path
import shutil
import sqlite3
import stat
import struct
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.capabilities import HealthResult, HostContext
from desktop_app.components.archives import extract_archive, inventory, verify_tree
from desktop_app.components.cache import CacheQuotaError, CacheStore
from desktop_app.components.catalog import CatalogError, CatalogVerifier, TrustPolicy
from desktop_app.components.contracts import ComponentState, FileSpec, Version
from desktop_app.components.downloads import DownloadBusy, DownloadService
from desktop_app.components.lifecycle import ComponentManager
from desktop_app.components.lifecycle_store import LifecycleError, LifecycleStore
from desktop_app.components.locks import ComponentBusy, file_lock
from desktop_app.components.registry import ComponentRegistry, IntegrityError
from desktop_app.core import Cancelled
from test_component_downloads import NOW, policy, sign
from test_components import descriptor

HOST = HostContext('linux','x86_64',Version.parse('0.4.0'),Version.parse('1.0.0'))
MODEL = '模型/參數.json'
PROCESS_OBSERVATIONS = []


def joined(worker, timeout=15):
    worker.join(timeout)
    if worker.is_alive():
        worker.kill();worker.join()
        raise AssertionError('C06 subprocess fixture exceeded its bounded wait')


def observed(worker, operation, stage):
    PROCESS_OBSERVATIONS.append(dict(operation=operation,stage=stage,exit_code=worker.exitcode,
                                     actual_spawned_process=True))


def health(spec, directory, host):
    data = json.loads((directory/MODEL).read_bytes())
    return HealthResult(data.get('format')=='c06-fixture' and data.get('factor',0)*21==42,
                        '合成模型格式與資料運算；非 OCR 或 GPU 推論')


def bundle(root, component_id='test-engine', version='1.0.0', *, payload=None, **changes):
    files = {MODEL:payload if payload is not None else b'{"format":"c06-fixture","factor":2}',
             'LICENSE.txt':b'C06 synthetic test fixture license'}
    root.mkdir(parents=True,exist_ok=True)
    archive = root/(component_id+'-'+version+'.zip')
    with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED) as output:
        for name,data in files.items():output.writestr(name,data)
    spec = descriptor(component_id,version,source_url='https://example.invalid/package',
        download_bytes=archive.stat().st_size,package_sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
        unpacked_bytes=sum(map(len,files.values())),
        files=[dict(path=name,size=len(data),sha256=hashlib.sha256(data).hexdigest()) for name,data in files.items()],
        resources=dict(ram_mib=8,vram_mib=0,disk_mib=1),health_check='fixture.health',**changes)
    return spec,archive


def manager_for(root, public, envelope, fault=lambda stage:None):
    trusted = TrustPolicy(1,'test-catalog',1,{'test-key':public},frozenset(),('https://example.invalid',))
    verifier = CatalogVerifier(trusted,lambda:NOW)
    registry = ComponentRegistry(Path(root)/'state')
    return ComponentManager(registry,verifier,HOST,{'fixture.health':health},reserve_bytes=0,fault=fault)


def crashing_install(root, public, envelope, key, archive, stage, repair=False):
    def fault(point):
        if point==stage:os._exit(86)
    manager_for(root,public,envelope,fault).install(envelope,*key,archive,repair=repair)


def crashing_remove(root, public, envelope, key, stage):
    def fault(point):
        if point==stage:os._exit(87)
    manager_for(root,public,envelope,fault).remove(*key)


def hold_lease(root, public, envelope, component_id, ready, finish):
    manager = manager_for(root,public,envelope)
    with manager.lease(envelope,component_id):
        ready.set()
        finish.wait(20)


def crash_with_lock(path, ready):
    with file_lock(path,exclusive=True):
        ready.set()
        os._exit(88)


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)/'中文元件測試';self.root.mkdir()
        self.spec,self.archive = bundle(self.root/'external')
        self.new,self.new_archive = bundle(self.root/'external',version='2.0.0')
        self.key = Ed25519PrivateKey.generate();self.public=self.key.public_key().public_bytes_raw()
        self.envelope = sign(self.key,[self.spec,self.new])
        self.manager = manager_for(self.root,self.public,self.envelope)
        self.registry = self.manager.registry

    def install(self, spec=None, archive=None, **options):
        return self.manager.install(self.envelope,*(spec or self.spec).key,archive or self.archive,**options)

    def assert_active(self, version='1.0.0'):
        with self.manager.lease(self.envelope,self.spec.component_id) as lease:
            self.assertEqual(str(lease.spec.version),version)
            verify_tree(lease.directory,lease.spec)

    def test_install_verified_stage_health_active_and_lease(self):
        source=self.archive.read_bytes();result=self.install()
        self.assertEqual(result.state,'ready');self.assertEqual(self.archive.read_bytes(),source)
        self.assertEqual(self.registry.get(*self.spec.key).state,ComponentState.READY)
        self.assertIsNotNone(self.manager.store.owned(self.spec));self.assertEqual(self.manager.store.journals(),())
        self.assert_active();self.assertEqual(list(self.manager.staging.iterdir()),[])

    def test_update_retains_old_version_and_rollback_rechecks_both(self):
        self.install();result=self.install(self.new,self.new_archive)
        self.assertEqual(result.previous_version,'1.0.0');self.assert_active('2.0.0')
        verify_tree(self.registry.installation_path(self.spec),self.spec)
        self.manager.rollback(self.envelope,self.spec.component_id);self.assert_active('1.0.0')
        self.manager.rollback(self.envelope,self.spec.component_id);self.assert_active('2.0.0')

    def test_no_rollback_without_previous_version(self):
        self.install()
        with self.assertRaises(LifecycleError):self.manager.rollback(self.envelope,self.spec.component_id)
        self.assert_active()

    def test_existing_install_is_revalidated_without_reextracting(self):
        self.install()
        with patch('desktop_app.components.lifecycle.extract_archive',side_effect=AssertionError('must reuse')):
            self.install()
        self.assert_active()

    def test_unknown_existing_directory_is_not_adopted_or_deleted(self):
        target=self.registry.installation_path(self.spec);target.mkdir(parents=True)
        unknown=target/'使用者文件.txt';unknown.write_text('保留')
        with self.assertRaises(LifecycleError):self.install()
        with self.assertRaises(LifecycleError):self.manager.remove(*self.spec.key)
        self.assertEqual(unknown.read_text(),'保留')

    def test_incompatible_host_rejects_before_installation(self):
        self.manager.host=replace(HOST,architecture='arm64')
        with self.assertRaises(LifecycleError):self.install()
        self.assertFalse(self.registry.installation_path(self.spec).exists())

    def test_bad_archive_hash_never_touches_old_active(self):
        self.install();self.new_archive.write_bytes(b'corrupt')
        with self.assertRaises(IntegrityError):self.install(self.new,self.new_archive)
        self.assert_active();self.assertEqual(self.manager.store.journals(),())

    def test_staging_health_failure_does_not_activate_or_replace_old(self):
        self.install()
        self.manager.health_checks={'fixture.health':lambda *a:HealthResult(False,'unhealthy')}
        with self.assertRaises(LifecycleError):self.install(self.new,self.new_archive)
        self.manager.health_checks={'fixture.health':health}
        self.assert_active();self.assertFalse(self.registry.installation_path(self.new).exists())

    def test_unknown_probe_and_post_publish_failure_roll_back(self):
        self.install();calls=[]
        def probe(spec,path,host):
            if spec==self.new:
                calls.append(path)
                if path==self.registry.installation_path(spec):return HealthResult(False,'relocation failure')
            return health(spec,path,host)
        self.manager.health_checks={'fixture.health':probe}
        with self.assertRaises(LifecycleError):self.install(self.new,self.new_archive)
        self.assertGreaterEqual(len(calls),2);self.assert_active()
        self.manager.health_checks={}
        with self.assertRaises(LifecycleError):self.install(self.new,self.new_archive)

    def test_health_probe_modifying_payload_is_rejected(self):
        def probe(spec,path,host):
            (path/MODEL).write_bytes(b'modified')
            return HealthResult(True)
        self.manager.health_checks={'fixture.health':probe}
        with self.assertRaises(IntegrityError):self.install()
        self.assertFalse(self.registry.installation_path(self.spec).exists())

    def test_insufficient_space_and_cancellation_leave_old_unchanged(self):
        self.install()
        with patch('desktop_app.components.lifecycle.shutil.disk_usage',return_value=SimpleNamespace(free=1)):
            with self.assertRaises(LifecycleError):self.install(self.new,self.new_archive)
        cancel=Event();cancel.set()
        with self.assertRaises(Cancelled):self.install(self.new,self.new_archive,cancel=cancel)
        self.assert_active()

    def test_cancel_after_publish_rolls_back_directory_and_registry(self):
        self.install();cancel=Event()
        self.manager.fault=lambda stage:cancel.set() if stage=='published' else None
        with self.assertRaises(Cancelled):self.install(self.new,self.new_archive,cancel=cancel)
        self.assertFalse(self.registry.installation_path(self.new).exists());self.assert_active()

    def test_exception_at_each_precommit_stage_automatically_rolls_back(self):
        self.install()
        for stage in ('journaled','staged','published','registered'):
            with self.subTest(stage=stage):
                def fault(point):
                    if point==stage:raise OSError('simulated failure')
                self.manager.fault=fault
                with self.assertRaises(OSError):self.install(self.new,self.new_archive)
                self.assert_active();self.assertFalse(self.registry.installation_path(self.new).exists())
                self.assertEqual(self.manager.store.journals(),())
        self.manager.fault=lambda point:None

    def test_database_commit_failure_restores_old_active_and_payload(self):
        self.install()
        with patch.object(self.manager.store,'commit',side_effect=LifecycleError('disk full')):
            with self.assertRaises(LifecycleError):self.install(self.new,self.new_archive)
        self.assert_active();self.assertFalse(self.registry.installation_path(self.new).exists())

    def test_revocation_before_commit_cannot_switch_active_version(self):
        self.install();trusted=self.manager.verifier.policy
        def fault(stage):
            if stage=='registered':self.manager.verifier.policy=replace(trusted,revoked_keys=frozenset({'test-key'}))
        self.manager.fault=fault
        with self.assertRaises(CatalogError):self.install(self.new,self.new_archive)
        self.manager.verifier.policy=trusted;self.assert_active()
        self.assertFalse(self.registry.installation_path(self.new).exists())

    def test_existing_transaction_directory_is_not_taken_over(self):
        base=self.manager.staging/('a'*32);base.mkdir(parents=True)
        unknown=base/'使用者資料';unknown.write_text('保留')
        with patch('desktop_app.components.lifecycle.uuid.uuid4',return_value=SimpleNamespace(hex='a'*32)):
            with self.assertRaises(LifecycleError):self.install()
        self.assertEqual(unknown.read_text(),'保留');self.assertEqual(self.manager.store.journals(),())

    def test_repair_missing_and_changed_known_files(self):
        self.install();target=self.registry.installation_path(self.spec)
        (target/MODEL).write_bytes(b'changed')
        self.manager.repair(self.envelope,*self.spec.key,self.archive);self.assert_active()
        (target/MODEL).unlink()
        self.manager.repair(self.envelope,*self.spec.key,self.archive);self.assert_active()
        shutil.rmtree(target)
        self.manager.repair(self.envelope,*self.spec.key,self.archive);self.assert_active()

    def test_repair_failure_after_old_move_restores_modified_original(self):
        self.install();target=self.registry.installation_path(self.spec);old=b'original modified bytes'
        (target/MODEL).write_bytes(old)
        def fault(stage):
            if stage=='old_moved':raise OSError('rename failure')
        self.manager.fault=fault
        with self.assertRaises(OSError):self.manager.repair(self.envelope,*self.spec.key,self.archive)
        self.assertEqual((target/MODEL).read_bytes(),old)
        self.assertEqual(self.manager.store.active()[self.spec.component_id][0],'1.0.0')

    def test_repair_and_remove_refuse_unknown_files_or_empty_directories(self):
        self.install();target=self.registry.installation_path(self.spec)
        for name,is_dir in (('notes.txt',False),('私人目錄',True)):
            item=target/name
            if is_dir:item.mkdir()
            else:item.write_text('保留')
            with self.assertRaises(IntegrityError):self.manager.repair(self.envelope,*self.spec.key,self.archive)
            with self.assertRaises(IntegrityError):self.manager.remove(*self.spec.key)
            self.assertTrue(item.exists())
            if is_dir:item.rmdir()
            else:item.unlink()
        self.assert_active()

    def test_remove_verified_optional_component_preserves_external_files(self):
        self.install();unknown=self.root/'使用者文件.txt';unknown.write_text('保留')
        source=self.archive.read_bytes();result=self.manager.remove(*self.spec.key)
        self.assertEqual(result.state,'missing');self.assertEqual(unknown.read_text(),'保留')
        self.assertEqual(self.archive.read_bytes(),source)
        self.assertFalse(self.registry.installation_path(self.spec).exists())
        self.assertFalse(self.registry.get(*self.spec.key).installed)
        with self.assertRaises(LifecycleError):
            with self.manager.lease(self.envelope,self.spec.component_id):pass

    def test_remove_modified_known_file_refuses_until_explicit_repair(self):
        self.install();target=self.registry.installation_path(self.spec);(target/MODEL).write_bytes(b'user edited')
        with self.assertRaises(IntegrityError):self.manager.remove(*self.spec.key)
        self.assertEqual((target/MODEL).read_bytes(),b'user edited')

    def test_cancel_remove_after_directory_move_restores_original(self):
        self.install();cancel=Event()
        self.manager.fault=lambda stage:cancel.set() if stage=='old_moved' else None
        with self.assertRaises(Cancelled):self.manager.remove(*self.spec.key,cancel=cancel)
        self.assert_active();self.assertEqual(self.manager.store.journals(),())
        cancel.set()
        with self.assertRaises(Cancelled):self.manager.activate(self.envelope,*self.spec.key,cancel=cancel)

    def test_required_component_cannot_be_removed(self):
        required,archive=bundle(self.root/'external','required',required=True)
        envelope=sign(self.key,[required]);manager=manager_for(self.root,self.public,envelope)
        manager.install(envelope,*required.key,archive)
        with self.assertRaises(LifecycleError):manager.remove(*required.key)
        verify_tree(manager.registry.installation_path(required),required)

    def test_dependencies_must_be_active_healthy_and_protected_from_removal(self):
        dependency,archive=bundle(self.root/'external','runtime')
        parent,parent_archive=bundle(self.root/'external','parent',dependencies=[dict(component_id='runtime',versions=dict(minimum='1.0.0',maximum_exclusive='2.0.0'))])
        envelope=sign(self.key,[dependency,parent]);manager=manager_for(self.root,self.public,envelope)
        with self.assertRaises(LifecycleError):manager.install(envelope,*parent.key,parent_archive)
        manager.install(envelope,*dependency.key,archive);manager.install(envelope,*parent.key,parent_archive)
        with self.assertRaises(LifecycleError):manager.remove(*dependency.key)
        manager.remove(*parent.key);manager.remove(*dependency.key)

    def test_runtime_update_cannot_break_active_dependent_version_range(self):
        dependency,archive=bundle(self.root/'external','runtime')
        next_runtime,next_archive=bundle(self.root/'external','runtime','2.0.0')
        parent,parent_archive=bundle(self.root/'external','parent',dependencies=[dict(component_id='runtime',versions=dict(minimum='1.0.0',maximum_exclusive='2.0.0'))])
        envelope=sign(self.key,[dependency,next_runtime,parent]);manager=manager_for(self.root,self.public,envelope)
        manager.install(envelope,*dependency.key,archive);manager.install(envelope,*parent.key,parent_archive)
        with self.assertRaises(LifecycleError):manager.install(envelope,*next_runtime.key,next_archive)
        self.assertEqual(manager.store.active()['runtime'][0],'1.0.0')
        with manager.lease(envelope,'parent'):pass

    def test_lease_blocks_all_maintenance_but_allows_shared_readers(self):
        self.install()
        with self.manager.lease(self.envelope,self.spec.component_id):
            with self.manager.lease(self.envelope,self.spec.component_id):pass
            for operation in (lambda:self.install(self.new,self.new_archive),
                              lambda:self.manager.remove(*self.spec.key),
                              lambda:self.manager.repair(self.envelope,*self.spec.key,self.archive),
                              self.manager.recover):
                with self.assertRaises(ComponentBusy):operation()
        self.install(self.new,self.new_archive);self.assert_active('2.0.0')

    def test_expired_catalog_cannot_install_activate_or_lease(self):
        self.install();self.manager.verifier.policy=replace(self.manager.verifier.policy,revoked_keys=frozenset({'test-key'}))
        with self.assertRaises(CatalogError):self.install(self.new,self.new_archive)
        with self.assertRaises(CatalogError):self.manager.activate(self.envelope,*self.spec.key)
        with self.assertRaises(CatalogError):
            with self.manager.lease(self.envelope,self.spec.component_id):pass
        self.manager.remove(*self.spec.key)  # 移除不執行元件，可清除已撤銷但仍可確認所有權的軟體。

    def test_symlink_payload_is_not_followed_for_install_repair_or_remove(self):
        self.install();target=self.registry.installation_path(self.spec);source=self.root/'外部檔案';source.write_bytes(b'private')
        (target/MODEL).unlink()
        try:(target/MODEL).symlink_to(source)
        except OSError as exc:self.skipTest(str(exc))
        with self.assertRaises(IntegrityError):self.manager.repair(self.envelope,*self.spec.key,self.archive)
        with self.assertRaises(IntegrityError):self.manager.remove(*self.spec.key)
        self.assertEqual(source.read_bytes(),b'private')

    def test_corrupt_future_or_unknown_lifecycle_metadata_is_not_reset(self):
        with sqlite3.connect(self.manager.store.database) as db:db.execute('PRAGMA user_version=99')
        before=self.manager.store.database.read_bytes()
        with self.assertRaises(LifecycleError):LifecycleStore(self.registry.directory)
        self.assertEqual(self.manager.store.database.read_bytes(),before)

    def test_malformed_journal_cannot_choose_arbitrary_path_for_recovery(self):
        with self.manager.store.connection() as db:
            db.execute('INSERT INTO journal VALUES (?,?)',('bad','{"path":"/tmp/private"}'))
        with self.assertRaises(LifecycleError):self.manager.recover()
        with self.manager.store.connection() as db:self.assertEqual(db.execute('SELECT COUNT(*) FROM journal').fetchone()[0],1)

    def test_crash_at_each_install_stage_recovers_old_or_committed_version(self):
        self.install()
        context=multiprocessing.get_context('spawn')
        for stage in ('journaled','staged','published','registered','committed'):
            with self.subTest(stage=stage):
                worker=context.Process(target=crashing_install,args=(str(self.root),self.public,self.envelope,
                    self.new.key,str(self.new_archive),stage))
                worker.start();joined(worker)
                self.assertEqual(worker.exitcode,86)
                observed(worker,'install',stage)
                reopened=manager_for(self.root,self.public,self.envelope);self.manager=reopened;self.registry=reopened.registry
                self.assertTrue(reopened.store.journals())
                with self.assertRaises(LifecycleError):
                    with reopened.lease(self.envelope,self.spec.component_id):pass
                self.assertTrue(reopened.recover());self.assertEqual(reopened.recover(),())
                self.assert_active('2.0.0' if stage=='committed' else '1.0.0')
        self.assertTrue(self.registry.installation_path(self.spec).exists())

    def test_crash_during_repair_and_remove_restores_precommit_and_finishes_commit(self):
        self.install();context=multiprocessing.get_context('spawn')
        target=self.registry.installation_path(self.spec);(target/MODEL).write_bytes(b'pre-repair')
        worker=context.Process(target=crashing_install,args=(str(self.root),self.public,self.envelope,
             self.spec.key,str(self.archive),'old_moved',True))
        worker.start();joined(worker);self.assertEqual(worker.exitcode,86)
        observed(worker,'repair','old_moved')
        self.manager.recover();self.assertEqual((target/MODEL).read_bytes(),b'pre-repair')
        self.manager.repair(self.envelope,*self.spec.key,self.archive)
        for stage in ('old_moved','registered','committed'):
            worker=context.Process(target=crashing_remove,args=(str(self.root),self.public,self.envelope,self.spec.key,stage))
            worker.start();joined(worker);self.assertEqual(worker.exitcode,87)
            observed(worker,'remove',stage)
            self.manager.recover()
            if stage=='committed':self.assertFalse(target.exists())
            else:self.assert_active()

    def test_cross_process_lease_blocks_update_until_process_is_killed(self):
        self.install();context=multiprocessing.get_context('spawn');ready=context.Event();finish=context.Event()
        worker=context.Process(target=hold_lease,args=(str(self.root),self.public,self.envelope,self.spec.component_id,ready,finish))
        worker.start()
        try:
            self.assertTrue(ready.wait(10))
            with self.assertRaises(ComponentBusy):self.install(self.new,self.new_archive)
            worker.kill();joined(worker,10)
            observed(worker,'lease','killed_while_in_use')
            self.install(self.new,self.new_archive);self.assert_active('2.0.0')
        finally:
            if worker.is_alive():worker.kill();worker.join()

    def test_c05_offline_cache_flows_into_c06_and_does_not_change_source(self):
        service=DownloadService(self.root/'cache',self.manager.verifier,self.registry,reserve_bytes=0)
        result=service.import_offline(self.envelope,*self.spec.key,self.archive)
        self.assertEqual(self.registry.get(*self.spec.key).state,ComponentState.VERIFIED)
        self.install(archive=result.path);self.assert_active()

    def test_deep_manifest_is_bounded_before_creating_transaction(self):
        files=tuple(FileSpec(f'p{index}/'+('/'.join(f'd{level}' for level in range(30)))+'/f',hashlib.sha256(b'x').hexdigest(),1)
                    for index in range(300))
        license_file=next(item for item in self.spec.files if item.path=='LICENSE.txt')
        spec=replace(self.spec,files=(*files,license_file),unpacked_bytes=300+license_file.size)
        envelope=sign(self.key,[spec])
        with self.assertRaises(IntegrityError):self.manager.install(envelope,*spec.key,self.archive)
        self.assertEqual(self.manager.store.journals(),());self.assertFalse(self.manager.staging.exists())


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name);self.spec,self.archive=bundle(self.root/'source')

    def test_valid_zip_exact_files_and_bytes(self):
        destination=self.root/'payload';extract_archive(self.archive,destination,self.spec)
        verify_tree(destination,self.spec)

    def test_zip_paths_links_duplicates_extras_and_missing_are_rejected(self):
        variants=[('../escape',b'x',None),('/absolute',b'x',None),('CON.txt',b'x',None),
                  ('x:y',b'x',None),('file\\escape',b'x',None),('extra.txt',b'x',None),
                  ('linked',b'/tmp/private',stat.S_IFLNK|0o777)]
        for index,(name,data,mode) in enumerate(variants):
            archive=self.root/f'bad-{index}.zip'
            with zipfile.ZipFile(archive,'w') as output:
                entry=zipfile.ZipInfo(name)
                if mode is not None:entry.external_attr=mode<<16
                output.writestr(entry,data)
            with self.subTest(name=name),self.assertRaises((ValueError,IntegrityError)):
                extract_archive(archive,self.root/f'output-{index}',self.spec)
            self.assertFalse((self.root/'escape').exists())

    def test_duplicate_and_case_conflicting_manifest_entries_are_rejected(self):
        archive=self.root/'duplicate.zip'
        with zipfile.ZipFile(self.archive) as original,zipfile.ZipFile(archive,'w') as output:
            for entry in original.infolist():output.writestr(entry,original.read(entry))
            output.writestr('license.TXT',b'extra')
        with self.assertRaises(IntegrityError):extract_archive(archive,self.root/'output',self.spec)

    def test_declared_file_size_hash_and_unpacked_limit_are_enforced(self):
        bad=replace(self.spec,files=tuple(replace(item,sha256='0'*64) if item.path==MODEL else item for item in self.spec.files))
        with self.assertRaises(IntegrityError):extract_archive(self.archive,self.root/'bad-hash',bad)
        path=self.root/'large.zip'
        with zipfile.ZipFile(path,'w') as output:output.writestr(MODEL,b'x'*100000)
        with self.assertRaises(IntegrityError):extract_archive(path,self.root/'large',self.spec)

    def test_zip64_multidisk_and_huge_central_directory_rejected_before_open(self):
        data=self.archive.read_bytes();index=data.rfind(b'PK\x05\x06')
        for name,offset,value,fmt in (('count',10,65535,'<H'),('directory',12,8*1024**2,'<I'),('disk',4,1,'<H')):
            changed=bytearray(data);struct.pack_into(fmt,changed,index+offset,value)
            path=self.root/(name+'.zip');path.write_bytes(changed)
            with self.assertRaises(IntegrityError),patch('desktop_app.components.archives.zipfile.ZipFile',side_effect=AssertionError('preflight must reject')):
                extract_archive(path,self.root/name,self.spec)

    def test_truncated_self_extracting_and_unsupported_compression_rejected(self):
        for index,data in enumerate((self.archive.read_bytes()[:-10],b'MZ'+self.archive.read_bytes(),b'not zip')):
            path=self.root/f'bad{index}.zip';path.write_bytes(data)
            with self.assertRaises(IntegrityError):extract_archive(path,self.root/f'dest{index}',self.spec)
        path=self.root/'bzip.zip'
        with zipfile.ZipFile(self.archive) as source,zipfile.ZipFile(path,'w',compression=zipfile.ZIP_BZIP2) as output:
            for entry in source.infolist():output.writestr(entry.filename,source.read(entry))
        with self.assertRaises(IntegrityError):extract_archive(path,self.root/'bzip',self.spec)

    def test_cancellation_is_propagated(self):
        def stop():raise Cancelled('test')
        with self.assertRaises(Cancelled):extract_archive(self.archive,self.root/'cancel',self.spec,stop)

    def test_local_zip64_headers_are_rejected(self):
        path=self.root/'zip64.zip'
        with zipfile.ZipFile(self.archive) as source,zipfile.ZipFile(path,'w') as output:
            for entry in source.infolist():
                with output.open(entry.filename,'w',force_zip64=True) as target:target.write(source.read(entry))
        with self.assertRaises(IntegrityError):extract_archive(path,self.root/'zip64',self.spec)


class LockAndCacheTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name)

    def add(self, cache, data, *, owned=True):
        digest=hashlib.sha256(data).hexdigest();path=cache.directory/(digest+'.archive');path.write_bytes(data)
        if owned:cache.record(path,digest,len(data))
        return path

    def test_kernel_lock_survives_file_presence_and_releases_on_real_exit(self):
        context=multiprocessing.get_context('spawn');ready=context.Event();path=self.root/'kernel.lock'
        worker=context.Process(target=crash_with_lock,args=(str(path),ready));worker.start()
        self.assertTrue(ready.wait(10));joined(worker,10);self.assertEqual(worker.exitcode,88)
        observed(worker,'kernel_lock','holder_exit')
        self.assertTrue(path.exists())
        with file_lock(path,exclusive=True):pass

    def test_unknown_nonempty_or_linked_lock_file_is_preserved(self):
        path=self.root/'lock';path.write_bytes(b'user data')
        with self.assertRaises(ValueError):
            with file_lock(path,exclusive=True):pass
        self.assertEqual(path.read_bytes(),b'user data')
        link=self.root/'link'
        try:link.symlink_to(path)
        except OSError as exc:self.skipTest(str(exc))
        with self.assertRaises(IntegrityError):
            with file_lock(link,exclusive=True):pass

    def test_quota_prunes_only_owned_valid_complete_oldest_cache(self):
        cache=CacheStore(self.root/'cache',quota_bytes=10)
        first=self.add(cache,b'a'*8);second=self.add(cache,b'b'*8)
        os.utime(first,(1,1));unknown=cache.directory/'使用者筆記.txt';unknown.write_text('保留')
        removed=cache.prune()
        self.assertEqual(removed,(first.name,));self.assertFalse(first.exists());self.assertTrue(second.exists())
        self.assertEqual(unknown.read_text(),'保留')

    def test_cache_lease_blocks_prune_and_keeps_archive(self):
        cache=CacheStore(self.root/'cache',quota_bytes=1);path=self.add(cache,b'package')
        with cache.archive_lease(path):
            with self.assertRaises(ComponentBusy):cache.prune()
        self.assertTrue(path.exists());cache.prune();self.assertFalse(path.exists())

    def test_unknown_or_modified_cache_and_resume_fragment_are_not_deleted(self):
        cache=CacheStore(self.root/'cache',quota_bytes=1)
        unknown=self.add(cache,b'unknown',owned=False)
        modified=self.add(cache,b'valid');modified.write_bytes(b'changed')
        partial=cache.directory/('a'*64+'.part');partial.write_bytes(b'part')
        with self.assertRaises(CacheQuotaError):cache.prune()
        self.assertTrue(unknown.exists());self.assertEqual(modified.read_bytes(),b'changed');self.assertTrue(partial.exists())
        (cache.directory/(modified.stem+'.receipt.json')).write_text('['*2000)
        with self.assertRaises(CacheQuotaError):cache.prune()
        self.assertTrue(modified.exists())

    def test_download_admission_obeys_quota_and_legacy_lock_is_not_guessed_stale(self):
        key=Ed25519PrivateKey.generate();spec,archive=bundle(self.root/'source');verifier=CatalogVerifier(policy(key),lambda:NOW)
        envelope=sign(key,[spec]);service=DownloadService(self.root/'cache',verifier,reserve_bytes=0,quota_bytes=1)
        with self.assertRaises(CacheQuotaError):service.import_offline(envelope,*spec.key,archive)
        legacy=service.directory/(spec.package_sha256+'.lock');legacy.touch()
        with self.assertRaises(DownloadBusy):service.import_offline(envelope,*spec.key,archive)
        self.assertTrue(legacy.exists());self.assertEqual(archive.stat().st_size,spec.download_bytes)
        known=self.add(service.cache,b'old cache still guarded by a legacy writer')
        (service.directory/(known.stem+'.lock')).touch()
        with self.assertRaises(CacheQuotaError):service.cache.prune()
        self.assertTrue(known.exists())

    def test_receipt_reservation_survives_publication_interruption(self):
        cache=CacheStore(self.root/'cache',quota_bytes=1)
        data=b'package';digest=hashlib.sha256(data).hexdigest()
        with cache.lock(digest,exclusive=True):
            cache.reserve(digest,len(data))
            path=cache.directory/(digest+'.archive');path.write_bytes(data)
        self.assertTrue(cache.has_receipt(path,len(data)))
        cache.prune();self.assertFalse(path.exists())

    def test_reserve_does_not_adopt_existing_file_or_accept_path_escape(self):
        cache=CacheStore(self.root/'cache');data=b'unknown';path=self.add(cache,data,owned=False)
        with self.assertRaises(IntegrityError):cache.reserve(path.stem,len(data))
        self.assertFalse(cache.has_receipt(path,len(data)));self.assertEqual(path.read_bytes(),data)
        with self.assertRaises(ValueError):cache.reserve('../escape',1)
        self.assertFalse((self.root/'escape.receipt.json').exists())

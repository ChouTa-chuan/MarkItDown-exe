"""CPU維護程序實際終止與新程序恢復；只操作自己spawn、握手相符的測試程序。"""
import argparse
import base64
from datetime import datetime,timedelta,timezone
from importlib import metadata,resources
import json
import multiprocessing
import os
from pathlib import Path
import platform
import sys
import tempfile
from threading import Event
import uuid
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from desktop_app.capabilities import HostContext
from desktop_app.component_workers.binding import CPUWorkerBinding
from desktop_app.components.archives import verify_tree
from desktop_app.components.catalog import CatalogVerifier,TrustPolicy,canonical_json
from desktop_app.components.contracts import ComponentSpec,Version
from desktop_app.components.downloads import DownloadService
from desktop_app.components.lifecycle import ComponentManager
from desktop_app.components.locks import ComponentBusy
from desktop_app.components.registry import ComponentRegistry
from desktop_app.core import State
from desktop_app.resources import MIB,Policy
from check_cpu_worker_acceptance import environment
from cpu_lifecycle_acceptance import require,rejected,digest

CASES=(('upgrade','published','1.0.0'),('upgrade','committed','1.0.1'),
       ('repair','old_moved','1.0.1'),('repair','published','1.0.1'),
       ('remove','old_moved','1.0.1'),('remove','committed',None))


def receive(process,connection,timeout=180):
    """有限等待；子程序提早死亡／傳輸中斷不得視為抵達停點。"""
    if not connection.poll(timeout):raise AssertionError('Owned child handshake timed out')
    try:value=connection.recv()
    except EOFError as exc:raise AssertionError('Owned child exited before handshake') from exc
    require(isinstance(value,dict) and 'error' not in value,'Owned child failed: '+str(value))
    require(value.get('pid')==process.pid,'Owned child PID mismatch')
    return value


def stopped(value,process,token,operation,stage):
    require(value==dict(type='stopped',pid=process.pid,token=token,operation=operation,stage=stage),
        'Owned child stop identity mismatch')
    require(process.is_alive(),'Child exited before parent termination')


def cleanup(process):
    if process.pid is None:return
    if process.is_alive():process.kill()
    process.join(20)
    require(not process.is_alive(),'Owned child did not terminate')


def maintenance_child(factory,root,public,catalog,spec,archive,operation,stage,token,connection):
    try:
        manager=factory(root,public,catalog)
        def fault(point):
            if point==stage:
                connection.send(dict(type='stopped',pid=os.getpid(),token=token,operation=operation,stage=stage))
                # 只在fault callback等待，父程序將真實終止此Process；不是在產品中os._exit模擬崩潰。
                Event().wait(180)
                raise RuntimeError('Parent did not terminate owned maintenance child')
        manager.fault=fault
        if operation=='upgrade':manager.install(catalog,*spec.key,archive)
        elif operation=='repair':manager.repair(catalog,*spec.key,archive)
        else:manager.remove(*spec.key)
        raise AssertionError('Maintenance missed the requested stop')
    except Exception as exc:connection.send(dict(pid=os.getpid(),error=type(exc).__name__+': '+str(exc)))
    finally:connection.close()


def recovery_child(factory,validator,root,public,catalog,new,archive,expected,token,connection):
    try:
        manager=factory(root,public,catalog);recovered=manager.recover()
        require(len(recovered)==1 and not manager.store.journals(),'Recovery did not finish exactly one transaction')
        active=manager.store.active().get(new.component_id,(None,))[0]
        require(active==expected,'Recovery chose the wrong committed state')
        require(manager.recover()==(),'Repeated recovery must be a no-op')
        if expected is None:
            require(not manager.registry.installation_path(new).exists(),'Committed removal left a payload')
            manager.install(catalog,*new.key,archive)
        final=expected or str(new.version)
        validation=validator(manager,catalog,root,final)
        require(isinstance(validation,dict) and validation.get('version')==final,'Recovery validation identity missing')
        connection.send(dict(type='recovered',pid=os.getpid(),token=token,active_after_recover=active,
            final_version=final,validation=validation,recovered_transactions=len(recovered),idempotent=True))
    except Exception as exc:connection.send(dict(pid=os.getpid(),error=type(exc).__name__+': '+str(exc)))
    finally:connection.close()


def exercise(factory,validator,public,catalog,old,new,packages,root,report_path):
    """Linux可用合成元件驗證程序／交易；只有外層Windows CLI能接受原生OCR結果。"""
    root=Path(root);report_path=Path(report_path);require(not report_path.exists(),'Use a fresh recovery report')
    require(str(old.version)=='1.0.0' and str(new.version)=='1.0.1','Unexpected recovery component pair')
    context=multiprocessing.get_context('spawn')
    report=dict(accepted=False,windows_executed=False,checks_passed=0,cases=[],
        process_termination_executed=False,transaction_checks_accepted=False,
        clean_machine_accepted=False,power_loss_accepted=False,os_reboot_executed=False,release_ready=False)
    report_path.parent.mkdir(parents=True,exist_ok=True)
    def save():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        for operation,stage,expected in CASES:
            report['current_check']=operation+'/'+stage;save()
            # 六案各用獨有暫存根目錄；先記錄結果再回收自己的合成資料，非產品通用清理。
            with tempfile.TemporaryDirectory(prefix=operation+'-'+stage+'-',dir=root) as temporary:
                case_root=Path(temporary)/'中文元件';manager=factory(case_root,public,catalog)
                service=DownloadService(case_root/'cache',manager.verifier,manager.registry,reserve_bytes=0)
                archives={spec.key:service.import_offline(catalog,*spec.key,packages[spec.key]).path for spec in (old,new)}
                hashes={key:digest(path) for key,path in archives.items()}
                fixtures={case_root/'合成文件.md':'保留文件\n'.encode(),case_root/'合成設定.json':b'{"fixture":true}\n'}
                for path,data in fixtures.items():
                    with path.open('xb') as output:output.write(data)
                initial=old if operation=='upgrade' else new
                manager.install(catalog,*initial.key,archives[initial.key])
                token=uuid.uuid4().hex;receiver,sender=context.Pipe(duplex=False)
                worker=context.Process(name='cpu-maintenance-probe',target=maintenance_child,args=(factory,case_root,public,catalog,new,
                    archives[new.key],operation,stage,token,sender))
                try:
                    worker.start();sender.close();message=receive(worker,receiver)
                    stopped(message,worker,token,operation,stage)
                    # 真核心鎖必須仍被安裝程序持有；不能在它活著時搶先恢復。
                    rejected(ComponentBusy,manager.recover)
                    require(len(manager.store.journals())==1,'Stop has no durable transaction')
                    worker.kill();worker.join(20)
                    require(not worker.is_alive() and worker.exitcode not in (None,0),'Owned child was not actually terminated')
                    killed_pid=worker.pid;exitcode=worker.exitcode
                finally:cleanup(worker);receiver.close();sender.close()
                receiver,sender=context.Pipe(duplex=False)
                recovered=context.Process(name='cpu-recovery-probe',target=recovery_child,args=(factory,validator,case_root,public,catalog,new,
                    archives[new.key],expected,token,sender))
                try:
                    recovered.start();sender.close();value=receive(recovered,receiver)
                    require(value.get('type')=='recovered' and value.get('token')==token,'Recovery handshake mismatch')
                    recovered.join(20);require(not recovered.is_alive() and recovered.exitcode==0,'Recovery child exit failed')
                    recovery_pid=recovered.pid
                finally:cleanup(recovered);receiver.close();sender.close()
                fresh=factory(case_root,public,catalog)
                require(not fresh.store.journals() and fresh.recover()==(),'Recovery journals remain')
                require(not list(fresh.staging.iterdir()),'Recovery staging payload remains')
                for spec in (old,new):
                    if fresh.store.owned(spec) is not None:verify_tree(fresh.registry.installation_path(spec),spec)
                for path,data in fixtures.items():require(path.read_bytes()==data,'Synthetic user data changed')
                for key,path in archives.items():require(digest(path)==hashes[key],'Original cached package changed')
                require(value['active_after_recover']==expected and value['final_version']==(expected or str(new.version)),
                    'Recovery result identity differs')
                report['cases'].append(dict(operation=operation,stage=stage,maintenance_pid=killed_pid,
                    termination_exitcode=exitcode,recovery_pid=recovery_pid,active_after_recover=expected,
                    final_version=value['final_version'],lock_rejected_while_alive=True,
                    recovered_transactions=1,idempotent=True,payload_verified=True,data_preserved=True,cache_unchanged=True))
                report['cases'][-1]['validation']=value['validation']
                report['checks_passed']=len(report['cases']);save()
        report.update(transaction_checks_accepted=True,process_termination_executed=True)
        report.pop('current_check',None);save()
    except Exception as exc:report['error']=type(exc).__name__+': '+str(exc);save();raise
    return report


def native_manager(root,public,catalog):
    registry=ComponentRegistry(Path(root)/'state')
    policy=TrustPolicy(1,'cpu-recovery-development',1,{'ephemeral':public},frozenset(),('https://example.invalid',))
    binding=CPUWorkerBinding(registry.directory/'.locks/worker-use.lock',Policy(budget=2048*MIB,reserve=0))
    def health(spec,directory,host):
        result=binding.health(spec,directory,host)
        require(result.passed,'Actual frozen recovery health failed: '+result.detail)
        return result
    host=HostContext(platform.system().lower(),'x86_64',Version.parse(metadata.version('markitdown-desktop')),Version.parse('1.0.0'))
    return ComponentManager(registry,CatalogVerifier(policy),host,{'onnx.cpu.health':health},reserve_bytes=0)


def native_validate(manager,catalog,root,version):
    binding=CPUWorkerBinding(manager.worker_guard_path,Policy(budget=2048*MIB,reserve=0))
    source=Path(resources.files('desktop_app').joinpath('data','worker-health.png'))
    result=binding.run_managed(manager,catalog,source,Path(root)/'恢復後原生OCR.md')
    require(result.state==State.COMPLETED,result.message)
    value=result.report;expected=json.loads(Path(resources.files('desktop_app').joinpath('data','worker-health.json')).read_bytes())['expected']
    require(value['component_version']==version and value['runtime']['frozen'],'Wrong frozen recovery worker version')
    require(value['providers']==['CPUExecutionProvider']*3 and expected in ' '.join(value['text'].split()),'Recovery OCR failed')
    return dict(version=value['component_version'],frozen=value['runtime']['frozen'],providers=value['providers'])


def acceptance(previous_package,package,report_path):
    if sys.platform!='win32':raise RuntimeError('Requires actual Windows execution')
    before=environment();require(not any(before['native_available'].values()),'Controller must not contain OCR/Qt')
    old=ComponentSpec.from_dict(json.loads((previous_package/'component.json').read_bytes()))
    new=ComponentSpec.from_dict(json.loads((package/'component.json').read_bytes()))
    key=Ed25519PrivateKey.generate();public=key.public_key().public_bytes_raw();now=datetime.now(timezone.utc)
    stamp=lambda value:value.strftime('%Y-%m-%dT%H:%M:%SZ')
    payload=dict(schema_version=1,catalog_id='cpu-recovery-development',revision=1,trust_policy_version=1,
        issued_at=stamp(now-timedelta(minutes=1)),expires_at=stamp(now+timedelta(hours=1)),components=[old.to_dict(),new.to_dict()])
    catalog=canonical_json(dict(payload=payload,signature=dict(algorithm='ed25519',key_id='ephemeral',
        value=base64.b64encode(key.sign(canonical_json(payload))).decode())))
    packages={old.key:previous_package/'onnx-cpu-ocr-development.zip',new.key:package/'onnx-cpu-ocr-development.zip'}
    with tempfile.TemporaryDirectory(prefix='markitdown-cpu-recovery-') as temporary,patch.dict(os.environ,{'PATH':''}):
        result=exercise(native_manager,native_validate,public,catalog,old,new,packages,Path(temporary),report_path)
    require(environment()==before,'Controller environment changed')
    require(all(case['validation']['frozen'] for case in result['cases']),'Not all recoveries used frozen OCR')
    result.update(accepted=True,windows_executed=True,source_version=metadata.version('markitdown-desktop'),
        actual_frozen=True,controller_unchanged=True,controller_native_packages=False,
        gpu_executed=False,traditional_chinese_quality_passed=False)
    Path(report_path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-package',type=Path,required=True);parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    acceptance(args.previous_package,args.package,args.report)

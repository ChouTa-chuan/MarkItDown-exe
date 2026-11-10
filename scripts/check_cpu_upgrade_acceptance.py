"""Windows兩個獨立建置CPU版本的升級／明確回復；不把改描述或複製同一EXE當跨版。"""
import argparse
import base64
from datetime import datetime,timedelta,timezone
from importlib import metadata,resources
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Event
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from desktop_app.capabilities import HostContext
from desktop_app.components.archives import verify_tree
from desktop_app.components.catalog import CatalogVerifier,TrustPolicy,canonical_json
from desktop_app.components.contracts import ComponentSpec,Version
from desktop_app.components.downloads import DownloadService
from desktop_app.components.lifecycle import ComponentManager
from desktop_app.components.lifecycle_store import LifecycleError
from desktop_app.components.registry import ComponentRegistry
from desktop_app.component_workers.binding import CPUWorkerBinding
from desktop_app.core import Cancelled,State
from desktop_app.resources import MIB,Policy
from check_cpu_worker_acceptance import environment
from cpu_lifecycle_acceptance import digest,rejected,require

def exercise(manager,catalog,old,new,archives,root,report_path,ocr,health_observations):
    """交易情境可用合成ZIP測控制流程；真正frozen／精確版號由CLI的ocr回呼逐次驗證。"""
    require(old.component_id==new.component_id and old.version<new.version,'Invalid ordered component pair')
    root=Path(root);report_path=Path(report_path);require(not report_path.exists(),'Use a fresh upgrade report')
    data=root/'跨版保留合成文件.md';content='跨版本仍保留合成資料\n'.encode()
    with data.open('xb') as output:output.write(content)
    hashes={key:digest(path) for key,path in archives.items()}
    report=dict(accepted=False,checks_passed=0,checks=[],scope='cpu-component-cross-version',
        windows_executed=False,transaction_checks_accepted=False,
        process_termination_executed=False,clean_machine_accepted=False,release_ready=False)
    def save():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    def stable(version):
        require(manager.store.active().get(old.component_id,(None,))[0]==version,'Wrong active component version')
        require(not manager.store.journals(),'Unfinished cross-version transaction')
        for spec in (old,new):
            path=manager.registry.installation_path(spec)
            if manager.store.owned(spec) is not None:verify_tree(path,spec)
        require(data.read_bytes()==content,'Synthetic user document changed')
        for key,path in archives.items():require(digest(path)==hashes[key],'Original cached package changed')
    def install_old():
        manager.install(catalog,*old.key,archives[old.key]);ocr(str(old.version),'initial-old')
    def cancel_upgrade():
        cancel=Event();previous=manager.fault;seen=[]
        def fault(stage):
            previous(stage);seen.append(stage)
            if stage=='published':cancel.set()
        try:
            manager.fault=fault
            rejected(Cancelled,lambda:manager.install(catalog,*new.key,archives[new.key],cancel=cancel))
            require('published' in seen,'Candidate never reached cancellation point')
        finally:manager.fault=previous
        require(not manager.registry.installation_path(new).exists(),'Cancelled candidate remains installed')
        ocr(str(old.version),'after-cancelled-upgrade')
    def upgrade():
        result=manager.install(catalog,*new.key,archives[new.key])
        require(result.previous_version==str(old.version),'Previous version was not recorded')
        ocr(str(new.version),'upgraded-new')
    def pinned_old():
        before=len(health_observations)
        def lease():
            with manager.lease(catalog,old.component_id,expected_version=str(old.version)):pass
        rejected(LifecycleError,lease)
        require(len(health_observations)==before,'Pinned mismatch called the wrong health probe')
    def rollback():manager.rollback(catalog,old.component_id);ocr(str(old.version),'explicit-rollback-old')
    def return_new():manager.rollback(catalog,old.component_id);ocr(str(new.version),'explicit-return-new')
    def retire_old():
        manager.remove(*old.key)
        require(not manager.registry.installation_path(old).exists(),'Old payload still installed')
        rejected(LifecycleError,lambda:manager.rollback(catalog,old.component_id))
    def remove_new():
        manager.remove(*new.key)
        require(not manager.registry.installation_path(new).exists(),'New payload still installed')
        require(not manager.store.owned_keys(),'Component ownership remains after removal')
    cases=[('signed old install and OCR',install_old,str(old.version)),
        ('cancel published upgrade preserves old OCR',cancel_upgrade,str(old.version)),
        ('upgrade records previous version and runs new OCR',upgrade,str(new.version)),
        ('pinned old request rejects before health',pinned_old,str(new.version)),
        ('explicit rollback runs retained old worker',rollback,str(old.version)),
        ('explicit return runs retained new worker',return_new,str(new.version)),
        ('retire old clears rollback and preserves new',retire_old,str(new.version)),
        ('remove new preserves synthetic document and caches',remove_new,None)]
    report_path.parent.mkdir(parents=True,exist_ok=True);save()
    try:
        for label,operation,version in cases:
            report['current_check']=label;operation();stable(version)
            report['checks'].append(label);report['checks_passed']=len(report['checks']);save()
        # 交易案全過仍須等待CLI的真實frozen／版號序列與控制端環境檢查，不能提早接受原生驗收。
        report.update(transaction_checks_accepted=True,synthetic_data_preserved=True,archives_unchanged=True,journals_empty=True)
        report.pop('current_check',None);save()
    except Exception as exc:report['error']=type(exc).__name__+': '+str(exc);save();raise
    return report


def acceptance(previous_package,package,report_path):
    if sys.platform!='win32':raise RuntimeError('Requires actual Windows execution')
    report_path=Path(report_path);before=environment()
    require(not any(before['native_available'].values()),'Controller must not contain OCR/Qt')
    old=ComponentSpec.from_dict(json.loads((previous_package/'component.json').read_bytes()))
    new=ComponentSpec.from_dict(json.loads((package/'component.json').read_bytes()))
    require(old.key==('onnx-cpu-ocr','1.0.0') and new.key==('onnx-cpu-ocr','1.0.1'),'Unexpected package versions')
    require(old.package_sha256!=new.package_sha256,'Packages must differ')
    key=Ed25519PrivateKey.generate();now=datetime.now(timezone.utc)
    stamp=lambda value:value.strftime('%Y-%m-%dT%H:%M:%SZ')
    policy=TrustPolicy(1,'cpu-upgrade-development',1,{'ephemeral':key.public_key().public_bytes_raw()},
        frozenset(),('https://example.invalid',))
    payload=dict(schema_version=1,catalog_id=policy.catalog_id,revision=1,trust_policy_version=1,
        issued_at=stamp(now-timedelta(minutes=1)),expires_at=stamp(now+timedelta(hours=1)),components=[old.to_dict(),new.to_dict()])
    catalog=canonical_json(dict(payload=payload,signature=dict(algorithm='ed25519',key_id='ephemeral',
        value=base64.b64encode(key.sign(canonical_json(payload))).decode())))
    versions=[];healths=[]
    with tempfile.TemporaryDirectory(prefix='markitdown-cpu-upgrade-') as temporary:
        root=Path(temporary)/'中文跨版環境';registry=ComponentRegistry(root/'state')
        binding=CPUWorkerBinding(root/'state/.locks/worker-use.lock',Policy(budget=2048*MIB,reserve=0))
        def health(spec,directory,host):
            result=binding.health(spec,directory,host)
            healths.append(dict(version=str(spec.version),passed=result.passed))
            require(result.passed,'Actual frozen health failed: '+result.detail)
            return result
        verifier=CatalogVerifier(policy);host=HostContext('windows','x86_64',
            Version.parse(metadata.version('markitdown-desktop')),Version.parse('1.0.0'))
        manager=ComponentManager(registry,verifier,host,{'onnx.cpu.health':health},reserve_bytes=0)
        service=DownloadService(root/'cache',verifier,registry,reserve_bytes=0)
        archives={}
        for spec,directory in ((old,previous_package),(new,package)):
            archives[spec.key]=service.import_offline(catalog,*spec.key,directory/'onnx-cpu-ocr-development.zip').path
        source=Path(resources.files('desktop_app').joinpath('data','worker-health.png'))
        expected=json.loads(Path(resources.files('desktop_app').joinpath('data','worker-health.json')).read_bytes())['expected']
        def ocr(version,label):
            result=binding.run_managed(manager,catalog,source,root/(label+'.md'))
            require(result.state==State.COMPLETED,result.message)
            value=result.report
            require(value['component_version']==version and value['runtime']['frozen'],'Wrong actual worker identity')
            require(value['providers']==['CPUExecutionProvider']*3,'Wrong actual provider')
            require(expected in ' '.join(value['text'].split()),'Fixed English OCR failed')
            versions.append(version)
        with patch.dict(os.environ,{'PATH':''}):
            result=exercise(manager,catalog,old,new,archives,root,report_path,ocr,healths)
    require(environment()==before,'Controller package environment changed')
    require(versions==['1.0.0','1.0.0','1.0.1','1.0.0','1.0.1'],'Actual version sequence incomplete')
    result.update(accepted=True,source_version=metadata.version('markitdown-desktop'),windows_executed=True,
        previous_version='1.0.0',current_version='1.0.1',actual_ocr_versions=versions,
        actual_frozen=True,controller_unchanged=True,controller_native_packages=False,
        package_sha256={'1.0.0':old.package_sha256,'1.0.1':new.package_sha256},gpu_executed=False,
        traditional_chinese_quality_passed=False,cross_version_executed=True)
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--previous-package',type=Path,required=True);parser.add_argument('--package',type=Path,required=True)
    parser.add_argument('--report',type=Path,required=True);args=parser.parse_args()
    acceptance(args.previous_package,args.package,args.report)

"""C10 真實 PDF／Qt／frozen CPU 接線驗收；只使用合成文件及臨時簽章政策。"""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import metadata, resources
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from threading import Event
import time
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from PySide6.QtWidgets import QApplication
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from desktop_app.application import Runner
from desktop_app.components.catalog import TrustPolicy, canonical_json
from desktop_app.components.contracts import ComponentSpec
from desktop_app.components.management import ComponentManagement, TrustedSource
from desktop_app.conversion import convert_document
from desktop_app.core import Request, State
from desktop_app.desktop import Window
from desktop_app.resources import Policy, Snapshot, MIB, snapshot
from desktop_app.settings import Settings


def require(condition,message):
    if not condition: raise AssertionError(message)


def fixture_pdf(path, *, mixed=True):
    document=canvas.Canvas(str(path),pagesize=(800,600))
    document.drawString(40,550,'NATIVE CONTROL CONTENT PRESERVED 12345')
    cells=[['Item','Count','Total'],['Alpha','2','100'],['Beta','3','150']]
    for row,values in enumerate(cells):
        for col,text in enumerate(values):
            x,y=50+col*130,450-row*40
            document.rect(x,y,130,40);document.drawString(x+8,y+15,text)
    document.showPage()
    if mixed:
        document.showPage()  # 空白頁不能因缺元件而被送入 OCR。
        image=resources.files('desktop_app').joinpath('data/worker-health.png')
        document.drawImage(ImageReader(str(image)),20,250,width=760,height=170);document.showPage()
        document.drawString(40,550,'AFTER OCR ORIGINAL TEXT 98765');document.showPage()
    document.save()


def acceptance(package,output):
    output.mkdir(parents=True,exist_ok=True);app=QApplication.instance() or QApplication([])
    now=datetime.now(timezone.utc);stamp=lambda value:value.strftime('%Y-%m-%dT%H:%M:%SZ')
    key=Ed25519PrivateKey.generate();spec=ComponentSpec.from_dict(json.loads((package/'component.json').read_bytes()))
    # 驗收固定本次包的精確版號，不把歷史1.0.0寫死成新元件的要求。
    component_version=str(spec.version)
    policy=TrustPolicy(1,'c10-development',1,{'ephemeral':key.public_key().public_bytes_raw()},frozenset(),('https://example.invalid',))
    def signed(components,revision):
        payload=dict(schema_version=1,catalog_id='c10-development',revision=revision,trust_policy_version=1,
            issued_at=stamp(now-timedelta(minutes=1)),expires_at=stamp(now+timedelta(hours=1)),components=components)
        return canonical_json(dict(payload=payload,signature=dict(algorithm='ed25519',key_id='ephemeral',
            value=base64.b64encode(key.sign(canonical_json(payload))).decode())))
    settings=Settings(ram_budget_mib=2048,reserve_mib=0,ocr_backend='managed_cpu')
    events=[];outcomes=[];cancel_evidence=[];window=None
    with tempfile.TemporaryDirectory(prefix='markitdown-c10-') as temporary:
        root=Path(temporary)/'中文元件轉換';root.mkdir()
        service=ComponentManagement(root,source=TrustedSource(policy),settings=settings)
        catalog=root/'catalog.json';catalog.write_bytes(signed([spec.to_dict()],1))
        require(service.run('catalog_file',path=catalog).state=='completed','Catalog import failed')
        result=service.run('offline',spec.key,package/'onnx-cpu-ocr-development.zip')
        require(result.state=='completed',result.message)
        mixed=root/'混合文件.pdf';native=root/'原生表格.pdf';text=root/'中文.txt'
        fixture_pdf(mixed);fixture_pdf(native,mixed=False);text.write_text('基本文字流程仍可繼續。',encoding='utf-8')
        shutil.copyfile(mixed,output/'mixed-source.pdf');shutil.copyfile(native,output/'native-source.pdf')
        context=service.conversion_context();budget=Policy(budget=2048*MIB,reserve=0)
        ready=Event();paused=Event();release=Event()
        def notify(state,message):
            events.append(dict(state=state.value,message=message))
            if message.startswith('已固定受管 OCR'):ready.set()
            if state==State.PAUSED:paused.set()
        def pressure():
            value=snapshot()
            # reserve=0 且已配置階段 extra=0 時，available=0 本身不代表超預算；
            # 明確模擬程序樹用量超過 2 GiB，才能驗證上層回壓與恢復。
            return Snapshot(value.total,0,3072*MIB) if ready.is_set() and not release.is_set() else value
        try:
            with patch.dict(os.environ,{'PATH':'','TESSDATA_PREFIX':''}), ThreadPoolExecutor(max_workers=1) as executor:
                request=Request(mixed,root/'mixed.md',ocr_backend='managed_cpu',component_version=component_version)
                future=executor.submit(Runner(budget,read_snapshot=pressure,component_context=context).run,request,None,notify)
                try:
                    require(ready.wait(90),'Actual component lease was not acquired')
                    require(paused.wait(5),'RAM pressure did not pause conversion')
                    blocked=service.run('remove',spec.key)
                    require(blocked.state=='failed' and 'ComponentBusy' in blocked.message,'Live document did not protect its component')
                finally:release.set()
                outcome=future.result(timeout=120);outcomes.append(outcome)
                require(outcome.state==State.COMPLETED,outcome.message)
                evidence=outcome.components
                require(evidence and evidence[0]['frozen'] and evidence[0]['providers']==['CPUExecutionProvider']*3,
                        'Actual isolated CPU execution evidence missing')
                content=request.destination.read_text()
                require(content.count('route: native')==2 and content.count('route: blank')==1 and content.count('route: ocr')==1,'Per-page routing mismatch')
                require(content.count('source-component: onnx-cpu-ocr; version: '+component_version)==1,'Component provenance mismatch')
                for fragment in ('NATIVE CONTROL CONTENT PRESERVED 12345','AFTER OCR ORIGINAL TEXT 98765','WORKER HEALTH CHECK 12345','Alpha','Beta','100','150'):
                    require(fragment in content,'Missing original/recognized content: '+fragment)
                require('| Alpha | 2 | 100 |' in content and '| Beta | 3 | 150 |' in content,'Native table cell regression')
                shutil.copyfile(request.destination,output/'mixed-output.md')
                # 取消真正原生 OCR；不改用其他引擎，不留下正式輸出。
                cancel=Event();cancel_request=Request(mixed,root/'cancel.md',ocr_backend='managed_cpu')
                def cancellation(state,message):
                    if message.endswith('loading'):cancel.set()
                cancelled=Runner(budget,component_context=context).run(cancel_request,cancel,cancellation)
                require(cancelled.state==State.CANCELLED and not cancel_request.destination.exists(),'Native cancellation/atomic output failed')
                cancel_evidence=list(cancelled.components)
                # 提交進度在同一程序回呼中撤回版本，確定重驗發生在回呼之後。
                replacement=spec.to_dict();replacement['version']='2.0.0'
                def withdraw(stage):
                    if stage=='提交輸出':service.catalog_path.write_bytes(signed([replacement],2))
                withdrawn_request=Request(mixed,root/'withdrawn.md',ocr_backend='managed_cpu')
                rejected=False
                try:convert_document(withdrawn_request,lambda:None,withdraw,component_context=context,policy=budget)
                except ValueError:rejected=True
                require(rejected and not withdrawn_request.destination.exists(),'Withdrawn version published output')
                service.catalog_path.write_bytes(signed([spec.to_dict()],3))
                # GUI 使用相同可信來源快照跨 spawn，不替換 native runner／協定。
                window=Window(settings_path=root/'settings.json',component_service_factory=lambda directory,settings:ComponentManagement(directory,source=TrustedSource(policy),settings=settings))
                window.show();window.reserve.setValue(0);window.auto_budget.setChecked(False);window.budget.setValue(2048)
                window.backend.setCurrentIndex(window.backend.findData('managed_cpu'));window.managed_version.setText('2.0.0')
                window.add_sources([mixed,native,text]);window.output.setText(str(root/'batch'));window.start()
                deadline=time.monotonic()+60
                while window.job.isRunning() and time.monotonic()<deadline:app.processEvents();time.sleep(0.005)
                require(not window.job.isRunning(),'GUI batch timed out');app.processEvents()
                require([item.state for item in window.job.outcomes]==[State.FAILED,State.COMPLETED,State.COMPLETED],'Version failure stopped native/text batch')
                require('指定版本未啟用' in window.job.outcomes[0].message,'Pinned version failure was hidden')
                window.grab().save(str(output/'desktop-batch-isolation.png'))
                window.clear_sources();window.add_sources([mixed]);window.managed_version.setText(component_version);window.output.setText(str(root/'gui'));window.start()
                deadline=time.monotonic()+120
                while window.job.isRunning() and time.monotonic()<deadline:app.processEvents();time.sleep(0.005)
                require(not window.job.isRunning(),'GUI real managed conversion timed out');app.processEvents()
                require(window.job.outcomes[0].state==State.COMPLETED,window.status.text())
                require(window.job.outcomes[0].components[0]['frozen'],'GUI did not use actual frozen component')
                outcomes.extend(window.job.outcomes)
                window.grab().save(str(output/'desktop-managed-success.png'))
                shutil.copyfile(root/'gui/混合文件.pdf.md',output/'gui-mixed-output.md')
            require('onnxruntime' not in sys.modules and 'rapidocr_onnxruntime' not in sys.modules,'Controller imported optional OCR runtime')
            require(service.run('remove',spec.key).state=='completed','Completed document did not release lease')
            import psutil
            require(all(not psutil.pid_exists(item['pid']) for item in cancel_evidence if item['pid'] is not None),'Cancelled native process still running')
        finally:
            release.set()
            if window is not None:
                if window.job is not None and window.job.isRunning():window.cancel_batch();window.job.wait(15000)
                window.close();app.processEvents()
    report=dict(recorded_at=now.isoformat(),source_version=metadata.version('markitdown-desktop'),accepted=True,checks_passed=10,
        checks=['real signed offline install','native/blank/OCR page routing','frozen CPU provenance','original text/table and warnings retained',
                'RAM pause/resume and live lease blocks maintenance','native cancellation leaves no output','withdrawal before commit rejected',
                'GUI version failure isolates subsequent native/text files','GUI real managed conversion','lease release and controller runtime isolation'],
        package_sha256=spec.package_sha256,events=events,component_evidence=[asdict(item)['components'] for item in outcomes],
        cancel_evidence=cancel_evidence,ephemeral_key_not_saved=True,path_empty_during_conversion=True,
        windows_executed=False,gpu_executed=False,traditional_chinese_quality_passed=False,production_catalog_published=False)
    (output/'managed-native-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(accepted=True,checks=10,isolated_frozen_cpu=True)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();acceptance(args.package_directory,args.output)

"""C08 真正 Qt＋frozen CPU 驗收；只代入選檔路徑，不替換交易／推論服務。"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import sys
import tempfile
from threading import Event
import time
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QMessageBox

from desktop_app.component_dialog import ComponentDialog
from desktop_app.component_workers.binding import CPUWorkerBinding
from desktop_app.components.catalog import canonical_json, TrustPolicy
from desktop_app.components.contracts import ComponentSpec
from desktop_app.components.management import ComponentManagement, TrustedSource
from desktop_app.desktop import Window
from desktop_app.settings import Settings


def require(condition, message):
    if not condition: raise AssertionError(message)


def acceptance(package, output):
    output.mkdir(parents=True,exist_ok=True)
    app=QApplication.instance() or QApplication([])
    now=datetime.now(timezone.utc); stamp=lambda value:value.strftime('%Y-%m-%dT%H:%M:%SZ')
    key=Ed25519PrivateKey.generate()
    spec=ComponentSpec.from_dict(json.loads((package/'component.json').read_bytes()))
    policy=TrustPolicy(1,'c08-development',1,{'ephemeral':key.public_key().public_bytes_raw()},frozenset(),('https://example.invalid',))
    payload=dict(schema_version=1,catalog_id='c08-development',revision=1,trust_policy_version=1,
        issued_at=stamp(now-timedelta(minutes=1)),expires_at=stamp(now+timedelta(hours=1)),components=[spec.to_dict()])
    envelope=canonical_json(dict(payload=payload,signature=dict(algorithm='ed25519',key_id='ephemeral',
        value=base64.b64encode(key.sign(canonical_json(payload))).decode())))
    ticks=[]; observations=[]; loading=Event(); cancelled_pids=[]
    heartbeat=QTimer(); heartbeat.timeout.connect(lambda:ticks.append(time.monotonic())); heartbeat.start(20)
    def wait(dialog, maximum=180):
        deadline=time.monotonic()+maximum
        while dialog.busy() and time.monotonic()<deadline:
            app.processEvents(); time.sleep(0.005)
        if dialog.busy(): dialog.cancel(); dialog.job.wait(15000); raise AssertionError('Qt operation timed out')
        app.processEvents(); require(dialog.last_result is not None,'Missing GUI result')
        return dialog.last_result
    with tempfile.TemporaryDirectory(prefix='markitdown-c08-ui-') as temporary:
        root=Path(temporary)/'中文資料'; root.mkdir()
        catalog=root/'signed-catalog.json'; catalog.write_bytes(envelope)
        settings=Settings(ram_budget_mib=2048,reserve_mib=0)
        service=ComponentManagement(root,source=TrustedSource(policy),settings=settings)
        window=Window(settings_path=root/'settings.json'); window.show(); app.processEvents()
        dialog=ComponentDialog(service,window); window.component_dialog=dialog; dialog.show()
        original_runner=CPUWorkerBinding.runner
        class ObservedRunner:
            def __init__(self, runner): self.runner=runner
            def run(self,*args,**kwargs):
                original=kwargs.get('notify',lambda state,message:None)
                def notify(state,message):
                    if message.endswith('loading'): loading.set()
                    original(state,message)
                result=self.runner.run(*args,**{**kwargs,'notify':notify})
                observations.append(dict(state=result.state.value,pid=result.pid,report=result.report))
                return result
        try:
            wait(dialog)
            with patch('desktop_app.component_dialog.QFileDialog.getOpenFileName',return_value=(str(catalog),'')):
                dialog.catalog_button.click()
            require(wait(dialog).state=='completed','Signed catalog GUI import failed')
            require(dialog.table.topLevelItemCount()==1 and dialog.buttons['offline'].isEnabled(),'Component list/control mismatch')
            app.processEvents(); dialog.grab().save(str(output/'component-before-install.png'))
            # 只觀察真正 runner 回傳值，原 binding、IPC、交易、模型與原生推論均照常執行。
            with patch.object(CPUWorkerBinding,'runner',lambda binding,*args:ObservedRunner(original_runner(binding,*args))), \
                 patch.dict(os.environ,{'PATH':''}):
                with patch('desktop_app.component_dialog.QFileDialog.getOpenFileName',return_value=(str(package/'onnx-cpu-ocr-development.zip'),'')):
                    before=len(ticks); dialog.buttons['offline'].click()
                require(wait(dialog).state=='completed','Real frozen component GUI install failed')
                install_ticks=len(ticks)-before
                require(install_ticks>=5,'GUI event loop was not responsive during real install')
                require(dialog.selected().owned and dialog.selected().active,'Installed version is not owned/active')
                app.processEvents(); dialog.grab().save(str(output/'component-installed.png'))
                dialog.buttons['health'].click(); require(wait(dialog).state=='completed','Real GUI health failed')
                dialog.buttons['license'].click(); require(wait(dialog).state=='completed','Verified license GUI failed')
                require('Development-only ONNX CPU worker' in dialog.details.toPlainText(),'License text missing')
                app.processEvents(); dialog.grab().save(str(output/'component-license.png'))
                loading.clear(); dialog.buttons['health'].click()
                deadline=time.monotonic()+30
                while not loading.is_set() and dialog.busy() and time.monotonic()<deadline:
                    app.processEvents(); time.sleep(0.005)
                require(loading.is_set(),'Real native worker did not reach loading')
                dialog.cancel_button.click(); require(wait(dialog).state=='cancelled','Native health cancellation lost its state')
                cancelled_pids=[item['pid'] for item in observations if item['state']=='cancelled']
                require(cancelled_pids,'No actual cancelled worker observed')
                dialog.buttons['health'].click(); require(wait(dialog).state=='completed','Subsequent GUI health failed')
                with patch('desktop_app.component_dialog.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes):
                    dialog.buttons['remove'].click()
                require(wait(dialog).state=='completed' and not dialog.selected().owned,'GUI removal failed')
            require('onnxruntime' not in sys.modules and 'rapidocr_onnxruntime' not in sys.modules,
                    'GUI imported optional native OCR runtime')
            source=root/'來源.txt'; source.write_text('元件維護後，基本文字轉換仍可使用。',encoding='utf-8')
            window.add_sources([source]); window.output.setText(str(root/'output')); window.reserve.setValue(0)
            window.start(); deadline=time.monotonic()+30
            while window.job.isRunning() and time.monotonic()<deadline: app.processEvents(); time.sleep(0.01)
            require(not window.job.isRunning(),'Basic conversion timed out'); app.processEvents()
            require((root/'output/來源.txt.md').read_bytes()==source.read_bytes(),'Basic conversion changed')
            dialog.close(); app.processEvents(); window.grab().save(str(output/'desktop-with-component-entry.png'))
        finally:
            if dialog.busy(): dialog.cancel(); dialog.job.wait(15000)
            app.processEvents(); dialog.close()
            if window.job is not None and window.job.isRunning(): window.cancel_batch(); window.job.wait(15000)
            window.close(); heartbeat.stop(); app.processEvents()
    import psutil
    require(all(not psutil.pid_exists(pid) for pid in cancelled_pids),'Cancelled worker was left running')
    successful=[item for item in observations if item['state']=='completed']
    require(successful and all(item['report']['runtime']['frozen'] and item['report']['providers']==['CPUExecutionProvider']*3 for item in successful),
            'Native frozen CPU proof incomplete')
    report=dict(recorded_at=now.isoformat(),source_version=metadata.version('markitdown-desktop'),accepted=True,
        checks_passed=9,checks=['signed catalog GUI import','real frozen GUI offline install','UI heartbeat during real install',
        'real CPU health','verified original license in GUI','native health cancellation and child exit',
        'health succeeds after cancellation','confirmed GUI removal','basic text conversion after maintenance'],
        package_sha256=spec.package_sha256,package_bytes=spec.download_bytes,install_heartbeat_ticks=install_ticks,
        native_probe_observations=observations,control_process_imported_optional_ocr=False,
        path_empty_during_install_and_health=True,ephemeral_key_not_saved=True,windows_executed=False,gpu_executed=False,
        traditional_chinese_quality_passed=False,production_catalog_published=False,
        automation_scope='Qt offscreen; only file chooser/removal confirmation return values supplied; runner wrapper observes actual outcomes without replacing execution')
    (output/'ui-native-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(accepted=True,checks=9,native_probes=len(observations),install_heartbeat_ticks=install_ticks)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--package-directory',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True); args=parser.parse_args()
    acceptance(args.package_directory,args.output)

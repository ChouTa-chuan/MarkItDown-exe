"""C09 流程實測：真正 Qt／本機 Tesseract，預備模型不冒充已打包基本包。"""
import argparse
from dataclasses import asdict, replace
from datetime import datetime, timezone
import hashlib
from importlib import metadata, resources
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
from unittest.mock import patch

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from desktop_app.desktop import Window
from desktop_app.onboarding.service import SetupSession
from desktop_app.settings import Settings, load_settings, save_settings


def require(value,message):
    if not value: raise AssertionError(message)


def acceptance(models, output):
    output.mkdir(parents=True,exist_ok=True)
    app=QApplication.instance() or QApplication([])
    originals={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in models.iterdir() if p.is_file()}
    windows=[]; observations={}
    def pump(condition,timeout=40):
        deadline=time.monotonic()+timeout
        while condition() and time.monotonic()<deadline: app.processEvents(); time.sleep(0.005)
        require(not condition(),'Qt operation exceeded bounded wait'); app.processEvents()
    def launch(path):
        window=Window(settings_path=path); windows.append(window); window.show()
        QTimer.singleShot(0,window.offer_setup)
        pump(lambda:window.setup_dialog is None,5)
        pump(window.setup_dialog.busy)
        return window,window.setup_dialog
    def convert(window,source,directory):
        window.clear_sources(); window.add_sources([source]); window.output.setText(str(directory)); window.start()
        pump(lambda:window.job.isRunning(),60)
        require(window.files.topLevelItem(0).text(1)=='完成',window.status.text())
        return (directory/(source.name+'.md')).read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory(prefix='markitdown-c09-') as temporary:
        root=Path(temporary)/'中文首次設定'; root.mkdir()
        try:
            # 此處是驗收的預置條件，並非程式自行下載或安裝原生引擎。
            shutil.copytree(models,root/'models/tesseract')
            with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('must not connect')):
                window,dialog=launch(root/'settings.json')
                require(dialog.report.engine.ready,dialog.report.engine.message)
                observations['new_session']=asdict(dialog.report)
                require(len(dialog.report.engine.samples)==2,'Missing actual bilingual OCR')
                require(dialog.ram.isChecked() and dialog.engine.isChecked(),'New user recommendations not selected')
                app.processEvents(); dialog.grab().save(str(output/'setup-ready.png'))
                dialog.finish.click(); pump(dialog.busy)
                settings=load_settings(root/'settings.json')
                require(settings.onboarding_version==1 and not settings.allow_optional_downloads,'Completion/optional state mismatch')
                old_dialog=window.setup_dialog; window.offer_setup()
                require(window.setup_dialog is old_dialog and not old_dialog.isVisible(),'Completed setup reopened automatically')
                from PIL import Image
                assets=Path(resources.files('desktop_app').joinpath('data'))
                scan=root/'雙語掃描.pdf'
                with Image.open(assets/'worker-health.png') as english, Image.open(assets/'setup-chinese.png') as chinese:
                    english.convert('RGB').save(scan,'PDF',save_all=True,append_images=[chinese.convert('RGB')],resolution=144)
                shutil.copyfile(scan,output/'bilingual-scan.pdf')
                observations['scan_sha256']=hashlib.sha256(scan.read_bytes()).hexdigest()
                observations['saved_settings']=asdict(settings)
                with patch.dict(os.environ,{'PATH':'','TESSDATA_PREFIX':''}):
                    content=convert(window,scan,root/'output')
                require('WORKER HEALTH CHECK 12345' in content,'English scan failed')
                require('會議紀錄與資料轉換' in ''.join(content.split()),'Traditional Chinese scan failed')
                require(content.count('route: ocr')==2,'Expected two actual OCR pages')
                (output/'bilingual-scan.md').write_text(content,encoding='utf-8')
                app.processEvents(); window.grab().save(str(output/'desktop-after-setup.png'))
                # 既有使用者的後端／自備路徑及 RAM 不被首次設定覆寫。
                old_root=root/'existing'; old=Settings(ram_budget_mib=768,reserve_mib=123,
                    ocr_backend='onnx_verify',ocr_executable='explicit-missing-user-engine',ocr_data_dir='user-models',cpu_threads=3)
                save_settings(old,old_root/'settings.json')
                old_window,old_setup=launch(old_root/'settings.json')
                require(not old_setup.ram.isChecked() and not old_setup.engine.isChecked(),'Existing defaults changed')
                old_setup.finish.click(); pump(old_setup.busy)
                require(load_settings(old_root/'settings.json')==replace(old,onboarding_version=1),'Existing preferences overwritten')
                observations['existing_preferences_preserved']=True
                # 缺少基本引擎時只記錄未就緒；完成流程仍可轉文字，不能宣稱 OCR 可用。
                with patch.dict(os.environ,{'PATH':'','TESSDATA_PREFIX':''}):
                    missing_window,missing_setup=launch(root/'missing/settings.json')
                    require(not missing_setup.report.engine.ready,'Missing engine falsely reported ready')
                    observations['missing_engine']=asdict(missing_setup.report)
                    app.processEvents(); missing_setup.grab().save(str(output/'setup-missing-engine.png'))
                    missing_setup.finish.click(); pump(missing_setup.busy)
                    text=root/'仍可轉換.txt'; text.write_text('基本文字功能仍可使用。',encoding='utf-8')
                    missing_window.reserve.setValue(0)
                    require(convert(missing_window,text,root/'missing-output')==text.read_text(),'Missing OCR blocked text')
            require({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in models.iterdir() if p.is_file()}==originals,
                    'Original models changed')
        finally:
            for window in reversed(windows):
                if window.setup_dialog is not None and window.setup_dialog.busy():window.setup_dialog.reject();window.setup_dialog.job.wait(15000)
                if window.job is not None and window.job.isRunning():window.cancel_batch();window.job.wait(15000)
                app.processEvents();window.close()
    report=dict(recorded_at=datetime.now(timezone.utc).isoformat(),source_version=metadata.version('markitdown-desktop'),
        flow_accepted=True,full_c09_complete=False,checks_passed=9,
        checks=['production QTimer startup route','RAM recommendations','actual CPU bilingual probe',
        'persist setup and skip optional','completed startup does not repeat','two OCR PDF pages with empty PATH',
        'existing preferences preserved','missing engine does not block text','offline and original models unchanged'],
        observations=observations,tesseract_bundled=False,models_preseeded_for_acceptance=True,
        external_system_tesseract_used=True,windows_executed=False,gpu_executed=False,
        traditional_chinese_general_quality_passed=False,
        scope='Linux installed package and system native engine; not a clean-machine base installation or Windows/installer acceptance')
    (output/'flow-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(dict(flow_accepted=True,full_c09_complete=False,checks=9)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--models',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args();acceptance(args.models,args.output)

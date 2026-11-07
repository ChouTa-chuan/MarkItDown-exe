"""以固定四語模型及本機 Tesseract 實測，不冒充已內含 Windows 原生引擎。"""
import argparse
from dataclasses import asdict
from datetime import datetime,timezone
from importlib import metadata,resources
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from desktop_app.components.legacy_models import LegacyModelsAdapter
from desktop_app.core import Request,State
from desktop_app.languages import model_manifest
from desktop_app.models import digest
from desktop_app.resources import MIB,Policy
from desktop_app.settings import Settings,load_settings,save_settings


def accept(source_models,executable,output):
    if output.exists():raise FileExistsError(output)
    output.mkdir(parents=True);output=output.resolve();source_models=source_models.resolve();executable=executable.resolve()
    spec=model_manifest()
    for name,expected in spec['files'].items():assert digest(source_models/name)==expected,name
    asset_root=Path(resources.files('desktop_app').joinpath('data'))
    target=output/'models/tesseract-four-language-managed'
    adapter=LegacyModelsAdapter(target,managed=True,spec=spec)
    calls=[]
    def local_model_source(url,timeout):
        expected=f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{spec['commit']}/"
        assert url.startswith(expected);name=url[len(expected):];assert name in spec['files'];calls.append(name)
        return (source_models/name).open('rb')
    observed=adapter.install(opener=local_model_source);assert observed.models_available and len(calls)==5
    adapter.install(opener=lambda *a,**k:(_ for _ in ()).throw(AssertionError('unexpected download')))
    (output/'model-receipt.json').write_bytes((target/'.markitdown-model-owner.json').read_bytes())
    (output/'model-observation.json').write_text(json.dumps(asdict(observed),ensure_ascii=False,indent=2)+'\n')
    os.environ['PATH']='';os.environ['TESSDATA_PREFIX']=''
    from desktop_app.onboarding.service import SetupSession
    path=output/'settings.json';original=b'{"schema_version":6,"ram_budget_mib":2048,"reserve_mib":0,"cpu_threads":1}'
    path.write_bytes(original);old=load_settings(path);assert old.ocr_languages is None and old.schema_version==7
    save_settings(old,path);assert next(output.glob('settings.json.pre-v6-*.bak')).read_bytes()==original
    all_languages=('chi_tra','eng','jpn','kor')
    saved=Settings(ram_budget_mib=2048,reserve_mib=0,ocr_executable=str(executable),ocr_data_dir=str(target),ocr_languages=all_languages)
    save_settings(saved,path)
    setup=SetupSession(path).inspect();assert setup.engine.ready,setup.engine.message
    assert len(setup.engine.samples)==4
    (output/'four-language-health.json').write_text(json.dumps(asdict(setup.engine),ensure_ascii=False,indent=2)+'\n')
    from PIL import Image
    from desktop_app.application import Runner
    runner=Runner(Policy(budget=2048*MIB,reserve=0),max_resource_wait=15)
    references={};images=[];individual=[];output_quality=[]
    try:
        for language,stem in [('chi_tra','setup-chinese'),('eng','worker-health'),('jpn','setup-japanese'),('kor','setup-korean')]:
            reference=json.loads((asset_root/(stem+'.json')).read_text());expected=reference.get('expected',reference.get('reference'))
            references[language]=expected
            image=Image.open(asset_root/(stem+'.png')).convert('RGB');images.append(image)
            pdf=output/(language+'.pdf');image.save(pdf,'PDF',resolution=144)
            destination=output/(language+'.md')
            outcome=runner.run(Request(pdf,destination,ocr_executable=str(executable),ocr_data_dir=str(target),ocr_languages=(language,)))
            assert outcome.state==State.COMPLETED,outcome
            text=destination.read_text();exact=''.join(expected.split()) in ''.join(text.split())
            individual.append(dict(language=language,exact_reference=exact));assert exact,(language,text,expected)
            assert f'source-ocr-languages: {language}' in text
        mixed=output/'four-language-mixed.pdf';images[0].save(mixed,'PDF',resolution=144,save_all=True,append_images=images[1:])
        mixed_output=output/'four-language-mixed.md'
        outcome=runner.run(Request(mixed,mixed_output,ocr_executable=str(executable),ocr_data_dir=str(target),ocr_languages=all_languages))
        assert outcome.state==State.COMPLETED,outcome
        text=mixed_output.read_text();assert text.count('route: ocr')==4 and text.count('source-ocr-languages: chi_tra+eng+jpn+kor')==4
        # 混合品質另列，不為了通過功能驗收放寬原始字串或隱藏混字。
        pages=text.split('<!-- source-page: ')[1:]
        for language,page in zip(all_languages,pages):
            output_quality.append(dict(language=language,exact_reference=''.join(references[language].split()) in ''.join(page.split())))
    finally:
        for image in images:image.close()
    missing=output/'missing-models';missing.mkdir()
    for name in ['chi_tra.traineddata','eng.traineddata','LICENSE']:shutil.copyfile(source_models/name,missing/name)
    failed=runner.run(Request(output/'jpn.pdf',output/'missing.md',ocr_executable=str(executable),ocr_data_dir=str(missing),ocr_languages=('jpn',)))
    assert failed.state==State.FAILED and 'jpn' in failed.message and not (output/'missing.md').exists()
    blocked=runner.run(Request(output/'jpn.pdf',output/'unsupported.md',ocr_backend='onnx',ocr_languages=('jpn',)))
    assert blocked.state==State.FAILED and 'Tesseract' in blocked.message and not (output/'unsupported.md').exists()
    for language in ['jpn','kor']:
        result=subprocess.run([sys.executable,'-m','desktop_app.cli',str(output/(language+'.pdf')),str(output/(language+'-cli.md')),
            '--settings',str(path),'--ocr-languages',language],capture_output=True,text=True,timeout=120)
        (output/(language+'-cli.log')).write_text(result.stdout+result.stderr)
        assert result.returncode==0,result.stderr
        assert ''.join(references[language].split()) in ''.join((output/(language+'-cli.md')).read_text().split())
    from PySide6.QtWidgets import QApplication
    from desktop_app.desktop import Window
    from desktop_app.model_dialog import ModelDialog
    app=QApplication.instance() or QApplication([])
    window=Window(settings_path=path);window.show()
    try:
        window.languages.setCurrentIndex(window.languages.findData('jpn+eng'));window.save_preferences()
        assert load_settings(path).ocr_languages==('jpn','eng')
        window.add_sources([output/'jpn.pdf']);window.output.setText(str(output/'gui'));window.start()
        deadline=time.monotonic()+90
        while window.job and window.job.isRunning() and time.monotonic()<deadline:app.processEvents();time.sleep(.01)
        app.processEvents();assert window.job and not window.job.isRunning()
        assert window.job.outcomes[0].state==State.COMPLETED
        assert window.job.outcomes[0].request.ocr_languages==('jpn','eng')
        assert ''.join(references['jpn'].split()) in ''.join((output/'gui/jpn.pdf.md').read_text().split())
        assert window.grab().save(str(output/'desktop-japanese.png'))
        dialog=ModelDialog(target,window,managed_directory=target,four_languages=True);dialog.show();app.processEvents()
        try:
            assert all(state=='valid' for _,state in dialog.adapter.observe().states)
            assert dialog.grab().save(str(output/'four-language-models.png'))
        finally:dialog.close()
    finally:
        if window.job and window.job.isRunning():window.job.cancel.set();window.job.wait(15000)
        window.close();app.processEvents()
    note=target/'notes.txt';note.write_text('保留未知資料');adapter.remove();assert note.read_text()=='保留未知資料'
    assert not any((target/name).exists() for name in spec['files'])
    shutil.rmtree(missing)  # 本輪生成的唯讀測試副本，不保存模型 binary。
    report=dict(recorded_at=datetime.now(timezone.utc).isoformat(),source_version=metadata.version('markitdown-desktop'),
        check='C03-languages',accepted=True,checks_passed=10,checks=['pinned four-language source hashes','managed offline install/reuse',
        'v6-to-v7 exact backup','actual four-model health','four individual scan conversions','mixed four-page routing with quality observations',
        'missing/unsupported language failures','Japanese/Korean CLI','actual Qt selection/conversion/models','managed removal keeps unknown data'],
        individual=individual,mixed_quality=output_quality,model_source=spec,path_empty=True,frozen=False,
        native_executable_version=setup.engine.version,windows_executed=False,gpu_executed=False,
        native_ocr_bundled=False,full_c03_complete=False,release_ready=False)
    (output/'four-language-acceptance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print('Four-language native checks passed: 10; mixed quality:',output_quality)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--source-models',type=Path,required=True)
    parser.add_argument('--executable',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();accept(args.source_models,args.executable,args.output)

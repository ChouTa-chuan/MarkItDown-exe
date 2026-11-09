"""四語選擇與模型契約；合成資料僅驗接線，實際四語 OCR 另有原生驗收。"""
from dataclasses import replace
import hashlib
import io
import json
from pathlib import Path
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from desktop_app.core import Request
from desktop_app.languages import validate_languages,parse_languages,model_manifest
from desktop_app.settings import Settings,load_settings,save_settings
from desktop_app.components.legacy_models import LegacyModelsAdapter
from desktop_app.pdf_pipeline import _run_ocr


class LanguageTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)

    def test_valid_selection_and_legacy_are_distinct(self):
        self.assertIsNone(parse_languages('legacy'))
        self.assertEqual(parse_languages('kor+jpn+eng'),('kor','jpn','eng'))
        validate_languages(('chi_tra','eng','jpn','kor'))

    def test_invalid_duplicate_or_argument_injection_rejected(self):
        for value in [(),('jpn','jpn'),('jpn+eng',),('--psm',),['jpn'],('fra',),('jpn',True)]:
            with self.assertRaises(ValueError):validate_languages(value)

    def test_v6_migrates_without_changing_old_paths_or_default(self):
        path=self.root/'settings.json';raw=b'{"schema_version":6,"ocr_executable":"C:/OCR/tool.exe","ocr_data_dir":"C:/models","ocr_backend":"onnx","cpu_threads":3}'
        path.write_bytes(raw);saved=load_settings(path)
        self.assertEqual(saved.schema_version,7);self.assertIsNone(saved.ocr_languages)
        self.assertEqual(saved.ocr_executable,'C:/OCR/tool.exe');self.assertEqual(saved.ocr_backend,'onnx')
        self.assertEqual(path.read_bytes(),raw)
        save_settings(saved,path);backups=list(self.root.glob('*.bak'));self.assertEqual(len(backups),1)
        self.assertEqual(backups[0].read_bytes(),raw)

    def test_selected_order_survives_roundtrip(self):
        path=self.root/'settings.json';value=Settings(ocr_languages=('kor','jpn','eng'))
        save_settings(value,path);self.assertEqual(load_settings(path),value)

    def test_invalid_json_languages_never_overwrite_original(self):
        for value in ['jpn+eng',[],['jpn','jpn'],['--help']]:
            path=self.root/'settings.json';raw=json.dumps(dict(schema_version=7,ocr_languages=value)).encode();path.write_bytes(raw)
            with self.assertRaises(ValueError):save_settings(Settings(),path)
            self.assertEqual(path.read_bytes(),raw)

    def test_new_four_model_manifest_keeps_legacy_original(self):
        from desktop_app import models
        new=model_manifest();old=models.manifest()
        self.assertEqual(new['commit'],old['commit']);self.assertEqual(set(new['files']),{'chi_tra.traineddata','eng.traineddata','jpn.traineddata','kor.traineddata','LICENSE'})
        self.assertEqual(len(old['files']),3)
        for name,value in old['files'].items():self.assertEqual(new['files'][name],value)

    def test_four_model_adapter_install_reuse_and_unknown_file_preservation(self):
        payload={name:name.encode() for name in model_manifest()['files']}
        spec=dict(model_manifest(),files={name:hashlib.sha256(data).hexdigest() for name,data in payload.items()})
        adapter=LegacyModelsAdapter(self.root/'managed',managed=True,spec=spec)
        result=adapter.install(opener=lambda url,timeout:io.BytesIO(payload[url.rsplit('/',1)[-1]]))
        self.assertTrue(result.models_available);self.assertFalse(result.engine_ready)
        adapter.install(opener=lambda *a,**kw:self.fail('must reuse verified files'))
        note=adapter.directory/'notes.txt';note.write_text('保留');adapter.remove()
        self.assertEqual(note.read_text(),'保留');self.assertFalse(any((adapter.directory/name).exists() for name in spec['files']))

    def test_old_owned_model_directory_is_not_claimed_by_new_manifest(self):
        from desktop_app import models
        old=LegacyModelsAdapter(self.root/'managed',managed=True);old._claim_empty()
        new=LegacyModelsAdapter(old.directory,managed=True,spec=model_manifest())
        self.assertFalse(new.owns_directory());self.assertFalse(new.can_install())
        with self.assertRaises(PermissionError):new.install()

    def test_external_models_cannot_be_downloaded_or_removed(self):
        adapter=LegacyModelsAdapter(self.root,managed=False,spec=model_manifest())
        with self.assertRaises(PermissionError):adapter.install()
        with self.assertRaises(PermissionError):adapter.remove()

    def test_selected_missing_language_is_fatal_before_inference(self):
        with patch('desktop_app.pdf_pipeline.subprocess.run',return_value=SimpleNamespace(stdout='Available:\neng\nchi_tra\n')), \
             patch('desktop_app.pdf_pipeline.subprocess.Popen') as start:
            with self.assertRaisesRegex(RuntimeError,'jpn'):_run_ocr(None,lambda:None,lambda m:None,200,'/fixture/tesseract',languages=('jpn',))
            start.assert_not_called()

    def test_language_metadata_and_backend_gate_are_lazy_for_native_pdf(self):
        from desktop_app.conversion import convert_document
        from desktop_app.diagnostics import sample_pdf
        source=self.root/'native.pdf';sample_pdf(source);target=self.root/'out.md'
        convert_document(Request(source,target,ocr_backend='managed_cpu',ocr_languages=('jpn',)),lambda:None)
        self.assertIn('route: native',target.read_text());self.assertNotIn('source-ocr-languages',target.read_text())

    def test_non_tesseract_japanese_scan_does_not_load_other_engine(self):
        from PIL import Image
        from desktop_app.conversion import convert_document
        source=self.root/'scan.pdf'
        with Image.new('RGB',(1000,400),'white') as image:image.save(source,'PDF')
        with patch('desktop_app.onnx_ocr.OnnxOCR') as onnx:
            with self.assertRaisesRegex(RuntimeError,'日文／韓文'):
                convert_document(Request(source,self.root/'out.md',ocr_backend='onnx',ocr_languages=('jpn',)),lambda:None)
            onnx.assert_not_called()
        self.assertFalse((self.root/'out.md').exists())

    def test_new_health_assets_are_fixed_and_keep_reference_language(self):
        from importlib.resources import files
        for name,code in [('japanese','jpn'),('korean','kor')]:
            base=files('desktop_app').joinpath('data');raw=base.joinpath('setup-'+name+'.png').read_bytes()
            reference=json.loads(base.joinpath('setup-'+name+'.json').read_text())
            self.assertEqual(hashlib.sha256(raw).hexdigest(),reference['sha256']);self.assertEqual(reference['language'],code)

    def test_setup_checks_only_selected_models(self):
        from desktop_app.onboarding.service import probe_engine
        from importlib.resources import files
        calls=[];expected=json.loads(files('desktop_app').joinpath('data/setup-japanese.json').read_text())['expected']
        def command(args,*a,**kw):
            calls.append(args)
            if '--version' in args:return 'tesseract 5.5.0\n'
            if '--list-langs' in args:return 'Available:\njpn\n'
            return expected
        with patch('desktop_app.onboarding.service.native_command',side_effect=command):
            result=probe_engine(Settings(ocr_executable='/fixture/tess',ocr_data_dir=str(self.root),ocr_languages=('jpn',)),self.root,Event(),which=lambda name:name)
        self.assertTrue(result.ready,result.message);self.assertEqual(len(result.samples),1)
        self.assertEqual(calls[-1][calls[-1].index('-l')+1],'jpn')

    def test_setup_missing_language_does_not_claim_ready(self):
        from desktop_app.onboarding.service import probe_engine
        def command(args,*a,**kw):return 'tesseract 5.5.0' if '--version' in args else 'Available:\neng\n'
        with patch('desktop_app.onboarding.service.native_command',side_effect=command):
            result=probe_engine(Settings(ocr_executable='/fixture/tess',ocr_data_dir=str(self.root),ocr_languages=('kor',)),self.root,Event(),which=lambda name:name)
        self.assertFalse(result.ready);self.assertIn('kor',result.message)


class LanguageDesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
        from qt_support import release_test_widgets
        cls.addClassCleanup(release_test_widgets, cls.app)

    def test_language_preferences_and_custom_order_survive_other_saves(self):
        from desktop_app.desktop import Window
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json';save_settings(Settings(ocr_languages=('kor','jpn','eng')),path)
            window=Window(settings_path=path)
            try:
                self.assertEqual(window.languages.currentData(),'kor+jpn+eng')
                window.save_preferences();self.assertEqual(load_settings(path).ocr_languages,('kor','jpn','eng'))
            finally:window.close()

    def test_language_controls_follow_backend_and_batch_state(self):
        from desktop_app.desktop import Window
        with tempfile.TemporaryDirectory() as directory:
            window=Window(settings_path=Path(directory)/'settings.json')
            try:
                window.languages.setCurrentIndex(window.languages.findData('jpn+eng'))
                window.backend.setCurrentIndex(window.backend.findData('onnx'))
                self.assertFalse(window.languages.isEnabled());self.assertEqual(window.preferences().ocr_languages,('jpn','eng'))
                window.backend.setCurrentIndex(window.backend.findData('tesseract'));self.assertTrue(window.languages.isEnabled())
                window.set_running(True);self.assertFalse(window.languages.isEnabled())
                window.set_running(False);self.assertTrue(window.languages.isEnabled())
            finally:window.close()

    def test_four_model_dialog_keeps_external_directory_read_only(self):
        from desktop_app.model_dialog import ModelDialog
        with tempfile.TemporaryDirectory() as directory:
            dialog=ModelDialog(Path(directory),four_languages=True)
            try:
                self.assertEqual(len(dialog.adapter.spec['files']),5)
                self.assertFalse(dialog.download.isEnabled());self.assertFalse(dialog.remove_button.isEnabled())
            finally:dialog.close()

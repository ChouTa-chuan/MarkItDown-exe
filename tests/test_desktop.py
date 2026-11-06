import importlib.util
import os
from pathlib import Path
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@unittest.skipUnless(importlib.util.find_spec("PySide6"), "Install desktop dependencies")
class DesktopTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        from desktop_app.desktop import Window
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.window = Window(settings_path=self.root / "settings.json")
        self.addCleanup(self.window.close)

    def test_preferences_round_trip(self):
        from desktop_app.settings import load_settings
        self.window.auto_budget.setChecked(False)
        self.window.budget.setValue(768)
        self.window.reserve.setValue(512)
        self.window.save_preferences()
        saved = load_settings(self.root / "settings.json")
        self.assertEqual(saved.ram_budget_mib, 768)
        self.assertEqual(saved.reserve_mib, 512)

    def test_full_desktop_text_flow(self):
        source = self.root / "來源.txt"
        source.write_text("# 標題\n\n繁體中文測試", encoding="utf-8")
        self.window.add_sources([str(source), str(source)])
        self.assertEqual(len(self.window.sources), 1)
        self.window.output.setText(str(self.root / "output"))
        self.window.reserve.setValue(0)
        self.window.auto_budget.setChecked(False)
        self.window.budget.setValue(1024)
        self.window.start()
        self.assertFalse(self.window.start_button.isEnabled())
        deadline = time.monotonic() + 20
        while self.window.job.isRunning() and time.monotonic() < deadline:
            self.app.processEvents()
            time.sleep(0.01)
        if self.window.job.isRunning():
            self.window.cancel_batch()
            self.window.job.wait(10000)
            self.fail("Desktop worker timed out")
        self.app.processEvents()
        self.assertEqual(self.window.files.topLevelItem(0).text(1), "完成")
        target = self.root / "output" / "來源.txt.md"
        self.assertEqual(target.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))
        self.assertIn("繁體中文測試", self.window.preview.toPlainText())
        self.assertTrue(self.window.start_button.isEnabled())

    def test_missing_input_does_not_start_worker(self):
        self.window.start()
        self.assertIsNone(self.window.job)
        self.assertIn("請加入文件", self.window.status.text())

    def test_ocr_configuration_saved(self):
        from desktop_app.settings import load_settings
        self.window.ocr_engine.setText("C:/OCR/tesseract.exe")
        self.window.model_path.setText("C:/模型")
        self.window.save_preferences()
        settings = load_settings(self.root/"settings.json")
        self.assertEqual(settings.ocr_data_dir, "C:/模型")

    def test_device_and_cpu_controls_saved(self):
        from desktop_app.settings import load_settings
        self.window.device.setCurrentIndex(self.window.device.findData('cpu'))
        self.window.cpu_threads.setValue(2)
        self.window.save_preferences()
        saved = load_settings(self.root/'settings.json')
        self.assertEqual(saved.device, 'cpu')
        self.assertEqual(saved.cpu_threads, 2)
        self.assertFalse(self.window.device.model().item(2).isEnabled())

    def test_experimental_backend_does_not_change_default(self):
        self.assertEqual(self.window.backend.currentData(),'tesseract')
        self.window.backend.setCurrentIndex(self.window.backend.findData('onnx'))
        self.window.vram_budget.setValue(512)
        saved=self.window.preferences()
        self.assertEqual(saved.ocr_backend,'onnx')
        self.assertEqual(saved.vram_budget_mib,512)

    def test_model_dialog_cached_install(self):
        from desktop_app.model_dialog import ModelDialog
        from desktop_app.components.legacy_models import LegacyModelsAdapter
        from unittest.mock import patch
        import hashlib
        directory = self.root / "models"
        spec = {"source":"test", "commit":"test", "license":"test",
                "files":{"eng.traineddata":hashlib.sha256(b"fixture").hexdigest()}}
        with patch("desktop_app.models.manifest", return_value=spec):
            import io
            LegacyModelsAdapter(directory, managed=True).install(opener=lambda *a, **k:io.BytesIO(b'fixture'))
            dialog = ModelDialog(directory, managed_directory=directory)
            installed = []
            dialog.installed.connect(installed.append)
            dialog.start()
            self.assertTrue(dialog.job.wait(5000))
            self.app.processEvents()
            self.assertEqual(installed, [str(directory)])
            self.assertTrue(dialog.download.isEnabled())
            dialog.close()

    def test_v6_hidden_preferences_and_quality_survive_desktop_save(self):
        from desktop_app.settings import ComponentPreference, Settings, load_settings, save_settings
        saved = Settings(quality='fast', onboarding_version=2, update_channel='preview',
                         allow_optional_downloads=True,
                         component_preferences=(ComponentPreference('ocr.text', 'test-engine', '1.0.0'),))
        save_settings(saved, self.window.settings_path)
        self.window.load_preferences()
        self.window.reserve.setValue(512)
        self.window.save_preferences()
        actual = load_settings(self.window.settings_path)
        self.assertEqual(actual.component_preferences, saved.component_preferences)
        self.assertEqual(actual.quality, 'fast')
        self.assertEqual(actual.onboarding_version, 2)
        self.assertEqual(actual.update_channel, 'preview')
        self.assertTrue(actual.allow_optional_downloads)

    def test_external_model_dialog_is_read_only_and_does_not_start_download(self):
        from desktop_app.model_dialog import ModelDialog
        directory = self.root / '自備模型';directory.mkdir()
        target = directory / 'eng.traineddata';target.write_bytes(b'user data')
        dialog = ModelDialog(directory, managed_directory=self.root / 'managed')
        self.assertFalse(dialog.download.isEnabled())
        self.assertFalse(dialog.remove_button.isEnabled())
        dialog.start();dialog.remove()
        self.assertIsNone(dialog.job)
        self.assertEqual(target.read_bytes(), b'user data')
        self.assertIn('只讀', dialog.status.text())
        dialog.close()

    def test_unreadable_future_settings_are_not_overwritten_by_save_button(self):
        raw = b'{"schema_version":99}'
        self.window.settings_path.write_bytes(raw)
        self.window.load_preferences();self.window.save_preferences()
        self.assertEqual(self.window.settings_path.read_bytes(), raw)
        self.assertIn('儲存失敗', self.window.status.text())

    def test_migrated_external_path_and_backend_survive_unrelated_ui_save(self):
        import json
        from desktop_app.settings import load_settings
        raw = dict(schema_version=5, ocr_executable=' C:/自備引擎/tesseract.exe ',
                   ocr_data_dir='relative/中文模型', ocr_backend='onnx_verify', cpu_threads=3)
        self.window.settings_path.write_text(json.dumps(raw), encoding='utf-8')
        self.window.load_preferences();self.window.reserve.setValue(768);self.window.save_preferences()
        actual = load_settings(self.window.settings_path)
        self.assertEqual(actual.ocr_executable, raw['ocr_executable'])
        self.assertEqual(actual.ocr_data_dir, raw['ocr_data_dir'])
        self.assertEqual(actual.ocr_backend, raw['ocr_backend'])
        self.assertEqual(actual.cpu_threads, 3)
        self.assertEqual(len(list(self.root.glob('settings.json*.bak'))), 1)

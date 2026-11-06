"""以合成資料保存 Linux Qt 離屏畫面；不下載模型、不使用真實使用者文件。"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication
from desktop_app.components.registry import ComponentRegistry
from desktop_app.desktop import Window
from desktop_app.model_dialog import ModelDialog


def main():
    output = Path(__file__).parent / 'screenshots'
    output.mkdir(exist_ok=True)
    app = QApplication.instance() or QApplication([])
    with tempfile.TemporaryDirectory(prefix='c02-ui-') as directory:
        root = Path(directory)
        models = root / '外部模型';models.mkdir()
        payload = b'C02 synthetic UI fixture'
        names = ('eng.traineddata', 'chi_tra.traineddata', 'LICENSE')
        for name in names:(models / name).write_bytes(payload)
        spec = dict(source='合成畫面驗證，不是新 OCR 引擎', commit='synthetic-c02', license='test-only',
                    files={name:hashlib.sha256(payload).hexdigest() for name in names})
        settings = root / 'settings.json'
        settings.write_text(json.dumps(dict(schema_version=5, ram_budget_mib=896, reserve_mib=768,
                                            cpu_threads=3, ocr_data_dir=str(models))), encoding='utf-8')
        window = Window(settings_path=settings)
        window.show();window.save_preferences();app.processEvents()
        assert json.loads(settings.read_text())['schema_version'] == 6
        assert window.grab().save(str(output / 'desktop-v6.png'))
        with patch('desktop_app.models.manifest', return_value=spec):
            registry = ComponentRegistry(root / 'component-state')
            managed = root / 'models/tesseract-managed'
            readonly = ModelDialog(models, registry=registry, managed_directory=managed)
            readonly.show();app.processEvents()
            assert not readonly.download.isEnabled() and not readonly.remove_button.isEnabled()
            assert readonly.grab().save(str(output / 'legacy-readonly.png'))
            readonly.close()
            fresh = ModelDialog(managed, registry=registry, managed_directory=managed)
            fresh.show();app.processEvents()
            assert fresh.download.isEnabled() and not fresh.remove_button.isEnabled()
            assert not managed.exists()
            assert fresh.grab().save(str(output / 'managed-empty.png'))
            fresh.close()
        window.close()
    print('Linux offscreen Qt: v6 settings, external read-only models and empty managed directory verified; no downloads')


if __name__ == '__main__':
    main()

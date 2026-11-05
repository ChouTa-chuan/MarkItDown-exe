import importlib.util
from importlib.resources import files
import unittest
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')


@unittest.skipUnless(importlib.util.find_spec('PySide6'),'Install desktop dependencies')
class HelpTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def test_packaged_manual_and_ui(self):
        from desktop_app.help_ui import HelpDialog
        dialog=HelpDialog('user-guide.md','使用說明')
        self.assertIn('開始轉換',dialog.viewer.toPlainText())
        self.assertIn('雙引擎',dialog.viewer.toPlainText())
        self.assertIn('Windows',dialog.viewer.toPlainText())
        dialog.close()

    def test_packaged_attribution_and_folder(self):
        from desktop_app.help_ui import HelpDialog,license_root
        dialog=HelpDialog('third-party.md','第三方授權')
        self.assertIn('58',dialog.viewer.toPlainText())
        self.assertIn('Qt/PySide6',dialog.viewer.toPlainText())
        self.assertTrue((license_root()/'windows/inventory.json').is_file())
        dialog.close()

    def test_menu_has_both_documents(self):
        from desktop_app.desktop import Window
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            window=Window(settings_path=Path(directory)/'settings.json')
            menus=[a.menu() for a in window.menuBar().actions() if a.text()=='說明']
            self.assertEqual([a.text() for a in menus[0].actions()],['使用說明','第三方授權'])
            window.close()

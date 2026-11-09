"""以真實子程序驗證 GUI 入口正常退出及物件生命週期；不繞過 Qt cleanup。"""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import unittest


@unittest.skipUnless(importlib.util.find_spec('PySide6'), 'Install desktop dependencies')
class QtLifecycleTests(unittest.TestCase):
    def run_entrypoint(self, with_dialog=False, busy=False):
        source = '''
import tempfile
from pathlib import Path
from unittest.mock import patch
from threading import Event
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from shiboken6 import isValid
from desktop_app import desktop
from desktop_app.component_dialog import ComponentDialog
from desktop_app.components.management import ComponentManagement

app = QApplication([])
windows = []
destroyed = []
busy_observations = []
entered = Event()
real_window = desktop.Window
with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    def bounded_worker(thread):
        # 真實 QThread／取消事件，只驗生命週期，並不宣稱完成文件轉換。
        entered.set()
        if not thread.cancel.wait(5): raise RuntimeError('未收到取消要求')
    def factory():
        window = real_window(settings_path=root/'settings.json')
        windows.append(window)
        window.destroyed.connect(lambda: destroyed.append(True))
        if WITH_DIALOG:
            dialog = ComponentDialog(ComponentManagement(root), window)
            window.component_dialog = dialog
            dialog.show()
        if WITH_BUSY:
            source = root/'busy.txt'
            source.write_text('synthetic lifecycle fixture')
            window.add_sources([source])
            window.output.setText(str(root/'output'))
            window.start()
        def close_when_idle():
            # 只要求正常關閉；背景 refresh 未完成時讓它收尾後再試。
            if window.component_dialog and window.component_dialog.busy():
                QTimer.singleShot(10, close_when_idle)
            elif WITH_BUSY and not busy_observations:
                if not entered.is_set():
                    QTimer.singleShot(10, close_when_idle)
                    return
                accepted = window.close()
                busy_observations.append((accepted, isValid(window), window.job.cancel.is_set()))
                QTimer.singleShot(10, close_when_idle)
            elif window.job and window.job.isRunning():
                QTimer.singleShot(10, close_when_idle)
            else:
                if window.component_dialog: window.component_dialog.close()
                window.close()
        QTimer.singleShot(20, close_when_idle)
        return window
    with patch.object(desktop, 'Window', side_effect=factory), patch.object(real_window, 'offer_setup'), patch.object(desktop.BatchThread, 'run', bounded_worker):
        code = desktop.main()
    assert code == 0, code
    assert destroyed == [True], '主視窗仍延留至 QApplication 全域 cleanup'
    assert not isValid(windows[0]), '主視窗 C++ 物件尚未釋放'
    if WITH_DIALOG: assert not isValid(windows[0].component_dialog)
    if WITH_BUSY: assert busy_observations == [(False, True, True)], busy_observations
print('normal Qt exit; owned window destroyed before application cleanup')
'''.replace('WITH_DIALOG', repr(with_dialog)).replace('WITH_BUSY', repr(busy))
        result = subprocess.run([sys.executable, '-c', source],
            cwd=Path(__file__).resolve().parents[1],
            env={**os.environ, 'QT_QPA_PLATFORM': 'offscreen', 'PYTHONFAULTHANDLER': '1'},
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('normal Qt exit', result.stdout)

    def test_entrypoint_destroys_closed_main_window(self):
        self.run_entrypoint(False)

    def test_entrypoint_destroys_closed_component_dialog_with_parent(self):
        self.run_entrypoint(True)

    def test_busy_close_cancels_then_destroys_after_thread_finishes(self):
        self.run_entrypoint(busy=True)

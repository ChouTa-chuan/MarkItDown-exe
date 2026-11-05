"""模型管理介面：在背景下載、驗證與取消，開啟視窗不自動連網。"""
from pathlib import Path
from threading import Event
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                               QHBoxLayout, QMessageBox)
from . import models


class DownloadThread(QThread):
    status = Signal(str)
    installed = Signal(str)

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.directory = directory
        self.cancel = Event()

    def run(self):
        try:
            models.install(self.directory, self.cancel, self.status.emit)
            self.installed.emit(str(self.directory))
        except Exception as exc:
            self.status.emit(f"未完成：{exc}")


class ModelDialog(QDialog):
    installed = Signal(str)

    def __init__(self, directory, parent=None):
        super().__init__(parent)
        self.directory = Path(directory)
        self.job = None
        self.setWindowTitle("OCR 模型管理")
        self.resize(620, 320)
        layout = QVBoxLayout(self)
        spec = models.manifest()
        info = QLabel(f"繁體中文＋英文 CPU OCR · 約 6.4 MB\n來源：{spec['source']}\n"
                      f"固定版本：{spec['commit']}\n授權：{spec['license']}\n目錄：{self.directory}\n"
                      "下載完成可離線使用。此功能不下載 Tesseract 執行檔，也不啟用 GPU。")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.download = QPushButton("下載／驗證模型")
        self.download.clicked.connect(self.start)
        self.cancel_button = QPushButton("取消下載")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.remove_button = QPushButton("移除已驗證模型")
        self.remove_button.clicked.connect(self.remove)
        for button in (self.download, self.cancel_button, self.remove_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self):
        try:
            labels = {"valid":"已驗證", "missing":"未下載", "corrupt":"驗證失敗"}
            states = models.inspect(self.directory)
            self.status.setText("\n".join(f"{name}：{labels[state]}" for name, state in states.items()))
        except OSError as exc:
            self.status.setText(f"讀取失敗：{exc}")

    def start(self):
        if self.job is not None and self.job.isRunning():
            return
        self.download.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.job = DownloadThread(self.directory, self)
        self.job.status.connect(self.status.setText)
        self.job.installed.connect(self.installed.emit)
        self.job.finished.connect(self.done_download)
        self.job.start()

    def done_download(self):
        self.download.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

    def cancel(self):
        if self.job is not None:
            self.job.cancel.set()
            self.status.setText("正在取消，單次網路等待最多約 10 秒。")

    def remove(self):
        if QMessageBox.question(self, "移除模型", "確定移除本目錄內未修改的 OCR 模型與授權？其他檔案會保留。") != QMessageBox.Yes:
            return
        try:
            models.remove(self.directory)
            self.refresh()
        except (OSError, ValueError) as exc:
            self.status.setText(str(exc))

    def closeEvent(self, event):
        if self.job is not None and self.job.isRunning():
            self.cancel()
            event.ignore()
        else:
            event.accept()

    def reject(self):
        if self.job is not None and self.job.isRunning():
            self.cancel()
        else:
            super().reject()

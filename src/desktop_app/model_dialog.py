"""模型管理介面：在背景下載、驗證與取消，開啟視窗不自動連網。"""
from pathlib import Path
from threading import Event
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QPushButton,
                               QHBoxLayout, QMessageBox)
from . import models
from .components.legacy_models import LegacyModelsAdapter


class DownloadThread(QThread):
    status = Signal(str)
    installed = Signal(str)

    def __init__(self, adapter, parent=None):
        super().__init__(parent)
        self.adapter = adapter
        self.cancel = Event()

    def run(self):
        try:
            self.adapter.install(self.cancel, self.status.emit)
            self.installed.emit(str(self.adapter.directory))
        except Exception as exc:
            self.status.emit(f"未完成：{exc}")


class ModelDialog(QDialog):
    installed = Signal(str)

    def __init__(self, directory, parent=None, *, registry=None, managed_directory=None, four_languages=False):
        super().__init__(parent)
        self.directory = Path(directory).absolute()
        self.managed_directory = Path(managed_directory).absolute() if managed_directory else None
        self.registry = registry
        self.four_languages=four_languages
        from .languages import model_manifest
        spec=model_manifest() if four_languages else models.manifest()
        self.adapter = LegacyModelsAdapter(self.directory, registry,
                                           managed=self.directory == self.managed_directory,spec=spec)
        self.job = None
        self.setWindowTitle("OCR 模型管理")
        self.resize(620, 320)
        layout = QVBoxLayout(self)
        label='繁體中文＋英文＋日文＋韓文 CPU OCR' if four_languages else '繁體中文＋英文 CPU OCR · 約 6.4 MB'
        info = QLabel(f"{label}\n來源：{spec['source']}\n"
                      f"固定版本：{spec['commit']}\n授權：{spec['license']}\n目錄：{self.directory}\n"
                      "只驗模型，不代表 OCR 引擎就緒。此功能不下載 Tesseract 執行檔，也不啟用 GPU。\n"
                      "舊／外部目錄只讀；下載請使用程式專用目錄，原資料不搬移。")
        info.setWordWrap(True)
        layout.addWidget(info)
        self.status = QLabel()
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        buttons = QHBoxLayout()
        self.download = QPushButton("下載／驗證並使用受管模型")
        self.download.clicked.connect(self.start)
        self.cancel_button = QPushButton("取消下載")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        self.remove_button = QPushButton("移除已驗證模型")
        self.remove_button.clicked.connect(self.remove)
        for button in (self.download, self.cancel_button, self.remove_button):
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.managed_button = QPushButton('開啟程式專用模型下載目錄')
        self.managed_button.setVisible(self.managed_directory is not None and self.directory != self.managed_directory)
        self.managed_button.clicked.connect(self.open_managed)
        layout.addWidget(self.managed_button)
        self.refresh()

    def refresh(self):
        try:
            labels = {"valid":"已驗證", "missing":"未下載", "corrupt":"驗證失敗"}
            observation = self.adapter.observe()
            states = dict(observation.states)
            ownership = '程式受管目錄' if observation.owned else '只讀引用；未接管原資料'
            self.status.setText(ownership + '\n' + "\n".join(f"{name}：{labels[state]}" for name, state in states.items()))
            self.download.setEnabled(self.adapter.can_install())
            self.remove_button.setEnabled(observation.owned)
        except (OSError, RuntimeError, ValueError) as exc:
            self.status.setText(f"讀取失敗：{exc}")
            self.download.setEnabled(False)
            self.remove_button.setEnabled(False)

    def open_managed(self):
        dialog = ModelDialog(self.managed_directory, self, registry=self.registry,
                             managed_directory=self.managed_directory,four_languages=self.four_languages)
        dialog.installed.connect(self.installed.emit)
        dialog.exec()

    def start(self):
        if self.job is not None and self.job.isRunning():
            return
        if not self.adapter.can_install():
            self.status.setText('舊／外部目錄只讀，未下載或更動原資料。')
            return
        self.download.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.job = DownloadThread(self.adapter, self)
        self.job.status.connect(self.status.setText)
        self.job.installed.connect(self.installed.emit)
        self.job.finished.connect(self.done_download)
        self.job.start()

    def done_download(self):
        self.download.setEnabled(self.adapter.can_install())
        self.remove_button.setEnabled(self.adapter.owns_directory())
        self.cancel_button.setEnabled(False)

    def cancel(self):
        if self.job is not None:
            self.job.cancel.set()
            self.status.setText("正在取消，單次網路等待最多約 10 秒。")

    def remove(self):
        if self.job is not None and self.job.isRunning():
            return
        if not self.adapter.owns_directory():
            self.status.setText('舊／外部模型只讀，不移除原資料。')
            return
        if QMessageBox.question(self, "移除模型", "確定移除本目錄內未修改的 OCR 模型與授權？其他檔案會保留。") != QMessageBox.Yes:
            return
        try:
            self.adapter.remove()
            self.refresh()
        except (OSError, RuntimeError, ValueError) as exc:
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

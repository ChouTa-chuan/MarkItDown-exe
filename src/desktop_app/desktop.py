"""Initial Qt desktop workflow; precise analysis and GPU are not implemented."""
import multiprocessing
from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal, QStandardPaths
from PySide6.QtGui import QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .application import Runner
from .core import Request, State
from .settings import Settings, load_settings, save_settings


class BatchThread(QThread):
    event = Signal(int, str, str)
    converted = Signal(str)

    def __init__(self, sources, directory, settings, parent=None):
        super().__init__(parent)
        self.sources = sources
        self.directory = directory
        self.settings = settings
        self.cancel = Event()

    def run(self):
        runner = Runner(self.settings.policy(), max_resource_wait=self.settings.resource_wait_seconds)
        try:
            for index, source in enumerate(self.sources):
                request = Request(source, self.directory / (source.name + ".md"))
                outcome = runner.run(request, self.cancel,
                    lambda state, message, i=index: self.event.emit(i, state.value, message))
                self.event.emit(index, outcome.state.value, outcome.message)
                if outcome.state == State.COMPLETED:
                    self.converted.emit(str(request.destination))
                if self.cancel.is_set():
                    for rest in range(index + 1, len(self.sources)):
                        self.event.emit(rest, "cancelled", "批次已取消")
                    break
        except Exception as exc:
            self.event.emit(-1, "failed", str(exc))


class Window(QMainWindow):
    def __init__(self, settings_path=None):
        super().__init__()
        self.setWindowTitle("MarkItDown 桌面版 · 開發預覽")
        self.resize(1080, 760)
        self.setAcceptDrops(True)
        self.sources = []
        self.job = None
        self.settings_path = settings_path or Path(
            QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / "settings.json"
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("本機文件轉 Markdown｜Office / 文字型 PDF / HTML / UTF-8 文字"))
        layout.addWidget(QLabel("目前使用原生解析；自動精準分析、掃描 OCR 與 GPU 尚未開放。"))
        toolbar = QHBoxLayout()
        self.add_button = QPushButton("新增檔案／拖放")
        self.add_button.clicked.connect(self.choose_files)
        self.clear_button = QPushButton("清空清單")
        self.clear_button.clicked.connect(self.clear_sources)
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.clear_button)
        layout.addLayout(toolbar)
        self.files = QTreeWidget()
        self.files.setHeaderLabels(["文件", "狀態", "說明"])
        self.files.setColumnWidth(0, 340)
        layout.addWidget(self.files)
        output_row = QHBoxLayout()
        self.output = QLineEdit()
        self.output.setPlaceholderText("選擇輸出資料夾（既有檔案不會覆寫）")
        choose_output = QPushButton("輸出資料夾")
        choose_output.clicked.connect(self.choose_directory)
        output_row.addWidget(self.output)
        output_row.addWidget(choose_output)
        self.directory_button = choose_output
        layout.addLayout(output_row)
        form = QFormLayout()
        self.auto_budget = QCheckBox("自動規劃 RAM（系統優先）")
        self.auto_budget.setChecked(True)
        self.budget = QSpinBox()
        self.budget.setRange(1, 2147483647)
        self.budget.setValue(1024)
        self.budget.setSuffix(" MiB")
        self.budget.setEnabled(False)
        self.auto_budget.toggled.connect(lambda checked: self.budget.setEnabled(not checked))
        self.reserve = QSpinBox()
        self.reserve.setRange(0, 2147483647)
        self.reserve.setValue(2048)
        self.reserve.setSuffix(" MiB")
        form.addRow(self.auto_budget)
        form.addRow("手動 RAM 預算", self.budget)
        form.addRow("系統保留 RAM", self.reserve)
        layout.addLayout(form)
        buttons = QHBoxLayout()
        self.save_button = QPushButton("儲存資源設定")
        self.save_button.clicked.connect(self.save_preferences)
        self.start_button = QPushButton("開始轉換")
        self.start_button.clicked.connect(self.start)
        self.cancel_button = QPushButton("取消批次")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_batch)
        for button in [self.save_button, self.start_button, self.cancel_button]:
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.preview = QTextBrowser()
        self.preview.setOpenExternalLinks(False)
        self.preview.setOpenLinks(False)
        layout.addWidget(QLabel("最後完成文件的 Markdown 預覽（最多 256 Ki 字元）"))
        layout.addWidget(self.preview)
        self.status = QLabel("就緒；可拖放多份文件。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.wait_seconds = 30.0
        self.load_preferences()

    def load_preferences(self):
        if not self.settings_path.exists():
            return
        try:
            saved = load_settings(self.settings_path)
            self.auto_budget.setChecked(saved.ram_budget_mib is None)
            if saved.ram_budget_mib is not None:
                self.budget.setValue(saved.ram_budget_mib)
            self.reserve.setValue(saved.reserve_mib)
            self.wait_seconds = saved.resource_wait_seconds
        except (OSError, ValueError) as exc:
            self.status.setText(f"設定未載入：{exc}；原檔未變更。")

    def preferences(self):
        return Settings(ram_budget_mib=None if self.auto_budget.isChecked() else self.budget.value(),
                        reserve_mib=self.reserve.value(), resource_wait_seconds=self.wait_seconds)

    def save_preferences(self):
        try:
            save_settings(self.preferences(), self.settings_path)
            self.status.setText("資源設定已儲存。")
        except (OSError, ValueError) as exc:
            self.status.setText(f"儲存失敗：{exc}")

    def choose_files(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "選擇文件", "",
            "支援文件 (*.txt *.md *.docx *.pptx *.xlsx *.pdf *.html *.htm)")
        self.add_sources(paths)

    def choose_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "輸出資料夾")
        if directory:
            self.output.setText(directory)

    def add_sources(self, paths):
        if self.job is not None and self.job.isRunning():
            return
        for value in paths:
            path = Path(value).resolve()
            if path.is_file() and path not in self.sources:
                self.sources.append(path)
                self.files.addTopLevelItem(QTreeWidgetItem([str(path), "待處理", ""]))

    def clear_sources(self):
        self.sources.clear()
        self.files.clear()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls() and not (self.job and self.job.isRunning()):
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        self.add_sources([url.toLocalFile() for url in event.mimeData().urls() if url.isLocalFile()])
        event.acceptProposedAction()

    def start(self):
        if self.job is not None and self.job.isRunning():
            return
        if not self.sources or not self.output.text().strip():
            self.status.setText("請加入文件並選擇輸出資料夾。")
            return
        self.preview.clear()
        self.job = BatchThread(list(self.sources), Path(self.output.text().strip()), self.preferences(), self)
        self.job.event.connect(self.on_event)
        self.job.converted.connect(self.show_preview)
        self.job.finished.connect(self.on_finished)
        for index in range(self.files.topLevelItemCount()):
            self.files.topLevelItem(index).setText(1, "待處理")
        self.set_running(True)
        self.job.start()

    def set_running(self, running):
        for widget in [self.add_button, self.clear_button, self.start_button, self.directory_button,
                       self.output, self.auto_budget, self.reserve, self.save_button]:
            widget.setEnabled(not running)
        self.budget.setEnabled(not running and not self.auto_budget.isChecked())
        self.cancel_button.setEnabled(running)

    def on_event(self, index, state, message):
        labels = {"queued":"排隊", "running":"處理中", "paused":"等待資源",
                  "completed":"完成", "cancelled":"已取消", "failed":"失敗"}
        if index >= 0:
            item = self.files.topLevelItem(index)
            item.setText(1, labels.get(state, state))
            item.setText(2, message)
        self.status.setText(message or labels.get(state, state))

    def show_preview(self, path):
        try:
            with Path(path).open(encoding="utf-8") as source:
                self.preview.setMarkdown(source.read(256*1024))
        except OSError as exc:
            self.status.setText(f"轉換已完成，預覽失敗：{exc}")

    def cancel_batch(self):
        if self.job is not None:
            self.job.cancel.set()
            self.status.setText("正在取消；原生解析階段可能須等待目前步驟結束。")

    def on_finished(self):
        self.set_running(False)

    def closeEvent(self, event: QCloseEvent):
        if self.job is not None and self.job.isRunning():
            self.cancel_batch()
            self.status.setText("已要求取消，請等待工作程序停止後再關閉視窗。")
            event.ignore()
        else:
            event.accept()


def main():
    multiprocessing.freeze_support()
    app = QApplication.instance() or QApplication([])
    app.setOrganizationName("MarkItDownDesktop")
    app.setApplicationName("MarkItDownDesktop")
    window = Window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

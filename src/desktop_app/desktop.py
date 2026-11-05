"""Initial Qt desktop workflow; precise analysis and GPU are not implemented."""
import multiprocessing
from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal, QStandardPaths
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .application import Runner
from .core import Request, State, Quality
from .settings import Settings, load_settings, save_settings


class BatchThread(QThread):
    event = Signal(int, str, str)
    converted = Signal(str)

    def __init__(self, sources, directory, settings, quality=Quality.PRECISE, parent=None):
        super().__init__(parent)
        self.sources = sources
        self.directory = directory
        self.settings = settings
        self.quality = quality
        self.cancel = Event()

    def run(self):
        runner = Runner(self.settings.policy(), max_resource_wait=self.settings.resource_wait_seconds)
        try:
            for index, source in enumerate(self.sources):
                request = Request(source, self.directory / (source.name + ".md"), self.quality,
                                  self.settings.ocr_executable, self.settings.ocr_data_dir,
                                  self.settings.device, self.settings.cpu_threads,
                                  self.settings.ocr_backend, self.settings.vram_budget_mib)
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
        help_menu=self.menuBar().addMenu('說明')
        for title,document in [('使用說明','user-guide.md'),('第三方授權','third-party.md')]:
            action=QAction(title,self)
            action.triggered.connect(lambda checked=False,path=document,label=title:self.show_help(path,label))
            help_menu.addAction(action)
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
        layout.addWidget(QLabel("PDF 精準模式自動逐頁分析與 OCR；OCR 需另備 Tesseract。GPU 尚未開放。"))
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
        self.quality = QComboBox()
        self.quality.addItem("精準：PDF 自動分析／OCR", Quality.PRECISE.value)
        self.quality.addItem("快速：原生 MarkItDown", Quality.FAST.value)
        form.addRow("轉換模式", self.quality)
        device_row = QHBoxLayout()
        self.device = QComboBox()
        self.device.addItem("自動（目前 OCR 使用 CPU）", "auto")
        self.device.addItem("僅用 CPU", "cpu")
        self.device.addItem("GPU（待整合模型後端）", "gpu")
        self.device.model().item(2).setEnabled(False)
        self.device.setToolTip("GPU 項目須經模型推論驗證後開放，偵測到顯卡不代表已有加速。")
        device_row.addWidget(self.device)
        self.device_button = QPushButton("裝置診斷")
        self.device_button.clicked.connect(self.diagnose_devices)
        device_row.addWidget(self.device_button)
        form.addRow("運算裝置", device_row)
        self.cpu_threads = QSpinBox()
        self.cpu_threads.setRange(1, 256)
        self.cpu_threads.setValue(1)
        self.cpu_threads.setToolTip("限制支援 OpenMP／BLAS 的工作程序；不是整個系統的 CPU 百分比上限。")
        form.addRow("CPU 執行緒上限", self.cpu_threads)
        self.backend = QComboBox()
        self.backend.addItem("Tesseract（外部引擎）", "tesseract")
        self.backend.addItem("ONNX OCR（實驗性，繁體品質未達標）", "onnx")
        self.backend.addItem("雙引擎交叉核對（較慢，保留差異）", "onnx_verify")
        form.addRow("OCR 後端", self.backend)
        self.vram_budget = QSpinBox()
        self.vram_budget.setRange(192, 1048576)
        self.vram_budget.setValue(768)
        self.vram_budget.setSuffix(" MiB")
        self.vram_budget.setToolTip("三個 CUDA session 的 arena 預算總量，不是整張卡的硬上限；GPU 仍待實機驗證。")
        form.addRow("GPU 配置預算", self.vram_budget)
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
        self.ocr_engine = QLineEdit()
        self.ocr_engine.setPlaceholderText("留空自動偵測，或選擇 Tesseract 執行檔")
        engine_row = QHBoxLayout()
        engine_row.addWidget(self.ocr_engine)
        self.engine_button = QPushButton("選擇引擎")
        self.engine_button.clicked.connect(self.choose_engine)
        engine_row.addWidget(self.engine_button)
        self.model_path = QLineEdit()
        self.model_path.setPlaceholderText("留空使用 Tesseract 預設語言目錄")
        model_row = QHBoxLayout()
        model_row.addWidget(self.model_path)
        self.model_directory_button = QPushButton("選擇目錄")
        self.model_directory_button.clicked.connect(self.choose_model_directory)
        model_row.addWidget(self.model_directory_button)
        self.models_button = QPushButton("模型管理")
        self.models_button.clicked.connect(self.manage_models)
        model_row.addWidget(self.models_button)
        form.addRow(self.auto_budget)
        form.addRow("手動 RAM 預算", self.budget)
        form.addRow("系統保留 RAM", self.reserve)
        form.addRow("OCR 引擎", engine_row)
        form.addRow("OCR 模型目錄", model_row)
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
            self.ocr_engine.setText(saved.ocr_executable or "")
            self.model_path.setText(saved.ocr_data_dir or "")
            self.device.setCurrentIndex(self.device.findData(saved.device))
            self.cpu_threads.setValue(saved.cpu_threads)
            self.backend.setCurrentIndex(self.backend.findData(saved.ocr_backend))
            self.vram_budget.setValue(saved.vram_budget_mib)
        except (OSError, ValueError) as exc:
            self.status.setText(f"設定未載入：{exc}；原檔未變更。")

    def preferences(self):
        return Settings(ram_budget_mib=None if self.auto_budget.isChecked() else self.budget.value(),
                        reserve_mib=self.reserve.value(), resource_wait_seconds=self.wait_seconds,
                        ocr_executable=self.ocr_engine.text().strip() or None,
                        ocr_data_dir=self.model_path.text().strip() or None,
                        device=self.device.currentData(), cpu_threads=self.cpu_threads.value(),
                        ocr_backend=self.backend.currentData(), vram_budget_mib=self.vram_budget.value())

    def show_help(self,document,title):
        from .help_ui import HelpDialog
        dialog=HelpDialog(document,title,self)
        dialog.exec()

    def diagnose_devices(self):
        from .device_dialog import DeviceDialog
        dialog = DeviceDialog(self)
        dialog.exec()

    def choose_engine(self):
        path, _ = QFileDialog.getOpenFileName(self, "選擇 Tesseract 執行檔")
        if path:
            self.ocr_engine.setText(path)

    def manage_models(self):
        from .model_dialog import ModelDialog
        directory = Path(self.model_path.text().strip()) if self.model_path.text().strip() else self.settings_path.parent / "models/tesseract"
        dialog = ModelDialog(directory, self)
        dialog.installed.connect(self.model_path.setText)
        dialog.exec()

    def choose_model_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "選擇 OCR 模型目錄")
        if directory:
            self.model_path.setText(directory)

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
        self.job = BatchThread(list(self.sources), Path(self.output.text().strip()), self.preferences(),
                               Quality(self.quality.currentData()), self)
        self.job.event.connect(self.on_event)
        self.job.converted.connect(self.show_preview)
        self.job.finished.connect(self.on_finished)
        for index in range(self.files.topLevelItemCount()):
            self.files.topLevelItem(index).setText(1, "待處理")
        self.set_running(True)
        self.job.start()

    def set_running(self, running):
        for widget in [self.add_button, self.clear_button, self.start_button, self.directory_button,
                       self.output, self.auto_budget, self.reserve, self.save_button, self.quality,
                       self.ocr_engine, self.engine_button, self.model_path, self.models_button,
                       self.model_directory_button, self.device, self.device_button, self.cpu_threads,
                       self.backend, self.vram_budget]:
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

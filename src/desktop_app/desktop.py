"""Qt 桌面流程：批次轉換、PDF 精準模式、資源設定與離線說明；GPU 尚待實機驗收。"""
import multiprocessing
from dataclasses import replace
from pathlib import Path
from threading import Event

from PySide6.QtCore import QThread, Signal, QStandardPaths, QTimer
from PySide6.QtGui import QAction, QCloseEvent, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton,
    QSpinBox, QTextBrowser, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget)

from .application import Runner
from .core import Request, State, Quality
from .settings import Settings, ComponentPreference, load_settings, save_settings


class BatchThread(QThread):
    event = Signal(int, str, str)
    converted = Signal(str)

    def __init__(self, sources, directory, settings, quality=Quality.PRECISE, parent=None, *, component_context=None):
        super().__init__(parent)
        self.sources = sources
        self.directory = directory
        self.settings = settings
        self.quality = quality
        self.cancel = Event()
        self.component_context = component_context
        self.outcomes = []

    def run(self):
        runner = Runner(self.settings.policy(), max_resource_wait=self.settings.resource_wait_seconds,
                        component_context=self.component_context)
        try:
            for index, source in enumerate(self.sources):
                choice=next((item for item in self.settings.component_preferences if item.capability=='ocr.onnx.cpu'),None)
                request = Request(source, self.directory / (source.name + ".md"), self.quality,
                                  self.settings.ocr_executable, self.settings.ocr_data_dir,
                                  self.settings.device, self.settings.cpu_threads,
                                  self.settings.ocr_backend, self.settings.vram_budget_mib,
                                  choice.component_id if choice and self.settings.ocr_backend=='managed_cpu' else None,
                                  choice.version if choice and self.settings.ocr_backend=='managed_cpu' else None,
                                  ocr_languages=self.settings.ocr_languages)
                outcome = runner.run(request, self.cancel,
                    lambda state, message, i=index: self.event.emit(i, state.value, message))
                self.outcomes.append(outcome)
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
    def __init__(self, settings_path=None, *, component_service_factory=None):
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
        self.component_dialog = None
        self.setup_dialog = None
        self.component_service_factory = component_service_factory
        self.settings_path = settings_path or Path(
            QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)) / "settings.json"
        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        layout.addWidget(QLabel("本機文件轉 Markdown｜Office / 文字型 PDF / HTML / UTF-8 文字"))
        layout.addWidget(QLabel("PDF 精準模式自動逐頁分析；OCR 依所選後端與元件執行，GPU 尚待實機驗證。"))
        toolbar = QHBoxLayout()
        self.add_button = QPushButton("新增檔案／拖放")
        self.add_button.clicked.connect(self.choose_files)
        self.clear_button = QPushButton("清空清單")
        self.clear_button.clicked.connect(self.clear_sources)
        toolbar.addWidget(self.add_button)
        toolbar.addWidget(self.clear_button)
        self.components_button = QPushButton('選配元件管理')
        self.components_button.clicked.connect(self.manage_components)
        toolbar.addWidget(self.components_button)
        self.setup_button=QPushButton('首次設定／重新檢查')
        self.setup_button.clicked.connect(lambda:self.offer_setup(force=True))
        toolbar.addWidget(self.setup_button)
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
        self.backend.addItem("Tesseract（基本／自備引擎）", "tesseract")
        self.backend.addItem("ONNX OCR（實驗性，繁體品質未達標）", "onnx")
        self.backend.addItem("雙引擎交叉核對（較慢，保留差異）", "onnx_verify")
        self.backend.addItem('受管 CPU OCR（選配、繁體品質未達標）','managed_cpu')
        form.addRow("OCR 後端", self.backend)
        from .languages import PRESETS
        self.languages=QComboBox()
        for label,value in PRESETS:self.languages.addItem(label,value)
        self.languages.setToolTip('語言選擇用於 Tesseract；四語混合不代表自動分類或必然較準確，日韓尚未驗收 ONNX。')
        form.addRow('OCR 語言',self.languages)
        managed_row=QHBoxLayout()
        self.managed_id=QLineEdit('onnx-cpu-ocr')
        self.managed_id.setToolTip('預設 ONNX CPU 元件識別名稱；通常不用修改。')
        self.managed_version=QLineEdit()
        self.managed_version.setPlaceholderText('留空用啟用版本；指定版本須先啟用')
        managed_row.addWidget(self.managed_id); managed_row.addWidget(self.managed_version)
        form.addRow('受管元件／版本',managed_row)
        self.backend.currentIndexChanged.connect(self.update_managed_fields)
        self.update_managed_fields()
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
        self.loaded_settings = Settings()
        self.load_preferences()

    def load_preferences(self):
        if not self.settings_path.exists():
            return
        try:
            saved = load_settings(self.settings_path)
            self.loaded_settings = saved
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
            language_value='+'.join(saved.ocr_languages) if saved.ocr_languages else 'legacy'
            if self.languages.findData(language_value)<0:self.languages.addItem('自訂：'+language_value,language_value)
            self.languages.setCurrentIndex(self.languages.findData(language_value))
            choice=next((item for item in saved.component_preferences if item.capability=='ocr.onnx.cpu'),None)
            self.managed_id.setText(choice.component_id if choice else 'onnx-cpu-ocr')
            self.managed_version.setText(choice.version or '' if choice else '')
            self.vram_budget.setValue(saved.vram_budget_mib)
            self.quality.setCurrentIndex(self.quality.findData(saved.quality))
        except (OSError, ValueError) as exc:
            self.status.setText(f"設定未載入：{exc}；原檔未變更。")

    def preferences(self):
        from .languages import parse_languages
        # 未顯示的元件偏好仍須保留；v7 只新增語言，不重設舊引擎與其他設定。
        choices=self.loaded_settings.component_preferences
        if self.backend.currentData()=='managed_cpu':
            selected=ComponentPreference('ocr.onnx.cpu',self.managed_id.text().strip(),self.managed_version.text().strip() or None)
            existed=any(item.capability=='ocr.onnx.cpu' for item in choices)
            choices=tuple(selected if item.capability=='ocr.onnx.cpu' else item for item in choices)+(() if existed else (selected,))
        return replace(self.loaded_settings, ram_budget_mib=None if self.auto_budget.isChecked() else self.budget.value(),
                        reserve_mib=self.reserve.value(), resource_wait_seconds=self.wait_seconds,
                        ocr_executable=self.ocr_engine.text() if self.ocr_engine.text().strip() else None,
                        ocr_data_dir=self.model_path.text() if self.model_path.text().strip() else None,
                        device=self.device.currentData(), cpu_threads=self.cpu_threads.value(),
                        ocr_backend=self.backend.currentData(), vram_budget_mib=self.vram_budget.value(),
                        quality=self.quality.currentData(),component_preferences=choices,
                        ocr_languages=parse_languages(self.languages.currentData()))

    def update_managed_fields(self):
        enabled=self.backend.currentData()=='managed_cpu' and self.backend.isEnabled() and not (self.job and self.job.isRunning())
        self.managed_id.setEnabled(bool(enabled)); self.managed_version.setEnabled(bool(enabled))
        self.languages.setEnabled(self.backend.isEnabled() and self.backend.currentData()=='tesseract'
                                  and not (self.job and self.job.isRunning()))

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
        from .components.registry import ComponentRegistry
        managed_directory = self.settings_path.parent / 'models/tesseract-four-language-managed'
        legacy_directory = self.settings_path.parent / 'models/tesseract'
        directory = (Path(self.model_path.text()) if self.model_path.text().strip() else
                     legacy_directory if legacy_directory.exists() else managed_directory)
        try:
            if not self.model_path.text().strip() and not self.ocr_engine.text().strip():
                from .bundled_ocr import bindings
                _, bundled_data, origin = bindings()
                if origin is not None:
                    directory = Path(bundled_data)  # 內含模型只讀展示，不由使用者模型服務移除。
            registry = ComponentRegistry(self.settings_path.parent / 'component-state')
            dialog = ModelDialog(directory, self, registry=registry, managed_directory=managed_directory,four_languages=True)
        except (OSError, RuntimeError, ValueError) as exc:
            self.status.setText(f'模型登錄未開啟：{exc}；原模型未變更。')
            return
        dialog.installed.connect(self.model_path.setText)
        dialog.exec()

    def manage_components(self):
        if self.job is not None and self.job.isRunning(): return
        from .component_dialog import ComponentDialog
        from .components.management import ComponentManagement
        try:
            # 正式信任根尚未發布；預設只開啟本機管理，不採用使用者輸入的金鑰。
            factory = self.component_service_factory or ComponentManagement
            service = factory(self.settings_path.parent, settings=self.preferences())
            self.component_dialog = ComponentDialog(service,self)
            self.component_dialog.exec()
        except (OSError, RuntimeError, ValueError) as exc:
            self.status.setText(f'元件管理未開啟：{exc}；基本轉換仍可使用。')

    def offer_setup(self,force=False):
        if self.job is not None and self.job.isRunning(): return
        if self.setup_dialog is not None and self.setup_dialog.isVisible():
            self.setup_dialog.raise_(); return
        from .onboarding.service import SetupSession
        from .onboarding.dialog import SetupDialog
        try:
            session=SetupSession(self.settings_path,settings=self.preferences(),expected_settings=self.loaded_settings)
            if not force and not session.due: return
            self.setup_dialog=SetupDialog(session,self)
            self.setup_dialog.saved.connect(self.load_preferences)
            self.setup_dialog.open()
        except (OSError,RuntimeError,ValueError) as exc:
            self.status.setText(f'首次設定未開啟：{exc}；原設定保留，基本轉換仍可使用。')

    def choose_model_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "選擇 OCR 模型目錄")
        if directory:
            self.model_path.setText(directory)

    def save_preferences(self):
        try:
            saved=self.preferences()
            save_settings(saved, self.settings_path)
            self.loaded_settings=saved
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
        try:
            settings=self.preferences(); component_context=None
            if settings.ocr_backend=='managed_cpu':
                from .components.management import ComponentManagement
                factory=self.component_service_factory or ComponentManagement
                component_context=factory(self.settings_path.parent,settings=settings).conversion_context()
            self.preview.clear()
            self.job = BatchThread(list(self.sources), Path(self.output.text().strip()), settings,
                                   Quality(self.quality.currentData()), self,component_context=component_context)
        except (OSError,ValueError,RuntimeError) as exc:
            self.status.setText(f'轉換未開始：{exc}'); return
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
                       self.backend, self.vram_budget, self.components_button, self.setup_button]:
            widget.setEnabled(not running)
        self.budget.setEnabled(not running and not self.auto_budget.isChecked())
        self.cancel_button.setEnabled(running)
        self.update_managed_fields()

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
        if self.setup_dialog is not None and self.setup_dialog.busy():
            self.setup_dialog.reject(); event.ignore()
        elif self.component_dialog is not None and self.component_dialog.busy():
            self.component_dialog.cancel()
            self.status.setText('請等待元件操作收尾後再關閉。')
            event.ignore()
        elif self.job is not None and self.job.isRunning():
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
    QTimer.singleShot(0,window.offer_setup)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

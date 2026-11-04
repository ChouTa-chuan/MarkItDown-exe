"""Background, read-only device diagnostics. Detection never enables inference."""
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPlainTextEdit
from .devices import probe_devices, DeviceReport


class ProbeThread(QThread):
    result = Signal(object)
    def run(self):
        try:
            self.result.emit(probe_devices())
        except Exception as exc:
            self.result.emit(DeviceReport((), (), (f"診斷未完成：{exc}",)))


class DeviceDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("運算裝置診斷")
        self.resize(700, 400)
        layout = QVBoxLayout(self)
        self.output = QPlainTextEdit("正在查詢顯卡與執行後端，最多等待約 5 秒…")
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        self.job = ProbeThread(self)
        self.job.result.connect(self.show_report)
        self.job.start()

    def show_report(self, report):
        lines = ["目前實際 OCR 引擎：Tesseract／CPU", ""]
        for gpu in report.gpus:
            lines.extend([f"顯卡：{gpu.name}", f"UUID：{gpu.uuid}",
                          f"顯示記憶體：可用 {gpu.free_mib} / 總計 {gpu.total_mib} MiB",
                          f"驅動：{gpu.driver}", ""])
        lines.append("套件提供的 ONNX providers：" + (", ".join(report.providers) or "未知"))
        lines.extend(report.notes)
        self.output.setPlainText("\n".join(lines))

    def reject(self):
        if not self.job.isRunning():
            super().reject()

    def closeEvent(self, event):
        if self.job.isRunning():
            event.ignore()
        else:
            event.accept()

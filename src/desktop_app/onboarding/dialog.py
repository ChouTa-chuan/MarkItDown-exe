"""首次設定介面：離線背景檢查、保留偏好、可略過選配與安全關閉。"""
from threading import Event
from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit, QCheckBox, QPushButton

from ..core import Cancelled


class SetupThread(QThread):
    result=Signal(object)
    problem=Signal(str)

    def __init__(self,session,report=None,apply_ram=False,apply_engine=False,parent=None):
        super().__init__(parent); self.session=session; self.report=report
        self.apply_ram=apply_ram; self.apply_engine=apply_engine; self.cancel=Event()

    def run(self):
        try:
            if self.report is None: value=self.session.inspect(self.cancel)
            else: value=self.session.complete(self.report,apply_ram=self.apply_ram,apply_engine=self.apply_engine)
            self.result.emit(value)
        except Cancelled: self.problem.emit('檢查已取消；設定尚未儲存。')
        except Exception as exc: self.problem.emit(f'{type(exc).__name__}: {exc}')


class SetupDialog(QDialog):
    saved=Signal()

    def __init__(self,session,parent=None):
        super().__init__(parent); self.session=session; self.job=None; self.report=None
        self.saving=False; self.pending_close=False; self.did_save=False
        self.setWindowTitle('首次設定與基本引擎檢查'); self.resize(790,540)
        layout=QVBoxLayout(self)
        info=QLabel('離線檢查基本 CPU OCR，提供 RAM 建議；不下載模型、選配或更新。\n既有 OCR、路徑、品質與資源偏好預設保留。')
        info.setWordWrap(True); layout.addWidget(info)
        self.details=QPlainTextEdit(); self.details.setReadOnly(True); layout.addWidget(self.details)
        self.ram=QCheckBox('採用 RAM 建議（自動預算與系統保留量）'); self.ram.setChecked(not session.existing)
        self.engine=QCheckBox('填入找到的基本引擎／模型位置（保留已指定路徑與後端）'); self.engine.setChecked(not session.existing)
        layout.addWidget(self.ram); layout.addWidget(self.engine)
        self.status=QLabel('正在檢查本機能力…'); self.status.setTextFormat(Qt.TextFormat.PlainText); self.status.setWordWrap(True)
        layout.addWidget(self.status)
        row=QHBoxLayout(); self.retry=QPushButton('重新檢查'); self.finish=QPushButton('完成設定，略過選配'); self.later=QPushButton('稍後再設定')
        for button in (self.retry,self.finish,self.later): row.addWidget(button)
        layout.addLayout(row)
        self.retry.clicked.connect(self.inspect); self.finish.clicked.connect(self.complete); self.later.clicked.connect(self.reject)
        self.inspect()

    def busy(self): return self.job is not None and self.job.isRunning()

    def controls(self):
        idle=not self.busy(); self.retry.setEnabled(idle)
        self.finish.setEnabled(idle and self.report is not None); self.ram.setEnabled(idle); self.engine.setEnabled(idle)
        self.later.setEnabled(not self.saving)

    def inspect(self):
        if self.busy(): return
        self.report=None; self.did_save=False; self.saving=False
        self.status.setText('正在離線檢查；可選「稍後再設定」，不會下載。')
        self.job=SetupThread(self.session,parent=self); self.connect_job(); self.job.start(); self.controls()

    def connect_job(self):
        self.job.result.connect(self.on_result); self.job.problem.connect(self.status.setText)
        self.job.finished.connect(self.on_finished)

    def on_result(self,value):
        if self.saving: self.did_save=True; return
        self.report=value; ram=value.ram; engine=value.engine
        self.details.setPlainText(f'實體 RAM：{ram.total_mib:,} MiB　當下可用：{ram.available_mib:,} MiB'
            f'\n建議自動上限：約 {ram.automatic_budget_mib:,} MiB（實體 RAM 的 25%）'
            f'\n建議系統保留：{ram.reserve_mib:,} MiB；屬軟性預算，不保證瞬間不超量。'
            f'\n\n基本 CPU OCR：'+('已通過合成繁中／英文檢查' if engine.ready else '尚未就緒')+
            f'\n引擎：{engine.executable or "未找到"}\n模型：{engine.data_dir or "引擎預設位置"}'
            f'\n來源：{engine.origin}\n版本：{engine.version}\n語言：{", ".join(engine.languages)}'
            f'\n{engine.message}\n\n選配可之後從主視窗開啟；GPU 不會自動啟用。')
        self.status.setText('檢查完成。' if engine.ready else '檢查完成，但基本 OCR 尚未就緒；仍可完成設定並使用文字轉換。')

    def complete(self):
        if self.busy() or self.report is None: return
        self.saving=True; self.did_save=False; self.status.setText('正在儲存首次設定…')
        self.job=SetupThread(self.session,self.report,self.ram.isChecked(),self.engine.isChecked(),self)
        self.connect_job(); self.job.start(); self.controls()

    def on_finished(self):
        self.saving=False; self.controls()
        if self.did_save: self.saved.emit(); super().accept()
        elif self.pending_close: super().reject()

    def reject(self):
        if self.busy():
            if not self.saving:
                self.pending_close=True; self.job.cancel.set(); self.status.setText('正在取消檢查，請稍候…')
        else: super().reject()

    def closeEvent(self,event):
        if self.busy(): self.reject(); event.ignore()
        else: event.accept()

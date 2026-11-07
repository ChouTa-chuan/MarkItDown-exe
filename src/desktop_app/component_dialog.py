"""C08 元件管理視窗：Qt 主執行緒只顯示資料，所有磁碟／網路／健康操作放背景。"""
from threading import Event
import time

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QLabel, QMessageBox,
    QPlainTextEdit, QProgressBar, QPushButton, QSplitter, QTreeWidget, QTreeWidgetItem, QVBoxLayout)


STATE_LABELS = {'missing':'尚未安裝', 'downloaded':'已下載，未驗證', 'verified':'包檔已驗證，未安裝',
                'installed':'已安裝，待檢查', 'unchecked':'上次健康通過（使用前重驗）',
                'unhealthy':'健康未通過', 'incompatible':'不相容', 'corrupt':'完整性異常',
                'unapproved':'目前目錄未核准'}


class ManagementThread(QThread):
    status = Signal(str)
    progress = Signal(object, object)
    result = Signal(object)

    def __init__(self, service, operation, key=None, path=None, parent=None):
        super().__init__(parent)
        self.service=service; self.operation=operation; self.key=key; self.path=path
        self.cancel=Event()

    def run(self):
        last=[0.0]
        def report(received,total):
            # 限頻，避免大型包每 64 KiB 都產生 queued signal 壓垮 UI 事件佇列。
            now=time.monotonic()
            if received==total or now-last[0]>=0.1:
                last[0]=now; self.progress.emit(received,total)
        self.result.emit(self.service.run(self.operation,self.key,self.path,cancel=self.cancel,
                                         status=self.status.emit,progress=report))


class ComponentDialog(QDialog):
    def __init__(self, service, parent=None):
        super().__init__(parent)
        self.service=service; self.job=None; self.rows=(); self.last_result=None
        self.setWindowTitle('選配元件管理'); self.resize(1040,720)
        layout=QVBoxLayout(self)
        summary=QLabel('基本功能與原模型管理可繼續使用。選配元件由此明確下載／匯入；開啟視窗不會自動連網。')
        summary.setWordWrap(True); layout.addWidget(summary)
        toolbar=QHBoxLayout()
        self.refresh_button=QPushButton('重新讀取本機狀態')
        self.catalog_button=QPushButton('匯入簽章目錄')
        self.online_button=QPushButton('更新線上目錄')
        self.recover_button=QPushButton('恢復未完成維護')
        for button in (self.refresh_button,self.catalog_button,self.online_button,self.recover_button): toolbar.addWidget(button)
        layout.addLayout(toolbar)
        splitter=QSplitter(Qt.Orientation.Vertical)
        self.table=QTreeWidget(); self.table.setRootIsDecorated(False)
        self.table.setHeaderLabels(['元件／版本','類型','狀態','啟用版本','下載／解壓 MiB','授權'])
        self.table.setColumnWidth(0,280); self.table.setColumnWidth(2,230)
        self.table.itemSelectionChanged.connect(self.selection_changed)
        splitter.addWidget(self.table)
        self.details=QPlainTextEdit(); self.details.setReadOnly(True); self.details.setMaximumBlockCount(200)
        splitter.addWidget(self.details); splitter.setSizes([320,180]); layout.addWidget(splitter)
        self.buttons={}
        for entries in ((('install','下載並安裝'),('offline','匯入包檔並安裝'),('health','重新檢查健康'),('license','查看授權原文')),
                        (('repair','修復此版本'),('activate','啟用所選版本'),('rollback','回復前一版本'),('remove','移除此版本'))):
            row=QHBoxLayout()
            for operation,title in entries:
                button=QPushButton(title); self.buttons[operation]=button
                button.clicked.connect(lambda checked=False,action=operation:self.request(action)); row.addWidget(button)
            layout.addLayout(row)
        self.progress=QProgressBar(); self.progress.setRange(0,1000); self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.status=QLabel('正在讀取本機狀態…'); self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True); layout.addWidget(self.status)
        bottom=QHBoxLayout(); self.cancel_button=QPushButton('取消目前操作'); self.close_button=QPushButton('關閉')
        bottom.addWidget(self.cancel_button); bottom.addWidget(self.close_button); layout.addLayout(bottom)
        self.refresh_button.clicked.connect(lambda:self.start('refresh'))
        self.catalog_button.clicked.connect(self.import_catalog)
        self.online_button.clicked.connect(lambda:self.start('catalog_online'))
        self.recover_button.clicked.connect(lambda:self.start('recover'))
        self.cancel_button.clicked.connect(self.cancel); self.close_button.clicked.connect(self.reject)
        self.start('refresh')

    def busy(self):
        return self.job is not None and self.job.isRunning()

    def selected(self):
        item=self.table.currentItem()
        return next((row for row in self.rows if item is not None and row.spec.key==item.data(0,Qt.ItemDataRole.UserRole)),None)

    def update_controls(self):
        idle=not self.busy(); selected=self.selected()
        approved=bool(selected and selected.approved and selected.compatible)
        owned=bool(selected and selected.owned)
        actions=dict(install=approved,offline=approved,repair=approved and owned,health=approved and owned,
                     activate=approved and owned,license=owned,
                     rollback=approved and owned and selected.active and any(row.previous and row.spec.component_id==selected.spec.component_id for row in self.rows),
                     remove=owned and not selected.spec.required)
        for operation,button in self.buttons.items(): button.setEnabled(idle and actions[operation])
        self.refresh_button.setEnabled(idle); self.recover_button.setEnabled(idle)
        self.catalog_button.setEnabled(idle and self.service.source is not None)
        self.online_button.setEnabled(idle and self.service.source is not None and self.service.source.catalog_url is not None)
        self.table.setEnabled(idle); self.cancel_button.setEnabled(not idle)

    def selection_changed(self):
        row=self.selected()
        if row is not None:
            spec=row.spec
            self.details.setPlainText(
                f'{spec.display_name}\nID：{spec.component_id}　版本：{spec.version}　'+('必要元件' if spec.required else '選配元件')+
                f'\n下載：{spec.download_bytes:,} bytes　解壓上限：{spec.unpacked_bytes:,} bytes'
                f'\n預估 RAM：{spec.resources.ram_mib} MiB　VRAM：{spec.resources.vram_mib} MiB　磁碟：{spec.resources.disk_mib} MiB'
                f'\n授權：{spec.license_id}\n來源：{spec.source_url}'
                f'\n平台：{", ".join(spec.platforms)}／{", ".join(spec.architectures)}'
                f'\n能力：{", ".join(spec.capabilities)}\n狀態說明：{row.reason}'
                '\n授權原文在安裝後可核對查看。RAM 為軟性預算；元件啟用不會改變目前文件的 OCR 選擇。')
        self.update_controls()

    def start(self, operation, key=None, path=None):
        if self.busy(): return
        self.progress.setRange(0,0); self.status.setText('正在處理…')
        self.job=ManagementThread(self.service,operation,key,path,self)
        self.job.status.connect(self.status.setText); self.job.progress.connect(self.on_progress)
        self.job.result.connect(self.on_result); self.job.finished.connect(self.finished_operation)
        self.job.start(); self.update_controls()

    def on_progress(self, received,total):
        self.progress.setRange(0,1000); self.progress.setValue(int(received*1000//max(1,total)))
        self.status.setText(f'已取得 {received:,}／{total:,} bytes；完成後驗證與安裝。')

    def on_result(self, result):
        key=self.selected().spec.key if self.selected() else None
        self.last_result=result; self.rows=result.rows
        self.table.clear()
        for row in self.rows:
            spec=row.spec
            active='目前啟用' if row.active else '前一版本' if row.previous else '—'
            item=QTreeWidgetItem([f'{spec.display_name} · {spec.version}','必要' if spec.required else '選配',
                STATE_LABELS.get(row.state,row.state),active,
                f'{spec.download_bytes/1024**2:.1f}／{spec.unpacked_bytes/1024**2:.1f}',spec.license_id])
            item.setData(0,Qt.ItemDataRole.UserRole,spec.key); self.table.addTopLevelItem(item)
            if spec.key==key: self.table.setCurrentItem(item)
        if self.table.currentItem() is None and self.table.topLevelItemCount(): self.table.setCurrentItem(self.table.topLevelItem(0))
        if not self.rows: self.details.setPlainText('尚無可列出的元件。正式選配來源準備完成後才提供下載；基本轉換與原模型管理仍可使用。')
        self.status.setText(('未完成：' if result.state=='failed' else '已取消：' if result.state=='cancelled' else '')+result.message)
        if result.document is not None: self.details.setPlainText(result.document)

    def finished_operation(self):
        self.progress.setRange(0,1000); self.progress.setValue(1000 if self.last_result and self.last_result.state=='completed' else 0)
        self.update_controls()

    def import_catalog(self):
        if self.busy() or self.service.source is None: return
        path,_=QFileDialog.getOpenFileName(self,'匯入已簽署元件目錄','','JSON (*.json)')
        if path: self.start('catalog_file',path=path)

    def request(self, operation):
        if self.busy() or operation not in self.buttons or not self.buttons[operation].isEnabled(): return
        row=self.selected()
        if row is None: return
        path=None
        if operation=='offline':
            path,_=QFileDialog.getOpenFileName(self,'匯入與目錄相符的元件包檔','','元件包檔 (*.zip *.archive)')
            if not path: return
        # 確認框只用契約限制的 ID／版號，避免 display_name 觸發 QMessageBox AutoText。
        if operation=='remove' and QMessageBox.question(self,'移除受管版本',f'移除 {row.spec.component_id} {row.spec.version}？\n只處理已驗證的受管檔案，其他資料保留。')!=QMessageBox.StandardButton.Yes: return
        self.start(operation,row.spec.key,path)

    def cancel(self):
        if self.busy():
            self.job.cancel.set(); self.status.setText('正在取消並收尾；單次網路等待最多約 10 秒，請等待維護完成。')

    def closeEvent(self, event):
        if self.busy(): self.cancel(); event.ignore()
        else: event.accept()

    def reject(self):
        if self.busy(): self.cancel()
        else: super().reject()

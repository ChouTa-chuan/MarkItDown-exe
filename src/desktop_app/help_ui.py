"""提供原始碼與打包程式共用的離線操作手冊及第三方授權視窗。"""
from importlib.resources import files
from pathlib import Path
import sys
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog,QVBoxLayout,QTextBrowser,QPushButton


def license_root():
    return Path(files('desktop_app').joinpath('data/licenses'))


class HelpDialog(QDialog):
    def __init__(self,document,title,parent=None):
        super().__init__(parent)
        self.setWindowTitle(title);self.resize(880,680)
        layout=QVBoxLayout(self)
        self.viewer=QTextBrowser()
        self.viewer.setOpenExternalLinks(False)
        self.viewer.setOpenLinks(False)
        self.viewer.setMarkdown(files('desktop_app').joinpath('data/'+document).read_text(encoding='utf-8'))
        layout.addWidget(self.viewer)
        if document=='third-party.md':
            button=QPushButton('開啟完整授權資料夾')
            button.clicked.connect(lambda:QDesktopServices.openUrl(QUrl.fromLocalFile(str(license_root()))))
            layout.addWidget(button)

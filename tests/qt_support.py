"""測試自己建立的 Qt 視窗須在 QApplication 銷毀前釋放。"""
from PySide6.QtCore import QCoreApplication, QEvent, QThread
from shiboken6 import isValid


def release_test_widgets(app):
    # close() 預設只隱藏；延留的 Python signal／lambda 可能讓物件活到
    # PySide 的全域 cleanup。按頂層父子關係刪除，避免依賴全域 wrapper 順序。
    for widget in app.topLevelWidgets():
        if not isValid(widget):
            continue
        if not widget.close():
            raise AssertionError('Qt 測試仍有忙碌視窗，不能銷毀背景工作。')
        for thread in widget.findChildren(QThread):
            if not thread.wait(15000):
                raise AssertionError('Qt 背景執行緒未正常結束。')
        widget.deleteLater()
    QCoreApplication.sendPostedEvents(None, QEvent.Type.DeferredDelete)
    app.processEvents()

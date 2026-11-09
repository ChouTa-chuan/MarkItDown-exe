# Qt 視窗關閉與程序退出

2026-11-09，程式 **0.17.1**，架構 **0.4**。

先前 Linux 元件管理測試曾在 23 項斷言全部通過後退出 -11；混合程序也曾退出 139。本次重現 12 輪中的 1 輪 -11，LLDB 另取得 `PySide::destroyQCoreApplication → visitAllPyObjects → QPushButton wrapper → QObject::~QObject` 的 SIGSEGV。這是全域 Qt 清理階段的證據，並非文件轉換斷言失敗。

`close()` 預設只隱藏視窗。GUI 入口現在對自己建立的主視窗設定 `WA_DeleteOnClose`，由 Qt 事件迴圈依父子關係釋放主視窗及子視窗。忙碌時原 `closeEvent` 仍拒絕關閉並要求取消，工作收尾後才能關閉；沒有強制終止執行緒或跳過 Python／Qt cleanup。

六組 Qt 測試另明確清理自己建立的頂層視窗：確認正常關閉、等待已完成執行緒，再處理 deferred delete，避免測試留下的隱藏視窗延留至全域 wrapper 清理。這是測試資源責任；不能只改測試清理就宣稱應用程式入口也已修正，因此另測真正入口。

新增三個真實 Qt 子程序檢核：

1. 主視窗關閉後，在 `main()` 返回前收到 destroyed，C++ 物件已失效，子程序正常 exit 0。
2. 開啟並關閉元件管理視窗後，主視窗及子視窗均在 QApplication 全域清理前釋放。
3. 真實 QThread 忙碌時第一次關閉被拒、收到取消且視窗仍有效；執行緒收尾後才能釋放並正常退出。此合成工作只驗生命週期，不作 OCR 證據。

前兩項在入口修正前都失敗；修正後三項通過。元件管理 23 項修正後連續 12 輪正常 exit 0；完整結果、原始失敗、原生堆疊與進度截圖見[本次開發紀錄](development-records/runs/qt-lifecycle-2026-11-09/README.md)。

驗收限目前 Linux、Python 3.12／PySide6 6.12.0 與已記錄流程；不宣稱修復所有第三方 Qt 清理錯誤。Windows 新版建置結果另驗，C11 仍 2/5、完整導入 7/12、歷史基線 19/25。乾淨 Windows、各選配元件、人工操作、GPU、Inno 暫存清理及 ONNX 繁中品質缺口仍保留。

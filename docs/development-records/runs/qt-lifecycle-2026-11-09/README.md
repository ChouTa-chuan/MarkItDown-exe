# Qt 視窗生命週期與正常退出

2026-11-09（台北），程式 **0.17.1**、架構 **0.4**。沿用0.17 Windows基本包成果，本輪完成 Linux Qt 正常退出修正與回歸；C11仍2/5、完整7/12、歷史19/25。

- 原版23項管理測試12輪中11次exit0、1次exit-11，見 `before-summary.json`／`before-*.log`。不是把未重現當修復。
- 沙箱內LLDB握手失敗後，在一般核准的外層命令真正取得SIGSEGV。`lldb-repeat-1.log` 及 `lldb-type-1.log` 顯示PySide全域QApplication cleanup內的QObject destructor；反組譯對應QPushButton wrapper。LLDB本身exit0不等於被偵錯的child成功。`trace.c`／`trace.py` 只是前期診斷，未取得C stack；不屬於產品或驗收機制。
- 原 `close()` 只隱藏，視窗及signal/lambda引用可延留至全域cleanup。GUI入口改由WA_DeleteOnClose在Qt事件迴圈內依父子順序釋放；六組Qt測試各自清理頂層視窗、正常等待執行緒及處理deferred delete。
- 新增入口釋放驗證：前兩案在修正前都失敗（`lifecycle-before.log`），修正後三案通過（`lifecycle-final.log`），含元件管理視窗及真實QThread忙碌時拒關／取消／收尾後銷毀。首次設定服務以mock略過、忙碌工作為有界合成fixture，只驗生命週期，不作OCR品質證據。
- 修正後管理23項連續12輪exit0，見 `after-summary.json`；完整混合程序597項、596通過及1既有ONNX品質預期失敗，exit0（`full-mixed-final.log`／`full-mixed-final-exit.json`）。35模組隔離同597項，全child exit0、0跳過，見 `isolated-regression-final/summary.json`。沒有os._exit或強制終止繞過cleanup。
- 首輪全回歸未指定TESSDATA_PREFIX且升版後closure未刷新，混合程序1失敗／1錯誤／6跳過、exit1；隔離首輪也未接受。原 `full-mixed.log`／`isolated-regression/` 保留。以原四語固定hash模型目錄補齊環境、離線重新產生closure後，完整重跑並接受；7個鎖檔及第三方原文不改。

重跑設定：`PYTHONPATH=src`、`QT_QPA_PLATFORM=offscreen`、`PYTHONFAULTHANDLER=1`、`TESSDATA_PREFIX=/workspace/markitdown-four-language-models`；Python使用既有乾淨venv，測試前本機無網路安裝0.17.1。完整命令與來源hash見 `verification.json`。進度瀏覽器結果／截圖另存本目錄。

本輪沒有Windows新版實跑、乾淨機、GPU、人工UI或Setup發行。先前0.17 Windows測試保留原版本歸屬；推送將依既有規則觸發基本包CI，結果須另查。Inno精確收據保留的1份暫存清理仍待，ONNX繁中品質預期失敗仍不是品質通過，RAM仍為軟性預算。此修正只對本輪已驗流程負責，不宣稱修復所有第三方Qt內部錯誤。

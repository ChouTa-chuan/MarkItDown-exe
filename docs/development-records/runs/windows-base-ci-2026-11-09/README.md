# Windows 基本包自動驗證完成

2026-11-09（台北），程式 **0.14.0**、架構 **0.4**。[CI #7](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42539123115)（3384167）真正完成 Ubuntu 固定來源重建與 Windows 2022 基本包建置，**Windows 10/10 通過**，Python UTF-8 mode=true、Qt 自身視窗開啟並正常 exit 0（正常關閉要求共 4 次），沒有用 terminate 當成功。

通過範圍：原生／模型／原文與 profile hash、frozen core、不借外部 Python 指令、四語健康與四份掃描 PDF、中文空格搬移後完整自檢、UTF-8 檔名／原 bytes、四語 CLI／偏好保留、缺損模型與 EXE 不回退外部引擎、缺選配明確失敗、真正 Qt Windows 視窗及正常退出。derived-check-ledger 由同一固定 source 控制流程與真實 accepted=true／10 項計數推導，明確標記為推導，不冒充未下載的完整 raw report。

保存公開原頁、完整短診斷 JSON、run／commit／範圍等 provenance。完整報告、bundle 清單、合成輸出與 Windows 自身視窗截圖仍在需登入的 CI artifact（七天）；未下載就不宣稱已永久封存那些附件。引擎／模型／最終 app binary 不加入 Git，也沒有 Setup／tag／Release。

Linux 功能回歸已另存於 windows-ci-retry：31 個 child 全部正常 exit 0，555 項（554 通過、1 個固定 ONNX 繁體品質預期失敗、0 跳過）。混合單程序在普通執行曾 native teardown exit 139，原因仍未定位；本次 LLDB 下 555 項與測試 target 正常 exit 0，未重現，所以沒有 C stack。debugger 自己 exit 1 是因後續 backtrace 查詢時 target 已結束，不是測試失敗。原始預設 handshake 失敗與成功啟動的偵錯紀錄分存，不讀環境／憑證或變數。

本輪完成的是 hosted runner 的基本包開發驗證。C03 3/4、C04 2/4、C09 3/4、完整導入 **7/12**、歷史基線 **19/25** 保留；runner 預裝 Python／開發工具，不是無 Python 乾淨機，亦非完整安裝／升級／修復／解除安裝、人工 UI、選配各 profile 或 GPU 驗收。下一步接乾淨 Windows 與安裝生命週期，混合 Linux teardown 另追。

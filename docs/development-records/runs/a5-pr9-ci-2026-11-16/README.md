# A5：PR 9 Windows 逐檔元件驗證

日期：2026-11-16（台北）。[PR #9](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/9) 首輪全部 CI 通過；程式來源 `2104418f08ca64232136278dbdddb70c3ea91897`，文件 head `fc5bb3be682887b2f148e410825aac3a888af804`，實際 CI checkout 為 GitHub 暫時合併提交 `3ef16b67612b6b18a01898675843b4ee8cb4322f`。最終文件提交仍須通過同一 PR 的最新 CI 才一般 Merge；合併狀態以 PR 為準。

## 驗證結果與範圍

- Windows 基本包 run [43821808274](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43821808274)：原生輸入、建置、GUI／OCR、安裝修復移除、跨版與中斷恢復全部接受。
- Windows CPU run [43821808348](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43821808348)：建置、OCR、同版維護、跨版與中斷恢復接受。
- Linux run [43821808395](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43821808395) 與歷史索引 run [43821808360](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43821808360) 均 success。本機完整回歸數字及來源沿用 [progress.json](../../../progress.json)／[本機紀錄](../a5-cpython-components-2026-11-16/README.md)，沒有從未下載的 CI 原始 JSON 推算新的計數。
- 兩種 profile 的 `CPython components` annotation 均列出八個檔案，所有來源指紋與建置解譯器實際載入的檔案相符。OpenSSL 宣告／觀測皆 3.0.16；SQLite 宣告 3.49.1.0、觀測 3.49.1（版本表示尾碼差異）；libffi 宣告 3.4.4。
- **libffi 沒有支援的執行期版本 API，DLL 也沒有 PE FileVersion**，保持 `observed_version=null`、`build-declaration-only`；不能稱為獨立二進位版本認證。`_ctypes.pyd` 的 PE 版本是 CPython 版本，不是 libffi 版本。
- OpenSSL／libffi 原文及 SQLite 來源標頭原始註記的 hash 均與固定 profile 相同。原文由建置檢核重新驗證；annotation 保存其路徑與 hash，並非完整 artifact 的獨立下載核驗。
- 版本觀測來自**建置解譯器載入的來源 DLL**，再用 hash 對應 PyInstaller 收集的原檔；不宣稱已對 frozen 候選進行獨立 runtime probe。既有 native 證據仍負責收集檔與打包轉換的對應，A6 固定候選再審保留。

## 計數與未完成

基本包來源摘要相對 A4 增加新增的元件清單與三份原文，實體檔案與未對照檔案均增加四；逐檔來源／原文證據不會自動賦予 owner。現況計數只記 [progress.json](../../../progress.json)，原始摘要在下列 JSON。PYZ 未知模組維持零，不與實體未對照檔案數互相抵銷。未下載完整逐檔報告，不能據總數聲稱完整集合逐檔相同。

A5 的逐檔證據階段完成，後續接 A5b Qt 原始碼對應，再進 A6 固定來源候選與整體審閱。`runtime_sbom_complete`／`redistribution_approved`／`release_ready` 保持 false；既有 `cb8f24d` 候選未被替換，Windows hosted CI 不等於乾淨機或實體 GPU 驗收。沒有發布 Setup、worker、模型、tag 或 Release。

## 文件檢查補記

文件更新時誤把不存在的 `test_progress` 當成測試模組呼叫，unittest 回傳匯入錯誤；同次實際存在的歷史索引測試已通過。這是呼叫名稱錯誤，不是程式回歸失敗；之後改用實際索引測試、進度頁重建一致性及文件連結檢查。沒有把這次錯誤計入完整回歸通過數。

## 保存方式

[ci-results.json](ci-results.json) 保存 GitHub run／job 狀態、公開 check-run JSON annotation 與 artifact 的 id／digest／到期日；manifest 索引本地檔案 SHA-256。artifact digest 為 GitHub 中繼資料，**本輪未下載或獨立驗證壓縮檔內容**。原始日誌與大型報告仍在各 CI run，artifact 有期限，實際期限逐份見 JSON。此目錄不覆寫本機 A5 或 A4 原始證據。

[返回歷史索引](../../../history-index.md)

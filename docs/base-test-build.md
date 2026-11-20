# 固定基本包測試版流程

使用既有的 **Windows base validation** 手動執行。應用程式固定 checkout A13b 候選 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`。控制端使用執行工作流程的提交並獨立評估義務登記，兩個提交都會寫進報告。B1b 只接受基本包旗標為 disclosed 和 redistribution approved 為 true，strict complete 和 release ready 為 false。

## 報告式試跑

從自己的分支手動執行，設定 `prepare_test_build: true`、`publish_test_build: false`。可用 `ocr_inputs_run` 指定已有有效輸入的成功 run，空白時選最新可用者。既有一般驗證的 OCR 輸入 artifact 只保留一天，下載後仍要核對固定候選的引擎與四語模型 SHA。

Runner 從 run 44295039865 下載 `windows-base-validation-reports`，以 A13b 審閱保存的 SHA-256 核對 `bundle-provenance.json`，再以原始 inventory 核對實際重建 bundle 的完整路徑、檔案指紋與純 Python 模組清單雜湊。只有 `base_content_equivalence.py` 中列出確切路徑及理由的生成檔可以有差異，每筆實際差異在 `CONTENT-EQUIVALENCE.json` 留下新舊指紋。標準庫 ZIP 的外層可因生成而不同，各成員的名稱、大小及 CRC 必須一致。OCR 來源收據也要用當次輸入重核。試跑保存文字報告及已驗過雜湊的來源報告副本，供原始 artifact 到期後指定 `saved_baseline_run` 繼續核對同一份原件。

若到 **2026-11-25 11:45 UTC** 仍未取得完整清單且沒有來源報告副本，可明確選 `retained_review: true`，用 repo 保存的分類、原生檔、原文、模組雜湊與檔案數查驗。此模式涵蓋的範圍較小，產品 README 與對照摘要都會揭露。已下載但雜湊不符的原始報告需查明原因，不能在同次執行改走退路。

Hosted Windows 2022 執行四語 OCR、GUI、中文路徑、Qt 替換、安裝、修復與移除。實機、乾淨系統與人工驗收在大階段 C 執行。一般 PR CI 仍執行跨版本升級與中斷恢復。

## 審查通過後公開一次

1. 先確認 PR 的全部適用 CI 成功、Claude reviewer 無必須修正，並已一般 Merge 至 main。
2. 在當前 main 跑一次一般 Windows base validation。確認成功並記下當日 `windows-ocr-ci-inputs` 的 run，公開流程會核對來源提交和期限。
3. 用 main 手動執行 **一次**，設定 `prepare_test_build: true`、`publish_test_build: true`、`ocr_inputs_run` 為該次一般驗證 run。原始報告可用時採固定 run，已過期則指定已保存原始 provenance 的試跑 run。公開工作重跑會被拒絕。若失敗，保留紀錄並先查明原因。
4. 用 API 確認僅有 `MarkItDownBase-test-build` 與 `base-test-build-reports`，核對 30 天期限，將兩者名稱、digest、大小及到期日存進本輪證據目錄。接著另開小 PR 將 `PUBLIC_UPLOAD_ENABLED` 關回並更新 STATUS。

公開產品 uploader 要求 GitHub ref 為 `refs/heads/main`。腳本亦會核對同一 ref、啟用常數、gates、已通過的對照與實際 Setup SHA，並用 lifecycle 收據驗證上傳內容。Setup 同固定程式來源重建，外殼指紋可能不同。產品附件與下載方式見 [中文 README](base-test-build-download.md)。報告 artifact 附的 SHA256SUMS 對應產品目錄。此流程使用 GitHub Actions artifact，保留 30 天。

# A12b 既有證據接線

從 main 6e69456 開啟自有分支；沒有開啟中的 PR。固定候選仍為 A12 的 2555687，沒有重新建置或固定候選。

[逐列對照](origin-known-review.json) 保留 A12 所有 origin-known 列的 path／SHA、原分類及逐列理由；[工程證據評估](evidence-assessment.json) 接上 Python 封存摘要／fingerprint 與實際 MIT 套件綁定。來源歸屬完成不等於隨附元件或再散布義務已全部完成。完整 pure TOC 原始明細仍在原 CI 報告，本目錄未宣稱下載或重複保存該大型報告。

[Community 原文](official-vs2022-community.docx)、[來源紀錄](community-source.json) 與[白話摘要](community-summary.md) 只保存並陳述條文，不判斷特定使用者、CI 或 DLL 適用性。文件不加入安裝包，base-microsoft 仍 open。

使用者明確要求補註舊 A12 出口報告的關閉階段；[定點補註紀錄](targeted-amendments.json) 保存原 commit／Git blob／SHA。只補註 base-clean-machine-manual 必須到大階段 C 才能關閉，並機械刷新該舊 manifest 的對應 hash；A12 原始分類、狀態與數字不改，原版仍可由指定 Git commit 取得，不重複複製舊完整 JSON。

只將 base-source-attribution、base-archives、base-own-mit-binding 的工程狀態改為 evidence_complete；base-cpython／base-tesseract-models 保持 open，前者依使用者決定標 requires_user_decision=true。既有須使用者決定的條目狀態全部不改。base／cpu 三旗標 false，原 coverage／計數口徑不變。完整混合與獨立模組回歸通過，來源與數字見 docs/progress.json；最終 head CI／查驗／Merge 見 [PR 26](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/26)。

不動 spec、鎖檔與打包內容，不代為做 A13 決定，不交付產品、建立 Release 或 tag。A12b Merge 後才從最新 main 另開 A12c 分支。

[本輪 gates 摘要](gates-summary.json) 保存解除／剩餘阻擋；A12 原始 gates JSON 原地保留。原始測試日誌留本機與 CI，repo 只存必要小型結果。Windows／CPU 的 PR CI 是整合驗證，不能把它稱為重新固定候選或實體機驗收。最終 CI run、artifact hash 與期限記於 PR，避免補通知再觸發重複建置。

# A7 自有 MIT 對照與工作流驗證

2026-11-17（台北），程式0.19.1／架構0.4不變。從 PR 12 已合併的 main 7b787d3 開自己的 codex/a7-mit-notice-20261117 分支。

首個提交 8cd064b 修正指定文件及 A6 原排隊 run 的最終成功補註；A6 attempts.json 未改寫。12d3dce 獨立處理兩條 Windows 工作流的 step env／SHA 預檢；edb1d82 補真正多片的缺片與越界反例；07afa79 完成既有 A7 自有 MIT 目標。

## 實作與驗證

- 基本包沿用 `_internal/desktop_app/data/licenses/markitdown-desktop/LICENSE`，把它綁入 installed package notice 表；產生與 audit 兩端核對固定來源的原始位元組。缺少綁定、重複綁定、缺檔／改內容，以及把自有 MIT 綁給其他套件均拒絕；反例先重算資產 hash，確認不能重綁 hash 繞過。
- 工作流來源只經 step env EXPECTED_SOURCE 傳入；pwsh 先驗完整 SHA 再傳給 Python，run 程式碼不含來源 expression。靜態接線已核對，原生 Windows 的有效來源路徑已執行；本機未安裝 PowerShell，不冒稱做過本機 PowerShell 負向執行。
- 分片反例包含 parts[:-1] 與 part 編號越界，測試先確保多片，不把缺片退化為空清單。
- 完整 Linux 混合與獨立模組回歸通過，只有既有 ONNX 繁中 expected failure，沒有跳過。實際計數只記 [progress.json](../../../progress.json)，新結果原檔為 mixed-result.json／isolated-summary.json。
- [Windows 基本包 run 43996798825](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43996798825) 以來源 `07afa79add13d35ede89af8c332bc6dab1aed15e` 完成既有驗收與新增檢查。metadata 完整取回並以該 Git 樹離線重跑，MIT 路徑／hash／套件綁定相符，自有套件原文待審原因消除；來源與原始完整報告 hash、artifact digest／期限只保存於精簡 windows-mit-proof.json。

## 保存界線與接手

本目錄只放本輪新結果及精簡 Windows 證據。完整 Windows JSON／大型日誌留 CI，沒有下載或重複保存舊嘗試的完整 JSON；舊資料只引用 hash 與 run 編號。A6 README 追加補註前的 hash、原 manifest hash 及未變動的 attempts.json hash 已記於該補註。

此次來源是 A7 分支驗收，不重新定版 A6 的全套固定候選 8285450；CPU 與最終 head 的整合驗證依本輪 PR 檢查，最終 run／Merge 結果記在 PR。runtime_sbom_complete、redistribution_approved、release_ready 維持 false，產品里程碑不提高。

**A7 完成後先停。大階段 A 的整體複查及剩餘義務重新規劃交由 Claude planner；本輪沒有產生新的整體路線圖。**

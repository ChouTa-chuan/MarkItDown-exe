# A8 義務登記與旗標判定驗證

2026-11-17（台北），程式0.19.1／架構0.4不變；從 main 08c4dcb（PR 14）另開 codex/a8-redistribution-gates-20261117。

首個提交 fec86c9 先完成 A7 查驗留下的四項問題：PowerShell 使用 -cmatch 與嚴格結尾，補保留其他各片的最後 part 越界反例，更新 m5／A7 現況，CHANGELOG 說明環境相同比較布林欄位移除的原因。

核心僅新增 packaging/redistribution/obligations.json 與 scripts/redistribution_gates.py，另有必要測試及 [定義文件](../../../redistribution-gates.md)。腳本只讀既有 A6 兩份 source-review；每個原生檔與每個 reason 分別唯一對應，來源提交不同、未知或重複對應、沒有決定出處的核准、證據 hash／quote 不符均拒絕。

現況兩個 profile 的三旗標全 false，且輸入資料與原有計數不變。完整回歸與獨立程序結果見本目錄新結果；相關反例、合成全關閉正例、旗標相依與 base／cpu 獨立均通過。數字只記 [progress.json](../../../progress.json)；本 manifest 記來源 hash、條目與旗標摘要，不複製 A6 大型舊 JSON。合成 true 正例不當作真實法律／實機驗收。

未改 spec、套件收集、依賴鎖或既有計數程式；只有 C 節指定的第三方說明文字勘誤及重產 Markdown。舊原始證據／決定／授權原文／模型／架構快照原地保留，沒有打包減量或產品交付。A8 獨立提供判定入口，A12 出口須使用其結果，原建置報告保留為原始證據。

來源為 5e7fd532a4b97f33ff0aad460d80fb653b48183f；最終 head CI／Merge 與有期 artifact 的 run、hash／期限記於本輪 PR，不以 PR 暫時 merge 取代固定候選。A8 完成後先停，不接續 A9–A17。

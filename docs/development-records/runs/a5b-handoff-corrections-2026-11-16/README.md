# A5b 第一個提交：交接與使用者決定復原

2026-11-16。來源為已合併 PR 1–9 的 main `c51089a258b820b95af51816e516a05300dfb7c4`。

依使用者要求，在 A5b 第一個提交恢復 STATUS.md D 節的歷史使用者決定原文，明列 main 已合併 PR 1–9／A5 已通過 Claude reviewer，更新 next，並把完整 A5c 三項及獨立 PR／Windows CI 條件列為待辦。AGENTS 補記使用者直接決定不得因精簡合併或刪除。A5b 尚未更動 Qt 來源或 A5c 驗收標準。

使用者明確要求在既有 A5 CI README 補上最終 head 的四個 run；修改前先保存 [原版 README](a5-README-before-a5b.md) 與 [原版 manifest](a5-manifest-before-a5b.json)，再更新該 README 的 hash。原始 ci-results.json 不變，原始首輪與最終 CI 不混用。

純文件檢查涵蓋恢復原文逐行比對、連結、原始 JSON 不變、manifest hash、進度頁及歷史索引一致性。本提交未執行新程式回歸；A5 既有回歸／Windows 結果保持其原始來源。

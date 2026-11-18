# A12c 揭露式關閉規則

從 A12b 已一般 Merge 的 main `4f30196` 開自己的 `codex/a12c-disclosure-gates-20261118` 分支；開工無開啟中的 PR。A12b 最終 head、五條 CI、Windows metadata replay／Qt 替換及 Pages 結果見 [前階段小型收據](predecessor-ci.json) 與 [PR 26](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/26)。只存 run、hash 及期限，不重複保存舊完整 CI 報告。

本輪登記 schema 3，每項 accepted_gaps 仍空，其他條目欄位及狀態完全不變。新增 runtime_sbom_disclosed，redistribution_approved 改依揭露及原再散布義務；runtime_sbom_complete 遇未知或建置宣告缺口仍 false，release_ready 仍等待大階段 C。詳細格式、來源義務範圍及各元件 id 定義見 [判定文件](../../../redistribution-gates.md)。Qt attribution 是來源上位集合，未證明編入的宣告逐項保留缺口，並未稱為實際已編入。

[真實 A12 重跑摘要](gates-summary.json) 顯示 base／cpu 全部旗標 false，accepted_gaps 空，coverage、原 inventory_summary 及既有阻擋集合不變。原始 source-review／分類／gates 報告均原地保留；本輪沒有建立真實隨包揭露檔，也沒有代寫 A13 核准。

合成 base／cpu 正例證明：有使用者決定、精確缺口集合及同 hash 隨包揭露時，complete 仍 false，disclosed／redistribution_approved 可以 true，人工驗收未做時 release_ready 仍 false。另以合成 wheel 目錄驗 embedded 到 gates 的完整接線；反例包括錯誤缺口集合、缺決定、未標需使用者決定、工程狀態冒充核准、缺揭露檔、揭露內容／位置／候選 hash 不同、隱藏已存在目錄、無缺口卻列接受。這些不是實際使用者決定、候選產品或 Windows 實機驗收。

[首次反例失敗及原因](failed-attempts.json) 保留 fingerprint；最終針對性與完整混合／獨立模組回歸通過，數字及來源只在 docs/progress.json 維護。完整日誌留 CI；repo 只留必要小型結果。最終 head CI run、artifact digest／到期日、查驗與 Merge 見 [本輪 PR 27](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/27)，避免補通知反覆觸發建置。

沒有變更 spec、鎖檔、打包內容、候選來源或既有計數口徑；程式版本及架構版本不變。不交付產品、不建 Release 或 tag。完成 A12c 後停止；A12d 是否執行、A13 各項由使用者決定，A13b 才依決定實際加入揭露並重定候選。ONNX 繁中、RAM 軟性預算、Windows 實機／GPU 未驗收限制保留。

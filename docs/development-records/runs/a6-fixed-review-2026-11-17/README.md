# A6 固定來源候選與審閱紀錄

2026-11-17（台北），程式／架構版號不變。從已合併 PR 1–11 的 main 開自己的 codex/a6-fixed-candidate-20261117 分支；首個提交 d098e2c 已完成使用者指定的現況、最終 CI run 及 D 節維護修正。

本輪固定來源為 `8285450226abe1381e6a357e8bd33bff1ad46e0e`，基本包 [Windows run 43912954070](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912954070) 成功，實際 HEAD／選擇來源一致、既有驗收通過。精簡 metadata 已完整取回、核對指紋，並以原 Git 樹離線重跑分類。實際計數只記 [progress.json](../../../progress.json)。候選只保存在可拋棄 runner，沒有交付產品、Release 或 tag。

CPU 同來源 [43916217757](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43916217757) 已成功，包含既有功能與新增審閱資料產生步驟；metadata 完整性及原 Git 樹離線重跑均通過。原請求 [43912958713](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912958713) 長時間 queued、jobs 空白，取消指令與 API 回覆矛盾、未確認取消，保留作追溯；重送成功後不再觸發重複建置。

兩種固定候選來源相同，精確候選指紋與原始公開摘要見各 JSON。PR 的暫時 merge 僅做整合驗證，最終 head CI／Merge 結果見 [PR #12](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/12)；不以 PR 產物替換固定來源證據。

## 保存的資料

- base-source-review.json、cpu-source-review.json：實際候選指紋、原始完整報告／inventory 指紋、全部待審列、原生與套件來源摘要及分類輸入。accepted 是證據一致，不是權利核准。
- fixed-ci.json：API 取回的原始公開摘要、精確來源與 run、metadata 完整性及 artifact digest／期限。原始大型日誌與完整報告留在 CI；本檔沒有內嵌完整 inventory，過期後無法靠精簡檔重新驗整個舊 bundle。
- mixed-result.json、isolated-summary.json：完整本機混合與獨立程序回歸，只有既有 ONNX 繁中 expected failure，無跳過。程式來源為固定提交；文件／新證據當時仍在工作目錄準備。
- historical-replay.json：舊候選分類、狀態與指紋重現，原歷史資料未改寫。
- attempts.json、mixed-before-index-refresh.json、input-budget-check.json、attempt-e1761f9/：保存首次檢查、容量問題、索引更新與先前基本包成功實證，不改標為最新候選。
- self-review.json：Codex 自我查驗範圍與尚未通過的項目；不宣稱另有 Claude reviewer。

首次來源檢查因既有 out 暫存未忽略而拒絕；新增根目錄建置暫存忽略規則後，重新選定來源重跑。前一輪 CPU 的既有建置／維護／跨版／恢復驗收通過，但新審閱步驟 exit 1，原始 traceback 未取得。保存的同類完整 CPU 報告超過原精簡入口上限，容量不相容已重現；完整來源與精簡傳輸上限現已分開並有反例，新版 CPU 實證現已通過；實際完整報告容量亦超過原精簡入口限制，來源與公開資料容量分離已驗，但不把推論冒稱前次未取回的原始 traceback。

runtime_sbom_complete、redistribution_approved、release_ready 都維持 false。整體基本包審閱與後續具體缺口見 [A6 審閱](../../../a6-source-review.md)。


## 2026-11-17 補註：原排隊 run 的最終結果

[Run 43912958713](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912958713) 最終為 **completed／success**，來源仍是 8285450。GitHub API artifact 清單只有 windows-cpu-validation-reports 報告（artifact 14256147838，digest `sha256:5e5938919f532e744ec6f1941a8956f2cb796a348a7fe235cd522bbc71ae6482`，期限 2026-11-23T18:19:53Z），沒有 Setup／worker／模型產品 artifact。上面的 queued／取消回覆是當時紀錄，後續不重送。PR 12 已合併（7b787d3），合併後 CI 全綠；使用者確認 A6 Claude reviewer 通過，無必修項。

本次依使用者指示只追加此補註並更新 manifest 的 README hash，不改寫 attempts.json，不另存舊嘗試完整 JSON。補註前 README SHA-256：`b0b4889fc99cd2b140dbe9bb541fe1c78a08795aa5aa021f00fd4ff009aee0e0`；補註前 manifest SHA-256：`7a18604d2ad15ddc077d6967e9062ad16e43a1788ed6a8819ce40dea79238f73`；保持不變的 attempts.json SHA-256：`88b11552ddd56d33081fbfdf95287aa1de5e07c068515ae623c504c6d7022884`。

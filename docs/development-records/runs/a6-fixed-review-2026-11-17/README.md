# A6 固定來源候選與審閱紀錄

2026-11-17（台北），程式／架構版號不變。從已合併 PR 1–11 的 main 開自己的 codex/a6-fixed-candidate-20261117 分支；首個提交 d098e2c 已完成使用者指定的現況、最終 CI run 及 D 節維護修正。

本輪固定來源為 `8285450226abe1381e6a357e8bd33bff1ad46e0e`，基本包 [Windows run 43912954070](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912954070) 成功，實際 HEAD／選擇來源一致、既有驗收通過。精簡 metadata 已完整取回、核對指紋，並以原 Git 樹離線重跑分類。實際計數只記 [progress.json](../../../progress.json)。候選只保存在可拋棄 runner，沒有交付產品、Release 或 tag。

CPU 同來源 [43912958713](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912958713) 長時間 queued、jobs 為空；重送 [43916217757](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43916217757) 已開始執行，尚待結果。取消指令與 API 回覆互相矛盾，未確認取消、未宣稱已建置成功。後續先核對兩個 run 的即時狀態，不要繼續盲目重送；有結果就保存並重跑分類，再完成 CPU 整體審閱。

## 保存的資料

- base-source-review.json：實際候選指紋、原始完整報告／inventory 指紋、全部待審列、原生與套件來源摘要及分類輸入。accepted 是證據一致，不是權利核准。
- fixed-ci.json：API 取回的原始公開摘要、精確來源與 run、metadata 完整性及 artifact digest／期限。原始大型日誌與完整報告留在 CI；本檔沒有內嵌完整 inventory，過期後無法靠精簡檔重新驗整個舊 bundle。
- mixed-result.json、isolated-summary.json：完整本機混合與獨立程序回歸，只有既有 ONNX 繁中 expected failure，無跳過。程式來源為固定提交；文件／新證據當時仍在工作目錄準備。
- historical-replay.json：舊候選分類、狀態與指紋重現，原歷史資料未改寫。
- attempts.json、mixed-before-index-refresh.json、input-budget-check.json、attempt-e1761f9/：保存首次檢查、容量問題、索引更新與先前基本包成功實證，不改標為最新候選。
- self-review.json：Codex 自我查驗範圍與尚未通過的項目；不宣稱另有 Claude reviewer。

首次來源檢查因既有 out 暫存未忽略而拒絕；新增根目錄建置暫存忽略規則後，重新選定來源重跑。前一輪 CPU 的既有建置／維護／跨版／恢復驗收通過，但新審閱步驟 exit 1，原始 traceback 未取得。保存的同類完整 CPU 報告超過原精簡入口上限，容量不相容已重現；完整來源與精簡傳輸上限現已分開並有反例，新版 CPU 實證仍待，不能把容量推論冒稱該次原始錯誤訊息。

runtime_sbom_complete、redistribution_approved、release_ready 都維持 false。整體基本包審閱與後續具體缺口見 [A6 審閱](../../../a6-source-review.md)。

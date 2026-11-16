# A5b：Windows 控制端的 Qt 摘要接線

2026-11-16。程式來源 `5376c99743ed15ead83ab3f58882be5b78de2ef9`。自我查驗發現基本包 controller 將 `prepare_base_assets.py` 的 stdout 擷取到 `base-assets.log`，原本在子程序印出的 `Qt release sources` 註記不會到 GitHub 公開 annotation。這不是已觀測到的 Windows 通過結果；原 head `ba5c942` 即使其他 CI 通過，也不能當這項修正的實證。

修正後由控制端把真正產生的 `licenses/qt-sources.json` 複製成 report artifact 的 `qt-release-sources.json`，並重新公開有大小限制的摘要；一般 CLI 不額外印 JSON，原始日誌保留。新增測試以合成 Windows 觀測驗證報告位元組、公開 annotation 與副作用；合成資料只驗傳遞契約，不當原生 Windows 執行。沒有更動 A5c 指定的三個 CPython 程式／測試檔。

此程式來源的完整混合與獨立模組回歸均正常退出、無 failure／error／skip，只有既有 ONNX 繁中 expected failure；原始摘要為 [mixed-result.json](mixed-result.json)、[isolated-summary.json](isolated-summary.json)，現況計數只見 [progress.json](../../../progress.json)。原版來源 catalog、Windows wheel 靜態檢查及其結果保留在 [先前紀錄](../a5b-qt-source-2026-11-16/README.md)，不改寫或轉用其程式來源。

另一次 `gh pr view --json baseRefOid` 因本環境 gh 不支援該欄位而失敗，改用 REST API 核對精確 base／head；這是查詢相容性問題，不是測試失敗。後續以包含本修正的 PR #10 CI 取得真正 Windows Qt 摘要，另存新證據，不覆寫此 Linux／傳遞契約紀錄。A5c 三項仍列獨立 PR 待辦；產品門檻及完整 build 修補／參數限制保留。

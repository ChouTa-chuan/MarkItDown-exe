# A5b：PR 10 原生 Windows Qt 來源驗證

2026-11-16（台北）。[PR #10](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/10) 的程式來源為 `5376c99743ed15ead83ab3f58882be5b78de2ef9`，本輪 CI head `e6ad48f75c734447055e5c100ebb06d4197cfc8c`，實際 checkout 是 GitHub 暫時合併提交 `30c9eaff2685975817e8d15fc16bc33314a37477`。

## CI 與查驗

| 流程 | run | 結果 |
| --- | --- | --- |
| Linux 完整回歸 | [43847442914](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43847442914) | success |
| Windows 基本包 | [43847442920](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43847442920) | success，含原生輸入、建置、GUI／OCR、安裝維護、跨版與中斷恢復 |
| Windows CPU | [43847443006](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43847443006) | success，含既有 OCR／維護／跨版／恢復 |
| 歷史索引 | [43847442936](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43847442936) | success |

Windows 基本包 job `133232158175` 的 `Qt release sources` 公開 annotation 已實際讀回；Qt／PySide／shiboken 都為 `6.12.0`，Qt build 字串為 MSVC 2022、Windows llp64 shared release，觀測平台為 Windows。官方 Qt supermodule／qtbase／PySide 固定提交與本地 catalog 相同，catalog hash 也相符。

另外以本輪已下載且符合既有鎖定 hash 的 Windows wheel 讀取 `PySide6/QtCore.pyd`，確認其 SHA-256 與 Windows 建置解譯器實際載入的 Core extension 相同；比對原值及 wheel／entry／大小／hash 在 [ci-results.json](ci-results.json) 的 `qt_core_wheel_match`。這核對的是綁定擴充檔，不能改稱所有 Qt DLL 都已做獨立載入指紋驗收。Qt DLL 的 wheel 靜態 PE 版本另見 [較早的原始紀錄](../a5b-qt-source-2026-11-16/README.md)。

控制端已把真正來源報告複製至 `reports/qt-release-sources.json`，並重送公開摘要，不再只留在子程序日誌。此次新 annotation 實證的是傳遞接線修正後來源；更早 `ba5c942` 的結果不混用。所有本機完整回歸計數與精確來源仍見 [progress.json](../../../progress.json)／[接線修正紀錄](../a5b-qt-ci-forwarding-2026-11-16/README.md)，不從未下載的 Linux artifact 推算額外計數。

基本包新增隨包來源表，實體檔案／未對照數較 A5 增加一，原始摘要與現況計數見 JSON；沒有因新增來源表而自動授予 owner。未下載完整逐檔 artifact，不能只據總數斷言檔案集合只差這一個資源。PYZ 未知模組仍為零，與實體檔案計數分開。

## 保存與限制

JSON 保存各 run／job 的公開狀態、專案 JSON annotation、artifact id／digest／到期日。artifact digest 是 GitHub 提供的中繼資料，本輪**未下載或獨立核驗完整 artifact 壓縮檔**；原始日誌及完整報告留在 CI，有期限，實際逐份期限見 JSON。已獨立下載核對的 Windows wheel 與這項限制分開，不混稱為 artifact 已下載。

A5b 官方發布來源位置／版本對應與原生 Windows 查驗完成；最終文件 head 仍須依 PR 的相同全 CI 門檻才一般 Merge，精確合併狀態與最終 CI 以 PR 為準。此來源對應不證明可逐位元組重建、官方 wheel 的完整 build 修補／參數已核實，或所有 LGPL／SBOM／再散布義務關閉。建置解譯器的觀測也不冒充 frozen 候選獨立探測；`binary_reproduction_verified`、`upstream_build_patch_set_verified`、`runtime_sbom_complete`、`redistribution_approved` 均為 false。

下一個是 A5c 獨立 PR；本 PR 未實作其 CPython probe 接受條件、缺失原文反例或 extension observed_version 說明。A6 固定候選及最終審閱保留，原固定候選 `cb8f24d`、程式0.19.1／架構0.4及產品里程碑不提高，沒有產品發行、Release 或 tag。

[返回歷史索引](../../../history-index.md)

# A5c：PR 11 原生 Windows 新探測門檻驗證

2026-11-16（台北）。[PR #11](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/11) 程式來源 `afb2062d4854234356faf2bb959aac634c40f89e`，本輪 CI head `06e7538d67779d0083352b791354c14dd293fefe`，GitHub 暫時合併提交 `24094d6dbc1d28cf4a6b9c720b2c14ce612a8d70`。這輪使用 A5c 新接受條件，不沿用 A5／A5b 的通過結果。

## CI 與查驗

| 流程 | run | 結果 |
| --- | --- | --- |
| Linux 完整回歸 | [43883656659](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43883656659) | success |
| Windows 基本包 | [43883656557](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43883656557) | success，含原生輸入、建置、GUI／OCR、安裝維護、跨版及中斷恢復 |
| Windows CPU | [43883656409](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43883656409) | success，含既有 OCR／維護／跨版／恢復 |
| 歷史索引 | [43883657042](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43883657042) | success |

基本包 job `133357828365` 與 CPU job `133355964055` 的 `CPython components` annotation 已實際讀回。兩種 profile 的已收集 OpenSSL／SQLite 皆為 `matched-runtime-probe`，觀測值存在且 `loaded_source_matched=true`；OpenSSL 為 3.0.16，SQLite 宣告3.49.1.0／觀測3.49.1（尾碼表示差異）。libffi 保持3.4.4建置宣告、`observed_version=null` 與 `build-declaration-only`，沒有假造獨立認證。

Windows 真正通過的是正常建置與新 policy；拒絕 `probe_error`、缺觀測、來源不匹配、重綁 hash 與缺失 OpenSSL 原文的反例，屬 [本機合成／CLI 測試](../a5c-runtime-probe-2026-11-16/README.md)。沒有宣稱 Windows CI 做過實際故障注入。`_ssl.pyd`、`_hashlib.pyd`、`_sqlite3.pyd` 的 `observed_version` 指所連結 OpenSSL／SQLite，該 extension 自身的 PE 檔案版本另列。

本機完整回歸來源與數字仍見 [progress.json](../../../progress.json)／[原始結果](../a5c-runtime-probe-2026-11-16/README.md)，不從未下載的 Linux artifact 推算新的計數。包內來源／原文重驗、原生檔及 Python 封存摘要都由本輪 CI 產生，沒有因此賦予未知 owner 或提高再散布旗標。

## 保存及界線

[ci-results.json](ci-results.json) 保存 run／job 狀態、公開 JSON annotation 與 artifact id／digest／到期日。digest 是 GitHub metadata，本輪未下載或獨立核驗完整 artifact；原始日誌及大型報告留在 CI，有期資料的逐份期限見 JSON。沒有改寫既有 A5／A5b 或 A5c 本機證據。

A5c 新接受條件及查驗完成；最終文件 head 仍需相同全 CI 門檻才一般 Merge，即時最終 CI／合併狀態以 PR 為準。觀測來自建置解譯器載入的來源 DLL，不是 frozen 候選獨立探測；完整 runtime SBOM、建置修補／設定、Qt／再散布與乾淨機／人工／GPU 仍待。

下一個是 A6：先固定來源提交及候選證據，再重跑來源分類與整體審閱。原固定候選 `cb8f24d` 不被 PR 暫時 merge 取代；程式0.19.1／架構0.4與產品里程碑不提高，`runtime_sbom_complete`／`redistribution_approved`／`release_ready` 仍 false，沒有產品發行、Release 或 tag。

[返回歷史索引](../../../history-index.md)

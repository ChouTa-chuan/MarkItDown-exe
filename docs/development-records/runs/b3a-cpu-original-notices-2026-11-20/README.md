# B3a CPU worker 套件授權原文綁定

以 A13b 固定 CPU 候選 `b17d51b`（run [44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417)）對照現有授權資料和鎖定 wheel。兩個 wheel 均未附授權原文。repo 的 `supplemental/sources.json`、`inventory.json` 早已記錄來源與 SHA-256，候選包也已收錄兩份檔案，當時的逐檔分類為 `source-owner-unresolved`。本輪以既有路徑將兩份原文接到 `installed-manifest.json` 的套件列，並由包內 provenance 檢核重驗。原文沒有重新取得或改寫。

| 套件 | 版本依據 | 既有原文 SHA-256 |
| --- | --- | --- |
| flatbuffers 25.12.19 | 採用正式標籤 `v25.12.19` → `7e163021e59cca4f8e1e35a7c828b5c6b7915953` | `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30` |
| rapidocr-onnxruntime 1.4.4 | 同版號標籤 `v1.4.4` → `86ae3f5079df3422c1829cd84baf19bc8a7a9453`。wheel 未附來源提交，無法比對該 wheel 的來源提交 | `3e0af25fdd06aa9586ae97adb00ea927ebe5a3805ac77d2d3a81ce5f55693333` |

[逐套件對照](worker-originals.json)記錄了 wheel、METADATA、原文雜湊、上游提交及候選的實際路徑。兩個鎖定 wheel 的 METADATA 與固定候選逐套件報告相同。在 Linux 以這兩個 wheel 的解壓內容對照改動前後執行 `prepare_worker_assets.py` 的結果，目錄內所有檔案路徑相同，唯一改變的檔案為 `installed-manifest.json`。這項比對涵蓋資產準備輸出。Hosted Windows 建置與包內 provenance 的驗證結果見 B3a PR，與 A13b 固定候選分開記錄。

[兩個 profile 的 gates](gates-summary.json)均以原 A13b 審閱為輸入並以 0 結束。只有 CPU 的 `redistribution_approved` 阻擋清單移除 `cpu-flatbuffers`。兩筆授權原文的歷史分類及選擇器保留在固定審閱裡。`cpu-rapidocr-models` 仍為 open，該套件的三個 PP-OCR 模型及 `config.yaml` 由 B3b 處理。CPU 四旗標均為 false。

Linux 已執行混合程序和逐模組完整回歸，兩種執行結果一致。測試數記於 [進度資料](../../../progress.json) 的 `full_regression`，ONNX 繁中辨識品質仍為既有預期失敗。反例在重算通用雜湊後仍拒絕錯綁、缺檔或改檔。

首次 Linux 回歸因合成的跨 profile 測試未把新增證據複製到暫存根目錄而未通過。補入測試資料後，兩種完整回歸均重跑成功。首次摘要只在 manifest 保留 SHA-256。

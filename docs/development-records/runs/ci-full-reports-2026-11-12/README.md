# Windows CI 完整報告原檔保存

2026-11-12（台北）。程式 0.19.1／架構 0.4；保存對象的 source commit 為 `cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1`。此前 repo 只有公開摘要與 `report_sha256`，完整逐檔報告留在 GitHub Actions、保留七天（到期 2026-11-18）。依使用者指示，在到期前下載原始 artifact ZIP 並原位元組保存，作為後續來源分類的依據。

| 項目 | 基本包 | CPU 選配 |
| --- | --- | --- |
| Workflow run | [42982427175](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427175) | [42982427186](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427186) |
| Artifact 名稱／ID | `windows-base-validation-reports`／13838258991 | `windows-cpu-validation-reports`／13839056280 |
| 保存檔 | [windows-base-validation-reports.zip](windows-base-validation-reports.zip) | [windows-cpu-validation-reports.zip](windows-cpu-validation-reports.zip) |
| ZIP 位元組 | 2,436,414 | 634,069 |
| ZIP SHA-256 | `0808ecd9068d2a926663e9cc05da1b44533ce713654c713a06dc8be548281782` | `54831b0215cff8185e6fd0544c5be54bc8f57a6b771d76dafdc0e4937bc41a4e` |
| GitHub artifact digest | 與上列相同 | 與上列相同 |
| ZIP 成員數／CRC 檢查 | 384／通過 | 61／通過 |
| `bundle-provenance.json` SHA-256 | `2246b6a8a9c0a73049b044e2fa7837880d0109f0077f3c6846fa8e0ef6e26c18` | `9a0fc92b33f6c3d747f6c2762f1b944185c14eb9eed9ad217ca83531d421d64f` |
| 與既有公開摘要 `report_sha256` | **相符** | **相符** |
| 報告內 `source_commit` | `cb8f24d…` | `cb8f24d…` |
| 逐檔清單／未對照來源 | 1,655／154 | 741／303 |

公開摘要為[基本包](../candidate-inventory-ci-2026-11-11/windows-base-inventory-summary.json)與 [CPU](../candidate-inventory-ci-2026-11-11/windows-cpu-inventory-summary.json)；核對程序與觀察值存於 [verification.json](verification.json)，由 [verify_archive.py](verify_archive.py) 產生，可重跑。

## 取得方式

以 GitHub API 的 artifact 下載端點取得暫時簽章網址後 HTTPS 下載，兩者皆 HTTP 200，下載大小與 API 回報的 `size_in_bytes` 相同。暫時網址含時效簽章，**沒有保存在 repo**。首次嘗試被雲端環境網路政策拒絕（對 `productionresultssa31.blob.core.windows.net`、`productionresultssa1.blob.core.windows.net` 的 CONNECT 回 403）；使用者核准把這兩個主機加入本專案環境允許清單後重試成功。

## 內容與限制

- ZIP 維持 GitHub 產生的原位元組，未重新壓縮。內含 `bundle-provenance.json`（完整逐檔清單）、各階段 log、驗收 JSON 與合成樣本輸出；不含 EXE、Setup、worker 或模型本體，因此不構成安裝包交付。
- 以樣式比對掃描全部成員，未發現 token、私鑰或授權標頭；路徑為 hosted runner 的工作目錄。
- 同一 run 42982427175 的 [windows-native-build-reports.zip](windows-native-build-reports.zip)（artifact 13838700150，84,938 位元組，SHA-256 `3197fcbfa85e3515ef1c0cb8e50cd22766c6e332db10948c009eb35ceffdfabd`，與 GitHub digest 相同，19 個成員 CRC 通過）一併保存：內容是 Linux 準備工作的原生建置 log 與下載紀錄。`windows-ocr-ci-inputs`（原生輸入本體，8.8 MB）保留一天、於 11-12 到期，屬再散布未核准的二進位輸入，**未下載、未保存**。
- 報告自身旗標不變：`file_inventory_complete: true`，`runtime_sbom_complete`、`redistribution_approved`、`release_ready` 皆為 **false**。保存原檔不改變 C04 2/4、C11 2/5 或 7/12。
- 本次沒有重跑 Windows 建置；報告內容代表 2026-11-11 那一次候選。

[返回開發紀錄](../../README.md)

# 基本包排除來源不明 OpenSSL 後的 Windows CI

2026-11-13（台北）。[PR 3](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/3) head `746c4f4403d5047aa28a28fc1d33813f40b517e4`（程式 0.19.1／架構 0.4）。PR 流程以 GitHub 的暫時合併提交 `1926072c27626bf06bdefc0087bc295c2759a9f1` 執行，報告中的 commit 即該提交；這不是新的候選證據。

| 流程 | run | 結果 |
| --- | --- | --- |
| Windows base validation | [43354507078](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43354507078) | Success |
| Windows CPU component validation | [43354507071](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43354507071) | Success（此 PR 未更動 CPU 元件） |
| Linux full regression | [43354507025](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43354507025) | Success |
| History index check | [43354507032](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43354507032) | Success |

## 基本包結果（取自 job 公開摘要）

排除 `qopensslbackend.dll`、`libssl-3-x64.dll`、`libcrypto-3-x64.dll` 之後，hosted Windows 2022 上的既有自動驗收全部接受：應用 10 項（含 Qt 視窗開啟與正常退出）、安裝／同版修復／移除 6 段、0.16.0→0.19.1 跨版 11 段、三個中斷點續修（各 10 項）。

與排除前的候選（source `cb8f24d`，[摘要](../candidate-inventory-ci-2026-11-11/windows-base-inventory-summary.json)）比較：

| 項目 | 排除前 | 排除後 | 差異 |
| --- | ---: | ---: | ---: |
| Analysis 原生檔 | 201 | 198 | −3 |
| 來源未對照 | 154 | 152 | −2 |
| 需審閱 | 191 | 190 | −1 |
| 普通檔案數 | 1,655 | 1,653 | −2 |
| 總位元組 | 274,323,912 | 265,766,866 | −8,557,046 |

原生檔少 3 個、未對照少 2 個，與「三個檔案被排除，其中兩個 OpenSSL 原本屬於來源未對照」一致。普通檔案數只少 2 個，推測是同一 PR 加入 `LICENSE` 後自有套件多了一份隨包授權檔；需審閱只少 1 個的組成同樣未確認。

## 限制

- **逐檔清單沒有核對。** 完整報告 artifact `windows-base-validation-reports`（ID 14005494515，SHA-256 `16a374fa62562735fd5ed0890ec526c4c00c1edee108455694dc66e2aeaf5863`，2026-11-20 到期）這次落在另一個儲存主機 `productionresultssa7.blob.core.windows.net`，被雲端環境網路政策拒絕（CONNECT 403），未下載。上表的推論只依據公開摘要的計數；報告 `report_sha256` 為 `193147b1b38b1f886285dc5d865f1da8ee779d04b981582c2d0ef10bae4a4ed3`。
- 不是乾淨機或人工驗收；沒有 GPU。7/12、C04 2/4、C11 2/5 不變。沒有發布產物。

[返回歷史索引](../../../history-index.md)

# CPU 文字辨識元件排除 FFmpeg 後的 Windows CI

2026-11-13（台北）。[PR 3](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/3) head `0b532352526e68a04ebd5f2747a64502b5c119c9`（程式 0.19.1／架構 0.4）。PR 流程以暫時合併提交 `3a2aa3cbd1e4747a8b33847e0c1dfb115fe57b42` 執行；這不是新的候選證據。

| 流程 | run | 結果 |
| --- | --- | --- |
| Windows CPU component validation | [43357232050](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43357232050) | Success |
| Windows base validation | [43357232138](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43357232138) | Success |
| Linux full regression | [43357231995](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43357231995) | Success |
| History index check | [43357231996](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43357231996) | Success |

## CPU 元件結果（取自 job 公開摘要）

排除 `opencv_videoio_ffmpeg*.dll` 後，hosted Windows 2022 上的既有自動驗收全部接受：功能 11 項、同版維護 8 案、元件 1.0.0↔1.0.1 跨版 8 案、程序終止與獨立恢復 6 案；實際推論仍使用 `CPUExecutionProvider`。

與排除前的候選（source `cb8f24d`，[摘要](../candidate-inventory-ci-2026-11-11/windows-cpu-inventory-summary.json)）比較：

| 項目 | 排除前 | 排除後 | 差異 |
| --- | ---: | ---: | ---: |
| Analysis 原生檔 | 106 | 105 | −1 |
| bundle 總位元組 | 252,832,252 | 221,957,052 | −30,875,200 |
| 元件 ZIP 位元組 | 106,326,562 | 93,325,022 | −13,001,540 |
| bundle 普通檔案數 | 741 | 741 | 0 |
| 隨包原文檔 | 285 | 286 | +1 |
| 來源未對照／需審閱 | 303／337 | 303／337 | 0 |

原生檔少 1 個、體積少約 31 MB，與排除一個 FFmpeg DLL 一致。檔案數不變而原文檔多 1，推測是同一 PR 加入 `LICENSE` 後多了一份隨包授權檔，抵銷了少掉的 DLL；這一點沒有逐檔確認。

## 限制

- **逐檔清單沒有核對**：完整報告 artifact（ID 14008010057，SHA-256 `9bf653a89c9ff300b5d2b392e0938a80712e55f0dfa38bf7b9a64455e575272d`，2026-11-20 到期）未下載，原因同 [OpenSSL 那次](../openssl-exclusion-ci-2026-11-13/README.md)。報告 `report_sha256` 為 `b789bb5c60c2fa59b76b97b440377accbb32247956224e5c4dffd6bd11021691`。
- 元件版號仍是 1.0.1，但內容已不同於先前的 1.0.1 候選（ZIP 雜湊改變）。目前沒有對外發布過任何元件，尚無相容問題；正式發布前應重新定版。
- 不是乾淨機或人工驗收；沒有 GPU。7/12、C04 2/4、C11 2/5 不變。沒有發布產物。

[返回歷史索引](../../../history-index.md)

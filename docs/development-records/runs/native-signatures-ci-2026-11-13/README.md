# 取得非 wheel 原生檔數位簽章的 Windows CI

2026-11-13（台北）。[PR 4](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/4) head `8e4dc2d02fc4c4882c2eebff258fcd6a60440951`（程式 0.19.1／架構 0.4）。CPU 元件流程以暫時合併提交 `159da419467eb9fcd401861d8d241d076594e8f4` 執行；這不是新的候選證據。資料取自 job 公開摘要。

| 流程 | run | 結果 |
| --- | --- | --- |
| Windows CPU component validation | [43385475364](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43385475364) | Success |
| Windows base validation | [43385475281](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43385475281) | Success（摘要本次未逐項讀取） |
| Linux full regression | [43385475418](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43385475418) | Success |

## CPU 元件：簽章查詢成功

移除繼承的 `PSModulePath` 後，`identity_errors.files` 為 0，27 個非 wheel 原生檔全部取得簽章且狀態為 `Valid`：

| 來源目錄 | 公司（版本資源） | 簽署者 | 檔案數 |
| --- | --- | --- | ---: |
| CPython 3.12.10 安裝目錄 | Microsoft Corporation | Microsoft Windows Software Compatibility Publisher | 2 |
| CPython 3.12.10 安裝目錄 | Python Software Foundation | Python Software Foundation | 2 |
| CPython `DLLs` | Python Software Foundation | Python Software Foundation | 17 |
| CPython `DLLs` | The OpenSSL Project | Python Software Foundation | 2 |
| CPython `DLLs` | SQLite3 | Python Software Foundation | 1 |
| CPython `DLLs` | （無版本資源） | Python Software Foundation | 1 |
| Visual Studio 2022 `VC\Redist\MSVC\14.44.35112\x64\Microsoft.VC143.CRT` | Microsoft Corporation | Microsoft Windows Software Compatibility Publisher | 2 |

也就是：VC runtime 由 Microsoft 簽署、取自官方可再散布目錄；其餘來自 python.org 發行的 CPython，由 Python Software Foundation 簽署（其中 OpenSSL、SQLite 是 CPython 隨附並由 PSF 簽署的建置）。CPU 元件已沒有來自其他系統路徑的原生檔。

與排除 FFmpeg 後、調整微軟執行期前（[紀錄](../ffmpeg-exclusion-ci-2026-11-13/README.md)）比較：

| 項目 | 之前 | 現在 | 差異 |
| --- | ---: | ---: | ---: |
| Analysis 原生檔 | 105 | 61 | −44 |
| bundle 普通檔案數 | 741 | 697 | −44 |
| 來源未對照 | 303 | 259 | −44 |
| 需審閱 | 337 | 293 | −44 |
| 元件 ZIP 位元組 | 93,325,022 | 92,305,935 | −1,019,087 |

既有自動驗收全部接受：功能 11、同版維護 8、跨版 8、程序終止與恢復 6。`excluded_binaries_absent` 為 true。

## 限制

- 基本包同一提交的流程也通過，但其摘要本次沒有逐項讀取；它使用相同的簽章查詢程式，預期也已取得，尚未親自確認。基本包自建的 `tesseract.exe` 沒有簽章是預期情況。
- 簽章有效只說明檔案由該簽署者發行且未被改動；各元件的授權義務仍要另外處理。
- 不是乾淨機或人工驗收；沒有 GPU。7/12、C04 2/4、C11 2/5 不變。沒有發布產物。

[返回歷史索引](../../../history-index.md)

# 微軟執行期改用官方來源後的 Windows CI

2026-11-13（台北）。[PR 4](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/4) head `c3cd3eb838da0147a64ba146c5a74b38752239ba`（程式 0.19.1／架構 0.4）。PR 流程以暫時合併提交 `c6f8d66b4d162c2ff08cdb9fc6b70f495d618434` 執行；這不是新的候選證據。資料全部取自 job 的公開摘要，沒有下載 artifact。

| 流程 | run | 結果 |
| --- | --- | --- |
| Windows base validation | [43382813061](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43382813061) | Success |
| Windows CPU component validation | [43382813101](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43382813101) | Success |
| Linux full regression | [43382812990](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43382812990) | Success |

## 先前的來源（同一 PR 的前一次執行，run 43379996721）

公開摘要首次列出非 wheel 原生檔的來源目錄：基本包有 46 個 `system-native` 檔案來自 `C:\hostedtoolcache\windows\Java_Temurin-Hotspot_jdk\8.0.504-1\x64\bin`，版本資源公司欄為 Microsoft Corporation。也就是 `api-ms-win-*`、`ucrtbase.dll`、`msvcp140.dll` 是 PyInstaller 沿 PATH 從 runner 上的 Java JDK 目錄收進來的複本，不是 Windows 系統目錄，也不是 Microsoft 指定的散布來源。

## 調整後的基本包（本次執行）

Universal CRT 不再隨包；來源不在 CPython 或 wheel 的 VC runtime 改取自 Visual Studio 可再散布目錄。hosted Windows 2022 上既有自動驗收全部接受：應用 10 項、安裝 6 段、0.16.0→0.19.1 跨版 11 段、三個中斷點續修。

| 項目 | 調整前（run 43379996721） | 調整後 | 差異 |
| --- | ---: | ---: | ---: |
| Analysis 原生檔 | 198 | 153 | −45 |
| 普通檔案數 | 1,653 | 1,608 | −45 |
| 來源未對照 | 152 | 107 | −45 |
| 需審閱 | 190 | 145 | −45 |
| 總位元組 | 265,801,837 | 263,316,428 | −2,485,409 |

調整後的非 wheel 原生檔來源：

| 來源目錄 | 公司（版本資源） | 檔案數 |
| --- | --- | ---: |
| CPython 3.12.10 安裝目錄 | Microsoft Corporation | 2 |
| CPython 3.12.10 安裝目錄 | Python Software Foundation | 2 |
| CPython `DLLs` | Python Software Foundation | 19 |
| CPython `DLLs` | The OpenSSL Project | 2 |
| CPython `DLLs` | SQLite3 | 1 |
| CPython `DLLs` | （無版本資源） | 1 |
| `…\Microsoft Visual Studio\2022\Enterprise\VC\Redist\MSVC\14.44.35112\x64\Microsoft.VC143.CRT` | Microsoft Corporation | 1 |
| 本次 CI 建置的 `base-assets\native\bin`（`tesseract.exe`） | （無版本資源） | 1 |

Java JDK 目錄已不再出現。`excluded_binaries_absent` 為 true。

## 限制

- **數位簽章這次沒有取得。** 29 個檔案的查詢失敗，摘要記錄的錯誤是找不到 `Get-AuthenticodeSignature`。原因是 CI 外層為 PowerShell 7，子程序的 Windows PowerShell 5.1 繼承了它的模組路徑；修正已提交（移除繼承的 `PSModulePath`），結果要看下一次執行。在那之前，發行者只有版本資源的公司欄作為依據，簽章屬未證實。
- CPU 元件同樣套用了這兩項調整且 CI 通過，但其摘要本次沒有逐項讀取。
- 不隨包 Universal CRT 表示不支援 Windows 8.1 以前的系統；hosted runner 本身有系統內建的 UCRT，乾淨的 Windows 10／11 尚未驗證。
- 不是乾淨機或人工驗收；沒有 GPU。7/12、C04 2/4、C11 2/5 不變。沒有發布產物。

[返回歷史索引](../../../history-index.md)

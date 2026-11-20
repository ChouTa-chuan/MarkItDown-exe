# 大階段 C 驗收表

把這份表複製成兩份，使用 B3 CPU 重新定版後的新安裝包，在乾淨的 Windows 10 x64 和 Windows 11 x64 各填一份。目錄分別用 `stage-c-YYYY-MM-DD-win10` 和 `stage-c-YYYY-MM-DD-win11`。先做 C1 及 C2-1 至 C2-5，再做 C3 與 CPU 安裝、辨識，最後移除 CPU 元件、修復及移除基本包。將 B3 的受信任 CPU 元件包與目錄、合成樣本預先放在安裝目錄以外。第一次啟動前先斷網。安裝包從受信任的專案來源取得後，在 PowerShell 執行 `certutil -hashfile ".\安裝程式.exe" SHA256` 核對發布資訊，將實測 SHA 填在下方。每台 Windows 都要獨立記錄。

| 驗收資訊 | 實際值 |
| --- | --- |
| B3 後版本與來源提交 | 待填 |
| 安裝包檔名及來源連結 | 待填 |
| **安裝包 SHA-256** | **待填** |
| Windows 版本、組建及架構 | 待填（執行 `winver`） |
| 測試環境及乾淨快照識別碼 | 待填 |
| 驗收人、日期、時區 | 待填 |
| RAM 容量 | 待填 |

每列先做「操作」，達到「預期結果」且附件保存後，再把該列的 `[ ]` 改為 `[x]`。失敗、阻擋或尚未執行的列保持未勾，旁邊記錄實際結果、重現步驟與附件。遇到缺失後使用新安裝包重驗時，另填一份對應新 SHA 的紀錄。Windows CI 的紀錄可供參考，C 節需保存乾淨機與人工操作證據。

## 判定標準

- C1-2 若 SmartScreen 顯示「Windows 已保護您的電腦」或「未知發行者」，對已核對來源及 SHA 的未簽章測試版屬預期。截圖後選「更多資訊 → 仍要執行」。若組織原則禁止執行，記為阻擋並保存畫面。SHA 不一致或出現其他安全錯誤時停止安裝。
- C2-1 的基本包繁中結果只看內建 Tesseract。以指定合成參考句、關鍵字及段落順序判定。
- 已知的 ONNX 繁中差異只在受管 CPU 選配元件驗收列處理。若 B3 驗收資料仍列有此限制，將符合已知範圍的字詞差異記為「已知限制」，附實際結果與參考文字。這種差異不算失敗。引擎未啟動、沒有辨識輸出、英文不符合預期或超出所列範圍仍須記為失敗。若 B3 已修正，以 B3 的驗收門檻判定。
- GPU 不在本次驗收範圍，結果可記「不適用」。

## 準備乾淨機與樣本

- **確認未安裝 Python 或 OCR 引擎**：在「設定 → 應用程式」檢查已安裝清單，搜尋 Python、Tesseract 及曾裝過的 OCR 引擎。用 PowerShell 執行 `Get-Command python,python3,py,tesseract,ocrmypdf -All -ErrorAction SilentlyContinue` 或 `where.exe python`、`where.exe tesseract`，保存輸出。若只列出 `WindowsApps` 市集別名，記下這個結果並以安裝清單確認。另檢查常用安裝位置（例如 `%LOCALAPPDATA%\Programs\Python`、`%ProgramFiles%\Tesseract-OCR`）與 `$env:TESSDATA_PREFIX`，避免漏掉未加到 PATH 的引擎及模型。
- **斷網並取證**：在第一次開啟前拔除網路線、關閉 Wi-Fi 並中斷 VPN。VM 可在管理介面將虛擬網卡斷線。從 Windows 網路圖示確認未連線，並用 `Get-NetAdapter | Select-Object Name,Status` 和 `Get-NetConnectionProfile` 記錄所有外部網路連線狀態。確認沒有可用外部連線，再截取網路狀態與首次啟動畫面。需要下載 CPU 元件時，等 C1-3 完成才重新連線。
- **掃描 PDF 樣本**：可在驗收前下載 [C03 合成四語掃描 PDF](development-records/runs/c03-languages-2026-11-08/native/four-language-mixed.pdf)。按頁序以 Microsoft Print to PDF 各存一頁，順序為繁中、英文、日文、韓文。確認分頁後仍只有影像文字，並記錄原始 PDF 與測試檔 SHA。四語參考句採樣本 JSON 的 `expected` 或 `reference` 欄位。[繁中](../src/desktop_app/data/setup-chinese.json) · [英文](../src/desktop_app/data/worker-health.json) · [日文](../src/desktop_app/data/setup-japanese.json) · [韓文](../src/desktop_app/data/setup-korean.json)
- **基本轉換樣本**：另製作一份含可選取文字的簡單文件供基本轉換與批次操作。

## C1 · 乾淨機安裝與離線首次啟動

| 勾選 | 操作 | 預期結果 | 證據格式 |
| --- | --- | --- | --- |
| [ ] C1-1 | 以乾淨 Windows 快照登入一般使用者，確認無先前 MarkItDown、Python、開發工具、另裝 OCR 引擎或四語模型。 | 已記錄 OS 組建與驗收前狀態。 | `c1-environment.txt` 或等效截圖，包含系統版本及安裝清單。 |
| [ ] C1-2 | 從已核對 SHA 的 Setup 安裝，確認安裝路徑與捷徑。 | 安裝完成，Windows 可找到應用程式及移除項目，捷徑指向實際安裝。 | `c1-setup-sha256.txt`、SmartScreen（如出現）、安裝完成及捷徑／已安裝應用程式截圖。 |
| [ ] C1-3 | 安裝完成後先斷網，再第一次開啟應用程式，完成首次設定並用一份合成文字檔試轉。 | 首次畫面及本機健康檢查可開啟，顯示 OCR 狀態與 RAM 建議，基本轉換離線完成，未要求先下載模型、選配或更新。 | `c1-offline.png`、首次設定截圖、輸入與輸出 Markdown。 |

## C2 · OCR、路徑、修復與移除

使用每種語言一份只有影像文字的 PDF，並保存可對照的正確文字。選用隨基本包提供的 Tesseract，逐份選對應語言，比對指定辨識句、閱讀順序和輸出位置。

| 勾選 | 操作 | 預期結果 | 證據格式 |
| --- | --- | --- | --- |
| [ ] C2-1 | 繁中 `chi_tra` 掃描 PDF。 | Markdown 讀出指定繁中字句，關鍵字及段落順序吻合。 | PDF、參考 TXT、輸出 MD、OCR 語言截圖。 |
| [ ] C2-2 | 英文 `eng` 掃描 PDF。 | Markdown 讀出指定英文句，關鍵字及段落順序吻合。 | PDF、參考 TXT、輸出 MD、OCR 語言截圖。 |
| [ ] C2-3 | 日文 `jpn` 掃描 PDF。 | Markdown 讀出指定日文句，關鍵字及段落順序吻合。 | PDF、參考 TXT、輸出 MD、OCR 語言截圖。 |
| [ ] C2-4 | 韓文 `kor` 掃描 PDF。 | Markdown 讀出指定韓文句，關鍵字及段落順序吻合。 | PDF、參考 TXT、輸出 MD、OCR 語言截圖。 |
| [ ] C2-5 | 以含繁中與空白的輸入檔名、資料夾與輸出路徑轉檔。 | 能讀取並產生可開啟的 UTF-8 Markdown，路徑及檔名完整。 | 遮蔽個資的來源與輸出路徑、目錄截圖、輸出 MD。 |
| [ ] C2-6 | 完成 C3 並記錄合成輸出與設定，使用同一 SHA 的 Setup 執行修復，再啟動及試轉。 | 應用程式可重新啟動並轉換，既有設定、模型、使用者文件與輸出保留。 | 修復畫面、修復前後 SHA-256 CSV 與修復後輸出 MD。 |
| [ ] C2-7 | 從 Windows 已安裝的應用程式移除，再檢查捷徑及合成使用者資料。 | 程式入口及移除項目消失，使用者文件、輸出及設定資料保留。 | 移除畫面、前後目錄／捷徑截圖與移除前後 SHA-256 CSV。 |

### C2-6 與 C2-7 的檔案 SHA-256

- 兩次操作都分別記下操作前與操作後的 **設定檔、同一份合成輸入 PDF、既有 Markdown 輸出**，以及在準備階段已有且應保留的使用者自備模型。設定檔預設為 `%LOCALAPPDATA%\MarkItDownDesktop\MarkItDownDesktop\settings.json`。本機模型通常在同一資料目錄的 `models\` 下；實際有設定外部路徑時，使用該路徑。請選定持久檔案，不將快取、日誌或應用程式管理的暫存列入比對。
- 每次操作前先關閉程式，產生「前」清單。操作後尚未重開程式或再轉檔時，先產生「後」清單。檔案仍須存在且 SHA-256 完全一致。修復再啟動的轉檔寫到新的檔名，保留原輸出。移除後另以 `Test-Path -LiteralPath` 確認原安裝位置的程式入口已移除。
- 下例每次做前後快照時執行一次。改用實際檔名，將 `$stamp` 依次設為 `repair-before`、`repair-after`、`uninstall-before`、`uninstall-after`。在 C2-6 前也對用於修復的同一份 Setup 執行 `Get-FileHash -Algorithm SHA256`，與本表首列記錄的安裝包 SHA 核對。

```powershell
$stageEvidence = 'C:\StageC'
$stamp = 'repair-before'
$settingsPath = Join-Path $env:LOCALAPPDATA 'MarkItDownDesktop\MarkItDownDesktop\settings.json'
$filesToCheck = @(
    $settingsPath
    (Join-Path $stageEvidence 'samples\繁中 掃描.pdf')
    (Join-Path $stageEvidence 'outputs\繁中 輸出.md')
    # 如有需要保留的自備模型，在此加上實際檔案路徑。
)
Get-FileHash -LiteralPath $filesToCheck -Algorithm SHA256 -ErrorAction Stop |
    Export-Csv -LiteralPath (Join-Path $stageEvidence "$stamp.sha256.csv") -NoTypeInformation -Encoding UTF8
```

驗收時以 `Compare-Object (Import-Csv .\repair-before.sha256.csv) (Import-Csv .\repair-after.sha256.csv) -Property Path,Hash` 比對。移除時改用兩份 `uninstall-*.sha256.csv`。無差異才勾選資料保留。若記錄有帳戶名稱，公開前將各快照中的路徑以相同規則遮蔽，再計算附件本身的 SHA-256。

## C3 · 人工操作

先執行這節及 CPU 選配元件驗收，再做 C2-6 和 C2-7。

| 勾選 | 操作 | 預期結果 | 證據格式 |
| --- | --- | --- | --- |
| [ ] C3-1 | 把兩份支援的合成文件拖入視窗。 | 檔案進入清單，名稱可辨識，可開始轉換。 | 清單截圖或短錄影。 |
| [ ] C3-2 | 選擇輸出資料夾，對兩份文件執行批次轉換。 | 可看到各檔狀態，每份成功的檔案各有可開啟的 MD。 | 批次結果截圖、輸入輸出清單與對應 MD。 |
| [ ] C3-3 | 查看完成結果並比對預覽與輸出的同一段文字、標題或表格。 | 預覽可閱讀，顯示的內容對應已完成的檔案。 | 預覽截圖及該檔 MD。 |
| [ ] C3-4 | 查看自動 RAM 預算，改為設備可承受的手動 MiB 及系統保留量。例：8 GiB RAM 的乾淨機可先試手動預算 3072 MiB、系統保留 2048 MiB。儲存、重開並轉換。 | 自動與手動可切換，重開保留設定。若資源不足，介面顯示等待或明確錯誤。RAM 設定為軟性預算。 | 儲存前後與重開後截圖、設定值、轉換狀態。 |
| [ ] C3-5 | 閱讀該安裝包的限制與已知缺口，確認適用的 OCR、RAM 與 GPU 說明。 | 複核者記錄 B3 後版本實際揭露的限制、可接受範圍及需追蹤的問題。 | `c3-limitations.md`，附限制檔的 SHA、確認人與日期。 |

## C3 · CPU 選配元件

以 B3 核准的 CPU 元件版本驗收，並使用同一套合成參考句。先完成 C1 的離線首啟再取用核准檔案。從受信任的簽章目錄或離線包安裝。每次辨識明確選「受管 CPU OCR」，保留輸出使用的後端、路由與元件版本。完成此節後再進行基本包修復與移除。

| 勾選 | 操作 | 預期結果 | 證據格式 |
| --- | --- | --- | --- |
| [ ] C3-6 | 在「選配元件管理」取用 B3 核准的 CPU 版本，下載並安裝或匯入包檔。重新開啟管理視窗檢查版號、啟用與健康狀態。 | 安裝與完整性、健康檢查通過。畫面顯示正確元件、啟用版號與最近健康結果。 | 核准目錄／包雜湊、安裝結果與元件狀態截圖。 |
| [ ] C3-7 | 使用受管 CPU OCR 辨識繁中影像 PDF。 | 走 CPU OCR 路由並產出對應頁面的 Markdown；依 B3 參考句與已知限制規則判定。 | 帶頁碼、路由與元件版本的 MD、參考 TXT、差異紀錄及後端截圖。 |
| [ ] C3-8 | 使用同一 CPU 版本辨識英文影像 PDF。 | 英文參考句的關鍵字和閱讀順序符合預期，輸出使用該 CPU 版本。 | PDF、參考 TXT、MD、後端及版本畫面。 |
| [ ] C3-9 | 在 OCR 後端選回「Tesseract（基本／自備引擎）」，使用內建引擎並儲存，再保存設定、合成輸入、既有輸出及應保留的自備模型 SHA。從管理視窗移除受管 CPU，核對同一組 SHA，再另存一份基本包轉換結果。 | CPU 元件版號不再啟用，基本包用 Tesseract 仍能完成掃描轉換，原有檔案及設定 SHA 不變。 | 移除前後元件狀態、SHA 清單與 Tesseract 重測輸出。 |

## 填寫後保存

將兩份完成表各存為 `README.md`，放在 `docs/development-records/runs/stage-c-YYYY-MM-DD-win10/` 與 `docs/development-records/runs/stage-c-YYYY-MM-DD-win11/`。每份另有 `manifest.json`，各列結果可填 `pass`、`fail`、`blocked`、`not-run` 或 `not-applicable`，已知限制另註明在 `note`。所有相對路徑以該目錄為起點；大型附件在 README 說明可追溯的位置及 SHA。公開前先遮蔽個資，再核對附件雜湊。由負責驗收的人確認每列結果後，再依專案流程處理 `base-clean-machine-manual`。

最小 `manifest.json` 範例如下。日期與提交是格式示意，實際提交、Setup SHA 與附件 SHA 都從 B3 後的驗收填入。有附件時逐檔列出，以 `Get-FileHash -LiteralPath <附件> -Algorithm SHA256` 取得 `sha256`。

```json
{
  "date_taipei": "2026-11-20",
  "source_commit": "待填 B3 後來源提交",
  "installer_sha256": "待填本次安裝包 SHA-256",
  "results": {
    "C1-1": {
      "status": "pass",
      "evidence": ["c1-environment.txt"]
    },
    "C1-2": {
      "status": "not-run"
    }
  },
  "attachments": {
    "c1-environment.txt": {
      "sha256": "待填附件 SHA-256"
    }
  }
}
```

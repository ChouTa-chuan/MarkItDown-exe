# Windows 安裝包與驗收流程

已實作開發預覽安裝包來源、建置與安裝／解除安裝自動驗收流程；**目前尚未在 Windows 編譯或執行**，沒有交付已驗證的 Windows Setup.exe。剩餘六項里程碑檢核都需要 Windows 或 GPU 實機，總進度維持 19/25，沒有把準備工作列為實機通過。

## 現在可以自動完成的流程

手動觸發 `.github/workflows/windows-build.yml` 後，預設在 Windows 2022 執行器執行：

1. 解析 PowerShell 腳本，檢查雜湊清單、錯誤碼與逾時行為。
2. 以 x64 Python 3.12 建立隔離環境，按鎖定雜湊安裝依賴，核對上游原始碼及授權。
3. 跑完整測試並保存原始日誌；跳過及已知品質預期失敗不等於通過。
4. 建置原生 Windows PyInstaller 資料夾，檢查公開 PDF 樣本及內建自我檢查。
5. 產生檔案雜湊清單，以 Inno Setup 6.3+ 編譯每位使用者的預覽安裝包及 SHA-256 sidecar。
6. 在這台可拋棄執行器上靜默安裝，核對安裝後檔案、執行自我檢查、開啟／正常關閉桌面。
7. 解除安裝，確認安裝目錄移除、使用者資料哨兵仍存在，保存全部報告。

工作流程仍只接受手動觸發，不建立 GitHub Release；本輪沒有推送或觸發遠端工作流程。Windows 建置機需有 Inno Setup 6.3+，預設路徑為 Program Files (x86)/Inno Setup 6/ISCC.exe；未找到時明確失敗。編譯器版本會記錄於建置摘要，目前沒有承諾逐位元可重現的安裝包。

## 安裝包設計

- Inno Setup 來源：packaging/windows-installer.iss。x64 Windows，最低版本門檻 10.0.17763；這是建置目標，尚非實測支援矩陣。
- 預設位於使用者 LocalAppData/Programs/MarkItDownDesktop，不要求系統管理員，建立開始功能表捷徑；桌面捷徑可選。
- 更新時替換受管理的 `_internal` 原生依賴；解除安裝不刪除使用者設定、下載模型與輸出文件。這些資料應放在安裝目錄外。
- 附完整授權及手冊；ONNX 模型隨包，Tesseract 原生執行檔仍未整合，預設後端仍是 Tesseract。Windows 原生元件及最終再散布審核待完成。
- 預覽安裝介面使用英文；程式介面及操作手冊維持繁體中文。未簽章，未宣稱正式發佈可用。

## 內建離線自我檢查

打包程式新增下列入口，不需要電腦另裝 Python：

```powershell
& 'C:\path\MarkItDownDesktop.exe' --self-test --report 'C:\reports\runtime.json'
```

五項檢查為離線手冊與 58 套件／214 文件授權雜湊、三個 ONNX 模型雜湊、中文路徑與 UTF-8 原位元組、原生 PDF，以及 ONNX CPU 英文掃描 PDF。三種轉換都走實際 spawn 背景程序及 RAM 調度。只建立生成樣本，暫存離開後清理，不讀取使用者文件。

報告保留各項失敗、平台與 frozen 狀態；只有全部通過才回傳 0，失敗回傳 1。既有報告不覆寫。這不是 GPU、繁中準確率或真人桌面操作驗收。

目前 Linux 打包程式在 **PATH 不提供任何外部工具** 的條件下通過五項檢查，見 [實際結果](installation-self-test-linux.json)。這證明該 Linux 產物的獨立執行能力，不能取代 Windows 結果。

## Windows 本機執行

建置機需 Python 3.12 x64 及 Inno Setup 6.3+：

```powershell
.\packaging\build-windows.ps1 -BuildInstaller
```

產物位於 dist/MarkItDownDesktop、dist/installer；每次建置使用獨立的 dist/reports/build-* 報告目錄。也可傳入 `-IsccPath` 指定既有編譯器。不加 `-BuildInstaller` 時只產生資料夾預覽。

在沒有既有安裝的可拋棄帳戶或 VM，測試安裝與解除安裝：

```powershell
.\packaging\test-windows-installer.ps1 -SetupFile '.\dist\installer\MarkItDownDesktop-Setup-0.1.0-windows-x64.exe' -ReportDirectory 'C:\reports\lifecycle-01'
```

若已有安裝，此生命週期測試會拒絕執行，避免替換或移除既有程式。一般使用者不需要執行這項開發測試。

乾淨機安裝後，只執行驗收、不解除安裝：

```powershell
.\packaging\verify-windows-install.ps1 -ReportDirectory 'C:\reports\installed-01'
```

檔案清單檢查會拒絕缺失、修改、額外檔案、路徑逃逸、重複大小寫名稱及連結／junction；允許 Inno 自己的 uninstaller metadata。SHA-256 清單用於內容一致性，不是數位簽章或來源認證。

驗收腳本本身只需要 Windows PowerShell 5.1+，不呼叫外部 Python。可加 `-RequireNoPython` 保守拒絕任何偵測到的 python/python3/py 命令，包含 Windows Store 別名；沒有此參數時仍記錄偵測結果。命令偵測不能證明電腦所有位置皆無 Python。

## 驗收門檻與目前狀態

| 門檻 | 目前證據 | 狀態 |
| --- | --- | --- |
| 建置／驗收腳本與清單檢查 | PowerShell 7.6.9 Linux：9 組檢查，含真實子程序錯誤碼、逾時、中文／空格路徑及檔案竄改反例 | 工具通過；不是 Windows 執行 |
| 內建自我檢查 | Linux frozen 五項通過，無外部工具 PATH | Linux 通過 |
| Windows Setup 編譯及安裝／解除安裝 | 來源及自動流程已保存 | **未執行** |
| 無 Python 的乾淨 Windows | 自動驗收腳本已保存；仍須記錄實際機器條件及結果 | **未執行** |
| 人工桌面操作、繁中路徑／OCR、重開機後操作 | Windows 驗收待辦 | **未執行** |
| GPU、VRAM、CPU 回退實際壓力 | 沒有相應硬體；自我檢查僅 CPU | **未執行** |
| Windows 原生 OCR、Qt／原生二進位再散布、簽章 | 尚未完成 | **待辦** |

工具結果見 [PowerShell 記錄](windows-tooling-results.json)。PowerShell 5.1 相容語法是實作目標；目前實際解析與執行使用 Linux PowerShell 7.6.9，不宣稱已在 Windows PowerShell 5.1 跑過。

GitHub Windows 執行器已安裝 Python，其自動安裝測試不算「無 Python 乾淨 Windows」。`clean_machine_accepted` 及 `gpu_executed` 不會因一般安裝測試通過而自動改為 true。剩餘里程碑需取得相應實機證據後才能關閉。

# C04：基本版依賴拆分

2026-11-08（台北），程式 **0.8.1**、架構 **0.4**。本輪完成 C04 的「基本版 Python 閉包、雜湊鎖定與既有授權核對」子檢核；**完整 C04 未關閉，已驗收仍為 7/12**，既有 **19/25**。

## 已完成的拆分

| 平台／用途 | 固定套件數 | 來源 |
| --- | --- | --- |
| Linux 基本執行環境 | 38 | [runtime 鎖定](../packaging/profiles/base-linux-runtime.txt) |
| Windows 基本執行環境 | 38 | [runtime 鎖定](../packaging/profiles/base-windows-runtime.txt) |
| Linux 基本建置環境 | 47 | [build 鎖定](../packaging/profiles/base-linux-build.txt) |
| Windows 基本建置環境 | 49 | [build 鎖定](../packaging/profiles/base-windows-build.txt) |

[base.json](../packaging/profiles/base.json) 明列桌面／PDF／Office 功能，執行與建置工具分開計算。版號與所有允許的 SHA-256 逐一沿用原上位鎖定，不重新解析成更新版本；原 Linux 55／Windows 58 套件開發清單保持固定。新 lock 不含兩個本地專案 wheel，專案與固定 vendor 另以 `--no-deps` 安裝。

基本執行環境不含 RapidOCR、OpenCV、pyclipper、shapely、PyYAML、python-docx 或 reportlab。NumPy 是 Excel／其他核心依賴；**Magika 用於 Microsoft MarkItDown 的檔案辨識，仍需要 CPU ONNX Runtime**。這個 runtime 不是選配 OCR 可用的證明，也不代表已內含 RapidOCR 的 OCR 模型或 GPU 引擎。上游保持原樣，沒有刪掉必要閉包來縮小清單。

## 如何重現與驗證

```bash
# 在既有完整開發環境執行，離線核對已保存的輸出
python scripts/packaging_profiles.py

# 只有明確更新來源後才重新產生；不自行升級套件
python scripts/packaging_profiles.py --generate

# 更新 Linux metadata 時必須使用對應上位鎖定的 Linux 環境
python scripts/packaging_profiles.py --capture-metadata --generate
```

產生器從兩份專案 pyproject 的必要相依、指定 extras 及建置輸入追蹤完整閉包，檢查版本範圍、Requires-Python、平台 marker 及傳遞 extras。Windows 目標在 Linux 求值時使用明確的 Windows／AMD64／CPython 3.12 marker，不沿用主機條件；這是 metadata 分析，**不是 Windows 執行證據**。

Windows metadata 逐一比對既有 wheel 原文與授權雜湊；Linux metadata 快照來自既有完整鎖定環境。兩份快照、完整相依邊、marker 與每份 lock 的 SHA-256 保存在 [base-closure.json](../packaging/profiles/base-closure.json)。缺少相依、版本不符、來源變動、混入選配、生成輸出過期或授權變動時均失敗，不靜默省略套件。

每份 profile 另外列出對應版本的既有 Windows wheel 授權／METADATA：runtime 各 145 份，Linux build 對應 183 份、Windows build 187 份。這些是既有原文的引用與雜湊，原 221 份授權資產不變；**不將 Windows wheel 授權引用冒充 Linux binary 清單、原生引擎授權或最終 SBOM／再散布審核**。

## 真正乾淨環境驗收

使用新的 venv、`include-system-site-packages = false` 與新 runtime 雜湊鎖定實際安裝。除了 38 個第三方套件、兩個本地專案及 venv 自帶 pip，不接受其他套件；`pip check` 通過，確認沒有 OCR 選配與測試產生工具。生成樣本由另一個完整開發環境準備，不把產生工具裝回基本環境。

在空 PATH／空 TESSDATA_PREFIX 下，繁體文字、HTML、DOCX、XLSX、PPTX 與原生 PDF 六種格式走真正 spawn 轉換；另以 Qt 執行 DOCX／PDF／文字批次，核對檔案輸出並保存畫面。缺少原生 OCR 的掃描 PDF 明確失敗、不產生輸出，沒有偷偷改用 ONNX。此失敗是缺元件行為檢查，不能當作基本 OCR 完成。

重現入口為 [check_base_profile.py](../scripts/check_base_profile.py)：完整環境先用 `--prepare-fixtures --fixtures <新資料夾>`，乾淨 Linux 基本環境再用 `--fixtures <資料夾> --output <新輸出資料夾>`。執行前需將本地專案 wheel 安裝進基本 venv；只有本地 wheel 使用 `--no-deps`，第三方依賴必須先按新 lock 加 `--require-hashes` 安裝。

本輪 **15 項新測試**，含平台 marker、延遲 extras、循環、版本衝突、缺閉包、授權／metadata／hash 改動及選配混入反例。子檢核與格式／核心／裝置／授權回歸 **52/52**，乾淨基本環境實際驗收 **6/6**；全專案 **424 項：423 通過、1 既有繁體品質預期失敗、0 跳過**。樣本與原始結果見[本輪開發紀錄](development-records/runs/c04-locks-2026-11-08/README.md)。

## 接續工作

1. 將 profile 接進 PyInstaller、授權選取與 profile 專用自我檢查；舊 diagnostics 仍要求開發包內含 ONNX OCR，尚未替換。
2. C03 固定 Windows Tesseract、必要 DLL、雙語模型與原始授權，再整合基本包與離線自動設定。
3. 基本版與選配各自實際產生原生 bundle、清單、授權及自檢；Windows 乾淨環境驗證後才能關閉完整 C04／C09，GPU 另待 C12。

既有 `packaging/desktop.spec`、`build-windows.ps1` 與手動 Windows workflow 仍使用原開發包，不因加入 profile 鎖定就變成基本版發行管線。本輪未重建 frozen／Windows 安裝包、發布目錄／金鑰、建立 tag／Release 或觸發手動發行。ONNX 繁體品質缺口、Windows／GPU 實機與 RAM 軟性預算限制保留。

[架構指引](architecture-guide.md) · [開發進度](progress.html) · [版本差異](../CHANGELOG.md)

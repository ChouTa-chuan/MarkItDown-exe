# C04：基本版依賴拆分

> 目前0.19.1的Windows基本包與CPU獨立profile已有建置／維護／逐檔清單證據；完整C04仍2/4，來源／再散布與乾淨隔離環境待查。新接手請讀[目前交接指南](../PROJECT_HANDOFF.md)，下方依賴拆分紀錄保留其原版本範圍。

> 本頁保存 0.8.1／0.9.0 的拆分與核心包證據。0.13.0 新增[同平台內含四語基本包](bundled-base.md)：Linux frozen full 自檢已通過，舊 schema 1 的缺引擎行為仍保留。完整 C04 仍 2/4，Windows 及各 profile 最終驗收未關閉。

2026-11-08（台北），程式 **0.9.0**、架構 **0.4**。已完成 C04 的「基本依賴拆分」及「Linux 基本核心打包／自檢」兩個子檢核；**完整 C04 未關閉，已驗收仍為 7/12**，既有 **19/25**。

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

0.8.1 的依賴拆分新增 **15 項測試**，含平台 marker、延遲 extras、循環、版本衝突、缺閉包、授權／metadata／hash 改動及選配混入反例。子檢核與格式／核心／裝置／授權回歸 **52/52**，乾淨基本環境實際驗收 **6/6**；全專案 **424 項：423 通過、1 既有繁體品質預期失敗、0 跳過**。樣本與原始結果見[依賴拆分紀錄](development-records/runs/c04-locks-2026-11-08/README.md)。

## 0.9.0：Linux 基本核心獨立程式與自檢

新增 `packaging/base.spec`，保留原 `desktop.spec` 與 Windows 開發流程。必須使用已按 base build lock 安裝的獨立 x64 CPython 3.12 venv；`prepare_base_assets.py` 核對套件集合、版號與目前專案版本，再選取 38 個 runtime、兩個本地專案的實際 METADATA／可取得原授權，以及實際 Python 授權。禁止直接使用完整開發環境，未混入 RapidOCR／OpenCV／OCR 模型或測試產生工具。

新的 build profile 清單與全部資產雜湊內嵌於 `desktop_app/data/build-profile.json`。PyInstaller 收集實際 binary 的來源及系統 copyright，型別辨識保留 Magika／CPU ONNX Runtime。wheel 的授權目錄也納入擷取，避免漏掉以 Apache-2.0.txt 等命名的原文；缺少 wheel 原文的套件另保留既有、具來源／hash 的官方補充文字。來源證據與可取得原文不等於完成全部授權／Qt 再散布義務或原生 OCR 審核。

| 自檢 | 結果與解讀 |
| --- | --- |
| `--self-test --scope core --report <新檔案>` | 基本資產、固定 runtime／選配缺席、Unicode 文字 spawn、原生 PDF 四項通過；`complete: true` 僅限 core |
| `--self-test --report <新檔案>` | 四項 core 加必要內含 OCR；因 C03 未整合，第五項失敗，退出碼 1，`complete: false` |
| 兩種範圍共通 | `release_ready: false`、`native_ocr_integrated: false`、`full_c04_complete: false`，不能以 core 通過發布完整基本版 |

沒有 profile 的來源／歷史開發包保留原五項 ONNX 自檢；使用者不能用 CLI 任意改選 profile。缺少原生引擎的判斷依內含能力，不借用系統 Tesseract；損壞 profile 仍保存失敗報告。輸出檔案保護沿用，既有證據不覆寫。

在獨立基本 build venv 安裝本地專案後，依序執行以下步驟，**等待建置命令成功結束再啟動驗收**。目錄均須使用新的位置：

```bash
python scripts/prepare_base_assets.py --output /tmp/base-assets
MARKITDOWN_BASE_ASSETS=/tmp/base-assets python -m PyInstaller --noconfirm --clean --distpath /tmp/base-dist --workpath /tmp/base-work packaging/base.spec
python scripts/check_base_frozen.py --executable /tmp/base-dist/MarkItDownBaseCore/MarkItDownBaseCore --fixtures <已驗 hash 的合成來源目錄> --output /tmp/base-results
```

上例是 Linux；Windows 必須在原生 Windows 建置並用 PowerShell 設定同名環境變數，不能直接用 Linux 產物當 EXE。合成來源可沿用 0.8.1 的產生器／固定 SHA-256，由完整測試環境產生，驗收控制端與實際 frozen 程式分開。

新增 **16 項 profile／診斷測試**，子檢核含依賴／授權／核心／格式／裝置／Qt **86/86**；實際 frozen **7/7**，另有四份公開 PDF 的 **5/5**，保存原文字元、逐格表格、金額與順序。從新工作目錄、空 PATH／空 TESSDATA_PREFIX／空 PYTHONPATH 執行核心及六格式檢查，不需外部 Python 或 OCR；缺少原生／選配 OCR 都失敗且不留下輸出。全專案 **440 項：439 通過、1 既有繁體品質預期失敗、0 跳過**。

實際原文、binary 來源、完整 bundle 檔案雜湊、core／full 報告及中間紀錄見[本輪紀錄](development-records/runs/c04-build-2026-11-08/README.md)。沒有把故意缺 OCR 的完整自檢失敗計作 OCR 功能通過；測試驗證的是能正確拒絕就緒。

## 接續工作

1. 完成 C03 原生引擎後擴充基本 profile 的完整 OCR 自檢，並對選配 profile 分別產生原生清單與證據。
2. C03 固定 Windows Tesseract、必要 DLL、雙語模型與原始授權，再整合基本包與離線自動設定。
3. 基本版與選配各自實際產生原生 bundle、清單、授權及自檢；Windows 乾淨環境驗證後才能關閉完整 C04／C09，GPU 另待 C12。

既有 `packaging/desktop.spec`、`build-windows.ps1` 與手動 Windows workflow 仍使用原開發包，不因加入 profile 鎖定就變成基本版發行管線。本輪僅重建 Linux 基本核心 frozen，未建 Windows 安裝包、發布目錄／金鑰、建立 tag／Release 或觸發手動發行。ONNX 繁體品質缺口、Windows／GPU 實機與 RAM 軟性預算限制保留。

[架構指引](architecture-guide.md) · [開發進度](progress.html) · [版本差異](../CHANGELOG.md)

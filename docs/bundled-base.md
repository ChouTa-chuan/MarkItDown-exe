# 內含四語基本包與離線自檢

程式 **0.13.0**、架構 **0.4**。C03 的「基本包內含四語模型、離線自動設定與完整自檢」完成 **Linux 開發包驗收**，C03 **2/4 → 3/4**；Windows 最小候選與四語資料包只做靜態組裝，未執行 Windows PE。完整導入仍 **7/12**、既有 **19/25**；C04 **2/4**、C09 **3/4**，完整項與 Windows／GPU 未關閉。

## 模組責任

| 模組 | 責任與範圍 |
| --- | --- |
| `scripts/prepare_bundled_ocr.py` | 不連網地驗四語固定 hash／原授權，組裝 OCR payload。Windows 入口須符合 0.12.0 固定實際候選證據，原生來源契約與 21 份原文另核對；Linux 明確標為系統引擎的開發包 |
| `src/desktop_app/bundled_ocr.py` | 讀取建置內嵌契約，驗所有檔案、平台、AMD64 PE／ELF、固定模型、未知檔案及連結；只讀解析內含路徑，失敗不借用 PATH |
| `build_profile.py` schema 2 | 保留 schema 1 舊基本核心包；新 schema 明列內含 OCR 清單與全部資產 hash。`release_ready` 一律 false |
| `prepare_base_assets.py`／`packaging/base.spec` | 只收同平台 payload；原生入口由 PyInstaller BINARY analysis 收集實際相依，模型／原文為 DATA；保存實際 binary 來源／系統 copyright |
| 轉換／首次設定／模型管理 | OCR 頁自動使用內含路徑；首次四語健康、保留自動設定以支援搬移；模型視窗只讀呈現內含模型 |
| `diagnostics.py`／`check_bundled_base.py` | core 與 full 語意分開，full 真正跑四語健康與四份掃描 PDF；另一支工具驗搬移、CLI、缺檔、損毀、拒絕主機引擎替換及實際 library loader |

Windows payload 共 **28 份檔案＋manifest**，包含固定 5.5.3 最小 EXE、四語模型／原授權與原生來源文字。Linux 開發 payload 共 **8 份檔案＋manifest**，使用本機 Tesseract **5.5.0** 的複本；其相依函式庫與 copyright 由實際 Analysis 另收進 bundle。兩個引擎不同，Linux 的辨識成功不能當作 Windows 5.5.3 已執行。

## 預設與自備設定

帶內含 OCR 的基本包，在引擎／模型路徑空白時自動解析目前安裝位置，不需下載、PATH 或 `TESSDATA_PREFIX`。首次完成後不將內含絕對路徑寫入使用者設定，搬移整個程式資料夾仍可解析。設定 schema **7**、既有偏好與語言預設保持；不強迫四語共同解碼。

明確指定自備執行檔時保留原有路徑／模型行為；指定自備模型目錄但引擎自動時，使用內含引擎與該目錄，首次檢查尊重所選語言。只有兩者皆自動的內含基本設定才檢查全部四語。模型視窗預設只讀展示內含模型，下載與移除停用；另開專用受管目錄仍沿用原功能。

舊 schema 1 基本核心包仍會明確拒絕缺 OCR，不借用系統引擎。沒有 build profile 的來源／歷史開發包沿用本機尋找。內含必要檔案缺少、雜湊不符、平台不符或混入未知 DLL 時，停止該次 OCR，不寫部分輸出；基本文字轉換仍可使用。自備執行檔為明確覆寫選項，不是自動回退。

## 離線組裝與原生建置

```bash
# Windows 候選可在 Linux 做靜態組裝；不執行 PE。
python scripts/prepare_bundled_ocr.py --windows-candidate /path/minimal-candidate \
  --tessdata /path/verified-four-models --output /path/new-windows-payload

# Linux 開發驗證明確使用現有 /usr/bin/tesseract 複本，不冒充 Windows 引擎。
python scripts/prepare_bundled_ocr.py --linux-development \
  --tessdata /path/verified-four-models --output /path/new-linux-payload

# 在對應平台的隔離 base build venv，先安裝目前本地專案。
python scripts/prepare_base_assets.py --native-assets /path/same-platform-payload \
  --output /path/new-base-assets
MARKITDOWN_BASE_ASSETS=/path/new-base-assets python -m PyInstaller \
  --noconfirm --clean --distpath /path/new-dist --workpath /path/new-work packaging/base.spec
```

所有目錄使用新位置；等待準備／建置成功再驗收，不與同一環境的 pip 重裝並行。上例最後一行是 Linux shell；Windows 須原生 Windows 使用對應環境變數語法及 Windows payload。既有手動 Windows 開發／安裝 workflow 保持固定，未觸發發行，也沒有建立 tag／Release。

## 自檢的解讀

| 情況 | 退出碼與報告 |
| --- | --- |
| 新基本包 `--self-test --scope core --report <新檔>` | 四項核心通過；`complete: true`、`native_ocr_verified: false`，沒有聲稱跑過 OCR |
| 新基本包 `--self-test --report <新檔>` | 核心及內含四語健康／四份掃描 PDF 通過才退出 0；Linux 實際 `complete: true`、`native_ocr_verified: true` |
| 舊核心包 full | 缺必要內含引擎仍退出 1；既有 schema 1 行為與負例保留 |
| 任一開發包 | `release_ready: false`、`full_c04_complete: false`；`native_ocr_integrated` 表示有內含契約，與實際執行通過分開 |

新增 **27 項**，相關回歸 **185/185**。真正 Linux frozen **12/12**：空 PATH／模型環境、原六格式＋掃描、自動日韓 CLI、設定原文不變、中文資料夾搬移、缺／損模型與文字隔離、替換引擎連結拒絕、選配缺席、loader 確認 Tesseract／Leptonica 從 bundle 載入，以及 Windows payload 靜態核對。實際 source Qt／首次流程另 **3/3**；該 Qt 測試覆寫 asset root 到真正 bundle，不能當成 frozen GUI 或 Windows UI 驗收。

全專案 **527 項：526 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。[本輪樣本、MD、來源／授權清單、原始日誌與畫面](development-records/runs/c03-bundle-2026-11-08/README.md)保存。大型引擎、模型、bundle、wheel、venv 不放 Git。

下一步完成 Windows 原生基本包建置、四語 OCR／中文路徑與乾淨機／安裝生命週期，以及 C04 各 profile 與完整 C09 的 Windows 驗收。Linux 的固定樣本通過不代表任意版面／語言混排準確率；ONNX 繁體品質、Windows／GPU 與 RAM 軟性預算限制保留。

[內含資產決策](decisions/0006-bundled-native-profile.md) · [架構指引](architecture-guide.md)

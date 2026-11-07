# C10：自動分析與可用元件協作

程式 **0.8.0**、架構 **0.4**，2026-11-07（台北）。完成 Linux 代表性範圍的 C10，新導入 **7/12（C01／C02／C05／C06／C07／C08／C10）**，既有 **19/25**。C09 首次流程仍為三項子檢核完成，基本包自帶 OCR 須待 C03／C04；Windows／GPU、正式目錄與產品發行門檻保留。

## 使用方式與自動路由

預設仍是 Tesseract，舊 ONNX／雙引擎設定與品質限制沿用。桌面新增「受管 CPU OCR（選配、繁體品質未達標）」；需要此路徑時明確選擇，元件預設 ID 為 `onnx-cpu-ocr`，版本留空使用已啟用版本；指定版號時須先在元件管理啟用，程式不自行切換。

精準 PDF 按既有逐頁判斷選擇原生、空白或 OCR。原生／空白頁不要求選配元件，即使沒有正式來源、沒有啟用版本或指定版未啟用，也不因此要求 OCR。只有遇到 OCR 頁才取得能力／版本並啟動受管引擎；原生表格、來源註記、跨頁提示與閱讀順序處理不變。

缺少來源、未啟用、能力不足、版本不符、健康／完整性失敗、目錄到期或撤回時，當次文件失敗並清楚顯示原因。使用者可開啟「選配元件管理」處理，或明確選擇另一個已備妥後端再重試；不自動下載、啟用 GPU、改用 Tesseract／其他 ONNX 或降低精準模式。其他批次文件繼續，既有輸出不覆寫。

**正式來源與發行金鑰尚未發布。** 一般開發版不內建測試金鑰，選受管後端的掃描頁會明確拒絕未配置來源。真正端到端驗收以相同程式路徑注入短效可信政策，使用同一 C07 frozen 元件，私鑰不保存。這不是已上線的元件下載服務或已驗收的 Windows 安裝包。

## 模組與租約

| 模組 | 責任 |
| --- | --- |
| `component_workers/managed.py` | `ManagedContext` 與惰性 `ManagedOCRSession`；固定元件、版本與能力、持有文件租約、重驗及結果橋接 |
| `components/management.py` | 從可信應用程式建立跨程序公鑰政策快照；不從使用者設定／目錄匯入信任根 |
| `components/catalog.py` | 政策可供可信本機 spawn 重建，仍執行原契約驗證；簽章目錄仍是受限 JSON |
| `components/lifecycle.py` | 租約取得前檢查指定版本及要求能力，避免先執行錯誤版本探針 |
| `application.py`／`workers.py` | 傳遞政策／取消／permit／根 PID；回傳巢狀資源狀態與有界執行證據 |
| `resources.py`／C07 client／binding | 全應用程序樹 RAM、上層回壓、原生准入與健康暫停，不重複估算已配置模型 |
| `conversion.py`／`pdf_pipeline.py` | 原生分支沿用、只替換 OCR 呼叫；租約持有到排他提交完成，提交前重驗 |
| `desktop.py`／`cli.py`／`settings.py` | 明確後端與元件／版號偏好，延用 schema v6；保留其他偏好順序與舊設定 |

每份精準文件先建立未啟動的 session，不先碰登錄或健康。第一個 OCR 頁才驗證來源／登錄／active、指定版本、`ocr.onnx.cpu` 能力、相容性、實檔與真實健康；取得 C06 共享租約後，整份文件及後續原生頁／輸出提交都固定這個版本。每個原生 worker 另持有自己的 C07 guard。

每次 OCR 前後重讀目前簽章目錄；提交前重驗安裝內容，再次檢查目錄與有效期間。提交進度回呼也在最終檢查之前，故該時點撤回版本不會提交部分 Markdown。管理操作在整份文件使用期間須取得排他鎖，不能中途移除／更新元件；例外、取消及輸出保護拒絕時釋放租約。

輸出保留每頁 `source-page`、路由及警示，受管 OCR 頁加上 `source-component` 的 ID／版本／協定／CPU。`Outcome.components` 保存每份文件首次受管工作的狀態、PID、frozen 與三個實際 provider 等有界證據，不將 OCR 全文或圖片塞入 IPC。並非每次 DPI 重試的完整日誌或一般品質評分。

主程式仍沒有 OS sandbox 或永久抗本機磁碟回滾信任庫；每份工作的公鑰政策是可信應用程式建立的固定快照，工作期間重驗簽章目錄，不宣稱新增跨程序即時信任根撤銷廣播。C05 的原有信任政策／版本界限繼續適用。

## 資源與品質

原生 PDF 分析先用 256 MiB 的既有估計准入，受管模型的 768 MiB 估計只在真正需要 OCR 時由 C07 准入。外層開始後量測完整實際程序樹，不再額外加算已載入的整份模型估計；子程序也量測同一根 PID，包含桌面、PDF 與外部 runtime。

上層 permit 暫停會傳到 C07 的准入／執行迴圈；健康與頁面等待 RAM 的狀態以專門事件回到父程序，顯示等待資源，重複狀態會去重。取消沿用同一事件，不在等待暫停時失去取消能力。RAM 仍是軟性預算，原生運算不保證立即暫停，非硬性限額。

C07 協定、固定模型與三個 CPU session 不變，未重建或修改元件 ZIP。原生頁與 OCR 的兩次解析度上限、文字選取與警示判準沿用；ONNX 繁體已知缺口及嚴格 expectedFailure 保留，不因完成路由就宣告準確率提高。受管 CPU 不支援 GPU，明確 GPU 請求會拒絕。

輸出新增懸空連結保護：最後檔名不再 resolve 到其他位置，既有連結也視為既有輸出；提交仍以硬連結排他發布。這項不改寫原檔，也不保證抵禦擁有同一帳號權限的所有檔案系統競爭。

## 驗證

- 新增 **20 項**契約／路由／租約／版本／提交／資源／桌面測試，真實 spawn／檔案／SQLite／PDF；合成元件與 fake OCR 僅驗接線，不當作原生推論。
- C10 **242/242**：20 項新檢查、原 C05–C08 的 152 項、原版面矩陣 63 項及裝置回歸 7 項，0 跳過。全專案 **409 項：408 通過、1 既有繁體品質預期失敗、0 跳過**。
- 真正 frozen CPU／Qt **10/10**：簽章離線安裝、四頁混合路由、實際 provider／frozen、文字／逐格表格與警示、RAM 暫停／恢復及使用中拒絕移除、原生取消、提交前撤回拒絕、GUI 版號失敗不阻擋原生／文字、GUI 真實成功、租約釋放與控制端未 import ONNX／RapidOCR。
- 空 PATH／空 TESSDATA_PREFIX 下，使用原 C07 ZIP，SHA-256 `11c8e0e9ff648954c3e99a30630e47fd5f1fe6307fa813c5e062d374f3db6d18`。控制應用程式 0.8.0 與獨立元件 1.0.0 經原協定協作，沒有混裝 runtime。工程樣本與新畫面見[本輪紀錄](development-records/runs/c10-2026-11-07/README.md)。

```bash
python -m pip install --no-deps --no-build-isolation .
TESSDATA_PREFIX=<verified models> QT_QPA_PLATFORM=offscreen python scripts/check_component_acceptance.py --check C10 --report /tmp/c10.json
QT_QPA_PLATFORM=offscreen python scripts/check_managed_conversion_acceptance.py --package-directory /tmp/c07-package --output /tmp/c10-native
```

CLI 提供 `--ocr-backend managed_cpu`、`--component-id`、`--component-version`；一般開發入口的正式信任來源仍未配置，不能藉 CLI 指定任意金鑰繞過。預設 Tesseract、快速模式與非 PDF 的原流程保持可用。後續為 C03／C04 基本包及完整 C09、Windows／GPU 實機與正式發行準備。

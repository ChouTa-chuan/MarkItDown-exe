# C07：獨立 CPU 選配工作程序

程式 **0.5.0**、架構 **0.4**。完成一個真正的 Linux x86_64 frozen CPU OCR 元件及版本化協定，新增導入 **5/12**，既有基線 **19/25**。原始證據見[本輪開發紀錄](development-records/runs/c07-2026-11-07/README.md)。桌面完整管理、自動文件分析的元件選擇及 Windows／GPU 驗收分別保留給 C08／C10／C03–C04／C11–C12。

## 模組責任

| 模組 | 責任 |
| --- | --- |
| `component_workers/protocol.py` | v1 JSON-lines 契約、固定欄位、版本、任務 ID、尺寸及結果驗證 |
| `component_workers/client.py` | 程序啟動、RAM 准入、控制訊息、逾時／取消、程序樹清理及輸出提交 |
| `component_workers/server.py` | 單工作 CPU worker、自己持有 guard、固定模型雜湊、三個 CPU session 與真實 OCR |
| `component_workers/binding.py` | 可信固定入口、相容性、受管目錄／guard 核對、健康與使用租約橋接 |
| `packaging/ocr-worker.spec` | 每個平台獨立打包 Python、RapidOCR、ONNX Runtime、模型、原生依賴及授權 |
| `scripts/prepare_worker_assets.py` | 實際建置環境的 metadata／原始授權、CPython 授權與原生套件 copyright 證據 |
| `scripts/package_cpu_worker.py` | 在 C01 界限內生成 ZIP32、逐檔 SHA-256 與元件描述；不簽署正式目錄 |
| `scripts/check_cpu_worker_acceptance.py` | 無 OCR 套件的控制端，實際驗證離線匯入、安裝、健康、推論、取消及移除 |

沿用既有 `OnnxOCR`、固定三模型、C05 簽章／下載及 C06 安裝服務。沒有新增 runtime 依賴；測試控制端 lock 是原 Linux 鎖定版本／雜湊的子集，另含建置用 setuptools，不是已驗收的 C04 GUI 基本 profile。主要開發依賴仍保留 ONNX；本輪證明選配可以獨立運作，未宣稱整個基本包已拆分完成。

## 控制與資料流程

控制端用固定參數陣列啟動 `MarkItDownOCRWorker`（Windows 目標名加 `.exe`），不執行下載描述提供的任意命令。元件必須經 C05 驗證目錄、C06 驗檔／健康及租約；`CPUWorkerBinding` 只接受固定元件 `onnx-cpu-ocr/1.0.0`。元件目錄需屬同一登錄根；guard 固定為其 `.locks/worker-use.lock`。

1. 控制端先做 RAM 准入，建立私有工作目錄，以有界區塊複製 PNG 並記錄輸入雜湊。
2. worker 先取得自己的共享 guard，再回覆 `hello`：協定 `1.0.0`、元件與版本、PID、CPU 及是否 frozen。控制端核對 PID／版本／實際打包狀態；載入引擎前再做 RAM 准入。
3. 控制端發送一個 `run`，含任務 ID、`ocr`／`health`、固定相對檔名、輸入大小與 SHA-256、CPU 執行緒／像素／輸出界限。
4. 正常回覆順序為 `progress(loading)` → `ready` → `progress(inference)` → `progress(export)` → `completed`；三個實際 session 都必須使用 `CPUExecutionProvider`。
5. OCR 文字存於 `result.json`，完成訊息僅含大小／SHA-256。控制端須同時核對正常退出、無多餘訊息、結果檔與 schema、任務／輸入雜湊及 runtime 狀態，才排他提交 Markdown。

每程序只執行一個工作。錯版本、錯任務、亂序、截斷、重複 JSON 欄位、超限、提前退出、結果雜湊不符或完成後不退出都使該工作失敗，後續批次仍可執行。既有輸出不覆寫；取消／失敗不留下正式結果。輸出保留 ONNX 品質警示，不自動修字。

## 界限與資源

| 項目 | v1 界限／行為 |
| --- | --- |
| 控制訊息 | 每行 16 KiB，最多 64 個事件，接收佇列 32、控制佇列 8；JSON 不接受 NaN |
| stderr | 只排空，超過 256 KiB 停止；不保存可能含文件內容的原生診斷 |
| 輸入／結果 | PNG 最多 64 MiB／1,600 萬像素；JSON 結果最多 8 MiB |
| 時間 | 預設握手 10 秒、整工作 120 秒、資源等待 30 秒、取消寬限 1 秒；可配置上限 600 秒 |
| RAM | 元件預估 768 MiB，啟動另加 64 MiB；載入前重驗，執行中量測控制端完整程序樹，遲滯恢復 |
| 暫停／取消 | checkpoint 邊界生效；原生呼叫可能延遲響應，取消超時終止程序樹 |
| 執行環境 | worker 專屬 loader 路徑、CPU thread 上限、低優先權；移除 PYTHONPATH／PYTHONHOME／LD_PRELOAD，快取與暫存使用工作目錄 |

RAM 是**軟性預算**，不是預先配置、硬性限額或保證其他作業不受影響。worker 是受信任的本機原生程式，程序隔離不構成 OS sandbox。沿用 proxy／CA，未變更全域 HOME、主環境套件或系統驅動。

## 與交易維護的協作

父程序在 `manager.lease()` 範圍內使用元件；worker 自己另持有共享 guard。父程序退出後，維護程序仍不能在存活 worker 讀取時改動元件。控制 stdin EOF 會使 worker 有界退出（72），釋放核心鎖。

C06 維護在恢復、搬移、切換 active／提交、刪除時取得排他 guard；做真實健康檢查時釋放 guard，仍持有父程序維護鎖，讓健康 worker 可以取得自己的共享 guard。新增目錄逐層 fsync 再搬移；真實核心鎖與程序退出已測，沒有宣稱做過物理斷電或 Windows 測試。

## 本輪證據與限制

- C07 23 項（含真正 native CPU 子程序、父通道 EOF／guard、協定與資源反例），加 C06／C05 92 項回歸共 **115/115**；注入故障程序明確標示為 fixture，不作 OCR 證據。
- 全專案 **344 項：343 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。
- 另以實際打包元件及只安裝五項鎖定依賴的控制端驗證 **10/10**：簽章離線匯入、staging／正式位置實際健康、租約下 OCR、無效影像隔離、後續成功、原生取消、RAM 不足不啟動、閒置移除及控制環境不變。控制端沒有 ONNX、RapidOCR、NumPy、Pillow、Qt；PATH 留空仍成功，worker 回報 frozen 與三個實際 CPU provider。
- 健康影像為專案合成英文 `WORKER HEALTH CHECK 12345`；它驗證可運作，**不代表繁體品質已達標**，也沒有完整 PDF／表格品質提升結論。原繁體 expectedFailure 保留。
- 實際 Linux 開發 ZIP 為 814 檔、202,741,436 bytes，解壓 536,330,062 bytes；含 symlink 的來源打包時實體化並核對 bundle 邊界。描述 canonical JSON 為 152,846 bytes，未超過 256 KiB。OpenCV 帶入額外原生依賴，後續再評估縮減。
- 原 58 套件／214 份鎖定授權原文不改；新增實際環境 metadata、原授權、CPython 與原生 copyright 證據隨包保存。最終原生再散布審查、專案原始碼授權及 Windows 授權閉包仍待處理，這不是正式可散布產品。

本機生成的原生 ZIP 不加入 Git，保留其 SHA-256、描述、實際二進位來源／授權 manifest 及重建方法。`example.invalid` 是刻意不可下載的開發來源；驗收只用記憶體臨時測試金鑰，沒有正式發行目錄、私鑰、tag 或 Release。

## 重建與重跑

在原有完整 Linux 鎖定開發環境內安裝本專案後，使用全新輸出目錄：

```bash
python scripts/prepare_worker_assets.py --output /tmp/c07-assets
MARKITDOWN_WORKER_ASSETS=/tmp/c07-assets python -m PyInstaller --noconfirm --clean --distpath /tmp/c07-dist --workpath /tmp/c07-build packaging/ocr-worker.spec
python scripts/package_cpu_worker.py --bundle /tmp/c07-dist/MarkItDownOCRWorker --output /tmp/c07-package
python -m venv /tmp/c07-controller
/tmp/c07-controller/bin/python -m pip install --require-hashes -r packaging/requirements-controller-test-linux.txt
/tmp/c07-controller/bin/python -m pip install --no-deps --no-build-isolation .
/tmp/c07-controller/bin/python scripts/check_cpu_worker_acceptance.py --package-directory /tmp/c07-package --report /tmp/c07-report/frozen-acceptance.json
python scripts/check_component_acceptance.py --check C07 --report /tmp/c07-tests.json
```

同平台／版本可重建並重新驗證功能；二進位與暫存來源路徑未承諾位元組可重現。Windows 必須在 Windows 實際建置與驗證。本輪沒有重建主程式 frozen、啟動手動 Windows workflow 或更動目前 PDF 自動路由；下一段接續 C08 元件管理介面。

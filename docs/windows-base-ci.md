# Windows 基本包自動建置與驗證 CI

程式 **0.14.0**、架構 **0.4**。本輪新增獨立 Windows 基本包驗證流程；這份準備紀錄不代表 Windows 已通過。C03 **3/4**、C04 **2/4**、C09 **3/4**、完整導入 **7/12**、既有 **19/25** 保留，實際遠端結果另追加保存。

## 工作流程與責任

新增 `.github/workflows/windows-base-validation.yml`，main 的原始碼／建置相關更新才自動觸發，文件單獨更新不重跑。它不建立 Setup、tag 或 Release，不觸發既有手動 Windows 安裝包發行流程；權限僅 `contents: read`。

1. Ubuntu 24.04 的 native-inputs job：雜湊鎖定基本建置套件及兩個主機工具，下載四份固定 source archive、官方工具鏈與四語模型，真正重建最小 Windows PE，保存來源 receipt。
2. 同一次 CI 透過一天到期的輸入 artifact 傳遞候選、原文、四語模型及 receipt；不把 binary 加進 Git。這是建置管線輸入，不是正式安裝包。
3. Windows 2022 job：原生 Windows Python 3.12 建立獨立 base build venv，按原 Windows build lock 安裝，核對來源／profile，組裝同平台內含四語，再以 Windows PyInstaller 真正建置資料夾 EXE。
4. Windows 控制端實際跑 core／full 四語健康與掃描、中文空格搬移、四語 CLI／UTF-8 檔名及設定保留、損毀模型／EXE 拒絕回退、缺選配與 Qt 原生視窗開啟／正常關閉。預備一套真正可用的外部引擎／模型，讓故障測試能查出誤用回退。
5. 只上傳驗收報告／自身視窗截圖，並將實際 JSON 與日誌末段寫入 job summary，失敗也保存。尚未產生的報告不補造通過。

GitHub Windows runner 已預裝 Python 與多種開發工具，不能算無 Python 乾淨機。`clean_machine_accepted`、`release_ready`、完整 C03／C04／C09 及 GPU 保持 false；CI GUI 自動開關也不當成人工操作驗收。

## 模組

| 模組 | 用途 |
| --- | --- |
| `fetch_windows_ci_inputs.py` | 固定公開來源串流 hash／bytes，有界檔案，暫時網路錯誤最多三次重試；完整性失敗不重試，保留 Retry-After |
| `prepare_bundled_ocr.py --build-evidence` | 接受同一可信建置管線的固定來源 receipt，檢查四份 source、工具鏈、原文與候選 hash；receipt 是稽核資料，並非來源簽章、授權核准或使用者設定信任根 |
| `run_windows_base_ci.py` | stdlib 控制端，等每步完成才進行後續，逐項保存依賴、原始碼、資產、PyInstaller 與驗收日誌 |
| `check_windows_base.py` | 真正 Windows 才執行；Linux 會在建立任何 child 前拒絕，不能靠模擬平台列為 Windows 通過 |
| `publish_windows_ci_summary.py` | 彙整已存在報告及已限制大小的日誌末段；方便透過公開 job summary 查核實際結果 |

先前固定候選的預設 hash 路徑保留。CI 原生重建可因工作目錄產生不同 binary hash，必須以同次建置 receipt 對應，不能改資料旗標宣稱已在 Windows 執行或可發行。四語模型、來源鎖定、原文、執行時 profile hash 門檻仍各自核對。

## 本地準備驗證

新增 **17 項**下載、來源 receipt、故障與平台 guard 測試，含原 native／payload／profile／授權回歸 **130/130**；全專案 **544 項：543 通過、1 既有 ONNX 繁體品質預期失敗**。固定 HTTPS 輸入 **10 份**實際下載成功，另從相同來源重建 PE 並以新 receipt 組裝四語 payload；這些皆為 Linux／靜態證據。

初始 guard 測試發現平台描述會呼叫 uname，改為先做真正 Windows 門檻才蒐集詳細平台；工具鏈下載曾遇暫時 504，有限重試後成功。原始失敗與最終結果分開保存在[本輪紀錄](development-records/runs/windows-ci-2026-11-08/README.md)。

## 尚待取得的證據

推送後觀察實際 CI，不以 workflow YAML 或本地 guard 通過代替 Windows 執行。即使一般 Windows CI 通過，仍需乾淨 Windows、完整安裝／升級／解除安裝、人工桌面及顯卡驗收，才可關閉對應里程碑。

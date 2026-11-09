# Windows 基本包自動建置與驗證 CI

程式 **0.14.0**、架構 **0.4**。**2026-11-09 Windows CI 10/10 已實測通過**（[CI #7](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42539123115)，source 3384167）。包含原生基本包、四語／中文搬移／CLI／完整性故障與真正 Qt 正常退出；runner 非無 Python 乾淨機，C03 3/4、C04 2/4、C09 3/4、整體 7/12 保留。以下階段過程與原始失敗按當時狀態記錄。

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

## 第一次實際執行

[CI #1](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42471909742) 的原生來源 job 已成功，Windows job 失敗；完整日誌與附件需要登入，尚無足夠根因證據。診斷補強後工具 20/20、相關 133/133、完整 547（546 通過、1 既有預期失敗）。追加有界且跳脫指令的 annotation，保存 CI 自身實際結果以利下一次定位。這不降低驗收門檻；完整紀錄見[第一次執行](development-records/runs/windows-ci-attempt1-2026-11-08/README.md)。

## 跨平台原位元組

已用真正 Git core.autocrlf=true checkout 重現固定 lock／來源契約／原文／receipt 的自動 CRLF 變更；.gitattributes 保護固定來源與歷史證據，不重新格式化舊檔。新增暫存 Git repo 的七類檔案完整 byte 比較，工具 21/21、相關 134/134。這仍是 Linux Git 行為驗證，尚未證實是第一次 CI 根因；[前後紀錄](development-records/runs/windows-ci-eol-2026-11-08/README.md)保存。

## 尚待取得的證據

推送後觀察實際 CI，不以 workflow YAML 或本地 guard 通過代替 Windows 執行。即使一般 Windows CI 通過，仍需乾淨 Windows、完整安裝／升級／解除安裝、人工桌面及顯卡驗收，才可關閉對應里程碑。

## 原生建置與 UTF-8 修正

CI #3 在 Windows 2022 已原生建置／四語自檢成功，中文空格搬移失敗。第一方 windows-utf8.manifest 接入 RT_MANIFEST 24／ID 1，使用 UTF-8 process code page（Windows 10 1903+），不調整系統地區，也不修改固定上游。新 CI receipt 必須對應目前 XML，歷史固定候選仍保留；本地真正重建及四語組裝通過，修正版 Windows 待驗。來源／原始失敗及 138/138、552 項回歸見[原生紀錄](development-records/runs/windows-ci-native-2026-11-08/README.md)。

## Frozen 診斷解碼

CI #4 的中文 native --list-langs 已過；frozen full 的 PDF 模型探針仍用 CP1252 解原生 UTF-8 中文而失敗。已明確指定診斷 UTF-8，本文嚴格 UTF-8 保留；真正 Tesseract child／CP1252 反例與 OCR 及 139 相關回歸通過，Windows 修正版待驗。[紀錄](development-records/runs/windows-ci-decode-2026-11-08/README.md)保存完整短摘要及本地證據。

基本包另以 PyInstaller X utf8 固定 Python UTF-8 mode，core 報告 python_utf8_mode 並由 Windows checker 斷言。最小 Linux frozen 在 LC_ALL=C、PYTHONUTF8=0、PYTHONCOERCECLOCALE=0 的環境仍以 UTF-8 輸出四語，這只驗 packaging flag，不冒充 Windows 或完整基本包。

## Qt 收尾與正常關閉

CI #5 已通過前 9 項，實際 Qt 已開窗；首次背景檢查忙碌時主窗會先取消並暫緩關閉。工具改在原 25 秒總期限內重新列舉自己的 child PID 視窗並正常要求關閉，仍必須 exit 0，kill／terminate 不能算成功。141 項本地回歸非 Windows GUI 證據，新 CI 另驗。[過程](development-records/runs/windows-ci-close-2026-11-08/README.md)保存。

2026-11-09 補充：CI #6 在下載固定來源失敗，Windows 未執行。早期 pip／fetch 日誌經 tee 保存，job 明確使用 bash pipefail，always 上傳並可摘要；原始完整性與正常退出標準不變。31 模組隔離正常退出及原下載狀態[分存](development-records/runs/windows-ci-retry-2026-11-09/README.md)，混合 native teardown 不當作已修好。

## 最終本輪結果

Windows 10/10、Python UTF-8 mode=true，Qt 自身視窗正常 exit0，正常關閉要求4次。永久保存[公開原頁／完整短摘要及來源](development-records/runs/windows-base-ci-2026-11-09/README.md)；完整需登入的 artifacts／Windows截圖未下載、不宣稱已永久封存。下一步是乾淨 Windows 與各 profile／安裝生命週期，仍未建立安裝包或核准發行。

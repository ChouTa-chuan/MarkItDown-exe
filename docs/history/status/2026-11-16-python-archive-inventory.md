# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | 已合併 PR 1–5（2026-11-16），現行規則、三角色設定與 Python 模組清單都在 main；已設分支保護（只能經 PR、只允許 Merge） |
| 本階段分支 | `claude/qt-lgpl-notice`，由 main 開出，對應 A3 |
| 其他分支 | `codex/ai-handoff-workflow-20261112`：內容已採納，不需要合併 |

依 AGENTS.md「合併時機」，每個編號一個 PR，CI 通過且查驗完成後即合併。接手時仍先看開啟中的 PR。

## B. 這個階段完成了什麼

本階段是大階段 A「關閉來源與再散布的剩餘缺口」的 A1、A2，首次依 [CLAUDE.md](CLAUDE.md) 的三角色流程進行（coder 實作、reviewer 查驗、規劃者確認）。

- **A1 Python 模組來源清單**：建置時把每個純 Python 模組記為標準庫、具體套件、自有程式或不明，寫入隨包的 `python-modules.json`；隨包檢核列舉 `base_library.zip` 成員，並把分類計數寫進 CI 公開摘要（`scripts/python_archive_inventory.py`）。reviewer 確認七項驗收條件通過，五項建議已修正。
- **A2 文件**：[來源分類](docs/source-classification.md)與[授權與第三方義務](docs/license-proposal.md)補記微軟執行期、OpenSSL、FFmpeg 的處理現況；使用說明註明需要 64 位元 Windows 10／11。
- 基本包的數位簽章已確認（run 43385475281）：28 個非 wheel 原生檔全部有效，自建的 `tesseract.exe` 未簽章屬預期。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。PR 5 的 Windows CI 已產出清單（[紀錄](docs/development-records/runs/python-archive-inventory-ci-2026-11-16/README.md)）：基本包 1,715 個模組中 5 個無法歸屬（全為 setuptools 隨附子套件），CPU 元件 562 個全部可歸屬；既有自動驗收全部通過。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**整體規劃**（每個編號一個 PR，完成即合併）

| 大階段 | 編號與任務 | 狀態 |
| --- | --- | --- |
| A 關閉來源與再散布缺口 | A1 Python 模組清單、A2 文件補記 | 完成（PR 5） |
| | **A3 Qt／LGPL 隨包說明**：Qt 以 LGPL-3.0 使用、原文位置、原始碼取得方式、如何替換 Qt 程式庫；連結須有依據（`src/desktop_app/data/licenses/windows/inventory.json` 的補充來源） | 進行中 |
| | A4 查明 5 個 setuptools 子模組為何收進基本包（PyInstaller 的 `pyi_rth_pkgres`／`pyi_rth_setuptools` 執行期掛鉤是線索），能拿掉就拿掉 | 待開始 |
| | A5 逐檔列出 CPython 隨附元件（OpenSSL、libffi、SQLite）的版本與原文 | 待開始 |
| | A6 大階段確認：重產候選報告、重跑來源分類、評估 `runtime_sbom_complete` | 待開始 |
| B 測試版安裝包 | B1 以 CI artifact 產出並附提交、版本、雜湊、隨包原文、限制；B2 驗收表；B3 CPU 元件重新定版；B4 由使用者確認門檻 | 待開始 |
| C 乾淨機與人工驗收 | C1 乾淨 Windows 10／11 安裝與離線首次啟動；C2 四語、中文路徑、修復移除；C3 人工操作 | 需使用者或實體 Windows |
| D 功能擴充 | D1 圖片檔走本機 OCR；D2 影音獨立選配元件 | 等使用者決定 |
| E GPU | 實卡驗收 | 延後 |

**優先順序原則**：先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據，預設不保存。GitHub 的 artifact 儲存主機每次不同，本環境的網路政策通常會擋下，不要依賴下載；需要的資料請讓 CI 寫進公開摘要。

## D. 近期新增的規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行 |
| 2026-11-13 | 使用者決定 | 自有程式採 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 使用者同意 | 排除 Qt TLS 外掛與來源不明的 OpenSSL；從 CPU 文字辨識元件排除 OpenCV 內附的 FFmpeg，影音日後另做獨立選配元件；微軟執行期改用官方來源 |
| 2026-11-14 | 使用者指示 | 專案由 Claude 與 Codex 輪流進行，每個 AI 至少完成一個小階段（PR）才換手；規則見 AGENTS.md「多個 AI 輪替」 |
| 2026-11-16 | 使用者指示 | 合併 PR 4、PR 5；之後每完成一個編號（如 A4、A5）視為小階段完成即可合併；`main` 已由使用者設定分支保護 |
| 2026-11-14 | 使用者指示 | Claude 採三角色分工：規劃者（主對話）、編程者 `coder`、查驗者 `reviewer`，流程見 CLAUDE.md；主對話推理強度為中 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（沒有開啟中的 PR 就用 main），讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR，不直接推送或自行合併 main。

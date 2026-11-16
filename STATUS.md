# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | 已合併 PR 1–5（2026-11-16），現行規則、三角色設定與 Python 模組清單都在 main；已設分支保護（只能經 PR、只允許 Merge） |
| 本階段分支 | `claude/qt-lgpl-notice`，由 main 開出，對應 A3（PR 6）。A3 合併後 Claude 暫停，**下一棒交給 Codex（GPT）**，從 main 開新分支做 A4 |
| 其他分支 | `codex/ai-handoff-workflow-20261112`：內容已採納，不需要合併 |

依 AGENTS.md「合併時機」，每個編號一個 PR，CI 通過且查驗完成後即合併。接手時仍先看開啟中的 PR。

## B. 這個階段完成了什麼

- **A3 Qt／LGPL 隨包說明**：基本包新增 `licenses/qt-lgpl-notice.md`，寫明 Qt（PySide6／shiboken6 6.12.0）以 LGPL-3.0 使用、授權原文在安裝後的位置、原始碼取得方式、如何替換 Qt 程式庫。網址只用 repo 內有依據的（`inventory.json` 的 project_urls 與補充來源）；**Qt 本體（qtbase 等）的原始碼位置沒有依據，照實寫「待補」**，在補上之前 LGPL 的對應原始碼義務不算完全關閉。
- 根目錄 `LICENSE` 複製進基本包的 `licenses/markitdown-desktop/LICENSE`（先前安裝包沒有自有程式的授權全文）；說明檔與 LICENSE 列為必要資產（`build_profile.py`）。
- `third-party.md` 改由 `scripts/license_inventory.py` 的 render() 範本產生，有逐字比對測試；過時的「尚未選定原始碼授權」已改為 MIT。
- 依三角色流程：coder 實作、reviewer 兩輪查驗（第一輪兩項需修正已解決）、規劃者跑完整回歸。說明檔中的路徑以 11-12 的 Windows 實際安裝清單核對過。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。新建置是否真的含這兩個檔案，看 PR 6 的 Windows CI。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**整體規劃**（每個編號一個 PR，完成即合併）

| 大階段 | 編號與任務 | 狀態 |
| --- | --- | --- |
| A 關閉來源與再散布缺口 | A1 Python 模組清單、A2 文件補記 | 完成（PR 5） |
| | A3 Qt／LGPL 隨包說明、自有 MIT 全文隨包 | 完成（PR 6） |
| | **A4 查明 5 個 setuptools 子模組為何收進基本包**，能拿掉就拿掉。線索：PyInstaller 6.22.3 有 `pyi_rth_pkgres`、`pyi_rth_setuptools` 兩個執行期掛鉤；不明模組為 `setuptools._distutils.compilers`、`.compilers.C`、`.compilers.platform`、`setuptools._vendor`、`setuptools._vendor.jaraco`（PR 5 的 Windows CI 摘要 `python_archives.unknown_names`）。排除會改變打包內容，需確認程式不依賴它們 | **下一個，交給 Codex** |
| | A5 逐檔列出 CPython 隨附元件（OpenSSL、libffi、SQLite）的版本與原文 | 待開始 |
| | A5b 補上 Qt 本體原始碼的位置與版本對應（需有依據，例如建置時記錄 PySide6 對應的 Qt 版本來源），補上後更新 `qt-lgpl-notice.md` 的「待補」 | 待開始 |
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
| 2026-11-16 | 使用者指示 | A3 完成後 Claude 暫停，換手給 Codex（GPT）從 A4 繼續 |
| 2026-11-16 | 使用者指示 | 合併 PR 4、PR 5；之後每完成一個編號（如 A4、A5）視為小階段完成即可合併；`main` 已由使用者設定分支保護 |
| 2026-11-14 | 使用者指示 | Claude 採三角色分工：規劃者（主對話）、編程者 `coder`、查驗者 `reviewer`，流程見 CLAUDE.md；主對話推理強度為中 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（沒有開啟中的 PR 就用 main），讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR，不直接推送或自行合併 main。

# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

兩個開啟中的 PR 依序相疊，都以 `main` 為目標。**合併順序 4 → 5，由使用者指示。** 接手請從 PR 5 的分支開新分支。

| PR | 分支 | 內容 | 狀態 |
| --- | --- | --- | --- |
| 1–3 | — | 已合併，`main` 為 `747edba` | 已合併 |
| [4](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/4) | `claude/ci-self-check-and-ms-runtime` | CI 自行檢查排除檔案、原生檔來源與簽章、微軟執行期改用官方來源、AI 輪替規則、Claude 三角色設定 | CI 通過 |
| 5 | `claude/python-archive-inventory`（目前最新） | Python 模組來源清單、`base_library.zip` 成員列舉、文件更新 | 見 PR 頁 |

`codex/ai-handoff-workflow-20261112` 的內容已採納，不需要合併。

## B. 這個階段完成了什麼

本階段是大階段 A「關閉來源與再散布的剩餘缺口」的 A1、A2，首次依 [CLAUDE.md](CLAUDE.md) 的三角色流程進行（coder 實作、reviewer 查驗、規劃者確認）。

- **A1 Python 模組來源清單**：建置時把每個純 Python 模組記為標準庫、具體套件、自有程式或不明，寫入隨包的 `python-modules.json`；隨包檢核列舉 `base_library.zip` 成員，並把分類計數寫進 CI 公開摘要（`scripts/python_archive_inventory.py`）。reviewer 確認七項驗收條件通過，五項建議已修正。
- **A2 文件**：[來源分類](docs/source-classification.md)與[授權與第三方義務](docs/license-proposal.md)補記微軟執行期、OpenSSL、FFmpeg 的處理現況；使用說明註明需要 64 位元 Windows 10／11。
- 基本包的數位簽章已確認（run 43385475281）：28 個非 wheel 原生檔全部有效，自建的 `tesseract.exe` 未簽章屬預期。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。**`python-modules.json` 在 Windows 上的實際輸出要看 PR 5 的 Windows CI**；reviewer 在 Linux 以真實打包分析試跑的結果是 1,655 個模組中 6 個無法歸屬。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. PR 4、PR 5 的合併時機。
2. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**可以直接做的下一步（依序）**

1. 讀 PR 5 的 Windows CI 公開摘要中的 `python_archives`：各來源的模組數、不明的數量與名稱、`base_library` 成員數；確認摘要沒有被公開頁截斷，且應用、安裝、跨版、續修驗收仍通過。不明的模組逐一查明原因。
2. **A3 Qt／LGPL 隨包說明**：在基本包加入說明檔，寫明 Qt 以 LGPL-3.0 使用、授權原文在包內的位置、對應原始碼的取得方式、如何替換 Qt 程式庫。每個連結都要有依據（可用 `src/desktop_app/data/licenses/windows/inventory.json` 記錄的補充來源），不憑印象寫網址。
3. 逐檔列出 CPython 隨附第三方元件（OpenSSL、libffi、SQLite）的版本與原文。
4. 大階段 A 完成後由規劃者整體確認，再評估 `runtime_sbom_complete` 是否有條件改為 true；之後重新產生候選報告並重跑來源分類。
5. CPU 元件正式發布前重新定版（內容已不同於先前的 1.0.1）。
6. 準備測試用安裝包與驗收表，再做乾淨 Windows 與人工驗收。GPU 延後。

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
| 2026-11-14 | 使用者指示 | Claude 採三角色分工：規劃者（主對話）、編程者 `coder`、查驗者 `reviewer`，流程見 CLAUDE.md；主對話推理強度為中 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（沒有開啟中的 PR 就用 main），讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR，不直接推送或自行合併 main。

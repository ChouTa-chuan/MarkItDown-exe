# 現況

更新：2026-11-13（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| 預設分支 | `main`（`2e06631`）；不直接推送，合併由使用者指示 |
| [PR 1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1) | `claude/confident-ride-o38ls7` → `main`，開啟中、CI 通過、可合併，等使用者決定合併時機 |
| 本階段分支 | `claude/status-and-history-index`，疊在 PR 1 之上，PR 目標為 `main`（CI 只在目標為 main 的 PR 執行）。PR 1 合併前，這個 PR 的差異會包含 PR 1 的內容。**合併順序：先 PR 1，再這一個** |
| 其他分支 | `codex/ai-handoff-workflow-20261112`：Codex 提出的輪替交接方案，未合併。其四組欄位與 PR 範本的內容已採納進這份檔案與新規則，做法改為單一現況檔＋自動索引；該分支不需要再合併 |

## B. 這個階段完成了什麼

- 建立這份現況檔，取代「開工先讀交接指南、進度資料、開發紀錄、CHANGELOG」的做法。
- 新增 `scripts/build_history_index.py`，由證據目錄、現況存檔與決策紀錄自動產生 [歷史索引](docs/history-index.md)；測試與 CI 會擋下過期的索引。
- 改寫 `AGENTS.md`：必讀只剩兩份、數字只寫在 `progress.json`、階段完成才整體更新、新證據以摘要與雜湊為主、指定未合併 PR 時要讀該分支。
- 新增精簡的 PR 範本，欄位與本檔 A–D 相同。
- 首頁改為指向本檔與進度頁，不再重抄數字；保存[成本診斷](docs/cost-diagnosis-2026-11-13.html)。

驗證結果與來源提交記在 `progress.json` 的 `full_regression`；本階段沒有新的 Windows 建置、安裝、GPU 或人工驗收。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. PR 1 與本階段 PR 的合併時機。
2. 授權：是否採 MIT、著作權人名稱、早期「Codex Assistant」提交的權利歸屬（[提案](docs/license-proposal.md)）。
3. 三項打包調整是否同意：排除 Qt TLS 外掛（連帶移除來源不明的 OpenSSL）、排除 OpenCV 的 FFmpeg、改用官方來源的 VC runtime。

**可以直接做的下一步（依序）**

1. 在 Windows 建置流程為系統路徑收集的 DLL 補記來源路徑、數位簽章與版本，並列出 Python 封存檔成員；完成條件是[來源分類](docs/source-classification.md)中候選與無證據項目（基本包 49、CPU 47）有 Windows 端證據可判定。
2. 上述決定確認後，加入 `LICENSE`、補 Qt／LGPL 隨包說明，重新產生候選報告。
3. 準備測試用安裝包與驗收表，再做乾淨 Windows 與人工驗收。GPU 延後。

**優先順序原則**：先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣。

**有期限的資料**：PR 1 首次執行的兩份 Windows 報告（run 43152427580、43152427554）於 2026-11-19 到期，未保存；它們以暫時合併提交執行，不是候選證據，預設不保存。

## D. 近期新增的規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行 |
| 2026-11-13 | 使用者同意 | Codex 交接方案採其內容、換其做法；現況檔不設硬性大小上限，但保持精簡 |
| 2026-11-13 | 使用者同意 | 舊證據不改動；只為有失敗紀錄的 20 筆在 `docs/history/keywords.json` 補關鍵字（事後判讀，與原始證據分開），自有程式授權採 MIT（著作權人名稱待提供，`LICENSE` 尚未加入） |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe 的指定分支或 PR。先讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的分支並開 PR，不直接推送或自行合併 main。

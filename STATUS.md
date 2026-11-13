# 現況

更新：2026-11-13（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

三個 PR 依序相疊，都以 `main` 為目標（CI 只在目標為 main 的 PR 執行），都還沒合併。**使用者決定：PR 是階段小成果，等完成較大的階段或里程碑後再一起合併；合併順序 1 → 2 → 3。** 在那之前 `main`（`2e06631`）維持接手前的狀態，接手請從最後一個分支開始。

| PR | 分支 | 內容 | 狀態 |
| --- | --- | --- | --- |
| [1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1) | `claude/confident-ride-o38ls7` | 保存 CI 報告、來源分類、Linux CI、授權提案 | CI 通過 |
| [2](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/2) | `claude/status-and-history-index` | 現況檔、自動索引、精簡規則、關鍵字表 | CI 通過 |
| [3](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/3) | `claude/license-and-openssl-cleanup`（目前最新） | `LICENSE`、基本包排除來源不明的 OpenSSL | CI 通過 |

`codex/ai-handoff-workflow-20261112` 是 Codex 提出的交接方案，內容已採納進現況檔與規則，不需要合併。

## B. 這個階段完成了什麼

- 加入根目錄 `LICENSE`（MIT，著作權人 周大詮 (ChouTa-chuan)），`pyproject.toml` 宣告授權，自有 `THIRD_PARTY_NOTICES` 說明 MIT 只適用自有程式。
- 基本包打包時排除 Qt 的 OpenSSL TLS 外掛，以及它從建置機系統路徑帶進來的 `libssl-3-x64`／`libcrypto-3-x64.dll`（`scripts/bundle_filters.py`、`packaging/base.spec`）。保留 Qt 的 Schannel 後端與 CPython 自己的 OpenSSL。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。
- PR 3 的 Windows 基本包 CI 通過：排除後應用、安裝、跨版與續修驗收全部接受，原生檔少 3 個、未對照來源少 2 個，與排除三個檔案一致（[紀錄](docs/development-records/runs/openssl-exclusion-ci-2026-11-13/README.md)）。**逐檔清單尚未核對**：完整報告所在的儲存主機被網路政策擋下。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. OpenCV 內的 FFmpeg（CPU 選配元件）：使用者希望保留影音能力並做成可選、可事後加裝。已說明這個 DLL 只是 OpenCV 的影片讀寫模組，不是 MarkItDown 處理影音所用的途徑；建議從 OCR 元件中排除，影音另做成獨立選配元件。等使用者確認這個做法，確認前不動 CPU 元件的內容。

**可以直接做的下一步（依序）**

1. 讓 CI 自己核對並公開關鍵檔案清單，不再依賴下載 artifact：在 Windows 驗收加入「不得出現被排除的三個檔案」的檢查，並把系統路徑來源的 DLL 清單寫進公開摘要。GitHub 的 artifact 儲存主機每次不同，逐一申請網路放行不可行。
2. 微軟執行期程式庫改用官方來源（使用者已同意）：改從 Visual Studio 的可再散布目錄取得 VC runtime，並在建置時記錄來源路徑、數位簽章與版本；評估 `api-ms-win-*`／`ucrtbase.dll` 是否改用 Windows SDK 的可再散布目錄或不隨包。
3. 產生 `base_library.zip` 與 PYZ 的成員清單，逐檔列出 CPython 隨附元件；之後重新產生候選報告並重跑[來源分類](docs/source-classification.md)。
4. 補 Qt／LGPL 的隨包說明與原始碼取得方式（見[授權與第三方義務](docs/license-proposal.md)第 3 節）。
5. 準備測試用安裝包與驗收表，再做乾淨 Windows 與人工驗收。GPU 延後。

**優先順序原則**：先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據，預設不保存。

## D. 近期新增的規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行；現況檔不設硬性大小上限 |
| 2026-11-13 | 使用者同意 | 舊證據不改動，只為有失敗紀錄的 20 筆在 `docs/history/keywords.json` 補關鍵字 |
| 2026-11-13 | 使用者決定 | 自有程式採 MIT，著作權人「周大詮 (ChouTa-chuan)」；專案由使用者主導、以不同 AI 工具開發，早期 Codex 產生的提交一併適用，不需另外聲明 |
| 2026-11-13 | 使用者決定 | PR 是階段小成果，累積到較大的階段或里程碑再一起合併 |
| 2026-11-13 | 使用者同意 | 排除 Qt TLS 外掛與來源不明的 OpenSSL；微軟執行期改用官方來源。FFmpeg 不直接移除，待確認做法 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe 的分支 `claude/license-and-openssl-cleanup`（或 STATUS.md A 節列出的最新分支）。先讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的分支並開 PR，不直接推送或自行合併 main。

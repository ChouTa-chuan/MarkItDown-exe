# 現況

更新：2026-11-13（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | `747edba`。2026-11-13 使用者指示合併 PR 1、2、3，現行規則、現況檔與索引都已在 main |
| 本階段分支 | `claude/ci-self-check-and-ms-runtime`，由 main 開出，PR 目標 `main`，沒有疊在其他未合併 PR 上 |
| 已合併 | [PR 1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1)、[PR 2](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/2)、[PR 3](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/3) |
| 其他分支 | `codex/ai-handoff-workflow-20261112`：內容已採納，不需要合併 |

接手時仍先看開啟中的 PR：main 之後可能再度落後於工作分支。合併一律由使用者指示。

## B. 這個階段完成了什麼

- 建置時為非 wheel 來源的原生檔（建置用 CPython 目錄、系統路徑）記錄來源目錄、PE 版本資源與 Windows 數位簽章（`scripts/native_identity.py`）。
- 隨包檢核（`scripts/check_bundle_provenance.py`）把上述資料依來源目錄與簽署者分組寫進 CI 公開摘要，並在候選包出現已決定排除的檔案（來源不明的 OpenSSL、OpenCV 的 FFmpeg）時直接拒絕。之後不必下載 artifact 也能核對。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。**Windows 上實際產出的來源與簽章資料，要看本階段 PR 的 Windows CI**；那份資料出來前，系統 DLL 的發行者仍屬未證實。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**可以直接做的下一步（依序）**

1. 讀本階段 PR 的 Windows CI 公開摘要（`non_wheel_native`、`excluded_binaries_absent`），確認系統 DLL 實際來自哪些目錄、由誰簽署。
2. 依上一步的實際資料，把微軟執行期程式庫改用官方來源（使用者已同意）：VC runtime 取自 Visual Studio 的可再散布目錄；`api-ms-win-*`／`ucrtbase.dll` 是 Windows 10 以後內建的系統元件，評估不隨包。變更後以 Windows CI 驗證，並更新[來源分類](docs/source-classification.md)。
3. 產生 `base_library.zip` 與 PYZ 的成員清單，逐檔列出 CPython 隨附元件；重新產生候選報告並重跑來源分類。
4. 補 Qt／LGPL 的隨包說明與原始碼取得方式（見[授權與第三方義務](docs/license-proposal.md)第 3 節）；CPU 元件正式發布前重新定版（內容已因排除 FFmpeg 而不同於先前的 1.0.1）。
5. 準備測試用安裝包與驗收表，再做乾淨 Windows 與人工驗收。GPU 延後。

**優先順序原則**：先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據，預設不保存。GitHub 的 artifact 儲存主機每次不同，本環境的網路政策通常會擋下，不要依賴下載。

## D. 近期新增的規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行；現況檔不設硬性大小上限 |
| 2026-11-13 | 使用者決定 | 自有程式採 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 使用者同意 | 排除 Qt TLS 外掛與來源不明的 OpenSSL；從 CPU 文字辨識元件排除 OpenCV 內附的 FFmpeg，影音日後另做獨立選配元件；微軟執行期改用官方來源 |
| 2026-11-13 | 使用者指示 | 輪替時要看 PR 而非只看 main（[工作流](docs/ai-handoff-workflow.md)）；為避免新接手者在 main 讀到舊規則，指示先合併 PR 1–3 再繼續 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（沒有開啟中的 PR 就用 main），讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR，不直接推送或自行合併 main。

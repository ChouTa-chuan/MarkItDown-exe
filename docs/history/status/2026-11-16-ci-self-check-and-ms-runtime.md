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
- PR 4 首次 Windows CI 的公開摘要顯示：基本包中 46 個檔名像 Microsoft 的系統 DLL（`api-ms-win-*`、`ucrtbase`、`msvcp140`）**不是來自 Windows 系統目錄，而是 PyInstaller 沿 PATH 從 runner 上 Java JDK 的 `bin` 目錄收進來的複本**；版本資源的公司欄為 Microsoft Corporation，但簽章欄位當次是空的，原因未明。排除的檔案確認不在候選包內（`excluded_binaries_absent: true`）。
- 依此調整（`scripts/bundle_filters.py`、兩份 spec）：Universal CRT 是 Windows 10 以後內建的系統元件，不再隨包；來源不在 CPython 或 wheel 的 VC runtime 改從 Visual Studio 的可再散布目錄取得，找不到就中止建置。簽章查詢改為讀檔傳入路徑，並把查詢錯誤寫進公開摘要。
- 調整後的 Windows CI 通過（[紀錄](docs/development-records/runs/ms-runtime-official-source-ci-2026-11-13/README.md)）：基本包原生檔與未對照來源各少 45 個，Java JDK 目錄不再出現，`msvcp140.dll` 來自 Visual Studio 可再散布目錄，既有自動驗收全部接受。
- 數位簽章已取得（[紀錄](docs/development-records/runs/native-signatures-ci-2026-11-13/README.md)）：CPU 元件 27 個非 wheel 原生檔全部 `Valid`，VC runtime 由 Microsoft 簽署、其餘由 Python Software Foundation 簽署；CPU 元件原生檔與未對照來源各再少 44 個。基本包同一提交的 CI 也通過，但摘要尚未逐項讀取。
- Linux 完整回歸通過，結果記在 `progress.json` 的 `full_regression`。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**可以直接做的下一步（依序）**

1. 讀基本包最新一次 Windows CI 的公開摘要，確認簽章欄位同樣有值（run 43385475281 或之後的執行）。
2. 通過後更新[來源分類](docs/source-classification.md)與[授權與第三方義務](docs/license-proposal.md)中 Microsoft runtime 的敘述；不隨包 Universal CRT 代表不支援 Windows 8.1 以前的系統，需寫進使用說明。
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
| 2026-11-14 | 使用者指示 | 專案由 Claude 與 Codex 輪流進行；每個 AI 至少完成一個小階段（PR）才換手。協作規則寫入 AGENTS.md「多個 AI 輪替」 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（沒有開啟中的 PR 就用 main），讀該分支的 AGENTS.md 與 STATUS.md，從 C 節「可以直接做的下一步」第一項開始；階段完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR，不直接推送或自行合併 main。

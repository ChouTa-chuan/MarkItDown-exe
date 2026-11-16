# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | 本階段起點為 PR 1–7 已合併的 `6032f9e`。A4 經 PR #8 進入 main；目前是否已合併以該 PR 即時狀態核對，分支保護只允許 Merge |
| 本階段分支 | `codex/a4-setuptools-audit-20261116`，由接手時尚未合併的 PR 6 head `fc02258` 開出，後以 merge 納入最新 main；沒有推送別人的分支。程式／測試提交 `8c26451`，納入 main 的提交 `653ed8e` |
| 本階段 PR／推送 | [PR #8](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/8)，目標 main；head `ca71bfa` 首輪 CI 全部通過，Windows 實際摘要已保存。最後結果文件提交仍依 GitHub 最新 head CI 查驗後 Merge；實際 head／合併狀態以 PR 即時資料核對，避免把純文件提交與受測 source 混淆 |
| 相依／合併次序 | 父 PR 6 及後來的 PR 7 已合併，不需再疊 PR；本輪 PR 只應包含 A4 差異。A4 Windows／Linux CI 全通過且查驗完成後，以 Merge 合併，不直接推 main |
| 其他分支 | `codex/ai-handoff-workflow-20261112`：內容已採納，不需要合併 |

依 AGENTS.md「合併時機」，每個編號一個 PR，CI 通過且查驗完成後即合併。接手時仍先看開啟中的 PR。

## B. 這個階段完成了什麼

- **A4 setuptools 調查與排除**：已重現 urllib3 的選用 backports 匯入，經 PyInstaller 別名拉入 setuptools 父套件與編譯工具的關係；原 unknown 為無來源檔的 namespace。基本包排除整套建置用 setuptools，保留實際建置環境、原文與鎖定，沒有按模組名猜測授權歸屬。
- `base.spec` 與建置後來源檢核共同拒絕 setuptools 子模組再度出現，基本包的公開 CI 摘要新增 `python_archives.build_only_modules_absent`；CPU 元件不改。新增反例驗證重算資產 hash 也不能繞過排除，並拆開修改檔案內原有的分號敘述。
- Linux 隔離基本包已真正建置及執行：EXE 內嵌 PYZ 沒有 setuptools；空 PATH 下通過既有 frozen core／格式驗收。完整混合與獨立模組回歸通過，原始結果、匯入圖摘要、失敗與限制見[本輪證據](docs/development-records/runs/a4-setuptools-audit-2026-11-16/README.md)，現況數字只見 [progress.json](docs/progress.json)。
- 自行查驗範圍：比較匯入圖與 EXE 內實際 PYZ、確認兩層拒絕條件、套件邊界不誤擋、CPU 規則不變及原文／模型／候選證據未變。這是 Codex 自行查驗，不是 Claude 子代理查驗；沒有新的必須修正項。
- **A4 的 Windows 與 Linux 首輪 CI 全部通過**：原未知 namespace 已不再出現，`build_only_modules_absent=true`，基本包安裝、跨版與程序恢復及 CPU 既有驗收均接受。精確 head／merge、公開摘要、artifact hash／期限與限制見[PR 8 證據](docs/development-records/runs/a4-pr8-ci-2026-11-16/README.md)。最後文件 head 仍須通過 CI 才 Merge；未提高產品里程碑、SBOM 或再散布旗標，也沒有發布產品。

## C. 未完成、阻擋與下一步

**等使用者決定**

1. 圖片與影音的支援方式與排程（目前程式只接受文字、Office、HTML、PDF）：建議圖片檔走既有的本機 OCR，影音另做獨立選配元件並使用本機語音辨識；上游的語音轉文字會把音訊送到線上服務，不符合「本機完成」。尚未排入工作。

**整體規劃**（每個編號一個 PR，完成即合併）

**本輪最先接續**：先核對 PR #8 是否已合併；未合併時，確認最新 head 全部 CI 與查驗通過，再以 Merge 合併。已合併就從最新 main 開自己的新分支，執行下表 **A5（下一個，交給 Codex）**。API 阻擋已解除，不再要求使用者重設相同網域或重複批准。

| 大階段 | 編號與任務 | 狀態 |
| --- | --- | --- |
| A 關閉來源與再散布缺口 | A1 Python 模組清單、A2 文件補記 | 完成（PR 5） |
| | A3 Qt／LGPL 隨包說明、自有 MIT 全文隨包 | 完成（PR 6） |
| | **A4 查明 setuptools 子模組並排除非必要建置工具**；Linux 與 Windows 實際驗證均已接受 | **驗證完成（PR #8；最後文件 CI／合併見 A 節）** |
| | **A5 逐檔列出 CPython 隨附元件（OpenSSL、libffi、SQLite）的版本與原文**。先讀實際 Windows CPython 安裝授權與 native manifest，對準 Windows runner 的 patch 版，不能用其他平台／版本的 props 直接代填；上游根目錄 LICENSE 不等於完整第三方原文 | **下一個，交給 Codex；PR #8 合併後從 main 開新分支** |
| | A5b 補上 Qt 本體原始碼的位置與版本對應（需有依據，例如建置時記錄 PySide6 對應的 Qt 版本來源），補上後更新 `qt-lgpl-notice.md` 的「待補」 | 待開始 |
| | A6 大階段確認：重產候選報告、重跑來源分類、評估 `runtime_sbom_complete` | 待開始 |
| B 測試版安裝包 | B1 以 CI artifact 產出並附提交、版本、雜湊、隨包原文、限制；B2 驗收表；B3 CPU 元件重新定版；B4 由使用者確認門檻 | 待開始 |
| C 乾淨機與人工驗收 | C1 乾淨 Windows 10／11 安裝與離線首次啟動；C2 四語、中文路徑、修復移除；C3 人工操作 | 需使用者或實體 Windows |
| D 功能擴充 | D1 圖片檔走本機 OCR；D2 影音獨立選配元件 | 等使用者決定 |
| E GPU | 實卡驗收 | 延後 |

**優先順序原則**：先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據，預設不保存。GitHub 的 artifact 儲存主機每次不同，本環境的網路政策通常會擋下，不要依賴下載；需要的資料請讓 CI 寫進公開摘要。

**平台狀態**：使用者將 `api.github.com` 加入並發布後，API／CLI 查詢與建立 PR 均成功。一般沙箱仍連不到環境代理，依 runtime 指引保留原代理／TLS，以獲准命令方式執行。CI 日誌儲存主機受限，改讀公開 API annotation；這不是開 PR／合併的阻擋。前次本機原始日誌可能隨環境更換消失，必要小型結果與 hash 已保存；沒有重跑相同本機回歸冒充新成果。

## D. 近期新增的規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-16 | 使用者本輪指示 | API 存取恢復後完成 A4 PR、Windows CI 與合併等阻擋項目，再依現況接續；沿用既有查驗與 Merge 條件，沒有新增產品發行授權 |
| 2026-11-16 | 使用者本輪接手指示 | Codex 從 C 節 A4 開始；更新 STATUS、推送自己的新分支、開 PR；CI 通過即可依 AGENTS 的查驗條件 Merge。不直接推 main、不推別人分支。A4 任務內排除已驗證非必要的 setuptools，不擴及其他打包調整 |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行 |
| 2026-11-13 | 使用者決定 | 自有程式採 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 使用者同意 | 排除 Qt TLS 外掛與來源不明的 OpenSSL；從 CPU 文字辨識元件排除 OpenCV 內附的 FFmpeg，影音日後另做獨立選配元件；微軟執行期改用官方來源 |
| 2026-11-14 | 使用者指示 | 專案由 Claude 與 Codex 輪流進行，每個 AI 至少完成一個小階段（PR）才換手；規則見 AGENTS.md「多個 AI 輪替」 |
| 2026-11-16 | 使用者指示 | A3 完成後 Claude 暫停，換手給 Codex（GPT）從 A4 繼續 |
| 2026-11-16 | 使用者指示 | 合併 PR 4、PR 5；之後每完成一個編號（如 A4、A5）視為小階段完成即可合併；`main` 已由使用者設定分支保護 |
| 2026-11-14 | 使用者指示 | Claude 採三角色分工：規劃者（主對話）、編程者 `coder`、查驗者 `reviewer`，流程見 CLAUDE.md；主對話推理強度為中 |
| 2026-11-16 | 使用者決定 | 規劃者改為子代理 `planner`（`claude-fable-5-2`），只在大階段開始前寫計畫、完成後整體複查；主對話改為不屬於角色的協調者，預設模型 `claude-opus-5-5`。原因：主對話會隨工作階段切換模型，角色模型應固定在子代理定義檔 |

## 接手指令

> 請接手 ChouTa-chuan/MarkItDown-exe，先列出開啟中的 PR，讀最新分支的 AGENTS.md 與 STATUS.md。確認 PR #8 已合併；若還沒，先完成其最新 head 的 CI 與 Merge。然後從最新 main 開自己的新分支做 C 節 A5，完成後依規則更新現況、推送並開 PR，全部 CI 與查驗通過即可 Merge。不直接推 main，不推別人的分支。

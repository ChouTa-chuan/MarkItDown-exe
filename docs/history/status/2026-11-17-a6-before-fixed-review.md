# 現況

更新：2026-11-17（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| main／已完成基線 | **main 已合併 PR 1–11**，A5b／A5c 已完成並合併（PR #10／#11）；使用者確認兩階段均由 Claude reviewer 查驗通過，沒有必須修正項目。A6 起點 `e23d383b7f38ac95c4b883513834abfd8f814600` |
| 本階段分支 | `codex/a6-fixed-candidate-20261117`，從最新 main 另開，未推送其他 AI 的分支；A6 尚未執行新驗證 |
| 本階段 PR | A6 尚未建立；A5b [PR #10](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/10) 與 A5c [PR #11](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/11) 均已合併，最終 head 全 CI 通過 |
| 合併規則 | 一個編號一個 PR；最終 head 全部 CI 通過、查驗無必修項才一般 Merge，不直接推 main、不刪分支、不改寫歷史 |

## B. 這個階段完成了什麼

- **A6 第一個提交先修正交接現況**：main 已合併 PR 1–11，A5b／A5c 最終 head 的四條 CI run 補入 progress.json，新增 D 節不重複原文摘要的維護規則；既有使用者決定與原始證據保留。以下 A5c 內容為沿用的已完成基線，A6 新候選／分類尚未執行。

- **A5c 三項已實作**：Windows 適用清單的 OpenSSL／SQLite 不能只有建置宣告；探測例外、無觀測或載入來源不匹配都拒絕。產生端保存原始診斷再失敗，重驗端也強制同一門檻，避免重算 hash 繞過。
- 補齊各元件列、`probe_error`（含空字串）、刪除 OpenSSL 原文的反例；合成 Windows 清單先驗有效，再在 CI／非 CI 下證明 audit／CLI 拒絕 hash 重綁的探測缺口。合成資料不當 Windows 實證；libffi 仍僅建置宣告，Linux 不適用清單維持不適用。
- CPython README 已說明 extension 的 observed_version 屬所連結 OpenSSL／SQLite，不是該檔自身 PE 版本。Linux 混合與獨立模組完整回歸正常退出，只有既有 ONNX 繁中 expected failure；[原始來源與結果](docs/development-records/runs/a5c-runtime-probe-2026-11-16/README.md)已保存，數字只記 [progress.json](docs/progress.json)。
- **A5c 原生 Windows 新門檻已驗**：基本包及 CPU 的 OpenSSL／SQLite 均有匹配觀測，libffi 限制保留；[CI 原始公開摘要與來源](docs/development-records/runs/a5c-pr11-ci-2026-11-16/README.md)另存，沒有把合成故障反例當 Windows 注入實證。
- A5b 已合併：原始 Qt 來源、原文與歷史實證不改寫；D 節全部使用者決定逐筆保留。

## C. 未完成、阻擋與下一步

**本輪 A6：固定來源候選、來源重分類與整體審閱**。main 已合併 PR 1–11；A5b／A5c 已由 Claude reviewer 查驗通過且沒有必修項。本輪從上述最新 main 的自己的新分支開始，先固定來源提交與候選證據，再重跑分類；不把 PR 暫時 merge 當交付候選，不提前上傳產品。

| 大階段 | 任務 | 現況／下一步 |
| --- | --- | --- |
| A 來源與再散布 | A1 模組清單、A2 文件、A3 Qt／自有 MIT 隨包 | 完成（PR #5／#6） |
| | A4 setuptools 排除 | **完成（PR #8，已合併並通過 Claude reviewer）** |
| | A5 CPython 隨附元件逐檔版本／原文 | **完成（PR #9，已合併並通過 Claude reviewer）** |
| | A5b Qt 本體原始碼位置及版本對應 | **完成（PR #10，已合併、Claude reviewer 通過）**；Qt 來源、Windows 版本與指紋查驗通過 |
| | A5c A5 驗收補強 | **完成（PR #11，已合併、Claude reviewer 通過）**；三項、反例及原生 Windows 新門檻皆已查驗 |
| | A6 固定來源候選、重跑來源分類、整體審閱 | **本輪開始**；固定來源／候選後重分類及整體審閱，才評估 runtime_sbom_complete，目前 false |
| B 測試版安裝包 | 產物證據、驗收表、CPU 元件重新定版及門檻確認 | 未開始，不在門檻關閉前上傳產品 |
| C 乾淨機／人工 | Windows 10／11、離線、四語、中文路徑、修復移除 | 需要使用者或實體 Windows，尚未接受 |
| D 擴充 | 圖片本機 OCR／影音獨立元件 | 等使用者決定，未排入本輪 |
| E GPU | 實卡驗收 | 延後 |

**A5c 原規格與完成條件（使用者 2026-11-16 指定，獨立 PR）**：

1. Windows 建置（`GITHUB_ACTIONS` 或 `win32`）時，OpenSSL／SQLite 相關檔案若不是 `matched-runtime-probe`，或有 `probe_error`，`check_bundle_provenance` 應判為不接受，並補反例測試；前版 `write_inventory` 只記 `probe_error` 而可通過，本輪已補強產生及重驗兩端。
2. `tests/test_cpython_components.py` 新增反例：刪除包內 `cpython-original/openssl.txt` 後，`verify_inventory` 必須拒絕。
3. README 或報告註明 `_ssl.pyd`、`_hashlib.pyd`、`_sqlite3.pyd` 等 extension 列的 `observed_version` 是所連結 OpenSSL／SQLite 的版本，不是該檔本身的版本。

本輪以新標準的 Windows 基本包及 CPU CI 通過並查驗；不沿用 A5b 作為新標準已驗的證據。最終文件 head 仍必須全 CI 通過才合併。

**平台／有期資料**：GitHub API 已恢復；一般沙箱連不到代理時依 runtime 指引用獲准命令，保留代理與 TLS。日誌／artifact 儲存主機仍可能受限，CI 需以公開 annotation 提供必要資料。Windows 報告保留七天、Linux 報告十四天，實際期限／hash 以每次 run 記錄為準；不依賴暫存或未下載附件。這些 PR 暫時 merge 驗證不取代 `cb8f24d` 固定候選，沒有產品發行。

## D. 新增規則與決定

使用者親自做的決定逐筆保留，不因精簡而合併或刪除；工具專用設定的適用範圍說明不能取代原決定。以下恢復原文自 [A4 現況存檔](docs/history/status/2026-11-16-a4-before-a5.md)。

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
| 2026-11-16 | 使用者本輪指示 | A4 已由 Claude reviewer 查驗通過；開始 A5，並在同一 PR 修正 A4 完成／main 已合併 PR 1–8 的現況與 next；補充 A4 unresolved_files=109 的計數口徑與基準，找不到寫未保存 |
| 2026-11-16 | 本輪明確授權的保存補註 | 僅對指定 A4 證據 README 追加說明；先保存原版 README／manifest，再更新該 README 的 hash。其他舊證據及原始 CI JSON 不變，不擴大成任意改寫歷史的授權 |
| 2026-11-16 | 既有使用者指示／AGENTS | 各編號一個 PR，全部 CI 與查驗通過即可一般 Merge；不直接推 main、不推別人分支、不 force push 或刪分支 |
| 2026-11-13 | 已確認授權決定 | 自有程式 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 已確認打包決定 | 排除 Qt TLS／來源不明 OpenSSL、CPU OCR 的 OpenCV FFmpeg；VC runtime 取官方來源，影音另行規劃 |
| 2026-11-13–16 | 已確認維護方式 | 現況／歷史分開，數字單一來源，階段完成才整體更新，原文／模型／圖及原始失敗保留；優先基本包，暫緩擴充元件系統 |
| 既有規則 | AGENTS／使用者 | 來源與再散布門檻未關閉前不發 Setup／worker／模型（含產品 artifact）、不建 Release 或 tag；ONNX 繁中、RAM 軟性預算、實機／GPU 限制維持 |
| 2026-11-14–16 | Claude 專用分工 | CLAUDE.md 與 .claude/ 保存其角色與模型；不把工具專用設定視為所有 AI 的規則 |
| 2026-11-16 | 使用者本輪指示 | A5 已由 Claude reviewer 查驗通過；開始 A5b，第一個提交恢復使用者決定、修正 main 已合併 PR 1–9／next、補 A5 最終四個 CI run；D 節精簡不合併或刪除使用者親自做的決定。指定 A5 README 補註前保存原版及原始 manifest，其他舊證據不變 |
| 2026-11-16 | 使用者補充 A5c | A5 的 runtime probe 接受條件、缺失 OpenSSL 原文反例與 extension 版本說明列入 C 節待辦；獨立 PR、全部 Windows CI 通過才合併，A5b 不處理 |
| 2026-11-17 | 使用者決定 | 之後在 D 節新增紀錄時，不要再加原文已涵蓋的摘要列。 |

接手先列 PR，再讀最新分支 AGENTS.md 與 STATUS.md；本輪 A6，先固定來源／候選並檢查證據可取得性；不重做 A5b／A5c，不把前階段 CI 當 A6 候選驗收。

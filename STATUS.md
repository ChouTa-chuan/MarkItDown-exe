# 現況

更新：2026-11-17（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| 本輪 main 起點 | **PR 12 已合併（7b787d3），合併後 CI 全綠**；A6 已由 Claude reviewer 查驗通過，沒有必須修正項目 |
| 本輪分支 | `codex/a7-mit-notice-20261117`，從最新 main `7b787d3dcf1e82fd43873c8c684a0412a38bcfb6` 開自己的新分支；不直接推 main、不推別人分支 |
| 本輪 PR | A6 [PR #12](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/12) 已合併；A7 尚未建立，先完成本輪指定修正與自有 MIT 對照 |
| 固定來源 | `8285450226abe1381e6a357e8bd33bff1ad46e0e`；基本包與 CPU 均已驗並離線重跑分類，PR 暫時 merge 不取代此候選 |

## B. 這個階段完成了什麼

- **A7 首個提交先修正過時文件**：PR 12 已合併（7b787d3），合併後 CI 全綠；使用者確認 A6 已由 Claude reviewer 通過、沒有必修項。A6 基本包審閱改以固定來源 8285450 的成功 run 為準，attempt-e1761f9 保留作歷史。
- **2026-11-17 補註**：run [43912958713](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912958713) 最終為 **completed／success**，只產生 windows-cpu-validation-reports 報告 artifact，沒有 Setup／worker／模型產品 artifact。A6 原紀錄的 queued 為當時狀態；本次只追加 README 補註及更新其 manifest hash，已保存的 attempts.json 不改寫，也不複製舊完整 JSON。
- A6 固定基本包／CPU 候選與分類已驗，證據見 [A6 紀錄](docs/development-records/runs/a6-fixed-review-2026-11-17/README.md)；數字沿用 [progress.json](docs/progress.json) 中標示的來源，本輪 A7 程式／工作流尚未修改、測試尚未執行。

## C. 未完成、阻擋與下一步

**PR 12 已合併（7b787d3），合併後 CI 全綠；本輪 A7 開始。** A6 Claude reviewer 無必修項。固定候選仍 8285450，不以合併後 CI 產物替換候選。

| 任務 | 現況／下一步 |
| --- | --- |
| A6／PR 12 | 完成並合併；合併後 Linux、Windows 基本包、CPU、歷史索引與 Pages 均成功。原排隊 run 最終 completed／success，僅報告 artifact，補註不改 attempts.json |
| A7 自有 MIT 對照 | 本輪處理已隨包 MIT 全文與 installed package notice 表的綁定，補完整性及錯誤套件綁定反例 |
| A7 工作流補強 | 以獨立提交改 step env EXPECTED_SOURCE，pwsh 先驗完整小寫 SHA，再使用環境變數；不把 expression 直接插進命令列 |
| A7 分片反例 | broken 清單補少一片與 part 編號越界，維持失敗拒絕條件 |
| A7 收尾 | 更新現況、完整回歸及 PR CI；全通過且無必修項後一般 Merge。完成後先停，由 Claude planner 整體複查大階段 A 與重新規劃剩餘義務 |
| 既有產品門檻 | 完整 SBOM／再散布、乾淨機／人工／GPU仍待；本輪不重排剩餘義務，不交付產品、Release 或 tag |

**平台**：GitHub API 可用；run 43912958713 最終成功，先前排隊／取消回覆保留為歷史，不重送。大型原始日誌留 CI，後續舊嘗試只保存 hash 與 run 編號，不複製完整 JSON。ONNX 繁中缺口、RAM 軟性預算、乾淨機／人工／GPU限制保留。

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
| 2026-11-17 | 使用者指示 | 之後不要再保存重複的舊嘗試完整 JSON，只留 hash 與 run 編號。 |
| 2026-11-17 | 使用者指示 | A7 完成後先停，大階段 A 的整體複查與剩餘義務的重新規劃，交由 Claude planner 處理。 |

接手先列 PR，再讀最新分支 AGENTS.md 與 STATUS.md；PR 12 已合併（7b787d3），合併後 CI 全綠。本輪 A7，完成後先停，交由 Claude planner 整體複查與重新規劃；固定候選仍 8285450。

# 現況

更新：2026-11-17（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| 本輪 main 起點 | **main 已合併 PR 1–11**，`e23d383b7f38ac95c4b883513834abfd8f814600`；A5b／A5c 已由 Claude reviewer 通過 |
| 本輪分支 | `codex/a6-fixed-candidate-20261117`，自己的新分支；沒有推送其他 AI 分支或直接推 main |
| 本輪 PR | A6 [PR #12](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/12) 已建立；最終 CI 與 Merge 結果以 PR 為準，CPU 固定候選尚缺新版審閱實證，現在不可合併 |
| 固定來源 | `8285450226abe1381e6a357e8bd33bff1ad46e0e`；基本包已驗，CPU 重送驗證執行中，PR 暫時 merge 不取代此候選 |

## B. 這個階段完成了什麼

- 首個提交 `d098e2c` 已完成使用者三項要求：現況／next／headline 更新至 main 已合併 PR 1–11、補 A5b／A5c 最終 CI run、D 節不重複摘要。既有 D 原文逐列保留。
- A6 新增固定完整 SHA／乾淨來源檢查、候選指紋、來源重分類與可離線重跑的精簡 metadata。完整來源報告與公開 metadata 使用不同有界容量；缺片／混合來源／改 hash／改候選／提高產品旗標均拒絕。Windows 工作流只新增報告保存，沒有交付產品。
- Windows **基本包固定候選**成功；[證據](docs/development-records/runs/a6-fixed-review-2026-11-17/README.md)及 [基本包整體審閱](docs/a6-source-review.md)已保存。來源分類與指紋離線重現，舊候選分類亦保持一致。新來源的 CPU metadata 尚未取得，不把前輪 CPU 既有驗收成功當作新版工具成功。
- 新版完整 Linux 混合／獨立模組回歸通過，只有既有 ONNX 繁中 expected failure，無跳過；數字只見 [progress.json](docs/progress.json)。保存來源預檢失敗、容量不相容、索引過期與修正後結果。Codex 自我查驗完成可執行範圍，不冒稱新 Claude reviewer。

## C. 未完成、阻擋與下一步

**A6 尚未整體完成**。基本包固定來源與分類已完成；CPU 原 workflow_dispatch 長時間 queued、jobs 空白；重送 43916217757 已開始執行，仍待結果。沒有合併、沒有提高 SBOM／再散布旗標。完整來源、run、artifact digest／期限、原始摘要與接手命令入口見證據 README。

| 任務 | 現況／下一步 |
| --- | --- |
| A1–A5c | 完成；main 本輪起點已合併 PR 1–11，A5b／A5c Claude reviewer 無必修項 |
| A6 固定候選與整體審閱 | 基本包已驗；先查 CPU [43912958713](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43912958713)／[43916217757](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43916217757)，不要盲目重送。成功後取回 metadata、核對固定 SHA、離線重跑及完成 CPU 審閱；失敗則先看 candidate-source-review-error annotation |
| A6 PR／合併 | 最終 head 全 CI 通過、無必修項且本輪候選證據齊備才一般 Merge；不直接推 main、不推別人分支、不刪分支 |
| A7 後續小項（尚未開始） | 自有 MIT 全文已隨包，但未綁入 installed package notice 表；A6 結束後另開 PR 補對照及反例，不忽略 review_reason |
| 其餘再散布 | 基本包優先：wheel 內含第三方來源／版本／原文、Microsoft 逐檔條款、Qt build／替換與靜態連結；CPU 模型／GEOS 另待，不把套件 owner／簽章當權利核准 |
| B 交付／C 實機／E GPU | 仍待門檻及使用者實機驗收，沒有上傳 Setup／worker／模型或建立 Release／tag |

**平台**：GitHub API 可用；CPU 原排程此次 API 與 CLI 狀態回覆矛盾，未確認取消。日誌／artifact 儲存主機仍受限，必要公開 metadata 經 annotation 保存；只保存報告 JSON，不搬產品。Windows 報告有時效，不能依賴未下載附件。ONNX 繁中缺口、RAM 軟性預算、乾淨機／人工／GPU限制保留。

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

接手先列 PR，再讀最新分支 AGENTS.md 與 STATUS.md；本輪 A6，先查 CPU 排程與 PR 最新 CI；固定候選仍 8285450，不重做 A5b／A5c，不把 PR 暫時 merge 當候選。

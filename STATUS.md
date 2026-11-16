# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| main／已完成基線 | **main 已合併 PR 1–8，A4 完成（PR #8）**；A5 起點為 `e87de4b33073e548802e08a7b37c9934429ca65b`。使用者確認 A4 已通過 Claude reviewer 查驗 |
| 本階段分支 | `codex/a5-cpython-components-20261116`，從上述最新 main 另開，沒有推送別人的分支。程式與本機回歸來源為 `2104418` |
| 本階段 PR | [PR #9](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/9)（A5，目標 main）；首輪全部 CI 與逐檔查驗通過，最終文件 head 仍由相同 CI 核對後一般 Merge。即時合併狀態與 merge commit 以 PR 為準 |
| 合併規則 | 一個編號一個 PR；所有 CI 通過且查驗無未解決必修項時，以一般 Merge 合併，不直接推 main、不刪分支、不改寫歷史 |

## B. 這個階段完成了什麼

- **A5 逐檔元件證據已實作**：`scripts/cpython_components.py` 在建置時記錄真正由 Windows CPython 目錄收集的 OpenSSL、libffi、SQLite 檔案，保存來源 hash、PE 檔案版本、官方建置宣告版本、與載入檔 hash 相符的 OpenSSL／SQLite 執行期版本；不是只用同名檔案猜版本。libffi 沒有支援的執行期版本 API，只有宣告時明列 `build-declaration-only`，不拿 ABI 編號當版本。
- `packaging/cpython/windows-3.12.10/` 固定官方 CPython 與外部相依 commit、原文 hash 及來源；完整 OpenSSL／libffi 原文與 SQLite 原始標頭註記逐位元組隨包保存。SQLite 是明列 offset／length 的原文節錄，不假稱保存整份標頭。不同 patch 版／架構不能套用此 profile。
- 原生 manifest 綁定新增清單的 hash，建置後重新驗證版本宣告、原文、逐檔覆蓋與來源指紋；候選清單連回各檔原文，但不因此授予 owner 或核准再散布。基本包與 CPU 共用既有原生來源管線，沒有擴充選配功能。
- **A4 現況已修正**：A4 完成、PR #8 已合併，不再寫等待合併。依本輪明確指示在 A4 證據 README 補充實體檔案與 PYZ 計數口徑；找到 A3 公開摘要的 109 基準並補存。完整逐檔基準未保存，不能證明兩次未對照的檔案集合相同。原版 README／manifest 先另存，原始 CI JSON 不變。
- Linux 混合與獨立模組完整回歸均正常退出，只有既有 ONNX 繁中 expected failure；來源、原始結果與限制見 [A5 紀錄](docs/development-records/runs/a5-cpython-components-2026-11-16/README.md)，現況計數只見 [progress.json](docs/progress.json)。**A5 Windows 基本包與 CPU 已取得原生實證，逐檔查驗通過**，來源與完整公開摘要見 [PR 9 CI 紀錄](docs/development-records/runs/a5-pr9-ci-2026-11-16/README.md)。觀測來自建置解譯器載入的來源 DLL，不冒充 frozen 候選獨立探測；libffi 仍僅建置宣告。

## C. 未完成、阻擋與下一步

**下一個，交給接手 AI：A5b Qt 本體原始碼位置與版本對應**。A5 首輪 Linux、Windows 基本包、Windows CPU、索引 CI 全通過，公開逐檔 annotation 已查驗；PR #9 最終 head 仍須全部通過才一般 Merge。接手先核對 PR 即時狀態與最新 main，不沿用舊 head。

| 大階段 | 任務 | 現況／下一步 |
| --- | --- | --- |
| A 來源與再散布 | A1 模組清單、A2 文件、A3 Qt／自有 MIT 隨包 | 完成（PR #5／#6） |
| | A4 setuptools 排除 | **完成（PR #8，已合併並通過 Claude reviewer）** |
| | A5 CPython 隨附元件逐檔版本／原文 | **完成（PR #9）：本機回歸及 Windows 基本包／CPU 逐檔查驗通過；最終 head／合併狀態見 PR** |
| | A5b Qt 本體原始碼位置及版本對應 | **下一個**；要有來源依據，不能按印象補網址 |
| | A6 固定來源候選、重跑來源分類、整體審閱 | A5／A5b 後，才評估 runtime_sbom_complete；目前保持 false |
| B 測試版安裝包 | 產物證據、驗收表、CPU 元件重新定版及門檻確認 | 未開始，不在門檻關閉前上傳產品 |
| C 乾淨機／人工 | Windows 10／11、離線、四語、中文路徑、修復移除 | 需要使用者或實體 Windows，尚未接受 |
| D 擴充 | 圖片本機 OCR／影音獨立元件 | 等使用者決定，未排入本輪 |
| E GPU | 實卡驗收 | 延後 |

**平台／有期資料**：GitHub API 已恢復；一般沙箱連不到代理時依 runtime 指引用獲准命令，保留代理與 TLS。日誌／artifact 儲存主機仍可能受限，CI 需以公開 annotation 提供必要資料。Windows 報告保留七天、Linux 報告十四天，實際期限／hash 以每次 run 記錄為準；不依賴暫存或未下載附件。這些 PR 暫時 merge 驗證不取代 `cb8f24d` 固定候選，沒有產品發行。

## D. 新增規則與決定

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-16 | 使用者本輪指示 | A4 已由 Claude reviewer 查驗通過；開始 A5，並在同一 PR 修正 A4 完成／main 已合併 PR 1–8 的現況與 next；補充 A4 unresolved_files=109 的計數口徑與基準，找不到寫未保存 |
| 2026-11-16 | 本輪明確授權的保存補註 | 僅對指定 A4 證據 README 追加說明；先保存原版 README／manifest，再更新該 README 的 hash。其他舊證據及原始 CI JSON 不變，不擴大成任意改寫歷史的授權 |
| 2026-11-16 | 既有使用者指示／AGENTS | 各編號一個 PR，全部 CI 與查驗通過即可一般 Merge；不直接推 main、不推別人分支、不 force push 或刪分支 |
| 2026-11-13 | 已確認授權決定 | 自有程式 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 已確認打包決定 | 排除 Qt TLS／來源不明 OpenSSL、CPU OCR 的 OpenCV FFmpeg；VC runtime 取官方來源，影音另行規劃 |
| 2026-11-13–16 | 已確認維護方式 | 現況／歷史分開，數字單一來源，階段完成才整體更新，原文／模型／圖及原始失敗保留；優先基本包，暫緩擴充元件系統 |
| 既有規則 | AGENTS／使用者 | 來源與再散布門檻未關閉前不發 Setup／worker／模型（含產品 artifact）、不建 Release 或 tag；ONNX 繁中、RAM 軟性預算、實機／GPU 限制維持 |
| 2026-11-14–16 | Claude 專用分工 | CLAUDE.md 與 .claude/ 保存其角色與模型；不把工具專用設定視為所有 AI 的規則 |

接手時先列 PR，再讀最新分支的 AGENTS.md 與 STATUS.md；A5 合併後從最新 main 開自己的新分支接 A5b。不要重做 A4，也不要再因舊的 Forbidden 紀錄要求重設已恢復的 API。

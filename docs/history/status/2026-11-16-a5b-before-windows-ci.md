# 現況

更新：2026-11-16（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| main／已完成基線 | **main 已合併 PR 1–9，A4／A5 完成（PR #8／#9）**；A5b 起點為 `c51089a258b820b95af51816e516a05300dfb7c4`。使用者確認 A5 的程式、原文、證據、測試已通過 Claude reviewer 查驗 |
| 本階段分支 | `codex/a5b-qt-source-20261116`，從上述最新 main 另開；未推送別人的分支。A5 本機完整回歸來源仍為 `2104418`，A5b 原始來源為 `bc2f77c`，Qt 摘要接線修正後完整回歸來源為 `5376c99` |
| 本階段 PR | [A5b PR #10](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/10)，目標 main；本機完整回歸與來源查驗通過，原生 Windows CI 執行中。A5 PR #9 已一般 Merge，最終 head `944ef12` 全部 CI 通過 |
| 合併規則 | 一個編號一個 PR；所有 CI 通過且查驗無未解決必修項時，以一般 Merge 合併，不直接推 main、不刪分支、不改寫歷史 |

## B. 這個階段完成了什麼

- **A5b 第一個提交 `c25e3c2` 已完成指定修正**：D 節恢復歷史使用者決定原文；main／next 改為 PR 1–9；A5 CI README 追加最終 head 四個 run，原版先另存、原始 CI JSON 不變。A5c 三項僅列獨立 PR 待辦。
- **Qt 發布來源對應已實作**：官方 Qt supermodule／qtbase 與 PySide／shiboken tag、固定提交、完整 gitlink、原始版本宣告及鎖定 Windows wheel 有來源依據，不再只列「待補」。基本包隨附 `licenses/qt-sources.json`，離線驗證來源並核對實際載入版本；更新中文 Qt 取得方法、原始碼下載及第三方說明範本。限制保留，未核准再散布。
- 已補基本包 controller 的 Qt 報告轉存／annotation 重送，避免摘要只留在子程序日誌；[修正與原始完整回歸](docs/development-records/runs/a5b-qt-ci-forwarding-2026-11-16/README.md)已另存，合成 Windows 觀測僅驗接線。
- Linux 完整混合及獨立模組回歸正常退出，只有既有 ONNX 繁中 expected failure；[來源／原始結果／靜態 wheel 證據](docs/development-records/runs/a5b-qt-source-2026-11-16/README.md)已保存，計數只見 [progress.json](docs/progress.json)。Windows wheel 的 PE 檢查不冒充 Windows 執行；A5b 原生 Windows 觀測尚待本 PR CI。

## C. 未完成、阻擋與下一步

**本輪 A5b：Qt 本體原始碼位置與版本對應**。main 已合併 PR 1–9；A5 最終 head `944ef12` 全部 CI 與 Claude reviewer 已通過。先完成 A5b，再以新分支／獨立 PR 做 A5c；不在 A5b 改動 A5 的 CI 驗收標準。

| 大階段 | 任務 | 現況／下一步 |
| --- | --- | --- |
| A 來源與再散布 | A1 模組清單、A2 文件、A3 Qt／自有 MIT 隨包 | 完成（PR #5／#6） |
| | A4 setuptools 排除 | **完成（PR #8，已合併並通過 Claude reviewer）** |
| | A5 CPython 隨附元件逐檔版本／原文 | **完成（PR #9，已合併並通過 Claude reviewer）** |
| | A5b Qt 本體原始碼位置及版本對應 | 來源對應、本機回歸與靜態 Windows wheel 已驗；本 PR Windows CI 待驗 |
| | A5c A5 驗收補強 | **待辦，獨立 PR，A5b 不處理**；詳見下列三項，Windows CI 全部通過才合併 |
| | A6 固定來源候選、重跑來源分類、整體審閱 | A5b／A5c 後，才評估 runtime_sbom_complete；目前保持 false |
| B 測試版安裝包 | 產物證據、驗收表、CPU 元件重新定版及門檻確認 | 未開始，不在門檻關閉前上傳產品 |
| C 乾淨機／人工 | Windows 10／11、離線、四語、中文路徑、修復移除 | 需要使用者或實體 Windows，尚未接受 |
| D 擴充 | 圖片本機 OCR／影音獨立元件 | 等使用者決定，未排入本輪 |
| E GPU | 實卡驗收 | 延後 |

**A5c 待辦（使用者 2026-11-16 指定，獨立 PR）**：

1. Windows 建置（`GITHUB_ACTIONS` 或 `win32`）時，OpenSSL／SQLite 相關檔案若不是 `matched-runtime-probe`，或有 `probe_error`，`check_bundle_provenance` 應判為不接受，並補反例測試；目前 `scripts/cpython_components.py` 的 `write_inventory` 偵測失敗只記 `probe_error` 而仍可通過，須補強。
2. `tests/test_cpython_components.py` 新增反例：刪除包內 `cpython-original/openssl.txt` 後，`verify_inventory` 必須拒絕。
3. README 或報告註明 `_ssl.pyd`、`_hashlib.pyd`、`_sqlite3.pyd` 等 extension 列的 `observed_version` 是所連結 OpenSSL／SQLite 的版本，不是該檔本身的版本。

這會改變 CI 驗收標準，A5c 的全部 Windows CI 必須通過才合併；A5b 不實作這三項。

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

接手先列 PR，再讀最新分支 AGENTS.md 與 STATUS.md；本輪 A5b，之後獨立 PR 做 A5c，不重做 A4／A5，也不沿用舊 Forbidden 要求重設 API。

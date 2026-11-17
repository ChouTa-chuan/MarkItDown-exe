# 現況

更新：2026-11-17（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | PR 1–18 已合併；A9（PR 18，0c3746d）五項 CI 全成功，經 Claude reviewer 兩輪查驗無必須修正項目 |
| 本輪分支 | `claude/confident-ride-o38ls7`：只記錄使用者決定（OpenSSL 補原文、A10 換手），不屬編號 |
| 下一棒 | **Codex（GPT）從最新 main 開新分支做 A10**（使用者指定）；A9b、A11 待指派 |
| 固定來源 | `8285450226abe1381e6a357e8bd33bff1ad46e0e`（A6）。**不含 A7**，A12 重新固定前不作為交付依據 |

## B. 這個階段完成了什麼

- **A9 基本包 wheel 內含第三方元件目錄**：新增 `packaging/embedded/base-windows.json` 與 `scripts/embedded_components.py`（由 `redistribution_gates.py` 呼叫），涵蓋 A6 base-wheels 全部原生檔。每個內含元件記名稱、版本、版本依據分級（wheel 宣告／執行期觀測／未知）、來源與 repo 內既有授權原文的 hash；查不到的版本一律記為未知，所屬條目保持 open。
  - 事實取自依鎖檔 hash 下載的 Windows wheel（只讀不執行）。reviewer 抽查 numpy 的 OpenBLAS、pypdfium2 的 PDFium、Pillow LICENSE 列出的 12 個程式庫、pandas 的 fast_float 版本，皆與 wheel 一致。
  - 第一輪查驗的必須修正：Pillow 的 `.pyd` 字串顯示內含 raqm、fribidi、libaom、dav1d、libyuv，LICENSE 未列，所以 Pillow 由「證據齊全」退回 open，這些元件記為未知。第二輪查驗無必須修正。
  - `base-wheels` 拆成 10 條 `base-wheels-<套件>`；只有 charset-normalizer、psutil 為 evidence_complete。`base-tesseract-models` 改為需使用者決定（A13）。
  - cryptography 的 `_rust.pyd` 含 `OpenSSL 4.0.3` 字串，表示靜態併入 OpenSSL，但 wheel 沒有附原文。補原文會改變隨包內容，列為待使用者決定（C 節）。
- 以 A6 兩份輸入實跑，三旗標皆 false。完整 Linux 混合與獨立模組回歸通過，只有既有 ONNX 繁中 expected failure、無跳過；數字見 [progress.json](docs/progress.json)。
- 未驗證：PE 匯入表、Windows 實機載入行為、目錄中 upstream 網址是否可連線。

## C. 未完成、阻擋與下一步

**整體規劃**（每個編號一個 PR，CI 通過且查驗完成即合併）

| 大階段 | 編號與任務 | 狀態 |
| --- | --- | --- |
| A 關閉來源與再散布缺口 | A1–A7（PR 5、6、8–13） | 完成 |
| | A8 義務登記表與旗標判定規則：新增 `packaging/redistribution/obligations.json`（分 base／cpu，每項含 id、對應的 review_reason 或檔案群、所需證據、狀態、使用者決定出處）、`scripts/redistribution_gates.py`、測試與 `docs/redistribution-gates.md`（三旗標定義；寫明 `unresolved_files` 是「無 wheel 擁有者」的計數，不是要歸零的指標）。旗標改由條目推導，不再只是常數。順帶修正 `scripts/license_inventory.py` render() 兩句過時文字（「Tesseract 執行檔尚未隨 Windows 包發佈」「完整 Windows 二進位檔尚未建置」）並重產 `third-party.md`。驗收：以 A6 的 base／cpu source-review 為輸入，每個原生檔與 review_reason 各對到恰好一個條目，未對到者拒絕；標「使用者已核准」卻無決定出處者拒絕；現況輸出三旗標皆 false 並列出未關閉條目；不動 spec、打包內容與既有計數口徑；限制為單一 JSON 加一支檢核腳本，避免過度設計 | 完成（PR 15） |
| | A8b 義務登記檢核補強：決定出處限固定存檔 D 節的使用者決定列、反向檢查 stale selector、release_ready 綁定 `stage-c-` 證據、結構封閉與 schema 2（使用者決定插入於 A9 之前） | 完成（PR 16） |
| | A9 基本包 wheel 內含第三方元件目錄（非 Qt、非 Microsoft）：元件名稱、版本、版本依據分級、來源與隨包原文；未知者保持 open | 完成（PR 18） |
| | A9b cryptography 內含 OpenSSL 原文隨包：A9 查得 `cryptography/hazmat/bindings/_rust.pyd` 有 `OpenSSL 4.0.3` 字串（靜態併入），wheel 未附原文。使用者已同意補：以固定上游來源（OpenSSL 對應版本標籤的 LICENSE 原文，記來源網址、版本依據與 sha256）加入隨包授權資料，接到既有原文管線與目錄（`packaging/embedded/base-windows.json` 的 openssl 元件），補缺檔／改內容反例；版本仍須有依據，不能只憑字串就標成 wheel-declared（可新增分級需先說明）。會改變安裝包內容（使用者已同意） | 待開始（使用者已同意；排在 A10 之後，與 A10 都會改 `obligations.json`） |
| | A10 Microsoft 執行期逐檔對照（基本包 14 檔：根目錄 3、PySide6 5、shiboken6 4、numpy.libs 與 pandas.libs 各 1 個改名的 msvcp140）：收集來源、PE 版本、簽章、與官方 Redist 同名檔雜湊比對、適用條款文件；改名複本單獨標示；review_reason 改由登記表狀態控制。條款是否允許由使用者在 A13 決定 | **可開始** |
| | A11 Qt 內含第三方（qt_attribution）、建置資訊（`QLibraryInfo.build()` 等）與「可替換 Qt」驗收（hosted Windows CI：替換 DLL 後可啟動、移除 Qt6Core 後啟動失敗，標明非實體機）；更新 `qt-lgpl-notice.md`。LGPL 做法是否足夠由使用者在 A13 決定 | **可開始** |
| | A12 以 A8–A11 完成後的 main 重新固定候選，產出基本包出口報告；`runtime_sbom_complete` 依 A8 定義推導，不得人工改寫。**順帶整理 `docs/progress.json`**：把 `previous_*` 等舊紀錄鍵搬到 `docs/history/`（搬移，不刪除內容；使用者已同意）。**不做打包減量**（使用者決定） | 待開始 |
| | A13 使用者確認基本包門檻（原 B4 前移）：Microsoft 各複本、Qt LGPL 做法、libffi 僅建置宣告、版本未知的內含元件、Tesseract 與 tessdata、品質限制揭露文字。協調者不得代為決定 | 需使用者 |
| | A14 CPU：flatbuffers、rapidocr 原文綁定（接線 `prepare_worker_assets.py`；錯綁與缺檔反例） | 待開始（B1 之後） |
| | A15 CPU：PP-OCR 模型來源、版本、雜湊與授權原文（不以套件的 Apache 宣告代替）；授權範圍需使用者確認 | 待開始（B1 之後） |
| | A16 CPU：Shapely／GEOS（LGPL）與 CPU wheel 內含元件（沿用 A9 格式），CPU Microsoft 6 檔（沿用 A10）；LGPL 做法需使用者確認 | 待開始（B1 之後） |
| | A17 CPU：查明 setuptools、pip、pyinstaller 等建置工具是否真的進了 worker；若要排除屬打包變更，需使用者同意 | 待開始（B1 之後） |
| B 測試版安裝包 | B1 基本包以 CI artifact 產出（附提交、版本、雜湊、隨包原文、限制），來源為 A12 的固定候選；B2 驗收表；B3 CPU 元件重新定版；B4 使用者確認測試版結果 | 待開始 |
| C 乾淨機與人工驗收 | C1 乾淨 Windows 10／11 安裝與離線首次啟動；C2 四語、中文路徑、修復移除；C3 人工操作 | 需使用者或實體 Windows |
| D 功能擴充 | D1 圖片檔走本機 OCR；D2 影音獨立選配元件 | 等使用者決定 |
| E GPU | 實卡驗收 | 延後 |

**執行順序**：A8 → A8b → A9、A10、A11（互不相依，各自一個 PR，可交給不同 AI，但都在 A8 之後；A8 不可與它們合併）→ A12 → A13 → B1。CPU 的 A14–A17 排在基本包 B1 之後（使用者決定）。

**大階段 B 的進入條件**

- B1：A8–A13 完成，且基本包 `redistribution_approved` 經使用者決定。CPU 不必先關閉。
- 可與 A 平行、但不產生可交付產物的準備：B1 workflow 設計（只輸出提交、版本、雜湊、原文清單，不上傳 Setup）、B2 驗收表草稿、限制說明文字。
- B3：A14–A17 完成並經使用者確認。
- `release_ready` 在大階段 C 的乾淨機與人工驗收之前維持 false。

**A7 查驗留下的小問題**（已在 A8 第一個提交處理）：兩個 Windows workflow 的 pwsh 預檢共 14 處改用 `-cmatch '^[0-9a-f]{40}\z'`（`-match` 不分大小寫，`$` 允許結尾換行；後面的 Python 檢查會擋，沒有安全缺口）；`tests/test_candidate_review.py` 再加一個「只有越界」的反例（保留其餘各片、把最後一片改成 part=N+1）；`progress.json` 的 m5 描述與 `a7_mit_notice.status` 更新；CHANGELOG 補一句 `full_regression.baseline_environment_identical` 欄位移除的原因（或還原）。

**A9、A10、A11 共同注意事項**（A8 查驗提出）：三者平行修改 `packaging/redistribution/obligations.json` 的不同條目。各自的 PR 要把要在 A13 由使用者決定的條目改為 `requires_user_decision: true`（base：`base-microsoft`、`base-qt`、`base-tesseract-models`；cpu 的 GEOS 與 rapidocr 模型條目留給 A15、A16）。元件細節（名稱、版本、版本依據分級、來源、隨包原文）放在另一個由 `evidence[]` 以路徑加 hash 引用的目錄 JSON，不塞進登記表；原生檔仍只對到一個條目。合併順序依完成先後，後合併者先把 main 合併進自己的分支並重跑 `redistribution_gates.py` 兩個 profile 再合併。

**等使用者決定**

- 目前沒有。cryptography 的 OpenSSL 原文已由使用者決定補上（A9b）。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據。artifact 儲存主機常被本環境網路政策擋下，需要的資料請讓 CI 寫進公開摘要。

**既有限制**：ONNX 繁中缺口、RAM 軟性預算、Windows 實機／GPU 未驗收；沒有產品交付、Release 或 tag。

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
| 2026-11-17 | 使用者決定 | 採用 Claude planner 的大階段 A 重新規劃：A 續編 A8–A17，使用者確認門檻由原 B4 前移為 A13（B1 之前）；A12 不做打包減量；A12 整理 `docs/progress.json`，把舊紀錄鍵搬到歷史目錄（搬移不刪除）；CPU 的 A14–A17 排在基本包 B1 之後；A8 交給 Codex（GPT） |
| 2026-11-17 | 使用者本輪指示 | A8 限制為單一 JSON 加一支檢核腳本，不動 spec、打包內容與既有計數口徑；三旗標現況仍為 false。A8 完成後先停，回報使用者。 |
| 2026-11-17 | 使用者決定 | 在 A9 之前插入 A8b（A8 檢核補強）；GPT 用量已滿，A8b 改由 Claude coder 接手 |
| 2026-11-17 | 使用者決定 | Claude 角色模型改為：規劃者 `planner` 用 `claude-opus-5-5`、編程者 `coder` 用 `claude-haiku-5-5`、查驗者 `reviewer` 用 `claude-sonnet-5-5`；協調者（主對話）預設 `claude-opus-5-5`；推理強度維持中。原因：Fable 5.2 在使用者方案中無法使用。取代 2026-11-16 planner 用 `claude-fable-5-2` 的設定 |
| 2026-11-17 | 使用者決定 | cryptography Windows wheel 靜態併入的 OpenSSL 要補授權原文隨包（列為 A9b，會改變安裝包內容）；A10 換手交給 Codex（GPT） |

接手先列 PR，再讀最新分支的 AGENTS.md 與 STATUS.md。Codex 從最新 main 開自己的新分支做 C 節的 A10（見 C 節共同注意事項；`obligations.json` 只改 Microsoft 條目並把它設為 `requires_user_decision: true`）；完成後依 AGENTS.md 更新現況、開 PR，CI 通過且查驗完成即可一般 Merge。A10 完成後先停，回報使用者。

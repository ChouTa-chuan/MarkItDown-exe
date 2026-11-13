# 專案維護約定

2026-11-13 改寫：目的是降低每一輪的閱讀與維護成本。先前「每次更新都維護全部文件」「先讀交接指南」的規定自此停用。

## 開工

- **必讀只有兩份**：本檔與根目錄 [STATUS.md](STATUS.md)。其他文件需要時才查。
- **先看 PR，不要只看 main。** PR 會累積到較大的階段才合併，main 可能落後好幾個階段，連上面的規則與說明都是舊的。接手時先列出開啟中的 PR 與遠端分支，切到最新的工作分支（使用者指定的，或相疊 PR 的最上層），讀**該分支**的這兩份檔案；判斷不出哪個最新才請使用者指定。步驟與常見錯誤見 [docs/ai-handoff-workflow.md](docs/ai-handoff-workflow.md)。
- 要追溯過去的做法、失敗或決定，查 [docs/history-index.md](docs/history-index.md) 找到那一筆再打開；不要整份翻閱開發紀錄。
- PROJECT_HANDOFF.md、docs/development-records/README.md、docs/development-status.md、docs/validation-results.json 是背景與歷史，保留但不再更新、也不列為必讀。
- 環境、工具權限與網路政策每個 session 自行核對；別的 session 裝過或下載過的東西不代表這裡也有。

## 分支與提交

- 一律在工作分支作業並同步 GitHub，獨立工作使用新分支；可自行提交、推送自己的分支及建立 PR。**不直接推送 main，合併由使用者指示。**
- 不強制推送、不刪除分支或標籤、不改寫歷史；一個提交只做一件事。不推送別人的工作分支。
- 新工作從最新的工作分支開新分支，不從落後的 main 開；PR 目標仍設為 main（CI 只在目標為 main 的 PR 執行）。疊在未合併 PR 上的工作，要在 STATUS.md 與 PR 寫明父分支與合併順序。
- 不把環境秘密、快取、venv 或個人文件加入版本控制。

## 文件怎麼維護

- **數字只寫一處**：測試數、里程碑進度、候選檔案數只記在 docs/progress.json；其他文件用連結引用，不重抄。改了它就執行 `python scripts/build_progress.py`。
- **小修**（修錯、調整文件、補測試）：只在 CHANGELOG.md「更新中」記一行。
- **階段完成**（一個 PR 可供合併、里程碑子項關閉，或有新的 Windows 驗證結果）才做整體更新：
  1. 把目前的 STATUS.md 複製到 `docs/history/status/YYYY-MM-DD-主題.md`，再改寫 STATUS.md。
  2. 更新 docs/progress.json 並重建進度頁。
  3. CHANGELOG.md 記一段：變更、相對前版差異、驗證、未完成事項。
  4. 執行 `python scripts/build_history_index.py` 重新產生索引。
- STATUS.md 固定四節：A 分支與 PR、B 本階段完成事項、C 未完成／阻擋／下一步、D 新增規則與決定。沒有內容的欄位寫明原因，不留空。保持精簡，沒有硬性大小上限。
- docs/history-index.md 由腳本產生，不手動編輯；測試會檢查它是否過期。
- 依實際證據更新進度，不為了湊更新而提高勾選。沒跑的測試寫「未執行」，沿用舊結果要標明來源提交。

## 證據

- 既有的 docs/development-records 原地保留，不搬移、不刪除、不改內容。
- **新證據**：repo 內只放一個小目錄，含 README.md（做了什麼、結果、限制）與 manifest.json（日期、來源提交、結果、檔案雜湊，可加 `keywords` 供索引查找）及必要的小型結果檔。原始日誌與大型報告留在 CI 執行紀錄，於 README 記下 run 編號、artifact 雜湊與到期日。
- 有時效且之後無法重建、後續工作又確實需要的原始檔，可以例外保存，並在 README 說明理由。
- 原始失敗要留紀錄；不把模擬、跳過或預期失敗列成通過。不加入使用者真實文件或環境秘密。

## 程式

- 使用繁體中文說明。自有程式的新模組、重要契約及複雜流程附中文註解，解釋責任、限制及設計原因，不逐行重述程式。
- 修改到的檔案，順手把用分號擠在同一行的敘述拆開；不為此專門重寫未動到的檔案。
- 程式版本以 pyproject.toml 為準，架構文件版本另計；目前採用 docs/architecture-guide.md v0.4。更新版號不代表已產生安裝包、tag 或 Release。
- vendor/markitdown、第三方授權原文及公開測試樣本保持來源與雜湊；若確須修改上游，以獨立變更及回歸證據處理。
- 架構圖更新時，在 docs/architecture/versions 新增快照並維護 docs/architecture 的索引與 snapshots.json；既有快照保持固定。
- 依變更範圍選擇驗證：純文件改動檢查連結與索引即可；程式變更跑相關測試，階段完成前跑完整回歸。新增或移除測試時，同步 `.github/workflows/linux-regression.yml` 的 `EXPECTED_TESTS`。

## 優先順序與界線

- 先讓基本包可交付；暫不擴充選配元件系統與驗收矩陣，除非使用者另有指示。
- 刪除檔案、更動授權、升級大版本相依套件、更改打包方式，須先取得使用者同意。
- 必要授權與再散布門檻未關閉前，不對外上傳 Setup、worker 或模型（包含 CI artifact 形式）。未另有指示時不建立 Release、預發布或 tag，也不觸發舊的手動發行流程（windows-build.yml）。PR 或 workflow_dispatch 觸發的驗證流程屬驗證，不是發布。
- 保存品質限制：ONNX 繁體已知缺口、Windows／GPU 未實機驗收、RAM 為軟性預算。
- 使用者的新指示優先於本檔；規則改變時更新本檔並在 STATUS.md D 節記下日期與來源。不藉由修改文件擴大授權。

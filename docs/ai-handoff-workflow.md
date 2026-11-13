# AI 輪替工作流

流程版本 2.0｜2026-11-13（台北）。給同事、Claude、Codex 或任何新的 AI session 輪替接手時參考。**這份是說明，不是開工必讀**；必讀只有 [AGENTS.md](../AGENTS.md) 與 [STATUS.md](../STATUS.md)，規則以 AGENTS.md 為準。

版本 1.0 由 Codex 在分支 `codex/ai-handoff-workflow-20261112` 提出（工作流文件、手寫交接索引、每次另存的交接紀錄）。2.0 保留它的四組交接資料與「不能只看 main」的原則，做法改為單一現況檔與自動索引，以降低每一輪的閱讀與維護成本。

## 1. 最重要的一件事：看 PR，不要只看 main

這個專案的工作都在分支與 PR 上進行，擁有者會累積到較大的階段才合併。**`main` 可能落後好幾個階段**，上面的說明文件、規則與進度網站也可能是舊的。只讀 `main` 就開工，會照舊規則重做已經完成的事。

接手時依序做：

1. **列出開啟中的 PR 與遠端分支**（GitHub 的 PR 清單，或 `git ls-remote origin`）。
2. **找出最新的工作分支**：使用者有指定就用指定的；沒有指定時，PR 之間若是一個疊一個，取最上層那一個。判斷不出來才問使用者。
3. **切到那個分支，讀它的 AGENTS.md 與 STATUS.md。** STATUS.md 的 A 節列出所有 PR、彼此的相疊關係與合併順序。
4. 核對 STATUS.md 說的狀態與實際是否一致：PR 是否仍開啟、CI 是否通過、分支最新提交是否就是 STATUS.md 描述的那個階段。不一致時以實際為準，並在自己的階段更新 STATUS.md。
5. **新工作從最新的工作分支開新分支**，不從 `main` 開。PR 的目標仍設為 `main`（CI 只在目標為 main 的 PR 上執行），並在 PR 說明寫清楚疊在哪個 PR 之上、合併順序。

常見的錯誤與後果：

| 錯誤 | 後果 |
| --- | --- |
| 只 clone `main` 就開始 | 看不到未合併的規則與成果，重複工作或與其衝突 |
| 把某個 PR 的「可合併」當成「已合併」 | 以為 `main` 已有那些內容 |
| 新分支從 `main` 開 | 少了前面階段的程式與規則，之後合併會衝突 |
| 自行合併 PR 或直接推 `main` | 違反規則；合併只能由使用者做或明確指示 |
| 推送到別的 AI 的分支 | 覆蓋或混入他人的工作；只推自己的分支 |

## 2. 每個階段要留下的四組資料

全部寫在 STATUS.md，欄位固定，沒有內容也要寫明原因：

- **A. 分支與 PR**：目前有哪些 PR、各自的分支、相疊關係、合併順序、CI 狀態，哪一個是最新的。
- **B. 這個階段完成了什麼**：實際完成的事與範圍；測試結果指向 `docs/progress.json`，不重抄數字。沒跑的驗證寫「未執行」。
- **C. 未完成、阻擋與下一步**：等使用者決定的事、平台或權限阻擋、有期限的資料；下一個可直接做的動作與完成條件。
- **D. 新增的規則與決定**：日期、來源（使用者指示／同意／待確認）、內容。

PR 說明使用同樣四節（`.github/pull_request_template.md`）。

## 3. 收工步驟

階段完成（一個 PR 可供合併、里程碑子項關閉，或有新的 Windows 驗證結果）時：

1. 跑與變更範圍相稱的驗證；程式變更在階段結束前跑完整回歸。
2. 把目前的 STATUS.md 複製到 `docs/history/status/YYYY-MM-DD-主題.md`，再改寫 STATUS.md。
3. 更新 `docs/progress.json` 並執行 `python scripts/build_progress.py`。
4. CHANGELOG.md 記一段。
5. 執行 `python scripts/build_history_index.py`。
6. 提交、推送自己的分支、開 PR（目標 `main`），確認遠端分支與本機一致。
7. 回覆使用者：PR 連結、完成與驗證、未驗證的部分、等他決定的事。

小修（修錯、調整文件、補測試）只需要在 CHANGELOG「更新中」記一行。

## 4. 舊做法與新做法的對應

| Codex 1.0 | 現在 |
| --- | --- |
| `docs/handoffs/TEMPLATE.md` 每次另存一份交接紀錄 | 直接改寫 `STATUS.md`；舊版存到 `docs/history/status/` |
| `docs/handoffs/README.md` 手寫交接索引 | `docs/history-index.md`，由腳本自動產生，測試與 CI 檢查是否過期 |
| 每次交棒同步交接指南、CHANGELOG、開發紀錄、進度資料 | 階段完成才更新 STATUS、progress.json、CHANGELOG；交接指南與開發紀錄不再更新 |
| 必讀：AGENTS、交接指南、工作流、交接索引、最近交接 | 必讀：AGENTS、STATUS |
| 測試數等數字寫在每份交接 | 數字只在 `docs/progress.json` |

`codex/ai-handoff-workflow-20261112` 分支保留在遠端作為紀錄，不需要合併。

## 5. 給使用者：交給下一個 AI 時怎麼說

> 請接手 ChouTa-chuan/MarkItDown-exe。先列出開啟中的 PR，切到最新的工作分支（不是 main），讀該分支的 AGENTS.md 與 STATUS.md，從 STATUS.md C 節的下一步開始。完成後依 AGENTS.md 更新現況、推送自己的新分支並開 PR；不直接推送或自行合併 main，也不要推送到別人的分支。

如果知道分支名稱，直接指定最省事，例如「請接手分支 `claude/license-and-openssl-cleanup`」。

## 6. 修改這份工作流

發現缺少步驟時，在自己的工作分支修改本檔與 AGENTS.md，於 STATUS.md D 節記下日期與來源，並更新下表。使用者的新指示優先；不藉由修改流程擴大授權。

| 版本 | 日期 | 來源與變化 |
| --- | --- | --- |
| 1.0 | 2026-11-12 | Codex 依使用者要求建立四組交接資料與輪替流程（在 Codex 分支，未合併） |
| 2.0 | 2026-11-13 | 使用者同意改為單一現況檔＋自動索引；新增「看 PR 而非只看 main」的接手步驟，因為 PR 會累積到較大階段才合併 |

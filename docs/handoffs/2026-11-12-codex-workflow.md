# 階段交接：AI輪替工作流與固定交接格式

日期／時區：2026-11-12（Asia/Taipei）  
交接者：Codex  
適用流程版本：1.0  
前一份交接：本格式首份；前階段見[PR 1 CI紀錄](../development-records/runs/pr1-ci-first-run-2026-11-12/README.md)與[專案指南](../../PROJECT_HANDOFF.md)。

## A. 工作分支與 PR

| 欄位 | 本次資料 |
| --- | --- |
| Repo | `ChouTa-chuan/MarkItDown-exe` |
| 工作分支 | `codex/ai-handoff-workflow-20261112` |
| Base 分支／SHA | `claude/confident-ride-o38ls7`／`dfce67563bd684a376c96e81d26de7a1e011c067` |
| PR 連結／狀態 | 本次PR尚未建立：此session無可用GitHub連接器，網路政策未允許GitHub API；[建立文件PR（已填base／head）](https://github.com/ChouTa-chuan/MarkItDown-exe/compare/claude/confident-ride-o38ls7...codex/ai-handoff-workflow-20261112?expand=1)只是比較／建立入口 |
| 父 PR／依賴及合併順序 | [PR #1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1)仍open，目標main。本文件分支承接其head；先將文件PR審入父分支，再由使用者決定PR #1合併。若父PR先合併，重新核對base與差異後再決定如何移入文件改動 |
| 主要內容提交 | 收工補記見本紀錄後續提交；最後純交接提交由Git歷史／最終回覆核對 |
| 推送／未提交狀態 | 撰寫此初稿時尚未推送；收工後補記實際結果，不代表已合併main |

本次使用獨立worktree，不修改另一AI的分支。建立分支時main為`2e066313f7a318fd5f9bde364794bceaccb46fa8`；父分支為上表dfce675。內容差異應以父分支比較，不能把父PR的11筆提交當成本次新增。

## B. 完成事項、測試結果及對應提交

- 新增[工作流1.0](../ai-handoff-workflow.md)、[交接範本](TEMPLATE.md)、[索引](README.md)與[PR範本](../../.github/pull_request_template.md)。固定四組資料、指定分支接手、內容／測試source及CI merge SHA、證據期限、未完成與第一個動作。
- 更新AGENTS、PROJECT_HANDOFF第12／13節、首頁入口、CHANGELOG及開發紀錄；新AI可以依已確認指示維護工作流版本與欄位，不需依賴完整聊天紀錄。
- 純文件改動，未更動程式、測試、CI執行流程、打包、授權、模型、進度資料或架構圖；沒有合併PR #1，沒有發布產品或雲端環境設定。

| 驗證 | Source SHA／CI merge SHA | 環境與命令／run連結 | 結果／真正exit | 證據路徑／hash／到期 |
| --- | --- | --- | --- | --- |
| 本次文件檢查 | 父提交dfce675加本次工作樹；主要內容提交見A組 | Linux／Python 3標準函式庫；本次新增相對連結存在性、四組欄位、入口、快照hash及受保護路徑差異；`git diff --check` | PASS，檢查程序exit 0；10份Markdown、36個新增相對連結、4組欄位、28份架構快照hash通過；diff check exit 0 | 本紀錄及Git差異；無有期artifact |
| 產品回歸／Windows／OCR／GPU | 未執行，無本次測試source或merge SHA | 本次只有文件變更，未觸發原生建置或完整回歸 | 未執行，不將既有698項當成本次執行 | 前次證據見下段 |

既有證據：PR #1 CI以`cd14fe7da32042859d9210a29c041b90f5af7e8b`對應的PR暫時merge執行，Linux 698 run／697 pass／0 failure／0 error／0 skip／1 ONNX繁中expected failure，45獨立模組全部exit 0；兩條Windows流程Success，精確merge SHA需讀其原始報告，不猜測。證據連結與hash見[原紀錄](../development-records/runs/pr1-ci-first-run-2026-11-12/README.md)。原候選source仍為`cb8f24d`，不能被本次文件或PR合併測試取代。

應用程式0.19.1／架構0.4，里程碑7/12不變（C03 3/4、C04 2/4、C09 3/4、C11 2/5）。固定進度網站由main部署；本次分支文件不等於已更新網站。沒有Release、tag、Setup或worker／模型發布。

## C. 未完成事項、阻擋與下一步

| 優先順序 | 工作與第一個動作 | 狀態／阻擋原因 | 預期產物與完成條件 |
| --- | --- | --- | --- |
| P0 | 核對本分支遠端head與交接紀錄，再用A組入口建立文件PR | 程式碼已允許分支提交／PR；本session無可用API，未建立PR，不需因此停止其他已授權工作 | PR以claude分支為base，只含本次文件差異；不直接推main、不自行合併PR #1 |
| P1（有期限） | 在可用GitHub工具環境下載PR #1兩份Windows完整報告、驗hash，另存新run並記錄來源／merge SHA | 舊報告已保存；新報告尚未下載，期限2026-11-19；是否可下載依新session工具核對 | 原位元組／hash／保存期限明確，不覆寫cb8f24d候選證據、不下載或發布未核准產品本體 |
| P2 | 讀來源分類與Windows工作流程，提出或實作系統DLL來源路徑／簽章／版本及Python封存成員的證據採集 | 可另開分支繼續不改打包方式的證據工作；讀當前head，避免重做其他AI的新提交 | 基本49／CPU47個candidate或gap逐項有可追溯證據；未證實項維持待辦，不以名稱猜來源 |
| 決策相依 | 審閱既有授權提案與三項打包調整 | 等使用者決定MIT／著作權人／早期提交權利歸屬；排除Qt TLS、OpenCV FFmpeg及改用官方VC runtime仍為提案 | 確認後才改授權或打包；PR #1合併時機也由使用者決定 |

有期報告：Windows base run `43152427580`／artifact `13915870195`；CPU run `43152427554`／artifact `13915590985`，皆2026-11-19到期。hash及原CI連結在[前紀錄](../development-records/runs/pr1-ci-first-run-2026-11-12/README.md)。

使用者目前不必補貼另一AI完整回覆；指定此分支或PR即可。授權、打包與合併的待決事項沒有因本次工作獲准。工具能力足夠的下一位可建立文件PR、保存報告及進行證據採集，不必等所有決策才繼續。

## D. 新需求與工作規則

| 日期／來源 | 已確認指示或待定提案 | 影響與已更新文件 |
| --- | --- | --- |
| 2026-11-12／使用者本次明確要求 | 每次告一段落保存分支與PR、完成／測試與提交、未完成／阻擋／下一步、新需求／工作規則；納入工作流與交接指南，讓新AI能持續維護 | 工作流1.0、AGENTS、PROJECT_HANDOFF第12／13節、統一範本／索引及PR範本 |
| 2026-11-12／既有已確認規則 | 新分支＋PR、不直接推main；合併另行指示；中文說明、保存證據與歷史架構圖 | 沿用父分支AGENTS，沒有擴大權限；後續AI更新流程需記錄來源／版本／影響 |
| 既有待定提案 | MIT及權利歸屬、三項打包調整、PR #1合併時機未確認 | 保持待定，參閱PROJECT_HANDOFF及授權提案，不能把CI成功或文件更新當成批准 |

## 可直接轉交的一句話

> 請接手分支 `codex/ai-handoff-workflow-20261112`，先讀該分支AGENTS.md、PROJECT_HANDOFF.md及docs/handoffs/README.md最新交接，依C組繼續已授權工作；完成後依同一流程新增交接、推送自己的工作分支並提供PR，不直接推送或自行合併main。

## 同階段收工補記（2026-11-12）

- 主要內容提交：`ebd2f75a554c1ac08f62568505029f255a8bf6fc`。此提交已成功推送至本次工作分支，推送exit 0；上方A組保留初稿狀態，此處為收工更新。
- 文件檢查結果如B組：10份Markdown／36個新增相對連結／4組欄位／28份快照hash，程序及diff check均exit 0。沒有本次產品CI或原生測試結果。
- 寫此補記時僅本檔有待提交的收工補記；最後純交接提交與實際遠端head以Git歷史及最終回覆核對，不填循環SHA。父分支及main未推送、未合併；本次PR仍未建立，使用A組指定base／head入口。

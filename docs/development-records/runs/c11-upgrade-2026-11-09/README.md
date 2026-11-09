# 基本包真跨版本升級與明確回復實測

2026-11-09（台北），程式 **0.16.0**、架構0.4。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42557368030)（990e600）成功：基本資料夾10項、安裝後app10項、安裝／同版修復／移除6段；基本包跨版生命週期 **11/11**。前版原source固定43cf811（0.15.0），以原controller／spec獨立建置及原installer初裝，沒有修改新版payload的版本字串假造舊版。

原0.15安裝後 → 損過期檔／catalog拒絕 → 新增路徑未知檔衝突拒絕 → 真Windows junction拒絕／不穿透 → 改安裝位置拒絕 → 真升級0.16 → 拒絕未指定降版 → 用「新相容安裝器＋真正0.15 payload」明確回復 → 再升級0.16 → 移除。原版、升級後及回復後app各10項通過，四語掃描、中文／CLI／故障保護與Qt正常退出均保留。新版自檢app_version直接讀真正執行的distribution metadata；各版本catalog全hash核對、過期檔與登錄／捷徑及合成外部settings／model／SQLite／output／cache／未知文件保留皆通過。

此為**基本profile、hosted runner、已知兩個build之間的跨版重新安裝與明確回復**。原0.15 installer沒有新降版／catalog保護，回復必須用本輪新相容installer；原版與相容Setup分開生成並在完整artifact留hash。這不是安裝中斷時自動交易回滾，也不是各profile相容、無Python乾淨機／完整離線首次流程、人工UI／標準帳戶、真實使用者資料遷移或GPU驗收。原C11第二項將基本包與各profile拆開，四項細分成五項；已完成基本包，**C11為2/5、完整7/12、歷史19/25**。

永久保存公開原頁／完整短診斷、run／commit／catalog與工具hash、固定官方授權原文，以及明確推導的檢核索引。原文hash與當次runner完全一致；授權文字source commit不代表compiler binary精確建置source或再散布核准。完整需登入CI報告／catalog／三份Setup hash／Windows截圖仍七天保留，未下載即不宣稱永久封存；binary不入庫，也沒有Setup下載、tag或Release。

第一次CI在Inno編譯時失敗，後改官方RemoveBackslashUnlessRoot重驗；[原始失敗](../c11-upgrade-attempt1-2026-11-09/README.md)固定保存，不倒填歷史。

第二輪的真正Windows app例外未能由公開診斷取得；本地確認空前版dist-info在舊項先列舉時可遮蔽版本，因此加入已知空目錄清除與未知內容拒絕，並固定主要錯誤步驟，再由本輪真正Windows重驗。[第二輪失敗與候選修正](../c11-upgrade-attempt2-2026-11-09/README.md)保留，不倒填為已取得原錯誤全文。

本地新增11／相關165，33模組579隔離（578通過、1既有ONNX繁體品質預期失敗）；最後修正以165相關及579完整隔離回歸覆蓋。[最終本地原始紀錄](../c11-upgrade-attempt2-2026-11-09/README.md)。Linux混合teardown仍未定位，品質門檻／GPU／RAM軟預算及最終發行門檻保留。下一步各profile相容與中斷恢復、乾淨Windows離線首次流程及人工UI驗收。

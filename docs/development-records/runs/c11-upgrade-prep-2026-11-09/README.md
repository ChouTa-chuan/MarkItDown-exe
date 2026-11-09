# 基本包跨版本升級／明確回復準備

2026-11-09（台北），程式0.15.0 → **0.16.0**、架構0.4。新增9項，Linux相關163/163；33模組577隔離正常退出（576通過、1既有ONNX繁體品質預期失敗）。這些不等於Windows安裝驗收，C11仍1/4／完整導入7/12。

新增可信source catalog產生的Inno規則，沿用原安裝位置，拒未知版本、catalog改寫、reparse point及未指定降版；過期檔只刪前版已列且原hash相同者，不遞迴清除文件。新版自檢顯示實際app_version。CI將固定43cf811（真正0.15.0）原controller／spec獨立建置，先真裝原版，再升級目前版、拒絕未指定降版、用新相容installer配真正前版payload明確回復，再升級與移除；各階段跑10項installed app檢查及合成資料保留。

原0.15 installer無新保護，回復須用明確標示的新相容安裝器。這是已知build間的跨版本重裝，不提供安裝中斷時自動交易回滾；完整profile／無Python乾淨機／離線首次流程／標準帳戶與人工UI仍待。舊手動workflow不動，Setup只在CI工作目錄，不建立Release或正式下載；Windows結果另追加。Linux混合native teardown問題未宣稱修復，品質目標及GPU／RAM軟預算限制保留。

最後補上新路徑未知檔衝突與逐目標父鏈reparse保護，新增Windows實際junction控制；相關163與新增9再驗均通過。完整577在較早修訂逐模組正常結束，最後變更以163相關回歸覆蓋，非宣稱混合程序問題已修復。進度頁首次Chromium因沙箱setsockopt被拒，保留原始失敗後在外層成功驗證／截圖，沒有更改網路或測試判準。

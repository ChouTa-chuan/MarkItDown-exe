# Windows測試安裝包準備盤點

2026-11-11（台北），程式0.19.1、架構0.4。重新連線後唯讀查得[同來源ad7d227的基本包CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42943978257)成功，公開原頁與六份可解析摘要保存。不是本次重新建置，也沒有再觸發發行流程。

基本app10、安裝／同版修復／移除6、真0.16.0→0.19.1跨版11，以及三停點普通Setup明確續修3/3（每案app10）均接受。CI自有暫存清理3/3、清1／剩0，真鎖檔拒絕與未知檔保留；scope仍ci-owned-fault-installer-artifacts，普通Setup沒有通用暫存清理。hosted runner預裝Python，不當乾淨機或人工UI完成。

本次離線驗CPU profile 24／5、基本profile Linux runtime38／build47及Windows runtime38／build49，原notice／metadata對照均通過；授權上位清單58套件／214份原文或metadata hash驗證通過。這些是靜態閉包／原文證據，不代替最終原生再散布審核、實際各bundle SBOM或應用程式公開授權決策。

[第一版測試包缺口與接續順序](../../../windows-test-build-readiness.md)另列。本次沒有跑本版完整回歸，也沒有重跑既有162項；162項仍引用原準備紀錄。環境可用性確認與瀏覽器檢查不當產品功能測試數。完整CI artifact七天未下載，公開摘要不是完整native原始報告備份；無Setup／tag／Release交付。

C04 2/4、C11 2/5、導入7/12／歷史19/25保留。既有歷史檔／模型／第三方原文與28份架構快照不改。

[返回開發紀錄](../../README.md)

首次CPU收尾進度頁截圖／瀏覽器日誌保留於screenshots-cpu-closeout-first與browser-cpu-closeout-first.log；當時尚未加入本版基本包結果，未另存該次HTML快照。最終頁面截圖另在CPU恢復實測目錄，沒有覆寫首次截圖。

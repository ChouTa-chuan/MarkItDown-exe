# 視覺進度Pages發布

2026-11-11（台北），使用者明確要求將進度頁發布到GitHub，使用固定網址。程式0.19.1／架構0.4及684項功能基線不變。

已建立獨立Pages流程，變更進度JSON／HTML／模板／產生器後自動部署，只上傳index.html、progress.html與.nojekyll。產生器不安裝其他相依、不複製整份docs、模型或安裝包。線上版標示為重新整理載入最新部署；離線檔保持原樣。

本地執行與workflow相同的build步驟，輸出三檔與hash通過；Chromium驗線上標示、互動分頁、7/12、手機無橫向溢出及零JavaScript錯誤。published-index.html、兩張截圖及build／browser JSON另存；這些為發布前本地檢查，尚未當作網站上線。

已查閱官方configure-pages@v5：首次建立Pages站台需要專案管理權限，GITHUB_TOKEN無此權限。此環境無可呼叫的GitHub管理設定工具；github.io網域的直接讀取被代理403拒絕，未改雲端網路設定。透過GitHub runner部署後會以HTTP 200與精確SHA-256驗證網站，實際結果接續保存。

固定網址：https://chouta-chuan.github.io/MarkItDown-exe/ 。首次設定與重跑說明見[Pages說明](../../../progress-pages.md)。

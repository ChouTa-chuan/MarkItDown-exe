# 視覺進度網站上線

2026-11-12（台北），使用者確認已完成Pages來源設定後，以既有流程重新部署。[run43133764140](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43133764140)來源bc5d601cbb9480d179edb26372891771b5fa955a，建置及部署成功。

固定網址：https://chouta-chuan.github.io/MarkItDown-exe/ 。GitHub runner實際對公開網址GET，HTTP 200，回傳SHA-256為59769d430451bca6b3ffe4cbe5ecf35a80cf41d5696b9bfa160fce6c3f579240，與本地目前產生器及前次Chromium驗互動／手機版的HTML完全一致；公開驗證JSON與原頁另存。本雲端環境未直接重新抓取github.io，網站HTTP核對由GitHub runner完成。

只發布index.html、progress.html與.nojekyll；後續進度JSON、HTML、模板或產生器同步main時自動重新部署，固定網址不變，重新整理載入最近快照。這次只發布進度網站，程式0.19.1／架構0.4與684項功能基線不變，未重跑或擴大Windows／GPU、乾淨機等驗收，也未交付Setup或建立Release。

[首次未啟用的失敗](../progress-pages-2026-11-11/first-deployment/README.md)保持原樣，沒有改寫為通過；[發布前HTML及瀏覽器證據](../progress-pages-2026-11-11/README.md)以相同hash關聯。本次未修改雲端網路設定或索取PAT。

[網站說明](../../../progress-pages.md) · [返回開發紀錄](../../README.md)

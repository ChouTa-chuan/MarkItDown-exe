# 線上視覺進度

固定網址：**https://chouta-chuan.github.io/MarkItDown-exe/**

2026-11-12已由使用者確認完成Pages來源設定，正在重新部署並核對線上內容；[首次未啟用的流程](development-records/runs/progress-pages-2026-11-11/first-deployment/README.md)原樣保存。部署完成後也可使用同一網站的`progress.html`路徑；本地`docs/progress.html`繼續保留供離線查看。

首頁顯示最近一次部署的進度快照。後續更新`docs/progress.json`、頁面模板或產生器並同步`main`時，GitHub Actions會自動產生與部署新版；頁面持續開啟時，重新整理即可載入最近部署。

網站只包含`index.html`、同內容的`progress.html`及`.nojekyll`。使用既有產生器與內嵌資料，沒有額外套件相依；工程原始日誌、模型、安裝包與整份docs不加入網站。發布後以HTTP 200與建置檔案SHA-256核對實際網站內容。

首次啟用GitHub Pages需要專案管理員操作：

1. 開啟[專案Settings → Pages](https://github.com/ChouTa-chuan/MarkItDown-exe/settings/pages)。
2. 在「Build and deployment」將「Source」選為 **GitHub Actions**。
3. 若首次流程已因Pages未啟用而停止，開啟[Publish visual progress](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/workflows/progress-pages.yml)，按「Run workflow」，保留`main`並執行。

一般CI令牌沒有首次建立Pages站台所需的管理員權限；這個步驟不需提供PAT或在對話中貼上任何金鑰。官方說明見[configure-pages的enablement權限](https://github.com/actions/configure-pages/blob/v5/action.yml)。若已啟用且來源為GitHub Actions，後續進度更新直接自動部署。

這次是進度網頁發布；程式0.19.1、架構0.4、功能驗收進度及Windows安裝包狀態維持原紀錄。

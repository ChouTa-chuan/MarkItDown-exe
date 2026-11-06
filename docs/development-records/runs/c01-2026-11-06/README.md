# C01 開發與驗收紀錄

日期：2026-11-06（台北）；程式 **0.2.0**，架構 **0.4**。本輪完成「元件／能力／版本契約與登錄」，新導入 **1/12**；既有 **19/25** 另計。

- [43 項逐項機器結果](acceptance.json)／[C01 原始日誌](component-tests.log)：使用已安裝 0.2.0 的真實暫存檔與 SQLite，43 全過，0 跳過。
- [完整回歸日誌](full-tests.log)：196 項，195 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過，44.698 秒；此時間僅本次觀察，不作效能承諾。
- [瀏覽器](browser.log)：三分頁、基線／新增計數、卡片實作狀態、篩選、鍵盤及手機寬度通過。
- [上游](upstream.log)／[授權](licenses.log)／[既有附件與架構快照雜湊核對](integrity.json)；前 75 份附件與前四份圖不變。
- [本輪附件清單與 SHA-256](manifest.json)，與先前保存清單分開；不覆寫舊截圖或日誌。

進度畫面：[里程碑](screenshots/milestones.png)／[原模組](screenshots/modules.png)／[C01 元件導入](screenshots/components.png)／[元件手機版](screenshots/components-mobile.png)／[里程碑手機版](screenshots/mobile.png)。均為本機 Chromium 開啟離線進度 HTML，不是 Windows 應用程式截圖。

重跑時先安裝專案及開發依賴：

```bash
python -m pip install --no-deps --no-build-isolation .
python scripts/check_component_acceptance.py --report /tmp/c01-acceptance.json
TESSDATA_PREFIX=<verified model directory> QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
python scripts/build_progress.py
python scripts/check_progress_browser.py --screenshots /tmp/c01-progress
python scripts/verify_upstream.py
python scripts/license_inventory.py --verify
```

本輪沒有下載真實元件、執行新 OCR 引擎或 GPU 推論，也未重建 frozen／Windows 產物。簽章欄位只驗格式，可信目錄與金鑰驗證留 C05；下載／交易安裝留 C05／C06。現有 GUI／模型／設定未接入 C01，下一項為 C02。詳見 [C01 模組說明](../../../components.md)、[架構指引](../../../architecture-guide.md)與[開發紀錄](../../README.md)。

# C06 開發與驗收紀錄

日期：2026-11-06（台北），程式 **0.4.0**，架構 **0.4**。完成 C06 交易維護 API，新導入 **4/12（C01／C02／C05／C06）**，既有 **19/25** 另計；C03／C04 Windows 原生 OCR／完整 profile 門檻保留。

- 最終 [92 項逐項結果](acceptance.json)／[原始日誌](component-tests.log)：51 項 C06＋41 項 C05 回歸，0 跳過，使用真實 ZIP、檔案、SQLite、Ed25519 與核心鎖；探針為合成模型資料運算，非實際 OCR worker。
- [11 次真實子程序退出明細](process-exits.json)：安裝五個階段、修復一次、移除三個階段、使用中強制終止一次、持鎖退出一次。恢復與重新取得鎖的斷言通過，未假裝執行過物理斷電或 Windows。
- 最終 [完整回歸](full-tests.log)：**321 項，320 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，乾淨 Linux venv 已安裝套件，60.731 秒僅為本次觀察。
- [實際 HTTPS 六項回歸](https-regression.json)／[日誌](https.log)：官方固定 LICENSE、大小／SHA-256、verified 登錄、零網路快取與離線匯入；未執行元件，測試私鑰僅在記憶體。
- [進度頁瀏覽器日誌](browser.log)與新畫面：[元件 4/12](screenshots/components.png)／[手機元件頁](screenshots/components-mobile.png)／[原里程碑](screenshots/milestones.png)／[模組](screenshots/modules.png)／[手機版](screenshots/mobile.png)。
- [上游](upstream.log)／[授權](licenses.log)／[舊產物與架構快照核對](integrity.json)。原 58 套件、214 授權原文與雜湊鎖定不變；主登錄 schema 2／設定 v6 保留，維護另用 schema 1。
- [本輪附件與 SHA-256](manifest.json)獨立保存，前 75 份工程附件、C01／C02／C05 產物與前七份圖不改寫。

開發過程日誌另外保存：

- [初次 C05 舊鎖斷言失敗](initial-c05-lock-regression.log)：舊斷言要求鎖檔刪除；改採持久核心鎖後，以可重新取得鎖驗證釋放。
- [第一次跨程序測試的收尾等待／中斷](initial-interrupted.log)：被終止程序的同步事件不能用來收尾，修正測試並加有界等待；此檔不是通過證據。
- [中間 84 項通過](intermediate-component-tests.log)、[91 項結果](pre-final-acceptance.json)／[日誌](pre-final-component-tests.log)、[早期完整回歸](pre-final-full-tests.log)、[早期 HTTPS](pre-final-https-regression.json)／[日誌](pre-final-https.log)。
- [同步前 92 項結果](pre-sync-acceptance.json)／[日誌](pre-sync-component-tests.log)／[完整回歸](pre-sync-full-tests.log)：之後再補「配額清理也要避開舊不明鎖」的反例並重跑，最終結果以上方檔案為準。

重跑（完整回歸仍需既有 GUI／Office／PDF／Tesseract 及固定語言資料）：

```bash
python -m pip install --no-deps --no-build-isolation .
python scripts/check_component_acceptance.py --check C06 --report /tmp/c06-acceptance.json
TESSDATA_PREFIX=<verified model directory> QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
python scripts/check_component_download_https.py --report /tmp/c06-https.json
python scripts/build_progress.py
python scripts/check_progress_browser.py --screenshots /tmp/c06-progress
```

元件服務尚未接入實際 worker／桌面／轉換流程，依 C07／C08／C10 接續；沒有重建 frozen／Windows 安裝包、發行正式目錄或執行 GPU，不建立 tag／Release 或觸發發行流程。

[維護 API 與邊界](../../../component-lifecycle.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

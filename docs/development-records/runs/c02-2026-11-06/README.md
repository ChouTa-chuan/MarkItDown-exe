# C02 開發與驗收紀錄

日期：2026-11-06（台北）；程式 **0.2.1**，架構 **0.4**。完成「舊模型 adapter 與設定遷移」，新導入 **2/12**，既有 **19/25** 另計。

- [逐項驗收結果](acceptance.json)／[原始日誌](component-tests.log)：C02 **61/61**，含 v1–v5 值保留、備份故障、SQLite 快照與升級回復、外部只讀、受管下載／取消／快取、桌面／CLI、固定真實模型與明確 OCR 路徑規則。
- [開發中首次回歸](initial-regression.log)保留當時 4 項失敗：舊測試仍要求遷移結果為 schema 5；改版確認後更新為 schema 6，原值保留的斷言繼續驗證。此檔不列為最終通過證據。
- [完整回歸日誌](full-tests.log)：**229 項，228 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**；已安裝套件的乾淨 Linux venv，Tesseract 5.5／固定繁中與英文模型。42.103 秒僅為本次觀察。
- [Qt 離屏日誌](ui.log)及[合成畫面產生腳本](capture_ui.py)：[設定 v6 桌面](screenshots/desktop-v6.png)／[外部模型只讀](screenshots/legacy-readonly.png)／[新受管空目錄](screenshots/managed-empty.png)。假模型僅供畫面，未執行新推論或下載。
- [進度頁瀏覽器日誌](browser.log)：[元件 2/12](screenshots/components.png)／[元件手機版](screenshots/components-mobile.png)／[既有里程碑](screenshots/milestones.png)／[模組](screenshots/modules.png)／[手機版](screenshots/mobile.png)。
- [上游](upstream.log)／[授權](licenses.log)／[歷史附件與快照完整性](integrity.json)；前 75 份附件、C01 驗收產物與前五份架構圖不覆寫。
- [本輪所有附件的 SHA-256](manifest.json)單獨記錄，不改寫舊清單。

重跑（已安裝完整開發依賴及原生 OCR 前置）：

```bash
python -m pip install --no-deps --no-build-isolation .
TESSDATA_PREFIX=<verified model directory> QT_QPA_PLATFORM=offscreen python scripts/check_component_acceptance.py --check C02 --report /tmp/c02-acceptance.json
TESSDATA_PREFIX=<verified model directory> QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen python docs/development-records/runs/c02-2026-11-06/capture_ui.py
python scripts/build_progress.py
python scripts/check_progress_browser.py --screenshots /tmp/c02-progress
```

本輪驗收未把跳過算成通過，沒有重建 frozen／Windows 產物、觸發 Windows 發行工作流程或執行 GPU。Qt 畫面是 Linux 離屏，不是 Windows UI 實測；真實固定模型的只讀核對不等於新 OCR 引擎 ready。通用可信目錄、交易安裝、使用中鎖及完整管理頁仍待後續檢核。

[模組與遷移說明](../../../component-migration.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

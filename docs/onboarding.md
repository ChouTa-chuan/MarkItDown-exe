# C09：首次流程與 RAM 子檢核

程式 **0.7.0**、架構 **0.4**，2026-11-07（台北）。完成首次設定流程的三項子檢核：RAM 建議／保留偏好、略過選配／完成標記／不重複、本機基本健康與失效不阻擋文字功能。

**完整 C09 仍未完成，新架構導入維持 6/12，既有基線 19/25。** 原 C09 包含「新裝離線可用」：基本包應內含引擎與雙語模型。目前驗收使用 Linux 系統既有 Tesseract 與預備的固定模型，不能代替 C03／C04 的 Windows 原生／profile 及全新基本包驗收。進度頁展開 C09 可逐項查看三個已驗收子檢核與一個待驗收項。

## 使用流程

正式入口在主視窗顯示後，以 `QTimer.singleShot` 開啟首次設定；`Window` 本身可供測試或其他程式嵌入，不在建構時隱式啟動對話框。完成版本目前為 1，只有版本未達標時自動提示；可按「首次設定／重新檢查」手動再開。

檢查完全離線，只處理打包的合成影像。顯示 RAM、引擎位置、模型位置、Tesseract 版本、雙語模型及兩份真實辨識結果是否達目標。檢查在背景，按「稍後再設定」或關閉會先取消原生工作並收尾，不儲存設定或完成標記。

按「完成設定，略過選配」才儲存。新使用者預設採 RAM 建議，並只在雙語健康通過後填入自動找到的引擎／模型位置；既有使用者兩個套用選項預設不勾。即使勾選引擎自動填入，也不取代已明確指定的路徑或 OCR 後端。

缺引擎、缺模型、資源不足或健康未達標都顯示未就緒原因，仍可完成流程並使用基本文字轉換。完成標記代表流程已完成，不是可永久沿用的 ready，也不代表 Windows 基本包已自帶 OCR；實際轉換仍使用原有檢查／失敗隔離。

## 模組與政策

| 模組 | 責任 |
| --- | --- |
| `onboarding/service.py` | 建立只讀設定快照、RAM 建議、本機引擎選擇、合成雙語健康及明確完成儲存 |
| `onboarding/dialog.py` | 背景檢查／儲存、套用選項、未就緒說明、略過與關閉保護 |
| `settings.py` | 延用 schema v6／舊版備份，新增 `expected_raw` 比對檢查開始前的設定原文 |
| `desktop.py` | 生產入口定時提示、手動入口、資源設定傳遞、完成後重新載入及父視窗保護 |
| `scripts/check_onboarding_acceptance.py` | 真正 Qt／Tesseract 與掃描 PDF、偏好保留、缺引擎文字功能的離線流程證據 |
| `packaging/desktop.spec` | 宣告兩份合成影像／metadata；未重建主程式 frozen 或原生基本包 |

RAM 建議維持既有政策：自動預算約實體 RAM 的 25%，保留量依容量取 1/8、最低 128 MiB、最高 2 GiB；畫面同時顯示當下可用量。不是預先配置或硬性上限，不保證其他應用不受影響。執行健康前與步驟邊界用現有 `Policy` 再做 256 MiB 的保守准入，量測或資源失敗不強行啟動原生檢查。

引擎優先使用明確路徑；失效時不回退。未指定時沿用本機 PATH 偵測。模型位置優先明確設定；否則只讀核對既有專用／舊模型目錄的固定三檔，再沿用 `TESSDATA_PREFIX` 或引擎預設。沒有下載、pip 安裝、GPU 切換、模型所有權接管或將外部引擎複製進基本包。

原生探針以參數陣列啟動，CPU 執行緒設為 1，單次版本／語言查詢 5 秒、單張合成辨識 12 秒，stdout／stderr 各限 64 KiB。取消先終止原生子程序，1 秒未退出才 kill；不將原生 stderr 全文寫入設定／使用者報告。這不是 OS sandbox 或硬性 RAM 限制。

兩份健康樣本是既有英文 `WORKER HEALTH CHECK 12345` 及固定 17 字繁體測試影像；先核對 SHA-256，再經既有正規化與 Tesseract `chi_tra+eng`／PSM 11 辨識。繁體影像與舊已知 ONNX 品質目標逐位元組相同，沒有重畫或放寬嚴格預期失敗。這些是合成健康目標，不能推論真實文件準確率。

設定完成使用原檔快照比對，拒絕在檢查期間覆蓋其他視窗更新；主視窗保存後同步記憶體基線。未來／損毀設定或連結拒絕重設，既有 v1–v5 原文在明確完成時按既有機制備份。沒有改變 schema、元件偏好、下載開關或品質／GPU 後端。

## 驗證與後續

- 新增 **22 項**：RAM、設定快照、舊版備份、明確路徑不回退、原生時間／輸出界限與取消回收、完成／稍後、Qt 與真實 Tesseract 雙語健康。合成 fixture 與真實推論分開。
- 流程與設定／遷移／桌面／核心回歸 **94/94**，`C09-flow` 報告明確標示 `full_c09_complete: false`。
- 全專案 **389 項：388 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。
- 真正 Qt＋本機 CPU 流程 **9/9**：正式 QTimer 接點、自動 RAM 建議、雙語健康、儲存與略過、再開不重複、空 PATH／空 `TESSDATA_PREFIX` 下兩頁真實掃描 PDF OCR、舊偏好保留、缺引擎仍可文字轉換、原模型不變且不連網。引擎是系統現有 `/usr/bin/tesseract`，模型由驗收先預置，未宣稱全新機器沒有前置條件。

原始結果、畫面、範例輸出與雜湊見[本輪流程紀錄](development-records/runs/c09-flow-2026-11-07/README.md)。沒有增加第三方依賴，原 Windows／Linux 鎖定與授權原文不變。完整 C09 等 C03／C04 的基本包證據；0.8.0 已完成 [C10 自動文件分析與元件協作](managed-conversion.md)，Windows／GPU 實機及正式元件來源仍保留各自門檻。

```bash
python -m pip install --no-deps --no-build-isolation .
TESSDATA_PREFIX=<verified models> QT_QPA_PLATFORM=offscreen python scripts/check_component_acceptance.py --check C09-flow --report /tmp/c09-flow.json
QT_QPA_PLATFORM=offscreen python scripts/check_onboarding_acceptance.py --models <verified models> --output /tmp/c09-flow
```

# 開發進度

更新：2026-11-05。互動視覺版見 [里程碑／模組](progress.html)。

## 核對結果與本輪交付

- 上輪未提交的 ONNX 整合已核對：固定 RapidOCR 1.4.4、三個模型雜湊、實際 CPU 推論及不依賴 Tesseract 的英文掃描 PDF。
- 候選 CUDA 路徑包含單卡／provider／VRAM 准入、三個 session 驗證、arena 配置、自動模式回退與 RAM checkpoint；取消不回退，明確 GPU 模式不靜默改用 CPU。
- 檢查並改善回退的資源釋放，避免例外 traceback 保留失敗 session。
- 保留 Tesseract 預設，ONNX 手動選配並標示實驗性。ONNX 繁體樣本有漏字／字形錯誤，尚未達品質要求。
- 重新比較時發現 Tesseract 對稀疏文字圖片漏行，加入文字分布判斷，選用稀疏版面模式，並補充嚴格的雙行繁體回歸測試。
- schema v4 保存後端及 VRAM 配置預算，讀取 v1–v3；Linux／Windows 雜湊鎖定已更新。

## 驗證

- 乾淨 Linux venv：80 項檢查，79 通過、1 繁體品質預期失敗、0 跳過。預期失敗不列為品質通過。
- 品質缺口追蹤：test_traditional_chinese_quality_known_gap 保留嚴格斷言，模型改善後須移除 expectedFailure。
- 同一張 17 字合成樣本：Tesseract 修正後 0 個字元差異；ONNX 2 個差異。僅此樣本，不是整體準確率。原文與輸出見 ocr-quality-sample.json。
- ONNX 英文掃描 CPU 推論可用；CUDA 記憶體／provider／回退分支為模擬測試，沒有真實 GPU 推論。
- PyInstaller Linux 已打包並以真正程式驗證文字、原生 PDF、ONNX 模型資源及英文掃描；最新結果記錄於 validation-results.json。
- 進度頁將測試通過與品質未達標分開揭露。Windows workflow 僅保存，未執行。

## 里程碑

| 階段 | 已完成／總檢核 | 未完成事項 |
| --- | --- | --- |
| 0 規格／調查 | 3/4 | Windows 打包可行性實測 |
| 1 核心轉換 | 5/5 | 此階段僅基線，不是最終品質驗收 |
| 2 桌面 MVP | 4/5 | Windows 實機 |
| 3 自動精準 | 3/4 | 複雜版面、表格與真實品質樣本 |
| 4 GPU／模型 | 1/3 | GPU 真實推論、VRAM／回退實機驗收 |
| 5 發佈 | 0/3 | Windows 安裝包、簽章與授權清單 |

合計 16/24，等權檢核而非工時或產品完成率。本輪補強既有項目，不因測試數增加就增加里程碑完成數。

## 後續

- 以真實繁中、低品質、旋轉與複雜表格建立品質資料集；ONNX 未達標前不取代 Tesseract。
- Windows 原生 OCR 打包、乾淨機及 GPU 硬體驗收；目前沒有相應機器，不能將模擬視為完成。
- 完整依賴／模型／Qt 授權、安裝精靈、簽章、磁碟配額、崩潰清理及硬性資源限制仍待完成。
- ONNX CPU 模型隨套件提供，不需額外 OCR 執行檔；Tesseract 原生檔仍未整合進 Windows 包。
- 原生函式期間無法立即暫停，RAM／GPU arena 都不是整機硬性上限。

全部變更只保存本地，未推送、未啟動遠端 CI、未發布。

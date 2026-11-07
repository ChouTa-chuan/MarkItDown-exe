# C03：繁中／英文／日文／韓文 OCR

2026-11-08（台北），程式 **0.10.0**、架構 **0.4**。依新增需求，基本包的語言目標擴充為四語。本輪完成模型／選擇／本機 OCR 子檢核，C03 **1/4**，**完整 C03 未關閉，總數仍為 7/12**；Windows 原生引擎／DLL、四語內含與乾淨機尚待完成，既有基線 **19/25**。

## 模組與資料

| 模組 | 責任與邊界 |
| --- | --- |
| `languages.py` | 四種語言碼、單語／混合選項、順序與輸入驗證、四語模型目錄 |
| `data/ocr-four-languages.json` | 四個固定模型及授權 SHA-256，與舊三檔清單分開 |
| `models.py`／`components/legacy_models.py` | 沿用有界下載、hash、取消、排他發布與所有權；可信呼叫端可指定新固定清單 |
| `model_dialog.py` | 四語來源／授權／狀態，明確下載及移除；只驗模型、不當成引擎就緒 |
| `settings.py`／`core.py` | 設定 v7／Request 新增 `ocr_languages`，保留舊預設與原文備份 |
| `desktop.py`／`cli.py` | 語言選項傳入批次；切後端不重設選擇，CLI 使用相同契約 |
| `pdf_pipeline.py` | OCR 頁才使用語言；明確選語缺模型即失敗，寫入來源語言註記 |
| `onboarding` | 只讀本機所選語言健康，固定日韓樣本及原繁中／英文樣本；取消／RAM 沿用 |
| `packaging` | 更新四語目錄與健康資產的打包來源；本輪未重建 frozen／Windows 包 |

四語與授權合計 **10,639,763 bytes，約 10.6 MB**，不含 Tesseract 執行檔、DLL 或運行時 RAM。新增日韓合計約 4.15 MB。來源固定在 tessdata_fast 的 `87416418657359cb625c412a48b6e1d6d41c29bd`，Apache-2.0；日文 `jpn` 與韓文 `kor` 的 SHA-256 已由真正官方 HTTPS 下載核對，原繁中／英文及 LICENSE 的 hash 不變。

原 `ocr-models.json`、舊模型目錄與收據保持相容。新的程式目錄為 `models/tesseract-four-language-managed`，不接管非空未知目錄、不搬走舊資料；既有外部路徑只讀。四語收據有自己的 manifest hash，舊收據不能因此取得新清單的移除權。只有明確下載才建立新收據，取消／錯誤不發布半檔，未知檔案保留。

## 操作方式

選擇 Tesseract 後，在「OCR 語言」選單選單語、日文＋英文、韓文＋英文或四語混合。舊版「相容預設」維持原行為：使用可用繁中／英文模型，缺繁中時提示；更新不強迫改成四語混合。明確選擇的語言須全部存在，缺少任一種就停止該文件，不靜默換語言。

模型管理會顯示四語與授權狀態。外部／舊目錄不提供直接維護，請明確開啟新的程式專用目錄下載；完成後填入該目錄，可選擇儲存偏好。模型驗證不會安裝 Windows 原生引擎，也不會啟用 GPU。

CLI 沿用設定中的引擎與模型位置，可用下列選項覆蓋當次語言：

```text
--ocr-languages jpn
--ocr-languages kor+eng
--ocr-languages chi_tra+eng+jpn+kor
--ocr-languages legacy
```

v7 將語言保存為有順序的 JSON 清單或 null。v1–v6 載入只在記憶體遷移，首次明確儲存前保存完整原始位元組備份；路徑、RAM、品質、後端、元件偏好與首次完成標記保留。舊程式不支援 v7 時應拒絕覆寫，不能拿降版程式直接改新設定。

語言只影響 OCR；原生 Office／文字型 PDF 按原文擷取，不需要這些 OCR 模型。Tesseract OCR 頁新增 `source-ocr-languages` 註記；原頁碼、警示與輸出保護沿用。混合選項是共同解碼，**不是自動語言分類，也不保證比單語準確**；相近漢字、直排、低品質與混排文件仍需核對。

日文／韓文目前僅驗證 Tesseract。若所選日韓語言遇上 ONNX／雙引擎／受管 CPU 的 OCR 頁，會在載入前明確拒絕，請自行切回 Tesseract；原生／空白頁仍可處理。不把 ONNX 英文／繁體模型推定為日韓可用，既有繁體品質缺口保留。

## 驗證與後續

新增 **18 項**契約、設定、所有權、缺模型、後端界線、健康資產與 Qt 測試；含模型／設定遷移／首次／桌面／PDF／核心回歸 **138/138**，0 跳過。全專案 **458 項：457 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。

真正本機 Tesseract／CLI／Qt **10/10**：固定模型、離線匯入與重用、v6 完整備份、四種模型健康、各單語掃描、四頁混合、缺模型／不支援後端、日韓 CLI、桌面與四語模型視窗、移除保留未知資料。空 PATH／空 TESSDATA_PREFIX 仍以明確引擎及模型位置執行；每種單語及這四頁混合都符合固定原文目標，品質觀察逐項保存，**不是一般文件準確率**。

實測引擎為既有 Linux `/usr/bin/tesseract`，不是程式已內含 Windows 引擎。本輪沒有新 Python 依賴、重建 frozen、Windows／GPU 執行、tag／Release 或手動發行。來源、合成 PDF／Markdown、健康、原始結果與畫面見[開發紀錄](development-records/runs/c03-languages-2026-11-08/README.md)。

下一步固定 Windows Tesseract／必要 DLL／原授權，整合四語到基本包，再完成 C03、完整 C04／C09 及乾淨 Windows 驗收；GPU 另待 C12。

[架構指引](architecture-guide.md) · [進度](progress.html) · [需求決策](decisions/0003-four-language-ocr.md)

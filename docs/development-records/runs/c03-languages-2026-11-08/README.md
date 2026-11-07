# C03 四語模型與語言選擇開發紀錄

2026-11-08（台北），程式 **0.10.0**、架構 **0.4**。新增日文與韓文，基本包目標擴充為四語；完成 C03 本機子檢核 **1/4**，完整 C03 未關閉，總數 **7/12**，既有 **19/25**。Windows 原生／DLL／四語內含、完整 C04／C09 及 GPU 尚待後續。

- [138 項逐項結果](acceptance.json)／[日誌](component-tests.log)：18 項新增語言／設定／所有權／後端／Qt，加原模型／遷移／首次／PDF／核心回歸，全過、0 跳過。[新增 18 項](language-tests.log)單獨保存。
- [完整回歸](full-tests.log)：**458 項，457 通過、1 既有繁體品質預期失敗、0 跳過**，已安裝套件的完整乾淨 Linux venv，69.300 秒為觀察；保留固定繁中目標，未降低品質門檻。
- [真正本機四語十項](native/four-language-acceptance.json)／[日誌](native.log)：官方固定 hash、真實模型離線安裝／重用、v6 原文備份、四模型健康、各單語 PDF、四頁混合、缺模型／後端拒絕、日韓 CLI、Qt 選擇與模型視窗、移除保留未知資料。
- [四模型健康與原生版本](native/four-language-health.json)使用既有 Linux `/usr/bin/tesseract`，四語各自健康；空 PATH／空 TESSDATA_PREFIX 仍可用明確路徑，不連網自動下載。這是本機引擎證據，**不是基本包已自帶 Windows Tesseract**。
- 四個生成輸入／輸出：[繁中 PDF](native/chi_tra.pdf)／[MD](native/chi_tra.md)、[英文 PDF](native/eng.pdf)／[MD](native/eng.md)、[日文 PDF](native/jpn.pdf)／[MD](native/jpn.md)、[韓文 PDF](native/kor.pdf)／[MD](native/kor.md)。來源是專案內四份固定健康影像，日韓字型來源與 hash 隨新影像 JSON 保存在程式資源，原繁中／英文影像不改。
- [四頁混合 PDF](native/four-language-mixed.pdf)／[MD](native/four-language-mixed.md)：選 `chi_tra+eng+jpn+kor`，四頁 OCR、語言來源及警示保留。本批各單語與混合原文都符合固定目標；十項報告逐語列 exact_reference，**不是一般文件準確率、直排或任意混排驗收**。
- [日文 CLI](native/jpn-cli.md)／[日誌](native/jpn-cli.log)、[韓文 CLI](native/kor-cli.md)／[日誌](native/kor-cli.log)；[Qt 日＋英實際轉換](native/desktop-japanese.png)、[GUI 輸出](native/gui/jpn.pdf.md)、[四語模型視窗](native/four-language-models.png)。圖內路徑為本輪合成驗收資料。
- [v7 語言設定](native/settings.json)及[v6 原始備份](native/settings.json.pre-v6-f32758694a3ff4af.bak)；[模型收據](native/model-receipt.json)與[模型觀察](native/model-observation.json)只記資料完整性，不冒充引擎 ready。驗收最後移除已驗證模型，未知筆記保留；圖中的模型位置因此不是永久可用狀態。
- [官方日韓下載觀察](official-downloads.json)及[全部模型來源／大小／hash](model-sources.json)：同一 tessdata_fast 提交 `87416418657359cb625c412a48b6e1d6d41c29bd`、Apache-2.0。日韓合計 4,148,675 bytes，四語含授權 10,639,763 bytes；模型 binary 不放 Git，沒有把系統引擎 binary 加進專案。
- [C03 1/4、C04 2/4、C09 3/4 進度](screenshots/components.png)、[窄版](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機里程碑](screenshots/mobile.png)及[瀏覽器日誌](browser.log)。[上游](upstream.log)、[原授權](licenses.log)、[依賴 profile](profiles.log)、[完整性](integrity.json)及[本輪檔案 SHA-256](manifest.json)。

過程保存：[初次只跑原 440 項](intermediate-original-440-tests.log)為 439 通過及一項既有品質預期失敗；加入新測試後的[首次 138 項](intermediate-acceptance.json)／[日誌](intermediate-component-tests.log)與最終手冊更新後的 138 項分開。真正原生十項無跳過或假模型；單元測試內合成 payload／fake 命令僅驗邊界，不當成辨識成功。

模型管理使用新的四語目錄及 manifest hash，舊清單／舊收據／外部資料不接管。明確所選模型缺少時失敗，日韓不靜默改用 ONNX；原生／空白頁不受 OCR 選擇影響。四語混合不是自動語言分類，ONNX 繁體缺口與日韓未驗保留，RAM 仍為軟性預算。

本輪未增加 Python 套件、重建 frozen／Windows 安裝包或執行 GPU，無 tag／Release、手動發行、正式目錄或金鑰更新。前十四份架構圖固定，新增[第十五份四語圖](../../../architecture/versions/v0.4-c03-four-languages.md)。下一步為 Windows 原生引擎／DLL／四語整包與完整驗收。

[四語指南](../../../four-language-ocr.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

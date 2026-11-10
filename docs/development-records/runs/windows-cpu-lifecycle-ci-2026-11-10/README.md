# Windows CPU選配元件維護實測

2026-11-10（台北），程式0.18.1、架構0.4。[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42794184827)（fd69854ee19ba031362750072e22a92bf5463a7c）原生CPU功能11/11及同版維護8/8通過，控制端無OCR／Qt且環境不變，三個實際provider皆為CPUExecutionProvider。

八案包括既有安裝重驗、不相容架構拒絕、活躍租約同時阻擋修復／移除、壞包保留安裝、publish後取消修復回復原payload、安裝影像損壞先被hash拒絕再修復且真健康通過、未知檔案阻擋移除且bytes保留、閒置移除保留合成文件／設定／快取並重裝。每案後重驗payload全hash、active／READY、交易無殘留、原cache與兩份合成資料。產品仍不刪除未知資料；驗收只收回自己建立且bytes相同的合成檔。

使用同一次真正frozen worker與精簡控制venv，維護期間PATH留空並沿用SystemRoot。CPU建置24／控制5鎖定依賴（另有pip、自有app），沿用前版原鎖與原文；測試簽章金鑰仍只在記憶體，來源example.invalid，不提供正式下載目錄。完整scope為same-version-cpu-component-maintenance；取消是fault callback在published觸發Event，並非程序強制終止、斷電／重啟、跨版升降級或乾淨Windows。

[準備與147項原始日誌](../windows-cpu-lifecycle-prep-2026-11-10/README.md)保持固定，本版完整回歸未執行；0.17.2的611項仍屬舊完整基線。相對84324ac的3023份既有紀錄／資產／鎖檔未變，42份run manifest共2594筆hash與28份架構快照核對通過；具體範圍見historical-integrity.json，不代表所有聊天逐字內容備份。

本目錄保存公開原頁、完整公開短摘要、監測、來源對照與五張本次視覺頁截圖，manifest附SHA-256。分頁、模組篩選、鍵盤／手機版與JavaScript檢查通過，見browser.log。需登入的完整CI報告artifact保留七天，本次未下載；不把公開摘要冒充完整native stdout／stderr／交易報告永久備份。元件ZIP hash僅辨識本次產物，沒有上傳worker／模型／Setup或建立Release。

C04仍2/4、C11仍2/5、導入7/12／歷史19/25；單一CPU元件維護不能關閉全profile生命週期。下一步跨版本元件相容／安裝與其他profile，再接無Python離線乾淨機與人工UI。ONNX繁中／日韓與GPU品質、最終原生再散布審查、RAM軟性預算／校準保留。本次不需要使用者立即安裝。

[返回開發紀錄](../../README.md) · [維護範圍](../../../windows-cpu-lifecycle.md)

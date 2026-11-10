# Windows CPU選配原生驗證

2026-11-10（台北），程式0.18.0、架構0.4。[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42791407466)驗收 **11/11**，來源f0708d0587155640b2aee87f19ad45cbea92fe97。這是hosted Windows原生實跑；非Linux模擬或乾淨Windows交付驗收。

建置24套件、精簡控制端5鎖定依賴分別安裝於獨立venv；控制端另有pip及自有app，不能把5當作環境全部套件數。CPU worker由PyInstaller獨立凍結，臨時測試金鑰簽章後離線匯入；三個實際provider均為CPUExecutionProvider，控制端沒有OCR／Qt且安裝前後環境一致。安裝notice清單實際26個package records，與24個建置閉包的口徑不同，不能互換。

11項範圍：簽章離線匯入、staging健康、安裝後健康、受管真OCR租約、壞PNG隔離、後續OCR成功、取消原生工作且不輸出、RAM不足啟動前拒絕、閒置元件移除、控制端環境不變，以及真正frozen父管道EOF退出72並釋放worker guard。健康／推論及EOF probe的PATH留空；SystemRoot沿用。固定英文健康樣本只驗功能，不代表任意文件品質。

前三輪及第四輪失敗原頁另存原run目錄；ReadFile候選未解決問題已移除。最後在自己的共享鎖內、背景stdin reader前初始化Windows原生庫，原RAM准入與握手／總期限保留，模型驗證與推論仍待有效工作。Windows實跑支持這個初始化順序修正，不把CRT／DLL的底層根因宣稱為已完整證明。固定health額外診斷僅限公開合成樣本；產品控制端不保存文件stderr。

本地新15／相關143項在hash鎖定venv通過、退出0；完整本版回歸未執行，0.17.2的611仍屬舊完整基線。兩份新CPU profile與基本profile驗證通過；離線視覺頁的分頁／篩選／鍵盤／手機版與JavaScript檢查通過，五張實際截圖另存screenshots／；相對3e1d3d2的2878份指定舊紀錄／模型／原文／鎖檔未變，40份run manifest的2572筆hash及28張架構快照核對通過，具體範圍見historical-integrity.json。不是所有聊天逐字內容備份。

此目錄保存公開原頁、完整公開短摘要、監測與本地原始日誌，manifest附SHA-256。需登入的完整CI報告artifact僅保留七天，本次未下載；不宣稱已永久保存原始native stdout／stderr／health-observations完整報告。元件ZIP hash僅辨識本次產物，沒有上傳worker／模型／Setup或建立Release。

C04仍2/4、C11仍2/5、導入7/12／歷史19/25。尚待各profile完整生命週期與原生再散布審查、乾淨無Python／離線Windows、人工UI、GPU／日韓及ONNX繁體品質與RAM校準。RAM仍是軟性預算；本次不要求使用者立即安裝。

[返回開發紀錄](../../README.md) · [驗收範圍](../../../windows-cpu-ci.md)

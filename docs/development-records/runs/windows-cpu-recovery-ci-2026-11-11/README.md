# Windows CPU維護程序中斷恢復實測

2026-11-11（台北），程式0.19.1、架構0.4。[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42943978279)（ad7d227c8b2b7ae67d141ea2f63d6547bd7b52d0）程序終止／獨立恢復6/6接受，原功能11/11、同版維護8/8、跨版8/8也重新通過。控制端無OCR／Qt且環境不變。

升級published還原舊active，committed保留新active；有效payload修復old_moved／published還原原版；移除old_moved還原，committed完成移除後普通重裝。各案真spawn安裝程序，核對自有Process的PID、隨機token、操作與停點後kill／join，非零終止碼；活著時核心鎖拒絕recover。另一新程序recover一筆交易，第二次recover無動作，驗active與全payload hash、journal／staging收尾、合成文件／設定與兩份快取原bytes。

六案恢復後實際OCR版號為1.0.0、1.0.1、1.0.1、1.0.1、1.0.1、1.0.1；最後一案先確認已移除，再正常重裝1.0.1。每案frozen／CPU provider／固定英文辨識均核對。公開精簡摘要保留六案安裝PID、終止碼、恢復PID、恢復狀態與實際版號／frozen；完整原報告仍由CI另存。私鑰僅在主程序記憶體，spawn只傳公鑰、簽章catalog及自有路徑。中文目錄／空PATH實跑，SystemRoot沿用。

[初輪161項失敗與後續通過日誌](../windows-cpu-recovery-prep-2026-11-11/README.md)固定；[首輪Windows接受但公開摘要截斷及162項長度驗證](../windows-cpu-recovery-summary-2026-11-11/README.md)另存，未猜補4096字元prefix。第二輪已取得可完整解析的精簡公開JSON；壓縮只影響公開副本，完整cpu-build.json不改。原生恢復程式與接受條件未變。

相對1329725的3073份既有紀錄／資產／profile鎖未變，48份run manifest共2648筆hash及28份架構快照核對通過；範圍見historical-integrity.json。不是所有聊天逐字內容備份。本版完整回歸未跑，舊611仍屬0.17.2。

本目錄保存公開原頁、完整公開精簡摘要、監測與來源對照；原monitor.log只到環境中斷前的進行中狀態，重新連線後取得的Success與完整JSON另由reconnect-observation.json及新原頁記錄，未補寫舊監測日誌。完整需登入的原始CI報告artifact七天未下載，不把公開摘要冒充永久保存完整native stdout／交易明細。沒有上傳worker／模型／ZIP／Setup或建立Release，來源仍example.invalid。最終視覺頁五張截圖與browser.log另存，分頁／篩選／鍵盤／手機版與JavaScript檢查通過。

C04仍2/4、C11仍2/5、導入7/12／歷史19/25。範圍為指定停點的程序終止與明確recover；斷電／OS重啟、所有profile、人工／乾淨機、最終原生再散布及ONNX繁中／日韓／GPU仍待。修復案初始payload有效，損壞修復另循既有八案。RAM仍為軟性預算。目前不需使用者立即安裝。

[返回開發紀錄](../../README.md) · [恢復範圍](../../../windows-cpu-recovery.md)

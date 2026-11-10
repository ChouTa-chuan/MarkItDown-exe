# Windows CPU元件跨版本實測

2026-11-10（台北），程式0.19.0、架構0.4。[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42802066110)（db601e28a00aee740d53d439af2ee580f8981ef0）跨版8/8、原功能11/11、同版維護8/8通過。控制端無OCR／Qt且環境不變；固定英文辨識與真正frozen／CPU provider逐次核對。

前版為固定乾淨提交fd69854ee19ba031362750072e22a92bf5463a7c（應用0.18.1／CPU元件1.0.0），新版為應用0.19.0／元件1.0.1；控制協定同為1.0.0。CI各自checkout／建置環境／來源／spec／packager，沒有改描述或複製同個EXE冒充跨版。根層previous_source由CI實際核對HEAD與工作區後記錄；兩份package hash不同，新包hash也與原功能驗收一致。

八案：舊版安裝與OCR、publish後取消升級保留舊版OCR、升級執行新版並記錄前版、固定舊版請求在新版active時於健康前拒絕、明確回復舊worker、切回新版、退休舊版清除回復入口、移除新版保留合成文件與兩份快取。實際OCR版本序列為1.0.0、1.0.0、1.0.1、1.0.0、1.0.1。每步核對仍受管payload全hash、active、交易收尾、快取與合成資料。

本地新增9／相關156項，含真IPC子程序舊新握手、結果換版拒絕、未知版本、來源dirty／錯SHA、真ZIP交易與錯誤回復的部分失敗報告。[準備與初兩輪日誌](../windows-cpu-upgrade-prep-2026-11-10/README.md)固定；[接續156項及PDF／Qt入口版號調整](../windows-cpu-upgrade-followup-2026-11-10/README.md)另存，原PDF／Qt完整流程與本版完整回歸沒有重跑，0.17.2的611仍為舊完整基線。

首run42801762340因後續版號接線修正被取代，最終Cancelled原頁另存，並非一次原生失敗或成功。公開run與job原頁、完整公開短摘要、監測、來源對照及五張本次視覺截圖已保存；分頁、模組篩選、鍵盤／手機版與JavaScript檢查通過，見browser.log。需登入的完整原始報告artifact七天未下載，不把公開摘要當成永久保存完整native輸出／交易日誌。金鑰只在記憶體，正式來源仍example.invalid；沒有上傳worker／模型／ZIP／Setup或建立Release。

相對a24ae9c的3044份既有紀錄／資產／profile鎖未變，45份run manifest共2618筆hash及28份架構快照核對通過；範圍見historical-integrity.json。這不是所有聊天逐字內容備份。

C04仍2/4、C11仍2/5、導入7/12／歷史19/25。取消為published停點觸發Event，不是強制終止／斷電／OS重啟；回復是明確操作，不代表任意安裝失敗自動回滾。其他profile、乾淨機／人工、最終原生再散布、ONNX繁中／日韓／GPU及RAM校準仍待，RAM是軟性預算。下一步其他profile與更完整故障恢復，目前不需使用者立即安裝。

[返回開發紀錄](../../README.md) · [跨版範圍](../../../windows-cpu-upgrade.md)

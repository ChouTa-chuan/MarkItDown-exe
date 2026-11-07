# C10 自動分析與元件協作開發紀錄

2026-11-07（台北），程式 **0.8.0**、架構 **0.4**。完成 C10，已驗收 **7/12（C01／C02／C05／C06／C07／C08／C10）**，既有 **19/25**。C09 仍為流程三項子檢核完成，基本包自帶雙語 OCR 待 C03／C04。

- [242 項結果](acceptance.json)／[日誌](component-tests.log)：20 項新接線、152 項原元件／桌面、63 項版面與 7 項裝置，全部通過、0 跳過。最後一輪含手冊及提示文字；合成 ZIP／fake OCR 只驗路由與生命週期，不冒充原生推論。
- [完整回歸](full-tests.log)：**409 項，408 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，乾淨 Linux venv 的已安裝套件，87.821 秒為本輪觀察。後續文字調整及手冊斷言由最終 242 項覆驗，未改 OCR 品質目標。
- [真正 frozen CPU／Qt 十項](managed-native-acceptance.json)／[原始日誌](native.log)：簽章離線安裝、混合路由、frozen／實際 CPU provider、文字與逐格表格／警示、RAM 暫停／恢復與使用中維護拒絕、原生取消、提交前撤回、GUI 錯版隔離與真正成功、租約釋放與控制端 runtime 隔離。
- [四頁合成 PDF](mixed-source.pdf)與[Markdown](mixed-output.md)、[GUI 輸出](gui-mixed-output.md)保留：兩頁原生、一頁空白、一頁英文掃描。原生表格逐格驗證 Alpha／2／100 與 Beta／3／150，原文及來源警示保留；[純原生 PDF](native-source.pdf)驗證沒有可信 OCR 來源仍可處理。沒有使用者真實文件。
- 新畫面：[指定版本失敗但其他批次成功](desktop-batch-isolation.png)、[受管 OCR 真實成功](desktop-managed-success.png)。截圖來自 Qt／合成驗收暫存目錄；最後只澄清主視窗固定提示文字，未重繪或修改截圖。
- [元件進度](screenshots/components.png)、[手機版](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機里程碑](screenshots/mobile.png)及[瀏覽器日誌](browser.log)：核對 7/12、C09 仍部分完成、篩選／鍵盤／窄版及 JavaScript 錯誤。
- [上游](upstream.log)／[授權](licenses.log)、[舊附件／架構／鎖定完整性](integrity.json)及[本輪 SHA-256](manifest.json)。新增[第十二份架構圖](../../../architecture/versions/v0.4-c10-managed-conversion.md)，十一份舊快照與先前附件固定。

過程保留：

- [初次 fixture 參數錯誤](initial-fixture-arguments.log)、[19 項中間通過](intermediate-managed-tests.log)、[20 項最終接線](managed-tests.log)；重複 health_check 由 fixture 組裝造成，修正後再驗。
- [初次全回歸舊 mock 失敗](initial-full-device-fixture.log)、[408 項中間全回歸](intermediate-full-408.log)、[234 項](intermediate-acceptance-234.log)及[241 項](intermediate-acceptance-241.log)中間結果。新增專門的真實 spawn 測試後最終為 409／242；裝置 mock 接收新 kwargs 並明確驗證取消／permit，不移除原斷言。
- [初次真實 RAM fixture 失敗](initial-native-pressure-fixture.log)與當時 [PDF](intermediate-native/mixed-source.pdf)：零 reserve／零額外估計本來允許執行，改成明確應用程式超預算；[中間十項通過](intermediate-native-passed/managed-native-acceptance.json)／[日誌](intermediate-native-passed/native.log)及輸出、畫面完整另存。主目錄十項是巢狀資源狀態接線後的最終驗收。

真正驗收沿用 C07 開發 ZIP，SHA-256 `11c8e0e9ff648954c3e99a30630e47fd5f1fe6307fa813c5e062d374f3db6d18`。主程式 0.8.0 與元件 1.0.0 使用原協定 1.0.0，空 PATH／空 TESSDATA_PREFIX 仍實際推論，控制程序不 import ONNX／RapidOCR。驗收短效 Ed25519 私鑰只在記憶體，正式來源與金鑰仍未發布，一般入口不內建測試信任根。

無新增依賴、重建元件 ZIP／主程式 frozen／Windows 安裝包或宣稱繁體品質達標。RAM 仍是軟性預算；Windows／GPU、正式元件來源與完整 C09 保留，沒有 tag／Release 或手動 Windows 發行。後續為 C03／C04 基本包及平台驗收。

[接線指南](../../../managed-conversion.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

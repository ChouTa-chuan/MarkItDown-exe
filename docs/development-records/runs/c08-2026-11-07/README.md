# C08 開發紀錄

2026-11-07（台北），程式 **0.6.0**、架構 **0.4**。新導入 **6/12（C01／C02／C05／C06／C07／C08）**，既有 **19/25**。

- [152 項逐項結果](acceptance.json)／[日誌](component-tests.log)：23 項新管理服務／Qt＋115 項 C05–C07 回歸＋14 項桌面／說明，全部通過、0 跳過；真實 Ed25519、ZIP、SQLite 與 Qt，HTTP 與合成健康 fixture 分別標示。
- [完整回歸](full-tests.log)：**367 項，366 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，已安裝套件、乾淨 Linux venv。61.526 秒為本次觀察；之後離線手冊新增 C08 操作，最終 152 項另含手冊實際顯示、目錄顯示名稱保留純文字，以及移除確認只用受限 ID／版號的斷言。
- [真實 Qt／frozen CPU 九項](ui-native-acceptance.json)／[原始日誌](ui-native.log)：空 PATH 下，真實離線安裝、兩個位置健康、UI heartbeat、獨立 CPU 健康、核對授權、原生取消與退出、取消後再次成功、確認移除及基本文字轉換。控制程序未 import ONNX／RapidOCR，五次真實 probe 結果與 PID 保存；安裝 heartbeat 1,435 次僅是該次觀察。
- 自動化只代入選檔／移除確認結果，runner 外層僅記錄真正回傳值；未替換交易、IPC、模型或原生推論。沿用同一 C07 ZIP，SHA-256 `11c8e0e9ff648954c3e99a30630e47fd5f1fe6307fa813c5e062d374f3db6d18`，沒有重建原生元件或新增依賴。
- 新視窗：[安裝前版本／容量／來源](component-before-install.png)、[真實元件已安裝](component-installed.png)、[授權原文](component-license.png)、[主視窗入口與基本文字轉換](desktop-with-component-entry.png)。這些畫面使用暫存目錄及短效測試信任政策，不是正式目錄已上線的畫面，私鑰沒有保存。
- 新進度畫面：[元件 6/12](screenshots/components.png)、[手機元件頁](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機版](screenshots/mobile.png)，[瀏覽器日誌](browser.log)核對篩選／鍵盤／窄版／JavaScript 錯誤。
- [上游](upstream.log)／[授權](licenses.log)、[舊附件／架構／鎖定完整性](integrity.json)與[新附件 SHA-256](manifest.json)。原先九份快照及所有既有工程附件保持固定，新加[第十份 C08 圖](../../../architecture/versions/v0.4-c08-component-ui.md)。

過程另外保存：

- [初次空目錄 fixture 失敗](initial-empty-catalog-fixture.log)：22 項有一項錯用 C05 不允許的空目錄；改為有效的版本撤回情境，再補目錄到期案例。[後續 23 項](intermediate-management-tests.log)通過，最終另納入 FIFO／特殊檔拒絕與桌面手冊斷言。
- [中間真實 GUI 驗收](intermediate-ui/ui-native-acceptance.json)／[日誌](intermediate-ui/ui-native.log)與當時四張畫面保留在同目錄。最終結果以上方九項為準。
- [補充確認文字前的 152 項](intermediate-before-confirmation-acceptance.json)／[日誌](intermediate-before-confirmation-tests.log)保留；最終元件日誌以上方 component-tests 為準。

新增背景管理服務與 Qt 介面，不改設定 v6／登錄 schema 2／維護 schema 1。健康檢查可重驗非 active 版本而不切換；接線時修正 native 健康取消須傳回 Cancelled，取消不再被誤記不健康。

正式元件來源與發行金鑰尚未發布，一般桌面預設不提供未核准下載，不內建測試金鑰；基本文字轉換及原模型管理繼續可用。Windows／GPU、C03／C04 原生 profile、C09 首次設定、C10 文件路由仍待後續，繁體品質及 RAM 軟預算限制保留。未重建主程式 frozen／Windows 安裝包，沒有 tag／Release 或手動 Windows 發行。

[設計與重跑方式](../../../component-management.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

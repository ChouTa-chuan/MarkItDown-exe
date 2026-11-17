# A10 Microsoft 執行期逐檔對照

本目錄保存 A10 來源重取的小型原始探測與條款參考資料，並非重建 bundle 或新候選。每份來源 bytes 與 A6 相同；後續完整基本包 CI 另驗真正 bundle。目錄與登記引用見 packaging/microsoft/base-windows.json。

PySide6／shiboken6 的 Microsoft PE 版本資源與 QT Company 簽署者分開保存，不把 Valid 誤認為 Microsoft 簽署或法律許可。Microsoft 官網原文仍被雲端代理拒絕，兩個官方部署文件由固定 MicrosoftDocs 原始碼取得，未核對轉載明確標記。base-microsoft 保持 open，A13 由使用者決定。

本輪程式反例已驗，完整回歸及最終 head CI 進行中，完成後補 manifest 與完整過程。原始首次失敗 run 44060276291 保留於 PR 20。

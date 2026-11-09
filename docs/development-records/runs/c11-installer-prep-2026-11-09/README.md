# C11 基本包安裝生命週期準備

2026-11-09（台北），程式 0.14.0 → 0.15.0，架構0.4。新增獨立 base-installer.iss，AppId／路徑／Start Menu 名稱與舊 Desktop installer 分開；每使用者 lowest、不新增遞迴 InstallDelete／UninstallDelete，也不觸發舊手動發行 workflow。

安裝器測試只限可拋棄 Windows CI，先拒絕既有同 AppId 註冊或捷徑，使用本次全新工作目錄與中文安裝路徑。信任同次建置保留的 catalog，逐檔驗 hash／版本／安全路徑，安裝目錄內的 catalog 不能自行成為新信任根。真正安裝後再跑原 10 項 Windows validator；故意刪入口／損壞英語模型，同版重新安裝後重驗全部 hash 及四語 full 自檢；最後移除受管檔案、註冊與捷徑，保留安裝目錄內未知文件以及外部唯一資料 fixture。

外部 fixture 放在 AppLocalData 的唯一測試子目錄，內有 settings／models／SQLite／outputs／cache 等合成哨兵；不覆寫真正設定、模型或資料庫。這只證明安裝器不刪哨兵，不冒充跨版本資料遷移。測試結束只清自己建立的 fixture 檔案。編譯出的 Setup 只在 CI 工作目錄供測試，不上傳發行品；僅報告及來源／原文證據上傳。

本地新增13項，C11相關154/154，32個正常 child 的完整回歸568項（567通過、1既有 ONNX繁體品質預期失敗、0跳過）。實際 Windows 安裝／修復／移除尚待 CI，不以 Linux合成 catalog／registry guard 當 Windows 成功。混合 Linux teardown exit139仍另追。

C11整項仍未完成；新列4個子檢核，hosted 安裝／同版修復／移除為第一項，仍待真實執行。跨版本升級／回復、無Python乾淨機離線及人工 UI保留；整體7/12、歷史19/25、C03 3/4、C04 2/4、C09 3/4不變。沒有 tag／Release／GPU或正式安裝包下載，binary／模型不入庫。

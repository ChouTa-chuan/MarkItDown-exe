# C11 Hosted 基本包安裝／修復／移除驗證完成

2026-11-09（台北），程式 **0.15.0**、架構0.4。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42542464205)（43cf811）成功：原生基本資料夾10項、實際安裝後應用程式10項，以及安裝生命週期6段全部通過，C11首項子檢核完成，整項仍未關閉。

真實結果：Inno編譯per-user測試Setup，中文路徑安裝；受管catalog **1652檔**全部核對、同版registry與Start Menu捷徑存在；真正刪除入口／破壞英語模型後重新安裝，全部hash與四語full自檢恢復；解除安裝移除受管檔案／registry／捷徑，外部唯一合成settings／model／SQLite／output／cache哨兵及安裝目錄內未追蹤文件保持原bytes。這不是實際使用者資料遷移或跨版升級／回復，也不是標準非管理員帳戶或無Python乾淨機驗收。

永久保存公開原頁、完整短摘要、run／commit／hash等來源與明確推導的六段索引。compiler license原文從官方固定提交取得，SHA-256與runner實際原文完全相同，原bytes保存；該source commit只標記授權文字來源，不宣稱是已安裝compiler binary的精確建置提交。Setup／compiler／catalog hash保存在公開摘要，但binary不入Git，也沒有Setup下載／tag／Release。完整需登入的CI報告／Windows截圖仍在七天artifact，未下載就不宣稱已永久封存。

本地相關154/154；32模組568項隔離正常退出（567通過、1既有ONNX繁體品質預期失敗），詳細raw紀錄在前次prep。混合Linux native teardown仍待查。C11 **1/4**，完整導入 **7/12**；C03 3/4、C04 2/4、C09 3/4、歷史19/25保留。下一步真實跨版本升級／回復、各profile、乾淨離線首次流程及人工UI；GPU／RAM軟預算與最終發行門檻不變。

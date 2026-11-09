# Windows CI 自有中斷產物清理實測

紀錄更新：2026-11-10（台北），程式 **0.17.2**、架構 **0.4**。[真正Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42599639656)（a40f438）接受。

三個實際程序中斷停點，普通匹配Setup明確續修、各app10項及移除後，自有產物清理 **3/3**；實際清理 **1** 份，殘留 **0**。Windows真實開檔鎖反例拒絕清理，未知同類檔名／同bytes合成文件保持原內容；公開摘要保留全部這些布林與計數，完整原始handle／PID／逐檔收據仍在需登入的CI artifact（七天），未下載、不假稱永久封存。

沿用基本包／安裝後app各10項、安裝／同版修復／移除6段、真正0.16→0.17.2跨版／明確回復11段、三停點續修各10項，全部接受。受管payload／registry／shortcut及資料哨兵仍核對。

清理範圍明確是 **ci-owned-fault-installer-artifacts**：本次控制端操作前不存在、在自己停點已觀察、終止後且續修前捕獲的記憶體收據；核對hash／size及原生file identity，等待自己PID樹退出，全部原檔handle拒寫／rename／delete分享後再delete-on-close。Windows身分與連結數使用GetFileInformationByHandle，不靠CRT fstat。沒有外部JSON授權、通配／遞迴刪除或unlink後備。

**普通Setup沒有新增這個清理入口**。此為測試框架自有產物清理，不能當作一般使用者任意中斷後都可自動清理、斷電耐久、所有profile、乾淨Windows／標準帳戶／人工UI、GPU或正式發行。C11仍 **2/5**、完整導入 **7/12**、歷史 **19/25**，沒有Setup／tag／Release。

保存公開原頁／完整短摘要、實測來源比較、必要同hash授權原文、視覺進度及各檔SHA-256。來源程式與CI實測commit一致，後續只改文件；原生API與刪除結果以Windows CI為準。[本地14／相關39與611完整回歸、前版0.17.1基線](../temporary-cleanup-prep-2026-11-09/README.md)保持固定，610通過＋1既有ONNX繁中品質預期失敗，混合及36模組正常exit0；不是一般準確率或RAM硬性限制證據。

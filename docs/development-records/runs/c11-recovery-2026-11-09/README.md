# Windows 安裝程序中斷後續修實測

2026-11-09（台北），程式 **0.17.0**、架構0.4。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42578549106)（e3c0273）成功。三個停點 **3/3**：intent提交後、第一個檔案實際複製後、payload寫完／舊metadata尚未清理。每案握手後taskkill自己Popen PID子樹，普通匹配Setup明確續修，受管檔案／registry／舊metadata清理及installed app各 **10/10**，解除安裝／資料哨兵與未知文件保留通過。

停點僅在DCiFaultInjection測試變體編譯，恢復使用一般Setup，兩者配同一真正payload；原版0.16固定990e600的controller／spec／generator／app獨立建置，並非改新版版本字串。拒無明確確認的silent續修及不匹配marker，完整payload未完成時app入口退出3且不建立診斷報告；全hash與舊目錄清理後才清除intent。一般基本資料夾／安裝後app各10項、同版安裝修復移除6段、真正0.16→0.17升級／明確回復11段也通過。

中斷可能遺留Inno尚未提交的暫存產物，本輪最後仍保留 **1** 份。只以已驗程式／已登錄Inno metadata的精確hash，或操作前不存在、在自己停點已看見、終止後且續修前綁定path／hash／PID的建立收據認列；不以.tmp通配排除或刪除未知檔案。**完整暫存清理未驗收**，解除安裝檢核涵蓋受管payload／登錄與資料保留，不宣稱程式目錄已清空。

此為**hosted Windows、已知兩份build、三個程序終止停點的明確續修**。不宣稱斷電／OS重啟、任意中斷時刻、壞或部分intent寫入損壞、解除安裝中斷、各profile、人工UI／標準帳戶、無Python乾淨機、真實使用者資料遷移或自動失敗回滾。C11第三項仍包含各profile，故 **C11維持2/5、整體7/12、歷史19/25**；基本包續修獨立列為已驗模組，不修改已保存的舊圖／舊進度。

永久保存公開原頁與完整短診斷、run／commit／catalog／工具hash、同hash固定官方授權原bytes及明確推導的檢核索引。完整需登入artifact（含實際PID／tree終止原始日誌、三案完整app報告／截圖及Setup hash）未下載，僅CI七天保留，不宣稱已永久封存。授權原文source不是compiler binary精確建置提交或再散布核准；binary不入Git，沒有Setup下載／tag／Release。

第一次Windows Inno編譯因引入檔分號註解失敗，已改Pascal //重驗；[原始失敗](../c11-recovery-attempt1-2026-11-09/README.md)固定保存，不倒填為通過。

本地相關180/180。最新全594斷言593通過、1既有ONNX品質預期失敗，但Qt管理23項全過後原生exit -11，原整輪accepted=false；單獨23項補驗exit0不抹除失敗，也不代表根因修復。[本次收據回歸與594原始紀錄](../c11-recovery-attempt2-2026-11-09/README.md)；[首次591與23項補驗](../c11-recovery-prep-2026-11-09/README.md)。Linux退出問題、品質／GPU／RAM軟預算及最終發行門檻保留，接各profile與更完整中斷／乾淨機／人工驗收。

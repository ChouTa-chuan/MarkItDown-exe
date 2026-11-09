# 程序中斷續修第二次Windows實測：Inno暫存產物所有權

2026-11-09（台北），程式0.17.0。run 42574395753／source f84f7fc7ddb60a3f4a805390e70aec6e5132789c：基本資料夾／安裝後app各10項、安裝6段、真正0.16→0.17跨版11段通過。intent中斷後一般Setup明確續修、app10項及移除保留接受（1/3）；first-file續修後完整性檢查遇額外is-ZJEQ9ALB9I.tmp拒絕，第二案app10項尚未完成，整輪recovery=false，不以第一案通過當三案完成。

官方固定issrc（31ee6e35383c530cca8f047216045d3f61ca8be1）Setup.Install.pas顯示先以.tmp抽出新的uninstaller，最終才RenameUninstallExe；未完成的暫存bytes不必等於已登錄的舊版／一般新版uninstaller。本輪未下載完整artifact，不能假稱已直接取得該檔內容。修正以嚴格收據區分：已驗source或已登錄Inno metadata的精確hash／size，或本次私有CI目錄內「操作前不存在、自己握手停點已觀察、終止後且續修前讀取」之新名稱，綁定path／hash／size／PID／stage／測試Setup hash。事後才出現、不在已知程式父目錄、改變bytes或只有is-*.tmp名稱都不能放行。

產物只核對並保留，不直接刪除；原catalog.verify仍逐檔驗真正payload，額外檔只有精確收據可列入，不加通配排除。完整暫存清理仍未驗收，結果會另列保留數量，不把程式可恢復說成乾淨移除所有產物。保留未知文件的原則不變。後續真正Windows三案另記，C11仍2/5／完整7/12。

本次新增3項收據邊界，相關180/180。34模組594斷言593通過＋1既有ONNX品質預期失敗，但Qt管理23項全過後exit -11，整輪仍不接受；首次591與單獨23項補驗紀錄保持不變。後續最後加入新名稱／PID綁定的內容以180相關回歸覆蓋，未宣稱594涵蓋較晚修訂或根因修復。完整登入CI artifact七天未下載，無Setup發行。

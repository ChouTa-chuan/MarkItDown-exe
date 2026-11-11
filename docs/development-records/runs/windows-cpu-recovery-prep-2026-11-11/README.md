# CPU維護程序中斷與恢復準備

2026-11-11（台北），程式0.19.1、架構0.4。沿用既有C06交易日誌／核心鎖／recover，增加真正spawn安裝子程序、抵達停點後由父程序kill、另一新子程序恢復及驗證的六案。

升級published前未提交還原舊active，committed保留新active；修復old_moved與published還原原有效payload；移除old_moved還原，committed完成移除後再正常重裝。六案各用獨立合成根目錄，父程序核對自己Process的PID、隨機token、operation與stage，從不依外部PID檔或模糊名稱終止程序。活著時recover須被真核心鎖拒絕；終止後新程序恢復一筆交易、重複恢復無動作，核對全hash／active、staging與journal清空、合成文件／設定及兩份快取原bytes。

原生CLI將在空PATH、無OCR／Qt控制端，用真正frozen worker驗恢復後版號／CPU provider與固定英文辨識；私鑰只在主程序記憶體，spawn只傳公鑰、簽章catalog與自有路徑。Linux合成ZIP只有transaction_checks_accepted，accepted與windows_executed維持false。

新增5項驗六案真kill／獨立恢復、故障recover不能以no-op掩蓋未完成交易、握手錯PID／token／操作／停點拒絕、提早退出不能當停點、Linux拒絕冒充Windows。初輪161項有1個負例fixture注入到父程序，錯誤日誌完整保留；縮限到恢復子程序後161項通過，補充逐案validation欄位後最後161項也通過、退出0，source_hashes對應最後一輪。本版完整回歸未跑，舊611仍屬0.17.2；Windows尚待原生實跑。

範圍為本次自有程序終止與明確恢復；斷電／OS重啟、所有profile、人工／乾淨機及GPU與ONNX品質仍待。修復案初始payload有效，損壞檔修復另有0.18.1八案證據。C04仍2/4、C11仍2/5、導入7/12／歷史19/25；9鎖／模型／第三方原文與28圖不改，無Setup／tag／Release。

[返回開發紀錄](../../README.md)

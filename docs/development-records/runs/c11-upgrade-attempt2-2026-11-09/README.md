# 跨版 CI 第二次實測：升級後自檢失敗與診斷修正

2026-11-09（台北），程式0.16.0。run 42555556126，source d0050ed29e6a6847741fad87db844422d4c58b41。原生準備成功，Windows基本資料夾10/10、實際安裝後app10/10、安裝／同版修復／移除6段通過。跨版前6段通過：真前版與兩種installer、原0.15 installed app10項、改舊檔／catalog、未知新路徑衝突、真junction及改位置拒絕。升級後check_windows_base子程序失敗，尚未接受升級／回復。

公開尾段選到cleanup的空卸載log，因此不能假稱已取得Windows實際app例外全文；完整登入artifact未下載、七天保留。這次先固定failed_step並優先保留acceptance/driver-error，讓清理步驟不再蓋掉主錯誤。

另發現舊版目錄只刪檔仍可能留下空dist-info。以真正importlib.metadata及「舊目錄先列舉」負向控制，本地可重現空前版遮蔽新版Version為None；移除空目錄才恢復新版本。這是可重現候選原因，非已直接讀到Windows原錯誤。新增只移除已知空舊目錄，遇未知內容先拒絕、不遞迴刪；並在呼叫升級後app前核對全hash／舊目錄確實消失，新增Windows未知舊目錄文件拒絕控制。後續實際結果另記。C11仍1/4、完整7/12，未當作中斷自動回滾、全profile或乾淨機完成。

後續本地修正新增2項（本版本共11項），相關165/165、33模組579（578通過、1既有ONNX繁體品質預期失敗）均正常exit0；followup命名的raw紀錄屬未提交前修正，與上方d0050ed之Windows失敗分開解讀。Linux混合native teardown仍未定位，不宣稱這次已修復。

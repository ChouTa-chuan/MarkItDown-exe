# 建置來源追溯檢核

2026-11-11，程式0.19.1、架構0.4；只更動自有建置／檢核工具與測試。

新增15項合成測試，相關64項通過。initial-fixture-errors.log是首輪測試fixture及模組名稱錯誤，不算產品通過；修正後原文、來源指紋、版號衝突、壞檔／缺檔／連結與路徑反例通過。合成包不是Windows執行證據。

基本與CPU Windows CI新增隨包原文／metadata／原生來源檢核，實際建置接續。啟動器原文來自實際PyInstaller wheel，原始第三方文字、模型、9鎖及28架構快照不改。來源與bundled hash不同會明列，不宣稱位元相同。

此項僅證明建置追溯一致性，CPU套件表為build來源，並非最終runtime SBOM；完整候選清單、應用授權、Qt／Microsoft原生再散布、乾淨機／人工／GPU仍待，不建立Release或交付Setup。

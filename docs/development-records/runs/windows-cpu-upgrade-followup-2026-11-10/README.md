# CPU跨版驗收腳本版號接續

2026-11-10（台北），程式0.19.0。另將原PDF／Qt驗收腳本由寫死1.0.0改為讀取本次component descriptor；來源標記與GUI要求也跟隨該精確版號。沒有重新跑完整PDF／Qt或全專案回歸。相關156項正常退出，該腳本語法編譯通過。

保存fbcf276的首個Windows run42801762340在更新前的公開頁快照與監測（當時仍進行中），不是失敗或成功證據；這次後續提交將由既有concurrency取代舊run再驗最新版，不以快照推斷最終狀態。

原準備紀錄與source_hashes固定不改；本次追加的scripts/check_managed_conversion_acceptance.py SHA另記source-hashes.json。完整Windows結果後續另存，C04 2/4、C11 2/5、導入7/12不提高，無產品發行。

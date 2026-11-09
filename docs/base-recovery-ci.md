# 安裝程序中斷後續修

**實測更新：Windows三停點3/3已接受**，一般Setup恢復後app各10項通過。[原始紀錄](development-records/runs/c11-recovery-2026-11-09/README.md)。各profile仍待，C11保持2/5；非斷電、OS重啟或自動回滾。以下保留準備／模組設計。

程式 **0.17.0**，架構0.4。Windows真實結果待CI；相關177已通過；全591斷言完成但Qt管理模組exit -11，整輪不接受，單獨23項補驗exit0仍保留問題，C11仍2/5。

| 模組 | 責任 |
| --- | --- |
| packaging/base-recovery-code.iss | 固定hash intent、完整暫存檔rename、匹配payload／明確續修確認、最終逐檔hash後清標記；CI停點用ifdef隔離 |
| scripts/base_install_transition.py | 由兩份真正source catalog產生RecoveryToken與所有TargetHashes；不從可修改的installed catalog取得路徑權限 |
| packaging/base-installer.iss | 原位置／reparse／版本／過期檔與未知資料檢查、SetupMutex；續修可識別舊版或新版登錄，不被同版分支跳過舊metadata清理 |
| packaging/desktop_entry.py | frozen入口先檢查未完成狀態，訊息「安裝尚未完成，請重新執行原安裝程式完成修復」，退出3；來源模式不受無關marker影響 |
| scripts/check_windows_base_recovery.py | CI-only三停點握手後終止自己Popen PID樹，再以一般installer明確續修；每案hash／registry／app10項／移除與合成資料保留 |
| scripts/run_windows_base_ci.py --recovery | 需搭配installer及固定前版source；recovery／upgrade／installer旗標分離，任何一項失敗都不算overall接受 |

正常安裝會在寫入程式檔案前保存固定ASCII intent，綁定目標與前版catalog hash；半套標記仍在時不啟動程式核心。重新執行匹配Setup，互動模式預設不續修、確認後繼續；silent工程驗收須明確/RESUMEINSTALL=1。續修只覆寫compiled source宣告的程式路徑；未知文件／目錄及外部資料保留。原16 Setup不具此保護，不能以原舊安裝器當中斷回復；先完成續修，再用相容安裝器明確回復版本。

三停點：intent提交後／第一檔實際複製後／payload完整寫入但舊metadata未清理。停點僅存在/DCiFaultInjection=1測試變體；一般Setup不含此分支，接受的恢復步驟必須使用一般Setup。taskkill只對自己啟動且握手完成的PID與子樹，沒有依名稱終止其他程序。這些是真正Windows程序中斷測試，不等於斷電、OS重啟、部分intent寫入損壞或任意安裝中斷時間的耐久性證明。完整intent暫存檔可恢復，損壞／模糊metadata先拒絕，不自動刪除。

中斷後Inno可能改變unins編號；驗收只使用本次HKCU登錄中、位於受管app目錄的uninsNNN.exe，不從命令字串執行其他參數或猜測固定unins000。舊過期檔遭修改／目錄有未知內容時仍先停止，沒有遞迴刪除資料或自動失敗回滾。各profile、中斷解除安裝、乾淨機／標準帳戶／人工UI／GPU及最終發行另驗。

[準備與本地原始紀錄](development-records/runs/c11-recovery-prep-2026-11-09/README.md)。前版固定990e600（0.16），原controller／spec／generator獨立建置；只保證本輪已知兩份payload，未知舊build不擴大相容宣稱。完整CI報告七天保留，僅公開摘要可另封存，Setup不入Git、不建立Release。

暫存產物收據修正：Windows中斷可能留下新uninstaller等opaque .tmp。驗收只接受已驗source／已登錄metadata的精確hash，或操作前不存在且在自己握手停點已觀察、終止後續修前綁定path／hash／size／PID的建立收據。未知、改變或不在已知父目錄的檔案不能憑is-*.tmp名稱放行；只保留、不盲目刪除。完整暫存清理另列未完成，payload hash、marker、app10項與資料保留標準不放寬。

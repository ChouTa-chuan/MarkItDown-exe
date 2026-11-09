# 基本包跨版本升級與明確回復

**實測更新：0.16 Windows CI 11/11已通過**，原版／升級／回復app各10項，[原始紀錄](development-records/runs/c11-upgrade-2026-11-09/README.md)。各profile仍待，C11為2/5；不是中斷自動回滾或乾淨機完成。以下保留設計／準備過程。

程式 **0.16.0**，架構0.4；Windows真實結果待CI，C11仍1/4。前版固定為43cf811356a7616b784cba09191afdfcb52e16a7（0.15.0）；各選配profile及乾淨機另驗。

| 模組 | 責任 |
| --- | --- |
| scripts/base_install_transition.py | 驗兩份source catalog實際bytes，產生固定版本／catalog hash及過期檔精確路徑／hash及空舊目錄規則，拒同版假跨版／大小寫別名與超出Inno數值範圍 |
| packaging/base-installer.iss | 沿用已登錄目錄，拒未知build／catalog與reparse path；降版須明確 /ALLOWDOWNGRADE=1；只移除已知且未修改的過期檔與空舊目錄；未知內容先拒絕 |
| scripts/check_windows_base_upgrade.py | 原0.15 installer初裝 → 損過期檔／catalog、未知新增檔衝突、真正junction及改路徑的拒絕控制 → 真升級 → 拒未指定降版 → 相容installer明確回復 → 再升級與移除，合成資料與未知文件保持原bytes |
| scripts/run_windows_base_ci.py --previous-source | 前版原source／controller獨立建置，當前build及installer／upgrade旗標分離，任何一項失敗overall就失敗 |
| desktop_app.diagnostics | 自檢新增app_version，讀目前執行的套件metadata，避免只信任registry或Setup標籤 |

回復用的是「新安裝政策＋真正0.15 payload」相容Setup，原0.15 Setup保持原樣、不能追溯加入新保護。新升級器只支援編譯時明列且catalog精確匹配的build；同版catalog不同須使用原匹配installer修復。檔案移除以可信source差異為準，使用者修改過的過期檔會阻止升級。空dist-info仍可能遮蔽Python新版metadata，須由深至淺僅移除已知空舊目錄；舊目錄若有未知文件／子目錄則先拒絕，不能遞迴刪除。failed_step固定主要失敗，避免cleanup log蓋過真正app錯誤。不是任意未知歷史版升級或使用者資料schema遷移。

過期檔在新payload寫入後逐一移除。若檔案被其他程序改寫／鎖住或中途斷電，可能留下部分狀態；本輪不宣稱自動失敗回滾。此類故障恢復、各profile相容仍需後續驗收。外部settings／model／SQLite／output／cache使用唯一合成fixture，並非真實使用者資料。

[準備與本地原始日誌](development-records/runs/c11-upgrade-prep-2026-11-09/README.md)。Setup僅在可拋棄CI測試，不上傳正式產品；完整CI報告七天保留，公開摘要可另保存。前版及本版沿用固定原生來源／四語、鎖檔及授權，不以實測取代最終再散布與簽章審查。

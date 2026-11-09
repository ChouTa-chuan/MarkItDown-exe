# 中斷測試的受管暫存清理

2026-11-10 更新實測紀錄，程式 **0.17.2**、架構 **0.4**。Windows 三案 **3/3** 已實測，實際清理 **1** 份／殘留 **0**，真鎖檔拒絕及未知文件保留通過；[原始紀錄](development-records/runs/temporary-cleanup-ci-2026-11-10/README.md)。

0.17／0.17.1 的 Windows 三停點續修成功，但可拋棄 CI 最後仍留下 1 份 Inno 暫存產物。本次只完成該測試環境的所有權清理機制；**一般使用者的 Setup 沒有新增通配清理或讀取外部收據的入口**，不能把此結果宣稱為正式安裝器任意中斷後都能自動清理。

| 模組 | 責任 |
| --- | --- |
| `scripts/base_temporary_cleanup.py` | 建立本次程序的記憶體收據、預檢整批內容／身分，以 Windows 原檔 handle 標記 delete-on-close |
| `scripts/check_windows_base_recovery.py` | 自身 PID／建立時間與子樹退出確認、三停點真正續修後移除、實際鎖檔反例及未知文件保留 |
| `scripts/publish_windows_ci_summary.py` | 公開保留清理範圍、實際清理數量／案例、鎖檔拒絕與未知暫存文件保留結果 |

刪除權限限於本次測試啟動前不存在、在自身 installer 停點已觀察、終止後且續修前綁定的檔案。收據包含精確目錄／相對路徑、hash／size、檔案身分、PID／停點與測試 Setup hash；排除受管 payload、catalog 及未知父目錄。原來的「已知程式 bytes」只能讓驗收認列並保留殘留，單憑相同內容或 `.tmp` 檔名不能取得刪除權限。JSON 診斷不是可匯入的清理授權。

開始刪除前，必須確認已觀察的自身程序都已退出，拒絕 PID 重用；預檢全部收據，任何缺檔、內容變動、同 bytes 替換、硬連結、symlink／junction 都先停止。Windows 開啟原檔時只分享讀取，拒絕其他寫入／rename／delete；核對 handle 的最終原路徑與身分，鎖定整批後才用 `SetFileInformationByHandle(FileDispositionInfo)` 標記刪除。沒有按名稱殺程序、`Path.unlink` 後備刪除、遞迴清空目錄或忽略非零結果。

CI 每案仍先執行普通匹配 Setup 明確續修、完整 app 10 項及移除驗收，才清理自己的中斷產物。另用真實開檔 handle 驗證 sharing violation 時拒絕清理；放入同類檔名、甚至同 bytes 的未登錄合成文件，清理後必須保持原 bytes。三案全部完成、至少實際清理一份產物並完成鎖檔反例，才能接受清理檢核。合成哨兵的最後移除只屬於 CI fixture 收尾。

本地契約測試保存在[準備紀錄](development-records/runs/temporary-cleanup-prep-2026-11-09/README.md)，本輪 Windows 結果見[實測紀錄](development-records/runs/temporary-cleanup-ci-2026-11-10/README.md)。完整 C11 仍為 2/5、完整導入 7/12、歷史基線 19/25。全 profile、無 Python 乾淨機、人工 UI、一般 Setup 的進一步暫存政策、斷電／任意故障時點及 GPU 另驗；不建立正式 Setup／tag／Release。

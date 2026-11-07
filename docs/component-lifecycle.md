# C06：交易安裝、鎖、修復與移除

程式 **0.4.0**，架構 **0.4**，2026-11-06（台北）。本輪完成 Linux 的元件維護 API，詳見[逐項驗收與程序退出紀錄](development-records/runs/c06-2026-11-06/README.md)。0.5.0 已透過 [C07](component-workers.md)接入實際 CPU worker；0.6.0 的 [C08](component-management.md)已接上背景桌面管理與不切換 active 的 check_health；現有文件自動路由留 C10，Windows／GPU 門檻保留。

## 模組與責任

| 模組 | 功能 |
| --- | --- |
| `components/lifecycle.py` | 安裝、修復、active 切換、版本回復、使用租約、依賴保護與移除 |
| `components/lifecycle_store.py` | 獨立 SQLite schema 1，保存所有權、active／前版與維護日誌；原 C02 登錄仍為 schema 2 |
| `components/archives.py` | ZIP 預檢、受限串流解壓、完整樹驗證與只刪已知檔案 |
| `components/locks.py` | POSIX flock／Windows LockFileEx，共享使用與排他維護；程序退出由核心釋放鎖 |
| `components/cache.py` | 下載快取收據、讀取租約、配額准入與安全回收，已接入 C05 |

主程式更新仍走 Windows 安裝包；C06 不安裝顯卡驅動，也不執行元件目錄提供的任意 shell 指令。

## 安裝如何完成

1. 取得排他維護鎖，先恢復既有未完成事務，再重新驗證 C05 目錄及指定版本。
2. 確認平台、app／worker 相容性、所有權、反向依賴及磁碟空間。既有目錄沒有本服務所有權紀錄時拒絕接管。
3. 記錄維護意圖，在同一資料根目錄的獨立 staging 解壓；逐檔確認檔名、大小與 SHA-256。
4. 檢查依賴均為 active 且健康，呼叫主程式註冊的健康探針。探針之後重新驗檔，不允許把探針改動過的 payload 當成通過。
5. 修復時先把舊目錄搬到事務暫存；再將完整 staging 搬至版本位置。搬移後由 C01 重新驗證檔案、相容性、依賴及健康，不沿用暫存路徑的結果。
6. 最後再次驗證來源信任，把所有權、active／前版及日誌 committed 狀態在同一 SQLite 交易提交，再清理已知暫存。

新版本有獨立目錄，舊版本保留供回復；同版本修復是明確重建已知受管檔案，失敗時還原修復前內容，成功後清理修復前的已知檔案。未知檔案／目錄、外部模型與使用者文件不在刪除範圍。

## 中斷與恢復

主登錄、檔案系統與 active 儲存無法共用一個 SQLite 交易，因此以持久化日誌協調：

| 退出時機 | `recover()` 的處理 |
| --- | --- |
| staging／搬移／登錄後、active 提交前 | 撤回新版本，還原已搬走的舊目錄及登錄狀態；active 保持原值 |
| active 與日誌 committed 已提交 | 保留新 active，驗證目標後完成暫存清理 |
| 日誌、所有權或路徑有未知內容 | 停止並保留資料，明確回報，不猜測來源或遞迴刪檔 |

恢復可重複呼叫；有待恢復事務時不發出使用租約。維護動作會先恢復，日後啟動流程應先呼叫 `recover()`。一般例外會在當次操作嘗試回復；強制退出則由下一次恢復處理。登錄世代維持單調遞增，不以回復覆蓋成較舊世代。

檔案內容有 fsync，POSIX 搬移亦同步父目錄。驗收使用實際 spawn 子程序在不同階段 `os._exit()`／強制終止，不宣稱做過物理斷電或 Windows 檔案系統實測。

## 使用中保護與版本選擇

`lease()` 在整個 context 期間保持共享核心鎖，維護操作需要排他鎖；有使用者時立即回報忙碌，由呼叫端稍後重試，不強制解鎖或刪正在用的元件。初版採保守的整個元件服務鎖，連同依賴一起保護，不在任務中切換版本。

固定空鎖檔不刪除，避免其他程序仍持有舊 inode／handle 而產生兩把鎖。程序結束時核心自動釋放，新程序可以重新取得；不使用 PID 或時間猜測鎖失效。Windows 路徑已有實作，仍需 C11 實機證據。

使用前重新驗證簽章目錄、active 所有權、實檔與健康。更新共用 runtime 前也反向檢查目前 active 元件是否仍相容，不能更新後才把其他元件弄壞。`rollback()` 只選明確前一版本，仍需目前目錄允許且通過相容／依賴／健康檢查；失敗不偷偷換別的引擎。

所有使用者必須經過租約 API 才有這項保護。程式 0.5.0 的 C07 worker 已在自己的程序持有 `.locks/worker-use.lock` 共享 guard；維護／恢復／搬移／active 提交時取得排他 guard，避免父程序退出後仍改動正在使用的檔案。健康 worker 執行時允許取得 shared guard，父程序維護鎖仍保留；控制通道失聯使 worker 退出並釋放鎖。新增目錄逐層 fsync，未宣稱物理斷電驗證。C06 原始合成探針證據保持固定；C07 另存真實 frozen OCR 健康、原生逾時／取消與回歸證據。現有文件自動路由的接線留 C10。

## 移除、資源與快取

- 只移除可確認所有權的選配版本；必要元件拒絕單獨移除。任何已安裝元件仍宣告依賴此版本時採保守阻擋，不自動重選替代版本。
- 未知檔案／空目錄／連結會阻擋修復與移除；修改過的已知檔案也不直接刪除，須先明確修復。移除不會刪來源包檔、設定、外部模型或使用者輸出，移除 active 版本後不自動啟用另一版。
- 安裝／修復／切換／移除可在提交前取消；回復本身不被取消打斷。解壓用 64 KiB 緩衝，可注入共用資源 checkpoint；磁碟准入包含新 staging／保留量，原包與舊版已占用的空間不會當成可用。RAM 仍是軟性預算，與主轉換流程的統一准入接線待 C10。
- C05 現使用持久核心鎖與發布前快取收據，預設配額 8 GiB；下載開始／續傳時先回收最舊、未使用且可驗證收據及內容的完整包。正在安裝讀取的包檔有 shared 快取租約，清理不能進行。
- 片段、未知／損毀檔案、舊版無收據快取及來源不明鎖均保留；無法安全騰出足夠配額時拒絕下載。舊版 O_EXCL 空鎖沒有存活證據，不自動移除。這不等於任意舊快取都能自動認領。

## ZIP 格式與介面範例

初版接受單卷 ZIP32 的 stored／deflate，中央目錄上限 4 MiB、項目 8,192，所有檔案須符合 C01 清單及展開上限。拒絕 ZIP64、自解壓、加密、特殊檔案／連結、路徑逃逸、重複／大小寫衝突與額外空目錄。大型 GPU 格式需後續明確擴充並另驗，不能只提高檔案大小限制。

```python
manager = ComponentManager(registry, verifier, host, trusted_health_checks)
manager.recover()  # 啟動整合時先處理未完成維護。
manager.install(catalog, component_id, version, verified_archive)
with manager.lease(catalog, component_id) as lease:
    # 在此範圍內使用 lease.directory；C07 的 CPUWorkerBinding.run_managed 已封裝此範圍與子程序 guard。
    consume_component(lease.directory)
manager.rollback(catalog, component_id)
manager.remove(component_id, version)
```

驗收指令：`python scripts/check_component_acceptance.py --check C06 --report /tmp/c06-acceptance.json`。最終結果包含 C05 回歸、實際子程序退出明細及是否有跳過；完整專案與實際 HTTPS 回歸另存於本輪紀錄。尚未發行正式元件目錄／金鑰、安裝 Windows 原生引擎或啟用 GPU。

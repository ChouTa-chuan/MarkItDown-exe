# Windows 九項通過與 Qt 正常關閉工具修正

2026-11-08（台北），程式 0.14.0、架構 0.4。[CI #5](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42476509935)（cbb3446）原生 Windows 基本包再次建置成功，實際 python_utf8_mode=true。四語健康／掃描、中文空格搬移／完整自檢、UTF-8 檔名、四語 CLI 與設定保留、缺／損模型／EXE 拒絕外部回退及缺選配共前 9 項通過。

實際 Qt 視窗已開啟並產生自身截圖；正常關閉在 25 秒後逾時，整體仍失敗。來源 closeEvent 顯示：首次背景檢查忙碌時先取消並暫緩主窗關閉，避免銷毀仍跑的 QThread；舊工具只送一次 WM_CLOSE，未在收尾後再要求關閉。

這次只修驗收工具：每輪僅列舉剛啟動的自身 child PID 視窗，在原總期限 25 秒內重送正常 WM_CLOSE，必須真實 exit 0；非零或逾時都失敗，terminate 只保留失敗後清理，不能算成功。回傳正常退出／要求次數供報告，不移除 GUI 或降低成功條件。

新增 2 項跨平台 closing protocol fixture，驗第一個要求被忙碌收尾拒絕後能正常退出，非零／期限到不能冒充成功，且 helper 不呼叫 kill／terminate；這是 Linux 的協定單元測試，不當作 Windows GUI 成功。相關 141/141。下一次 CI 仍須真正 Qt 視窗與正常 exit 0。完整導入 7/12、C03 3/4、C04 2/4、C09 3/4 及既有 19/25 保留。

完整 Windows artifact／自身視窗截圖仍在原 CI（七天）；這裡封存可取得的公開頁及完整短摘要，不宣稱下載了需登入的附件。沒有 binary／模型／使用者文件進 Git。

混合完整程序 555 項斷言（554＋1 既有預期失敗）結束後再次 native teardown exit 139，faulthandler 無 Python frame；不當作完整成功。原 log／exit 狀態保存，另以附上的逐模組 runner 調查，每個 child 都須正常退出，未用 os._exit 或強制終止繞過 teardown。逐模組結果後續另存，不先宣稱通過；應用程式／base spec 與已正常完成 553 回歸的 CI #5 原始碼不變。

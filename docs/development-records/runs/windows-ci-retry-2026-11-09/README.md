# Windows 下載階段診斷與隔離回歸保存

保存日期：2026-11-09（台北），程式 0.14.0、架構 0.4。此處補存 11-08 已實際執行的 31 模組隔離回歸，並於 11-09 讀取上一輪 Windows CI 結果，不把保存日期當成測試日期。

[CI #6](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42477745858) 固定來源下載步驟失敗，原生編譯未執行、Windows job 被略過；完整底層錯誤無可匿名讀取的報告，不能猜為 hash 不符或網路錯誤。此前 CI #5 九項實測仍有效，Qt 正常退出尚待重驗。

這次只補早期日誌：Ubuntu job 明確用 bash 的 -e／pipefail，pip／fetch 的 stdout/stderr 經 tee 保存，always 上傳並由既有公開摘要顯示尾段。原 SHA／長度／來源／重試與 Windows 正常退出門檻完全保留。以真正 bash 失敗命令＋tee 驗證仍返回非零，避免記錄日誌時吞掉失敗。

先前混合 555 項斷言完成後 native teardown exit 139 仍未定位；本頁保存逐模組全部原始 JSON／log：31 個真正 child 全部正常 exit 0，共 555 項、554 通過、1 個固定 ONNX 繁體品質預期失敗、0 跳過。沒有用 os._exit／kill 繞過 teardown，也不把逐模組通過宣稱為已修好混合退出問題。原 runner 見前次 windows-ci-close 紀錄（固定 555 項版本）。

本次沒有改應用程式或已通過九項的 Windows 轉換碼，完整導入 7/12、C03 3/4、C04 2/4、C09 3/4、既有 19/25 不變。沒有 Setup、Release、GPU 或乾淨機驗收；沒有引擎／模型／個人資料入 Git。

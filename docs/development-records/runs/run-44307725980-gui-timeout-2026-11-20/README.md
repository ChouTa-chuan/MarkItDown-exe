# run 44307725980 Windows 失敗原因（2026-11-20 查明）

## 做了什麼
PR 31 合併後的 main push（提交 35233ae）中，「Windows 2022 base build and OCR」失敗。2026-11-19 的 planner 複查因下載不到報告 artifact，只能判定為間歇性問題，查不到根因。2026-11-20 使用者同意把 artifact 主機 `productionresultssa7.blob.core.windows.net` 加進環境的網路允許清單後，協調者下載報告 artifact，並在到期前保存失敗原文。

## 結果
- 失敗步驟：升級測試要先重建前一版 990e600（0.16.0），失敗發生在前一版的 `check_windows_base.py` 驗收。前一版**建置成功**（`build_verified: true`）。
- 驗收共 15 個 invocation，回傳碼全部符合預期，9 項 checks 通過，其中包含四語 OCR、中文路徑、模型與引擎被竄改時拒絕。
- 唯一錯誤是 `AssertionError: Qt Windows window did not open`：GUI 檢查在 25 秒內沒等到可見視窗，或程序已先結束。
- 前一版的 `gui.log` 當時沒有複製進報告，所以無法區分以上兩種情況。
- 判定：與 A13b 無關，也不是產品功能缺陷。最可能是 hosted runner 上凍結程式冷啟動超過 25 秒。同一棵樹在 PR head 與後續兩次 main push 都通過。

## 對應修正（同一 PR）
- `scripts/check_windows_base.py`：
  - 等待時間由 25 秒放寬為 60 秒（`GUI_OPEN_SECONDS`）。只延長等待，視窗必須出現、程序必須仍在執行，驗收標準不變。
  - 錯誤訊息分清楚「程序已結束（附結束碼）」與「逾時仍無視窗」。
- `scripts/run_windows_base_ci.py`：前一版的 `acceptance/gui.log` 一併複製進報告。

## 限制
- 前一版用的是自己固定的檢查程式，等待時間仍是 25 秒。在 previous-source 的固定點往後移之前，升級測試仍可能偶發同樣的失敗；不過之後的報告會帶 `gui.log`，可以判斷是哪一種情況。
- 依 AGENTS「原始失敗要留紀錄」，這裡只保存兩個小型原始檔。其餘 artifact 成員是 `previous-base-build.log`（一行摘要）、`windows-build.json` 兩份與 `build-error.log`，只記錄 artifact 雜湊。

## 來源
- run 44307725980，job 134814609713。
- artifact `windows-base-validation-reports`：id 14428139204，4145 bytes，digest `sha256:b6829c6c953a4ecee498f0660e0d691434feb63205f26fa96b7998363593c1ad`，到期 2026-11-25T12:54:42Z。下載後的 zip SHA-256 與 digest 相同。

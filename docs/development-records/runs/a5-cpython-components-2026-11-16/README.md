# A5：CPython 隨附元件逐檔版本與原文

2026-11-16（台北），程式0.19.1／架構0.4。基線為已合併 PR 1–8 的 `e87de4b33073e548802e08a7b37c9934429ca65b`，A4 已完成，使用者確認通過 Claude reviewer。A5 使用自己的 `codex/a5-cpython-components-20261116` 分支，沒有修改別人的分支或直接推 main。

## 實作與證據層級

- [cpython_components.py](../../../../scripts/cpython_components.py) 在既有 native 資產管線中為 OpenSSL、libffi、SQLite 建立逐檔清單；只路由已判為 `python-runtime` 的來源，同名 wheel／系統檔不認領。基本包與 CPU 使用既有共同管線，不擴充選配系統。
- 固定的 [來源 profile](../../../../packaging/cpython/windows-3.12.10/profile.json) 保存 Windows CPython 3.12.10 x64 的官方 commit、`patchlevel.h`、建置設定及原文 hash。重新命名／改標籤不能套用另一 patch 版，缺少 profile 或不符架構就失敗。來源檔原位元組留在 repo，只有必要原文與清單隨包。
- OpenSSL／libffi 保存官方相依庫的完整原文；SQLite 保存官方相依來源標頭的第一個完整註記區塊，附來源整檔 hash、Git blob 及原始 byte offset／length，沒有假稱保存整份來源標頭。完整來源說明見 [packaging/cpython](../../../../packaging/cpython/README.md)。
- PE `FileVersion`、建置宣告版本、與已載入檔 source hash 相符的 OpenSSL／SQLite 執行期版本分欄。**libffi 只有建置宣告時，`build-declaration-only` 仍是限制，不是獨立二進位版本認證**。未知欄位不補值；probe 失敗留明確原因，不能借另一份同名 DLL 的版本。
- 原文與清單的 hash 重新驗證、native 檔覆蓋及 runtime probe 關聯均有反例；候選清單逐檔連回原文，但沒有因此填 owner 或關閉 SBOM／再散布。新增清單及原文可能增加實體檔案／未對照總數，不能拿它與 PYZ 未知模組數互相抵銷。

## 本機驗證與原始失敗

- 首次程式來源 `b52cec1` 的混合與獨立回歸接受，原始小型結果為 [mixed-before-source-version-check.json](mixed-before-source-version-check.json) 與 [isolated-before-source-version-check.json](isolated-before-source-version-check.json)。這不是後續新增 patchlevel 核對的驗證。
- 自我查驗補上官方 `patchlevel.h` 與原生架構核對。`c37ea5f` 加當時文件工作樹的完整回歸被**過期歷史索引**擋下，混合與獨立程序皆 exit 1；原始結果見 [mixed-before-index-refresh.json](mixed-before-index-refresh.json)、[isolated-before-index-refresh.json](isolated-before-index-refresh.json) 與 [index-failure.txt](index-failure.txt)。索引重建後相關測試通過，沒有放寬 driver 接受條件。
- 後續自我查驗保留一般 CLI 單一 JSON 摘要，CI 才另發有界 `CPython components` annotation；合成 fixture 不當成 Windows 實證。來源與最終執行狀態見 manifest 及 progress.json；完整日誌只留 `/tmp/markitdown-a5-audit`，不保證環境更換後存在。
- 執行方式：`PYTHONPATH=src:tests`、offscreen Qt、固定四語 `TESSDATA_PREFIX`、OMP／OpenBLAS／MKL 各一執行緒，以 `run_mixed_regression.py` 及 `check_isolated_tests.py` 執行，計數取 Linux workflow 的 EXPECTED_TESTS。結果 JSON 保存來源／程序退出，現況數字只記 [progress.json](../../../progress.json)。
- 上游、原始依賴授權及兩種 profile 的固定版本檢核通過，既有 vendor／模型／架構圖未改。A5 Windows 原生實證由本階段 PR CI 取得，本機 Linux 的 `applicable=false` 不算 Windows 通過。

## A4 現況與 109 基準的指定修正

- STATUS 與 progress.json 已改為 A4 完成（PR #8）、main 已合併 PR 1–8，next 改為 A5／後續 A5b。沒有把還原 A4 舊 Forbidden／等待合併當下一步。
- `unresolved_files` 是包內實體檔案沒有 owner 的數量；EXE 內 PYZ 的未知 Python 模組由另一欄計數。排除五個 namespace 不會自然使實體檔案計數減五。程式口徑已確認；兩輪總數相同不能證明未知檔案集合相同。
- **109 的 A3 基準已找到**：[a3-109-baseline.json](a3-109-baseline.json) 補存 PR #6 的 Windows run `43797247571`、job `133069447371` 公開 annotation，含暫時 merge／完整報告 hash。**完整逐檔基準：未保存於專案，本輪未取得完整 artifact**，所以不補造逐檔變化。
- 本輪使用者明確要求在既有 A4 README 補註，原版先保存為 [a4-README-before-a5.md](a4-README-before-a5.md) 與 [a4-manifest-before-a5.json](a4-manifest-before-a5.json)，再更新 A4 README 的索引 hash。A4 原始 `ci-results.json` 未改；此為特定補註，不是一般改寫舊證據的規則。

## 接續與限制

A5 PR 須核對全部 CI，以及公開 annotation 的逐檔來源／版本／原文；libffi 的宣告限制保留。這次來源盤點不是 A6 的固定版本候選重產，不取代 `cb8f24d` 原候選；Qt 原始碼義務、完整再散布、乾淨機／人工／GPU 仍未關閉。沒有 Setup、worker、模型、tag 或 Release 發布。

[返回歷史索引](../../../history-index.md)

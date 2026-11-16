# A4：PR 8 首輪 Windows 與 Linux CI 實證

2026-11-16（台北），應用程式／架構版號不變。本輪恢復 GitHub API 後建立 PR #8，將原先尚未執行的 A4 Windows 驗證補齊。

| 來源 | 提交 |
| --- | --- |
| 原本程式與本機測試 | `8c2645156babedbb8152f1113017366997cf3fb0` |
| 本輪受測 PR head | `ca71bfacbfde64d152dd9f043171303c21c5573e` |
| 當時 base main | `6032f9e6bc1b7b2d52af8d23b0c05395d5b3eefe` |
| CI 實際暫時 merge | `dd72bf4c363fc5bf17029c4db63b0cad71895f71`（Windows annotation 的 commit／source_commit） |

兩個 head 之間只有文件與已合併的 Claude 設定差異；A4 程式、spec、測試與驗證流程沒有改變。後續加入這份結果的純文件提交，仍需以 GitHub 上該 head 的實際 CI 與 PR 合併狀態核對，不能把首輪結果當成任何後續提交已執行的測試。

## 實際結果

| 流程 | run | 結果 |
| --- | --- | --- |
| Linux 完整回歸 | [43804367945](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43804367945) | Success；混合程序及獨立模組步驟皆通過 |
| Windows 基本包 | [43804367902](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43804367902) | 原生輸入與 Windows 建置／OCR／安裝／升級／恢復全部通過 |
| Windows CPU 元件 | [43804367917](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43804367917) | 獨立 CPU 建置、功能、維護、跨版與程序恢復全部通過 |
| 歷史索引 | [43804367944](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43804367944) | Success |

真實 API 回應的必要欄位與 JSON annotation 原值另存 [ci-results.json](ci-results.json)，hash 見 manifest。現況計數以 [progress.json](../../../progress.json) 為準，不在說明重抄。

- 基本包的 `python_archives.unknown_names` 為空，`unknown_modules=0`，且 `build_only_modules_absent=true`。原本 setuptools namespace 的缺口已透過實際排除關閉，不是改分類掩蓋；CPU 元件的模組清單仍全部可對照，未套用基本包排除規則。
- 基本包 annotation 的 `overall_accepted`、`installer_accepted`、`upgrade_accepted`、`recovery_accepted` 均為 true；CPU 的功能、同版維護、跨版與程序恢復亦接受。原生身分查詢沒有錯誤，既定排除檔案仍未出現。
- Windows 原生來源目錄顯示 runner 的 CPython 為 **3.12.10**。這是 Windows runner 的實際來源，不等於 Linux 的 patch 版；A5 逐檔盤點需以此輪實際使用的版本、檔案與安裝授權為起點，不能直接套用別的版本。

## 保存範圍與限制

- 本次只讀 GitHub API 的 run／job 狀態、公開 annotation 與 artifact 中繼資料。沒有下載完整 artifact 或產品本體；下表 hash 是 GitHub 回傳的 digest，沒有宣稱已在本機逐位元組驗證。
- 嘗試 `gh run view --log` 時，日誌主機 `results-receiver.actions.githubusercontent.com` 回覆 Forbidden。此限制不影響查 CI、開 PR 或合併；使用公開 annotation 核對 Windows 真實結果。Linux 在 API 層確認工作流程／每個步驟 Success，未讀取本輪原始回歸 JSON，因此現況保留前次已保存的本機計數及其來源，不冒充本輪讀到的原始計數。
- 所有原始日誌／完整報告仍在該次 Actions，未將大型附件複製進 repo。舊證據與原始失敗維持原樣。
- PR 暫時合併建置不取代 `cb8f24d` 的原候選，不代表新的可交付安裝包。清單總數變化不等於新候選已逐檔完成授權分類，A6 仍需重產固定來源候選報告。
- Qt 本體原始碼對應、CPython 第三方元件逐檔原文、完整 runtime SBOM／再散布、乾淨機／人工／GPU 仍待；本次不提高產品里程碑，不把 ONNX 繁中 expected failure 當品質通過，也沒有 Release、tag 或 Setup 發布。

完整 Actions 報告的 ID、digest 與到期時間見下表及 ci-results.json；期限為 GitHub API 回傳的 UTC。

| 流程 | 報告 artifact／ID | GitHub digest | 到期 UTC |
| --- | --- | --- | --- |
| linux | linux-regression-reports／14198245287 | `sha256:9dc45b63f9613acbefafedd6040f8a0c25e7c5cce2452ee9c35e19cb2c1ed016` | 2026-11-30T04:32:35Z |
| base | windows-base-validation-reports／14198227351 | `sha256:fd7df0cc775cb2235f8fc84a0390b3af43e23c7bb58bf97661c1e60f94eb94d3` | 2026-11-23T04:44:29Z |
| base | windows-native-build-reports／14197344631 | `sha256:3cd45e9ccb1163e90b8682d87055662f99a4c7aea4d7945b1aac1b4d3bd75d9b` | 2026-11-23T04:31:32Z |
| cpu | windows-cpu-validation-reports／14198745588 | `sha256:daaceaf6ad657cd3cba8b29243b961fdc4497318264ce8ada70e929d7b3d52a4` | 2026-11-23T04:43:36Z |

[返回歷史索引](../../../history-index.md)

## 2026-11-16 A5 補記：為何 unresolved_files 仍為 109

依使用者要求補充，原版 README／manifest 已先另存於 [A5 紀錄](../a5-cpython-components-2026-11-16/README.md)，原始 `ci-results.json` 沒有改動。

`unresolved_files` 與 `python_archives.unknown_modules` 是不同層級。A4 版本的 [candidate_inventory.py](https://github.com/ChouTa-chuan/MarkItDown-exe/blob/e87de4b33073e548802e08a7b37c9934429ca65b/scripts/candidate_inventory.py) 先用 `snapshot()` 列舉包內普通實體檔案，再由 `inventory()` 計算 `sum(not row['owners'] for row in rows)`；它不把 EXE 內每個 PYZ 模組再當成實體檔案。`base.spec` 把 `PYZ(analysis.pure)` 交給 EXE，而 EXE 的 owner 已另行記為 PyInstaller／自有應用程式。

因此排除 setuptools 的 PYZ 模組、讓 `unknown_modules` 由 5 變 0，**不代表實體檔案的 unresolved_files 應由 109 減去 5**。這個計數口徑已由程式碼確認；但僅有總數不能證明前後未對照的實體檔案集合完全相同，也不代表它們已完成授權審查。

**109 的前版基準出處已找到並補存**：A3／[PR #6 Windows base run 43797247571](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43797247571/job/133069447371)，check-run `133069447371` 的 `bundle-provenance` 公開 annotation 記錄 `unresolved_files=109`、PYZ `unknown_modules=5`。該次 head 為 `fc022585a18f7c9758a818b38d1ac0e123c89b3b`，報告來源為暫時 merge `a91280b807d88a59735aabe6c97a345f7df411b7`，完整報告 SHA-256 為 `12bd2bcd25a619d2ecf96099e0046546d3c7fbde00c6e338b9196c82a08a23b3`。公開摘要原值及查詢位置保存於 [a3-109-baseline.json](../a5-cpython-components-2026-11-16/a3-109-baseline.json)。

A4 本輪 `ci-results.json` 的基本包來源是 `dd72bf4c363fc5bf17029c4db63b0cad71895f71`，記錄 `unresolved_files=109`、`unknown_modules=0`。**前版完整逐檔基準：未保存於專案；本次也未取得完整 artifact**，故這裡只確認兩次公開摘要的數值與計數口徑，沒有補造 109 個檔案的逐檔變化。

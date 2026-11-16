## A. 分支與 PR

Head：`codex/a4-setuptools-audit-20261116` → base：`main`。

本輪只處理 STATUS C 節的 A4。從接手時尚未合併的 PR #6 head 開出自己的新分支，後以 merge 納入已合併 PR #6／#7 的 main（6032f9e）。父 PR 都已合併，本 PR 只含 A4 差異；沒有推送別人的分支或直接推 main。程式／測試來源：8c2645156babedbb8152f1113017366997cf3fb0。

## B. 完成事項與驗證

- Linux 匯入圖重現：urllib3 的選用 backports 匯入經 PyInstaller 別名帶入 setuptools 父套件、編譯工具及原有 namespace。基本包排除建置用 setuptools；建置環境、原文、固定依賴及 CPU 元件不變。
- spec 與建置後來源檢核都拒絕 setuptools 根／子模組，基本包公開 CI 小結新增 `python_archives.build_only_modules_absent`。反例確認重算資產 hash 不能繞過、相似名稱不誤擋、CPU 規則不變。
- Linux 隔離基本包實際建置；直接檢查 EXE 的 PYZ，沒有 setuptools。空 PATH 下通過既有 frozen core／格式驗收。
- 完整混合回歸與所有獨立模組 exit 0；真實計數只見 docs/progress.json。唯一 expected failure 保留既有 ONNX 繁中品質缺口，未把它列成品質通過。
- STATUS 原檔封存、現況／進度與 CHANGELOG 更新、索引與頁面重建。小型結果、hash、原始失敗與限制在 docs/development-records/runs/a4-setuptools-audit-2026-11-16/。

## C. 未完成／阻擋／下一步

A4 Windows CI 尚未執行，不能用 Linux 結果推定。合併前需全部 CI 通過，確認 Windows `unknown_names` 沒有 setuptools namespace、`build_only_modules_absent=true`，且既有建置與自動驗收通過；有失敗先修正自己的分支。沒有新的候選發布、乾淨機、人工或 GPU 驗收；runtime SBOM／再散布旗標維持未完成。

建立 PR 後的有期日誌／artifact 依各 workflow 的保留期；本機回歸與凍結驗收不是 GitHub CI。A4 關閉後接 A5，再接 A5b 與 A6。

## D. 新增規則與決定

使用者 2026-11-16 明確指示：本輪從 A4 接手，推送自己的新分支並開 PR；CI 全通過且依 AGENTS 完成查驗即可使用 Merge 合併，不直接推 main、不推別人的分支。沒有擴大到其他打包變更或產品發布。

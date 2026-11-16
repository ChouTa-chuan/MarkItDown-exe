# A5b：Qt 發布來源與版本對應

2026-11-16（台北）。從 main `c51089a258b820b95af51816e516a05300dfb7c4`（PR 1–9 已合併）另開 `codex/a5b-qt-source-20261116`。第一個提交 `c25e3c2` 已先完成使用者指定的決定復原、main／next 與 A5 最終 CI 參照；[該紀錄](../a5b-handoff-corrections-2026-11-16/README.md)原樣保留。

## 已完成

- [固定來源 catalog](../../../../packaging/qt/6.12.0/catalog.json) 保存官方 `v6.12.0` tag 解參照：Qt supermodule `ef25002ed292b132d1ed3246bfcee1d24a9cd966`、qtbase `025bdad181de241e81bf853c8a2d7bf3d19261a9`、PySide／shiboken `f50facb83fc3dc5f3240c854668c7a6dd93871b2`。qtbase 的 tag 與 supermodule gitlink 相同；其餘完整模組提交保存在 catalog，並逐一確認官方鏡像有該提交。
- 原始 `.gitmodules`、CMake 版本宣告及生成模板保存原位元組、SHA-256 與 Git blob。模板不冒充已填入版本；真正 PySide／shiboken 版本取其 `.cmake.conf`。qtbase 的 prerelease 預設也照原文保留，不能據此推定官方 wheel 的完整 build 設定。
- 基本包新增 `licenses/qt-sources.json`，含固定模組來源下載連結及本次建置觀測；既有資產 manifest 覆蓋其 hash。建置離線重驗 catalog／原始來源，再讀真正 `QtCore.qVersion()`、實際 PySide／shiboken 版本、平台、Qt build 字串與 Core extension 指紋；版本不符拒絕套用。CI 另發 `Qt release sources` 摘要。
- [Qt／LGPL 隨包說明](../../../../src/desktop_app/data/licenses/qt-lgpl-notice.md) 提供 qtbase、SVG、QML／Quick、工具與綁定的固定來源，並說明 supermodule tarball 不含子模組、如何按固定提交取得完整模組。第三方說明同步修改產生範本及產物，原始授權全文未改。

## 驗證與來源

程式來源 `bc2f77c46de1903877ab1a2ee4e489f2c7559aac` 的 Linux 混合及獨立模組完整回歸均 exit 0；原始小型結果見 [mixed-result.json](mixed-result.json)、[isolated-summary.json](isolated-summary.json)，現況計數只記 [progress.json](../../../progress.json)。只有既有 ONNX 繁中 expected failure，沒有 failure／error／skip。執行採 offscreen Qt、固定四語 TESSDATA_PREFIX、OMP／OpenBLAS／MKL 單執行緒，driver 為既有 run_mixed_regression.py／check_isolated_tests.py。

[windows-wheel-evidence.json](windows-wheel-evidence.json) 是 **Linux 上對既有 hash 鎖定 Windows wheels 的靜態檢查**：核對原輪檔 hash、頂層 Qt DLL 的 PE FileVersion 及生成版本檔，使用暫存工具 pefile 2024.8.26，未新增專案依賴。Qt DLL 顯示 `6.12.0.0`；這是整個 wheel 上位集合，不是 frozen 候選逐檔清單或 Windows 實際執行驗收。原輪檔可按既有 PyPI／鎖定來源重取，不加入 repo。

[module-source-availability.json](module-source-availability.json) 確認每個固定 gitlink 在官方 Qt GitHub 鏡像存在，未下載完整模組原始碼。[linux-qt-observation.json](linux-qt-observation.json) 是本機 Linux 實際建置解譯器的觀測，不能當 Windows。上游、原始授權及兩種平台 profiles 檢核通過；[來源探索及命令修正](exploration-notes.txt)照實記錄，不當成產品回歸失敗或通過。

本次紀錄建立時尚未執行 A5b PR 的 Windows CI；後續 Windows 原生觀測應另存新目錄，不能改寫這份 Linux／靜態證據的來源。

## 接續與界線

A5b 證明官方發布來源位置及版本對應，不宣稱已獨立核實官方 wheel 的完整 build 修補／參數、能逐位元組重建或完整 LGPL／再散布義務均完成。建置解譯器的 runtime 也不冒充 frozen 候選獨立探測。既有固定候選 `cb8f24d`、SBOM／再散布／發行旗標與產品里程碑不提高，沒有 Setup／worker／模型發行或 Release／tag。

**A5c 僅列待辦，本 PR 不處理**：CPython runtime probe 失敗拒絕、缺失 OpenSSL 原文反例、extension observed_version 說明由後續獨立 PR 完成，該 PR Windows CI 全部通過才合併。接續 A6 固定候選及整體審閱仍待。

[返回歷史索引](../../../history-index.md)

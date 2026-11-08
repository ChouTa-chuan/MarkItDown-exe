# C03 原生來源與 DLL 靜態檢查開發紀錄

日期：2026-11-08（台北）。程式 **0.11.0**、架構 **0.4**。完成靜態檢查機制；**C03 來源／授權子檢核仍未完成**，C03 1/4、C04 2/4、C09 3/4，完整導入 7/12、既有 19/25。

| 保存內容 | 證據／範圍 |
| --- | --- |
| [acceptance.json](acceptance.json)／[日誌](acceptance.log) | 最終 64/64；20 項新來源／PE 反例及 44 項 profile／診斷／授權回歸 |
| [full-regression.log](full-regression.log) | 478 項：477 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過 |
| [inspection.json](inspection.json)／[日誌](inspection.log) | 真實來源 7/7 靜態檢查；56 AMD64 PE、入口閉包 34、靜態未用 22、32 DLL 授權證據待補 |
| [required-redistribution.json](required-redistribution.json)／[日誌](required-redistribution.log) | 不帶可選頁面／objdump 的 5 項檢查；要求可再散布正確退出 1，封裝維持禁止；退出碼另存 provenance |
| [provenance.json](provenance.json)／[來源頁面](source-pages/) | 官方 URL、tag、下載 hash／bytes、官方發布 digest、7-Zip 檢查工具來源；頁面為取得時原始文字，非最新狀態 |
| [source-notices](source-notices/) | 從實際 installer 解出 LICENSE、AUTHORS、README.md 原始位元組；只確認 Tesseract 兩檔映射，未覆蓋所有 DLL |
| [installer-list.log](installer-list.log)／[解包紀錄](installer-extract.log) | 僅 7-Zip 列表／解包，不執行安裝器；入口與主 DLL 的 objdump 原始解析另存 |
| [initial-dll-name-scan.log](initial-dll-name-scan.log) | 初始八筆 MinGW `+` 名稱拒絕；修正後真實檢查通過，回歸也加入此名稱 |
| [initial-tests-error.log](initial-tests-error.log)／[初始 64 項](initial-acceptance-error.log) | 連結拒絕冒出底層 IntegrityError；轉為 NativeAssetError 後重跑，最終成功。初始 JSON 亦保存 |
| intermediate 報告／日誌 | 名稱修正後的 API 掃描及初版 CLI 真實檢查；最終加例外正規化後另報告，不混作同一次 |
| 授權／上游／profile verify 日誌 | 既有 221 原授權資產、上游與固定依賴閉包通過；不代表新增 DLL 全部已審 |
| screenshots／progress-browser.log | 當輪最終視覺進度、手機與分頁／鍵盤／計數測試；初次瀏覽器紀錄另存，四語目標橫幅修正後重驗；沒有 Windows UI 驗收 |
| integrity.json／manifest.json | 舊紀錄、快照、鎖定與授權保存檢查；本目錄逐檔 SHA-256／bytes |

檢查報告 `accepted` 只表示靜態機制成功。`bundle_allowed`、再散布、Authenticode、動態載入、Windows 執行及完整 C03 都未通過；32 DLL 缺口指本專案來源／原文證據未齊，不等於判定上游無授權。後續需補確切來源／版本／原文義務或最小原生建置，才整合完整基本包及 Windows 實驗證。

installer／EXE／DLL、7-Zip binary、模型、venv、快取及使用者真實文件均未入庫。原繁體品質影像／目標與所有既有快照、舊附件保持固定；沒有重建 frozen／Windows 安裝包、執行 GPU 或發布產品。

# 開發紀錄保存核對

核對日期：**2026-11-06（台北）**。核對既有基準提交：[`3d0e005`](https://github.com/ChouTa-chuan/MarkItDown-exe/commit/3d0e0056d46229a4478225b2904837b71deeef76)。本次補存由後續 Git 提交另行保存，程式版本維持 **0.1.1**、架構版本維持 **0.4**。

## 核對結論

原有 **18 次 Git 提交、374 個受版本控制檔案**均已同步 GitHub。此次下載基準提交的 GitHub 原始碼 ZIP，逐一以 Git blob 雜湊比對全部 374 檔，而非只核對首頁；本地／遠端分歧為 0／0，Git 物件完整性檢查通過。

主要工程文件已保存，但部分先前生成的截圖、示例與原始日誌只存在工作區。本次再補存 **75 份現有工程產物**：12 張畫面、8 份範例／輸出、53 份原始日誌及 2 份觀察／語法樹紀錄，各附 SHA-256。

這項結論適用於可取得的 Git 歷史、專案文件與工程產物；不宣稱已備份所有聊天逐字內容或已消失的暫存紀錄。

## 開發事項與保存位置

| 紀錄範圍 | 專案位置 | 核對結果 |
| --- | --- | --- |
| 每次程式修改與版本 | [完整提交索引](history.json)／[CHANGELOG](../../CHANGELOG.md)／[pyproject.toml](../../pyproject.toml) | 基準 18 次提交皆可追溯；舊 0.1.0 與新 0.1.1 分開記錄 |
| 需求、架構、模組及里程碑 | [完整架構指引](../architecture-guide.md)／[決策紀錄](../decisions/) | 已保存；原 v0.3 內容仍可從對應 Git 提交讀取 |
| 舊／新／首頁／第四節詳細圖 | [架構圖版本索引](../architecture/README.md)／[快照雜湊](../architecture/snapshots.json) | 四份快照逐一核對，包含第四節原圖與責任表 |
| 功能進度與元件導入 | [開發狀態](../development-status.md)／[視覺頁](../progress.html)／[資料來源](../progress.json) | 既有 19/25、新導入 0/12，沒有因保存紀錄提高進度 |
| PDF／表格／OCR 品質 | [驗證摘要](../validation-results.json)／[版面矩陣](../layout-acceptance.md)／[OCR 比較](../ocr-quality-sample.json) | 已保存通過、限制與 ONNX 已知缺口 |
| 實際 Linux frozen／工具檢查 | [內建自檢](../installation-self-test-linux.json)／[公開 PDF](../layout-frozen-results.json)／[PowerShell 工具](../windows-tooling-results.json) | 已保存平台與結果；Windows／GPU 未執行不改列通過 |
| 安裝、依賴與未來 Windows 流程 | [packaging](../../packaging/)／[手動工作流程](../../.github/workflows/windows-build.yml)／[Windows 驗收指引](../windows-acceptance.md) | 來源與鎖定檔已保存；沒有 Windows 實測產物可補存 |
| 授權與手冊 | [授權檢核](../license-inventory.md)／[原文目錄](../../src/desktop_app/data/licenses/)／[操作手冊](../../src/desktop_app/data/user-guide.md) | 原 58 套件／214 文件基線保留，最終 Windows 再散布審核仍待完成 |
| 中文註解與維護規則 | [自有程式](../../src/desktop_app/)／[AGENTS.md](../../AGENTS.md) | 程式碼已保存；補註解前的 33 份可執行 AST 本次重比對一致 |
| 畫面、示例、原始執行日誌 | [截圖索引](screenshots/README.md)／[範例索引](examples/README.md)／[日誌索引](logs/README.md) | 本次從工作區補存，保留失敗與早期狀態 |

## 原始產物與驗證方式

- [manifest.json](manifest.json)：75 份補存檔案的大小、SHA-256、原始檔名及用途。原始來源提交未記錄者保持 `null`，不推估版本；檔案修改時間只作觀察。
- [history.json](history.json)：基準提交以前全部可達 Git 歷史、父提交、台北時間、當時程式／架構版本及 GitHub 固定連結。
- [preservation-audit.json](preservation-audit.json)：整份 GitHub ZIP 的比對證據、提交／檔案／架構快照數、保留範圍及限制。
- [裝置觀察](observations/device-diagnostics.json)：既有 Linux 無 NVIDIA 推論證據的查詢結果。
- [補中文註解前的可執行 AST](observations/pre-comment-executable-ast.json)：原先保存的 33 份語法樹，本次與目前程式重比對一致；不是重新執行功能測試。

原始日誌包含當時的成功、預期失敗、調試失敗與建置資訊，保持原位元組與空白。現有 153 項功能測試摘要仍是 152 通過、1 項已知品質預期失敗；本次保存核對不宣稱重新跑過功能測試。

## 保存邊界

- 沒有將整段聊天作逐字匯出；主要決策、修改、版本、驗證與圖另以工程文件保存。
- 無法取得的更早原始草稿、已消失暫存日誌，不能事後補造或聲稱逐位元組完整。
- venv、模型下載快取、wheel、編譯產物及重複原始碼 ZIP 不提交 Git；保留其來源、雜湊／鎖定、授權與重建腳本。
- 沒有 Windows／GPU 實機報告，因為相關驗收尚未執行；完整保存紀錄不代表開發功能全部完成。
- 這次只補保存生成畫面、合成／上游公開樣本及工程日誌，不包含使用者真實文件或環境秘密。

[回專案首頁](../../README.md) · [架構圖紀錄](../architecture/README.md) · [開發狀態](../development-status.md)

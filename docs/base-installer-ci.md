# 基本包安裝、同版修復與移除 CI

程式0.15.0、架構0.4。此為 C11 的 hosted Windows 子檢核，不等於無Python乾淨機或完整Windows生命週期。0.14基本資料夾已通過10項；本版新增安裝器需由新CI真正驗證。

## 模組與流程

| 模組 | 責任 |
| --- | --- |
| packaging/base-installer.iss | 獨立開發預覽AppId、per-user、中文路徑；無遞迴刪除指令；與舊手動Desktop發行流程分開 |
| scripts/base_install_catalog.py | 完整檔案／版本／安全名稱與hash，expected取同次建置來源；不能改安裝catalog就重新取得信任 |
| scripts/check_windows_base_installer.py | 僅可拋棄Windows CI；拒已有註冊／捷徑，真安裝、10項installed app檢查、實際破壞及同版修復、四語自檢、移除與資料哨兵保留 |
| scripts/run_windows_base_ci.py --installer | 順序先驗原生資料夾，再驗安裝；base、installer、overall分開記錄，任一失敗都回傳非零 |
| scripts/check_isolated_tests.py | 完整測試逐模組正常退出，必須符合明確總數及固定ONNX品質預期失敗；不掩蓋混合teardown問題 |

安裝器包含基本程式與四語，不下載選配。測試先核對每使用者registry與Start Menu不存在，使用全新工作目錄／中文安裝路徑。外部fixture只新增唯一子目錄，合成settings／model／SQLite／output／cache不是真資料；另在app內放未追蹤文件，移除受管檔案時須保留。不能把哨兵保留宣稱為完整跨版資料遷移。

同版重新安裝會修復被刪入口及被破壞模型，必須重驗catalog與四語完整自檢。此輪不假造較高AppVersion當升級，也不把解除安裝當跨版回復。完整C11仍需真升級／回復、各profile、無Python乾淨機離線與人工UI。

編譯工具使用runner現有Inno，保存實際工具／license與Setup hash；不更改官方來源或核准再散布。Setup只在工作目錄使用，不上傳正式安裝品，僅保存報告。原文／hash和實測不取代最終授權／SBOM／簽章與發行審查。

本地13項新增、154相關、568完整（567通過、1既有預期失敗），僅Linux合成／真正檔案與原生CPU回歸；新Windows結果另追加。[準備紀錄](development-records/runs/c11-installer-prep-2026-11-09/README.md)。

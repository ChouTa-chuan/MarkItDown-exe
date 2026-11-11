# Windows CPU維護程序中斷恢復

2026-11-11（台北），程式0.19.1、架構0.4。沿用[兩版升級／回復](windows-cpu-upgrade.md)，新增六案，[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42943978279)六案6/6、原功能11／同版8／跨版8均通過；[完整公開精簡摘要與原頁](development-records/runs/windows-cpu-recovery-ci-2026-11-11/README.md)保存。

| 操作 | 停點 | 預期恢復結果 |
| --- | --- | --- |
| 升級1.0.0→1.0.1 | published | 還原舊active與舊OCR |
| 升級1.0.0→1.0.1 | committed | 保留新active與新OCR，完成清理 |
| 修復有效1.0.1 | old_moved | 還原原payload與OCR |
| 修復有效1.0.1 | published | 還原原payload與OCR |
| 移除1.0.1 | old_moved | 還原元件與OCR |
| 移除1.0.1 | committed | 完成移除，再以普通安裝重裝並OCR |

驗收使用multiprocessing spawn。父程序只對自己建立的Process核對PID／隨機token／operation／stage，收到確切停點後kill並join，要求非零exitcode；活著時recover須收到核心鎖忙碌。另一全新spawn程序建立管理器、recover一筆，核對active與重複恢復無動作；原生CLI再要求精確元件版號、frozen、CPU provider及固定英文辨識。每案驗全payload hash、journal／staging清空、合成文件／設定與兩份快取。

元件私鑰僅存在主程序記憶體；子程序只接收公鑰、簽章catalog與本次自有路徑。六案各自使用合成暫存根目錄，取回自己的測試資料不構成產品通用清理。沿用現有C06恢復入口，不增加任意PID終止功能。

[本地初輪161項原始日誌與失敗](development-records/runs/windows-cpu-recovery-prep-2026-11-11/README.md)保存。Linux真程序／合成ZIP僅驗交易流程；Windows原生接受須等六案完整與控制端環境不變通過。本版完整回歸未跑，舊611屬0.17.2。CI沿用兩個獨立來源CPU版本、無OCR／Qt控制端及空PATH，報告七天、不發布worker／模型／ZIP／Setup。

範圍為程序終止與明確recover。斷電／OS重啟、所有profile、人工／乾淨機、最終原生再散布及ONNX繁中／日韓／GPU仍待；修復案初始payload有效，損壞修復另循同版維護證據。RAM仍為軟性預算。C04 2/4、C11 2/5、導入7/12／歷史19/25保持。

公開摘要採完整JSON且小於4000 bytes，保留六案PID／exitcode／恢復後版號與frozen；完整原始報告不改。[162項與首輪截斷證據](development-records/runs/windows-cpu-recovery-summary-2026-11-11/README.md)另存。

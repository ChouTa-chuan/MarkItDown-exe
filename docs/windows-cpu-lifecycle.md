# Windows CPU選配元件維護

2026-11-10（台北），程式0.18.1、架構0.4。沿用[前版Windows CPU原生11項](windows-cpu-ci.md)，增加同版本維護8案，[真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42794184827)原功能11/11、同版維護8/8通過；[公開原頁與紀錄](development-records/runs/windows-cpu-lifecycle-ci-2026-11-10/README.md)保存。

| 情境 | 接受條件 |
| --- | --- |
| 既有安裝重驗 | 保持原active與全部檔案hash |
| 架構不相容 | 拒絕修復，不改原安裝 |
| 活躍租約 | 修復與移除皆收到核心鎖忙碌 |
| 壞包 | 原安裝、快取與登錄保留 |
| publish後取消修復 | 回復原payload，交易無殘留 |
| 安裝影像損壞 | 健康檢查先依hash拒絕，修復後真正frozen健康通過 |
| 未知檔案 | 拒絕移除且原bytes保留，由驗收收回自己的合成檔 |
| 閒置移除與重裝 | 合成文件／設定及原快取不改，重裝後健康／hash完整 |

由scripts/cpu_lifecycle_acceptance.py負責情境，scripts/check_cpu_worker_acceptance.py在同一無OCR控制端、中文受管目錄、空PATH呼叫，再由既有Windows CI明確要求原11與維護8案均通過。驗收保存部分計數與當前失敗案，沒有以一般例外冒充預期拒絕。新4／相關147項本地通過，[準備日誌](development-records/runs/windows-cpu-lifecycle-prep-2026-11-10/README.md)另存；本版完整回歸未執行。

取消以published停點觸發Event；不代表程序強制終止、斷電／重啟、跨版升降級或所有profile完成。文件與設定均由CI在自己的暫存根目錄建立，不讀取真實使用者資料。只有固定公開健康fixture保留有界診斷，測試金鑰不落盤；報告七天、不發布worker／ZIP／模型／Setup。C04仍2/4、C11仍2/5、導入7/12／歷史19/25；乾淨機／人工／GPU與ONNX繁體及日韓品質仍待，RAM為軟性預算。

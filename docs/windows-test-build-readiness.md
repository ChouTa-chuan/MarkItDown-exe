# 第一版Windows測試安裝包準備

2026-11-11（台北），程式0.19.1、架構0.4。第一輪安裝測試以基本包的離線轉換與繁中／英文／日文／韓文OCR為主線；CPU實驗選配另行驗收，GPU接續獨立規劃。尚未提供可下載的測試Setup。

| 項目 | 實際證據／缺口 | 接續工作 |
| --- | --- | --- |
| 同版基本包 | [最終0.19.1 Windows CI](development-records/runs/candidate-inventory-ci-2026-11-11/README.md)：app10、安裝6、0.16→0.19.1跨版11、三停點續修3/3及CI自有暫存清理通過 | 沿用modular base管線與固定四語，不把舊development整包腳本當基本包交付 |
| CPU選配 | [功能11／同版8／跨版8／程序恢復6](windows-cpu-recovery.md)已驗；測試catalog／私鑰為暫時用途，來源仍example.invalid | 製作候選包清單、支援版號與離線匯入說明；正式目錄／信任根須獨立準備 |
| 本版完整回歸 | [本版完整684項](development-records/runs/candidate-inventory-ci-2026-11-11/README.md)：683通過／1既有品質預期失敗／0跳過，混合及43模組exit0 | 此門檻已完成；候選原始碼／依賴變動時依影響重驗 |
| 包內容與再散布 | 9份profile鎖、58套件／214原文或metadata hash已驗；[Windows基本包／CPU啟動器原文與Analysis來源／收集後指紋檢核已接受](development-records/runs/bundle-provenance-ci-2026-11-11/README.md)；[最終普通檔案清單／CPU ZIP已接受](development-records/runs/candidate-inventory-ci-2026-11-11/README.md)，基本1655／CPU ZIP742檔；來源未對照154／303項、runtime SBOM與再散布待查 | 核對候選基本包／選配實物、隨包原文／通知、Qt替換與對應來源等既有要求；應用公開授權仍待決定 |
| 可供安裝的產物 | 目前CI只保留報告，native傳遞輸入僅供同次CI；沒有對使用者交付Setup | 準備固定source commit／版號／hash／隨包說明的測試產物與驗收表，再安排交付 |
| 乾淨機與人工 | hosted Windows不等同無Python乾淨機；自動Qt開關不等同人工操作 | 在乾淨Windows／標準帳戶驗離線首次啟動、四語、中文路徑、RAM設定與安裝／修復／移除；此階段才需要實際安裝 |
| GPU與品質 | GPU實卡未驗、ONNX繁中仍有已知缺口；固定英文／四語樣本通過不代表任意文件品質 | 另驗顯卡相容／VRAM／回退與真實四語文件，RAM預算仍為軟性 |

已完成本版684項完整回歸及Windows兩包的技術追溯檢核。接續順序為：來源缺口／原文義務與再散布審閱 → 準備測試產物和操作表 → 乾淨機與人工安裝測試。GPU加值獨立接續，基本包首次安裝測試不要求開啟GPU。

目前需要的是開發端準備，使用者尚不必安裝。測試包與具體步驟備妥後，才安排實機驗收；這份盤點不更動發行旗標、建立Release、上傳Setup或發布環境設定。C04 2/4、C11 2/5、導入7/12／歷史19/25保持。

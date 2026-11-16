# A6 固定候選與來源整體審閱

本輪從已合併 PR 1–11 的 main 開始，保留 A5b／A5c 的 Claude reviewer 結論。新增程式由 Codex 自我查驗，不冒稱取得新的 Claude 審閱。

本次固定來源是 `8285450226abe1381e6a357e8bd33bff1ad46e0e`。基本包與 CPU 選配各以 workflow_dispatch 的 candidate_source 指向此完整 SHA；它與之後 PR 的暫時合併提交、文件提交及一般 Merge 提交分開。候選不升版、不建立 tag／Release，不上傳 Setup、worker 或模型。

來源盤點與計數以 [progress.json](progress.json) 為現況單一來源；本輪 [證據目錄](development-records/runs/a6-fixed-review-2026-11-17/README.md) 保存候選指紋、原始公開摘要、可重跑分類輸入與本機回歸結果。操作方式見 [固定候選審閱流程](candidate-review.md)。過去 cb8f24d 的資料留在 [歷史分類](source-classification.md)，不把舊結果改標為本輪新驗證。

## 審閱範圍

- 完整包內檔案與 CPU ZIP 由同次 Windows provenance 重驗；精簡資料記錄完整報告／inventory 的 hash，未內嵌整份清單，日誌與大型資料仍依 CI 保存期限。
- 來源分類逐項涵蓋所有 source-owner-unresolved 列；完整待審列與其餘 review_reasons 也保留。分類只補證據判讀，不修改原 inventory 的 owners 或降低原待審計數。
- 固定的 Git 位元組、同次報告、模型指紋與原生 payload 是可驗的來源證據。wheel 擁有者、套件宣告或有效簽章不足以證明所有內含第三方權利已核清。
- OpenSSL／SQLite 的 confirmed 指匹配來源 hash、runtime 觀測版本及隨包原文，不是 frozen 檔案的獨立執行認證，也不是該 extension 的 PE 版本。libffi 維持僅建置宣告。
- 舊分類以原候選與原報告重跑，分類、狀態與指紋保持一致；只改善說明文字，原證據未變更。

## 基本包審閱結果

前一輪同來源成套驗證尚未完成，但基本包已產生可重跑資料（另存於證據目錄的 attempt-e1761f9，明列來源，沒有當成本輪最終成套候選）：

- 來源分類沒有僅依檔名推測或完全無證據的列；原 inventory 的待審與未對照計數仍維持原值。CPython、標準庫封存與專案產生檔的 origin-known 不會被自動提升為授權已核准。
- 套件原文待對照只剩自有 markitdown-desktop。MIT 全文已隨包，問題在於它沒有綁入 installed package notice 表；後續應補對照及反例，不能藉由忽略 review_reason 清除警示。
- Microsoft 待審列不限於官方 Redist 路徑，也含 CPython 與 wheel 內附複本。應逐檔對照來源、版本與適用條款；套件擁有權與 Microsoft 簽章不能代替條款。
- wheel 原生檔雖可對回安裝 RECORD，numpy／pandas、Pillow、lxml、cryptography、ONNX Runtime、PDFium 與 Qt 等內含第三方仍需來源／版本／原文對照。現有 METADATA 入口與 notice hash 可追溯，不視為已完成所有內含程式庫盤點。
- Qt 官方發布來源與實際版本已在 A5b 核對，完整 build 修補／設定、內含第三方對照與替換驗收仍待；libffi 及靜態連結的 CPython／原生工具鏈亦保留各自證據限制。


## CPU 審閱結果與整體決定

新基本包重跑及 CPU 同來源資料均已取得並離線重現；基本包上述待審義務仍維持。CPU 的未對照列亦全數分類，沒有 gap 或 candidate 列。實際計數與逐檔 hash 見 progress.json 及證據 JSON；原 inventory 的未對照／待審計數不因補充判讀而降低。

- CPU 的 flatbuffers、rapidocr-onnxruntime 仍缺套件原文對照，PP-OCR 模型須另核對原始來源與授權範圍，不能以套件 Apache 宣告代替模型查驗。
- Shapely 內含 GEOS 的原始碼取得與 LGPL 義務仍待；OpenCV、ONNX Runtime、numpy、Pillow 等 wheel 內含原生第三方也須建立版本／來源／原文閉包。
- Microsoft 待審包含官方 Redist、CPython 及 wheel 內附複本。wheel RECORD 證明外層套件來源；逐檔條款與內附 VC runtime 仍需核對。
- Python 純模組及 base_library 成員清單已存在，舊的「完全未列舉封存成員」缺口已解；編譯／靜態連結來源與第三方義務仍須依證據個別處理。CPython libffi 的獨立 runtime 版本認證限制保留。

**本輪完成 A6 固定候選、來源重分類及整體工程審閱。** 分類中已無 gap／candidate，完整 runtime SBOM 仍缺 wheel 內含第三方等閉包，所以 runtime_sbom_complete 維持 false；原文對照、Microsoft／Qt／模型／GEOS 等義務未關閉，redistribution_approved 與 release_ready 亦維持 false。既有產品里程碑不提高。

後續先做 A7：把已隨包的自有 MIT 全文綁定 installed package notice 表，補缺檔／改 hash／錯誤套件綁定反例，另開 PR；之後優先基本包逐項處理內附第三方、Microsoft 與 Qt 義務。CPU 原文／模型／GEOS 分開追蹤。交付與乾淨機／人工／GPU驗收仍需後續階段。

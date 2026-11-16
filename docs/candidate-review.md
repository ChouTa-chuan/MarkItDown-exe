# 固定候選的來源審閱

A6 把「同一來源、同一候選、同一份來源報告」綁在一起。PR CI 使用 GitHub 暫時合併提交，只證明 PR 的整合結果；固定候選另用 workflow_dispatch 明確填入完整 candidate_source，實際 HEAD 必須相符且工作目錄乾淨。

基本包與 CPU 選配的驗證工作流在既有安裝／升降版／恢復驗收之後，重驗候選 inventory，再執行 scripts/candidate_review.py。候選 Setup／worker 只在可拋棄 runner 上產生並計算指紋，不上傳產品。只有原有報告 artifact 與精簡的來源審閱 JSON metadata 留存。

## 如何重跑與保存

1. 選擇已提交、已推送的完整 SHA。以自己的分支啟動 windows-base-validation.yml 與 windows-cpu-validation.yml，兩者 candidate_source 填相同 SHA。若分支已移動，來源檢查會拒絕，必須重新明確選擇；不自動改用最新 SHA。
2. 確認兩條 run 的 head_sha、workflow_dispatch、報告 selection.source_commit 相符。accepted 只表示證據一致，不是再散布核准。
3. source-review.json 保存候選指紋、完整 inventory 指紋、待審列、原生來源、套件 METADATA 來源入口及分類輸入。完整 inventory 與原始日誌留在 CI，精簡檔明列沒有內嵌完整 inventory 的限制。
4. 必要 metadata 以有界 gzip＋base64 分片寫入公開 annotation，每步最多八片；只含報告 JSON，不含產品內容。離線 decode_parts 必須通過完整性、來源與 SHA-256 檢查，任何缺片／重複／跨來源混合均拒絕；超額時直接失敗，不截斷。報告 artifact 的期限與 digest 另外記錄。
5. 保存解碼後的小型 JSON、README 與 manifest，再用 `python scripts/candidate_review.py --replay <source-review.json>` 以原固定 Git 樹重算。這不要求目前 HEAD 等於舊候選，但原 Git 物件必須存在。

## 證據的意思與界線

來源分類加入 CPython 的實際元件觀測與隨包原文：OpenSSL／SQLite 必須有匹配來源 hash、元件宣告／觀測版本及原文 hash，libffi 僅建置宣告仍是 origin-known。extension observed_version 表示所連結元件版本，不是 extension 檔本身 PE 版本。Microsoft VC runtime 需官方 Redist 路徑、未改位元組、Microsoft 有效簽章與版本才列 origin-known，仍須審閱再散布條款。

所有待審檔案都列入審閱資料，不只來源未對照者。套件擁有權、檔名、簽章或 wheel 的授權宣告，都不能自動關閉其內附原生第三方來源／原文義務。Qt 發布版本對應亦不能代替完整 build 修補／設定與替換驗證。

runtime_sbom_complete、redistribution_approved、release_ready 在此工具一律 false；最終整體審閱必須列出實際差距及後續工作。Windows hosted CI 不取代使用者的乾淨機／人工與 GPU 驗收。

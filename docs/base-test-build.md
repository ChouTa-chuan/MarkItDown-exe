# 基本包測試版流程（B1a）

本階段只準備與試跑。B1b 必須等 Claude planner 複查大階段 A 通過後另行啟用；目前 `scripts/base_test_build.py` 的 `PUBLIC_UPLOAD_ENABLED = False`，即使手動勾選公開上傳也會拒絕。沒有 Release、tag 或產品交付。

使用既有的 **Windows base validation**（`windows-base-validation.yml`）的 `workflow_dispatch`，不呼叫舊 `windows-build.yml`。一般 PR／main 驗證維持既有流程；只有手動設定 `prepare_test_build: true` 才執行 B1a 工作，其餘兩個一般驗證工作會依模式跳過，不能把跳過列為通過。

## 固定來源與控制端

- **應用程式來源**固定為 A13b 候選 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`，版本從該提交的 `pyproject.toml` 讀取；`candidate_source` 舊參數不能改變 B1a 的來源。
- **控制端**為 dispatch 的工作分支提交，包含本流程與目前的義務登記表。兩份 checkout 分開；報告分別記錄 payload 與 workflow 提交，不覆寫 `GITHUB_SHA`。固定候選的舊 provenance 報告 `source_commit` 指的是 workflow SHA，控制端會依此語意驗證，payload 則以獨立 `git rev-parse HEAD` 核對。
- 控制端重跑實際 gates，必須仍為 base `redistribution_approved`／`runtime_sbom_disclosed` true、`runtime_sbom_complete`／`release_ready` false。不得從流程勾選取代義務判定。
- 重建固定程式來源不保證安裝包逐位元相同：生成 metadata、路徑與封裝可能不同。每次記錄實際安裝包 SHA-256 與是否等於 A13b 原安裝包。原生相依檔、Tesseract／四語模型及 wheel 隨包原文必須與固定候選的 SHA 相同，不能以版本號相同替代。

## 試跑方式與輸入期限

對自己的工作分支手動執行 Windows base validation，設定：

- `prepare_test_build: true`
- `publish_test_build: false`
- `ocr_inputs_run`：指定一個已成功的一般 Windows base validation run；空白會選最新仍有未過期輸入的成功 run。

OCR 輸入沿用既有驗證的 `windows-ocr-ci-inputs`（保留一天），避免本次試跑另外上傳 executable／模型 artifact。先核對 workflow、成功狀態、artifact digest 與期限，下載後再逐份核對固定候選的 Tesseract／四語模型 SHA 與建置來源契約。輸入過期時先重跑一般驗證以準備輸入，再試跑；不得忽略錯誤或改用不同 bytes。

Hosted Windows 2022 會實際建置固定候選、執行既有四語 OCR／GUI／中文路徑驗收、Qt 可替換驗收，以及安裝／修復／移除。此試跑不另跑跨版本升級與中斷恢復；一般 PR CI 仍跑它們。Hosted runner 不是乾淨實體 Windows 10／11，也不是 GPU 實卡驗收，不能關閉大階段 C。

## 附件與上傳界線

組裝出的產品目錄包含 Setup 及 `BUILD-INFO.json`（兩份提交、版本、安裝包 SHA-256、政策）、`LICENSE-FILES.json`（實際隨包授權目錄的路徑／SHA／大小，含原文與支援 metadata，不宣稱法律完整性）、`known-gaps.json`、`known-gaps.md`、`test-build-limitations.md`、中文 README、`SHA256SUMS.txt`。授權原文仍在安裝包內，既有原文不改寫。

B1a 的 runner 只上傳 `base-test-build-reports`，保留 **30 天**，以明確的九個 JSON／文字檔清單上傳。產品與報告不可在同一路徑或互相巢狀。成功組裝後會逐檔重讀並核對副本；複製失敗或雜湊改變即拒絕。執行檔不上傳。

另把同一份小型文字報告寫成有數量／大小上限與 SHA-256 的公開註記，讓無法連 artifact 儲存主機的環境也能重組查驗；分片缺少、重複、越界或 hash 不符皆拒絕。失敗試跑只保留已有文字報告，不能列為成功。

未來 B1b 的產品 uploader 已備妥且保留 30 天，但受控制端常數與成功組裝雙重限制。此階段不啟用它；B1b 需另行查驗與 PR。

# A12 固定候選來源審閱與基本包出口（2026-11-18）

A12 第二部分：以 main 的 `2555687eafc931600f30265f7bd290331cd49a0f`（含 A7–A11）作為新固定候選，重組來源審閱、更新義務登記表，產出基本包出口報告。A12 第一部分已把 progress.json 的舊紀錄鍵搬到 `docs/history/`。本輪沒有產品交付、Release、tag，也不建立 Setup、worker 或模型的對外 artifact。

## 候選與 run

- 來源：`2555687eafc931600f30265f7bd290331cd49a0f`，兩條 run 都由 `workflow_dispatch` 且 `explicitly_pinned: true`，ref 為 `refs/heads/main`，run_attempt 為 1。
- 基本包 [Windows base validation run 44217813413](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44217813413)：success，主 job 134512925919（Windows 2022 base build and OCR），另有 job 134511938750（Fixed Windows OCR inputs）。
- CPU [Windows CPU validation run 44217816852](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44217816852)：success，job 134511947535。
- 基本包候選（Setup）：`MarkItDownBase-Setup-0.19.1-windows-x64.exe`，102438267 bytes，sha256 `c00435f3806ac50fe1cff880af2e03aa3176b46533d859ba34535d8542ef8b3f`，與 CI installer 證據一致。
- CPU 候選：`onnx-cpu-ocr-development.zip`，92361577 bytes，sha256 `0c467903aac804e07dd991910423e824c70df59d6f4406f49c8e695acdd268a9`，component `onnx-cpu-ocr` 1.0.1，descriptor sha256 `05116cb38043609a8bccb1d4a0ee4820e4d3b3affae7d11daf21aac198e046af`。

Artifact（只記錄 digest 與期限，本環境未下載）：

| 來源 | Artifact | digest | 期限 |
| --- | --- | --- | --- |
| base 主 job | windows-base-validation-reports | `sha256:71847b7e22ae8bcf53178e526c23f50c8e900243be6345abdef2cf5b3adeb76e` | 2026-11-25T01:59:54Z |
| base 主 job | windows-native-build-reports | `sha256:09dde4c03abcf42f6f7b8f47ec13b430b17ed4f214052a6a93a2b8acc564d77a` | 2026-11-25T01:44:30Z |
| base OCR job | windows-ocr-ci-inputs | `sha256:0e5485441409959ebdea21402a8afe3835565abe93b63ffbcb65499d9ebd027d` | 2026-11-19T01:44:28Z |
| CPU | windows-cpu-validation-reports | `sha256:01dae75faba325e83a09c79a2e3410ca4d1b1e20b2a66ca97bad633d2f645472` | 2026-11-25T01:58:40Z |

## 做了什麼

1. **重組審閱資料**：從 CI 公開 annotation 的「Candidate review metadata」分片（base 32 片、CPU 30 片）以 `candidate_review.decode_parts` 重組，完整性、來源、profile 與 SHA-256 均通過。annotation 原始檔未保存，只保存重組後的 JSON 與其指紋。
2. **離線重跑**：`candidate_review.py --replay` 以 Git 樹 2555687 重算兩個 profile 的分類，結果與保存的 classification 完全一致。
3. **Microsoft 探測**：從「Microsoft runtime evidence」兩片重組 `windows-probe.json`（見下方 diagnostic 說明）。
4. **登記表**：`obligations.json` 兩個 profile 的 `source_commit` 改為 2555687；`redistribution_gates.py` 對兩個新輸入執行，base 與 cpu 均 exit 0。
5. **目錄綁定**：`embedded`、`qt`、`microsoft` 三個目錄的綁定欄位與對應條目的 sha256 引用同步（見下節），目錄內的檔案身分與原生檔 bytes 未變。
6. **出口報告**：`base-exit-report.json` 由登記表狀態與 gates 輸出推導，列出每個 base 條目的分類與 A13 待決事項。

## 新舊候選差異

| 項目 | A6（8285450） | A12（2555687） |
| --- | --- | --- |
| base 檔案數 | 1615 | 1767 |
| base 原生檔 | 153 | 153（bytes 無變動） |
| base 待審檔案 | 152 | 275 |
| base unresolved（source-owner-unresolved） | 114 | 264 |
| base 待審 reason | markitdown-desktop 原文待綁 27；Microsoft 14；source-owner 114 | markitdown-desktop 原文待綁 0；Microsoft 14；source-owner 264 |
| cpu 檔案數 | 704 | 706 |
| cpu 原生檔 | 61 | 61（bytes 無變動） |
| cpu unresolved | 265 | 266 |
| cpu 待審 reason | Microsoft 6；flatbuffers 1；rapidocr 31；source-owner 265 | 不變，source-owner 266 |

base 的 unresolved 增加 151 筆、減少 1 筆。新增的 151 筆中，150 筆是 A11 隨包的 Qt 第三方原文（`_internal/desktop_app/data/licenses/qt-thirdparty/…`），1 筆是 A9b 的 `cryptography-openssl.json`。被移除的 28 筆中，27 筆是 `markitdown-desktop` 套件原文綁定（A7）後不再適用的 reason，另 1 筆是自有 MIT LICENSE，原本的 source-owner-unresolved 因 A7 綁定已有套件歸屬。cpu 新增的 1 筆是隨包的 cryptography 原文。所有 unresolved 仍屬「無 wheel 擁有者」的計數，不是要歸零的指標。

## 登記表與選擇器

- **stale selector（1 處）**：`base-own-mit-binding` 的 `review_reasons` 原為 `package-original-notice-pending:markitdown-desktop`，候選已含 A7 綁定，該 reason 不再出現，因此移除選擇器。**狀態仍為 open，未改動。** 查驗者可依 A7 證據判斷是否關閉。
- 其餘選擇器與 `native_files` 無過期，新增原文檔案都歸入既有 `source-owner-unresolved` 單一條目（`base-source-attribution`／`cpu-source-attribution`），沒有新的 reason。
- 未改動任何條目的 status、required_evidence、requires_user_decision。

## 目錄綁定與 hash 同步（只做綁定，不改事實）

| 檔案 | 改動 | 理由 |
| --- | --- | --- |
| `packaging/embedded/base-windows.json` | `source_commit`；`source_review` 路徑與 sha256 改指 A12 base-source-review.json | 目錄須綁目前候選的來源審閱；`scripts/embedded_components.py` 的固定路徑同步改為 A12 |
| `packaging/qt/6.12.0/thirdparty/catalog.json` | 只改 `source_commit` | 逐檔 `source_sha256`、`bundled_sha256` 與候選一致，未改 |
| `packaging/microsoft/base-windows.json` | 只改 `source_commit`；`basis`、`probe` 不變 | 見下方說明 |
| `scripts/microsoft_runtime.py` | `check_catalog` 的探測基準比對改為「探測基準與基準檔自身 selection 一致」 | CI 探測是在 A6 基準上產生的，基準與候選不必同一 commit；候選綁定由逐檔 bytes 比對完成 |

- **Microsoft 基準為何仍指 A6**：CI 探測讀取的基準是 A6 的 source-review，其 `basis` 欄位記錄 A6 的路徑、sha256 與 selection 8285450。在不重跑 CI 的情況下無法改成 A12 基準，因此保留 A10 探測與 A6 基準，並由 `check_catalog` 逐檔核對 `a6_sha256`、`origin`、`distributions` 與候選 bytes（14 檔全部一致）。候選 CI 探測另存為本目錄的 `windows-probe.json`，與 A10 探測相比，只有 `source_directory`／`source_path`（建置路徑）不同，公司、版本、簽章與簽署者一致。
- **只做 hash 同步的條目**：`base-wheels-numpy`、`base-wheels-pandas`、`base-wheels-pillow`、`base-wheels-lxml`、`base-wheels-cryptography`、`base-wheels-onnxruntime`、`base-wheels-pypdfium2`、`base-wheels-cffi`、`base-wheels-charset-normalizer`、`base-wheels-psutil`（embedded 目錄 sha256 引用）；`base-microsoft`（microsoft 目錄 sha256）；`base-qt`（qt 目錄 sha256）。只更新 `evidence[].sha256`，其他欄位未動。
- **三個 profile 的 gates 結果**：base 與 cpu 都 exit 0，三旗標皆 false。

## Microsoft evidence diagnostic 的意義

CI annotation 「Microsoft evidence diagnostic」為正常診斷（notice），內容是 `files: 14`、`terms: []`、`raw_bytes: 18881`。`terms: []` 表示 runner 的 Visual Studio 2022 安裝目錄中，沒有找到符合「MICROSOFT SOFTWARE LICENSE TERMS」與 VS2022 版本字樣的授權文字；A10 本機探測的 `installed_terms` 也是 0。這只是安裝目錄內的候選文字是否存在，不是錯誤，也不影響目錄：目錄不讀取這個欄位，條款依據來自 A10 的官方原文快照。它不代表 Microsoft 條款已確認，也不代表授權允許。

## 基本包出口（摘要）

詳見 [base-exit-report.json](base-exit-report.json)。

- 三旗標（由 gates 推導，未人工改寫）：`runtime_sbom_complete` false（14 個條目阻擋）、`redistribution_approved` false、`release_ready` false。
- 條目分類（base 共 20 項）：已關閉 3（`base-own-license-choice` user_approved；`base-wheels-charset-normalizer`、`base-wheels-psutil` evidence_complete）；待 A13 決定 5（`base-microsoft`、`base-qt`、`base-tesseract-models`、`base-redistribution-decision`、`base-clean-machine-manual`）；證據未齊 12（`base-source-attribution`、`base-cpython`、`base-wheels-*` 8 項、`base-archives`、`base-own-mit-binding`）。
- `base-microsoft` 的目錄檢核通過（14 檔身分無缺口），但狀態仍 open 且需 A13；`base-qt` 目錄檢核通過但建置設定與 Mesa 版本未知；`base-tesseract-models` 沒有任何證據引用。

### A13 待決清單（使用者決定）

1. **A13-1 Microsoft 逐份再散布依據**（`base-microsoft`）：14 份複本；9 份 PySide6／shiboken6 PE 為 Microsoft、簽署者為 The QT Company Oy；2 份為改名複本（numpy／pandas 的 msvcp140）。EULA 與 REDIST 清單不能互相代替。
2. **A13-2 Qt LGPL 做法**（`base-qt`）：替換驗收已在 hosted Windows 完成（A11），但不是乾淨機；Mesa `opengl32sw.dll` 版本未知。
3. **A13-3 libffi 僅建置宣告**（`base-cpython`、`base-wheels-cffi`）：`_ctypes.pyd` 與 `_cffi_backend` 的 libffi 版本只有建置宣告。
4. **A13-4 版本未知元件的接受與揭露**（`base-wheels-numpy`、`pandas`、`pillow`、`lxml`、`cryptography`、`onnxruntime`、`pypdfium2`、`cffi`）：26 項版本 unknown；規則要求其條目維持 open，決定只能是接受與揭露的政策，不能因此關閉。
5. **A13-5 Tesseract 與 tessdata**（`base-tesseract-models`）：`tesseract.exe` 與四語 traineddata 的授權與再散布；目前沒有證據，需先補證據。
6. **A13-6 品質限制揭露**（`base-clean-machine-manual`）：ONNX 繁中缺口、RAM 軟性預算、Windows／GPU 實機未驗、非乾淨機；屬大階段 C。
7. **A13-7 再散布門檻確認**（`base-redistribution-decision`）：協調者與 AI 不得代為決定。

## 測試

- 新增 1 個測試：`tests/test_microsoft_runtime.py::test_probe_basis_must_name_the_catalog_basis_document`（探測基準與基準檔不符即拒絕）。`EXPECTED_TESTS` 由 884 改為 885。
- 因登記表改綁 A12，以下測試的固定輸入由 A6 改為 A12 候選（測試斷言未降低）：`test_redistribution_gates.py`、`test_embedded_components.py`、`test_qt_components.py`，以及 `test_microsoft_runtime.py` 的目前接線測試。`test_actual_a6_profiles_have_exact_coverage_and_false_flags` 名稱保留未改。A6 基準仍保留於 `ms.BASIS_PATH` 作為 Microsoft 探測的歷史輸入。
- 完整測試 `python -m unittest discover -s tests`：885 run，884 passed，1 expected failure（ONNX 繁中已知缺口），0 failure、0 skip。coder 首次執行時 `test_history_index.test_repository_index_is_current` 因新增本證據目錄而失敗；協調者重建歷史索引後通過。協調者另跑完整混合回歸（885／884）與 57 個獨立模組，全部正常退出。

## 限制

- 三旗標為 false。本輪不是再散布核准，也不是乾淨機或人工驗收。
- 本目錄的 gates 輸出與出口報告由腳本推導，不包含人工審閱結論；evidence_complete 與 user_approved 的設定仍由人工審閱決定。
- Microsoft 目錄的 limitations 仍寫著 A10 時的 "fixed A6 source" 句子，屬 A10 當時的描述，本輪未改目錄內容。
- `base-own-mit-binding` 的 reason 已不存在，但狀態仍 open；是否關閉由查驗者與使用者決定。
- 原始 annotation、完整 inventory 與 artifact 留在 CI，本目錄未保存。

## 檔案

- [base-source-review.json](base-source-review.json)、[cpu-source-review.json](cpu-source-review.json)：重組後的來源審閱，離線 replay 通過。
- [windows-probe.json](windows-probe.json)：A12 候選的 Microsoft 探測（CI 觀測）。
- [base-gates.json](base-gates.json)、[cpu-gates.json](cpu-gates.json)：gates 的完整輸出。
- [base-exit-report.json](base-exit-report.json)：基本包出口報告。
- [manifest.json](manifest.json)：日期、來源、結果、檔案雜湊與關鍵字。

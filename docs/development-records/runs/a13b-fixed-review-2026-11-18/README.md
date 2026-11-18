# A13b 固定候選來源審閱與改綁（b17d51b，2a）

A13b 第二部分的前半（2a）：以 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（A13b 第一部分 9ecedcf，加上候選審閱保留揭露檔列的 b17d51b）作為新固定候選，重組來源審閱、把登記表與目錄改綁到新候選，並記錄 Microsoft 探測的基準改指。**本階段沒有改任何條目的 status、decision_source、accepted_gaps，也沒有收回 check_catalog 的放寬，這些留給 2b。** 不交付產品，不建 Release 或 tag。

**結果摘要：`accepted: false`。** base gates 目前 exit 1（Microsoft 目錄的基準與新候選不一致，見下），因此本目錄不是可驗收的 2a 出口；cpu gates exit 0，四旗標皆 false。

## 候選與 run（只記錄，本環境未下載 artifact）

| 項目 | 內容 |
| --- | --- |
| 固定候選 | `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`，`workflow_dispatch`、`explicitly_pinned: true`，ref `refs/heads/claude/confident-ride-o38ls7`，run_attempt 1 |
| base | [run 44295039865](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295039865)，success；主 job 134770979765（另 job 134769787107 為 OCR inputs）；Setup `MarkItDownBase-Setup-0.19.1-windows-x64.exe` 102443112 bytes，sha256 `b79b75977b1d49589b3108d9363eb96016d2148f813db652468b2da7d7c075fe` |
| cpu | [run 44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417)，success；job 134769802426；`onnx-cpu-ocr-development.zip` 92373183 bytes，sha256 `1ed15ddb0a99c565509129c3ed83a7aaab4f7c11c0ba3712cc4b1742efd33bb5`，component onnx-cpu-ocr 1.0.1，descriptor sha256 `66fe8878d69387f1c28c513a88dc7dd36ffeba713e25ba9a97b45f2e9faaa443` |
| base 驗收 | build_verified、validation、installer、upgrade、recovery 皆 accepted（Redist VC runtime 能正常執行）；clean_machine_accepted false |

Artifact digest 與期限（只記錄）：

| 來源 | Artifact | digest | 期限 |
| --- | --- | --- | --- |
| base 主 job | windows-base-validation-reports | `sha256:caebc8c8ac24eb051ae346fb2e19220c2a026433f8b87c0c73c1c7b52d524490` | 2026-11-25T11:45:28Z |
| base 主 job | windows-native-build-reports | `sha256:1fcf3d5cc46fa06e4b670e9fd2d96c4576deea25d8da989480672113261b01d3` | 2026-11-25T11:30:54Z |
| base OCR job | windows-ocr-ci-inputs | `sha256:4f6756012d50890081940ce2c34c55ecf2a12ca842fd8dd5264eb42624bfbeeb` | 2026-11-19T11:30:45Z |
| cpu | windows-cpu-validation-reports | `sha256:8f38a60b9473ea915879d62adedd4dfc3b0a91ac9b1c5db3e7473ea51b89692e` | 2026-11-25T11:43:08Z |

Microsoft 探測來自 base 主 job 的 `Microsoft runtime evidence` 兩片（scope `built-bundle`，runner image 20261112.366.7）。

**前一個候選 9ecedcf 的紀錄（非固定候選）**：base [run 44289885218](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289885218)、cpu [run 44289891259](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289891259)、Microsoft 證據 [run 44289896406](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289896406)，皆 success。它是 VC runtime 替換的首次 CI 驗證（base 驗收同上），其 base Setup sha256 `e3068451c88277cf2f032c262b838958ca0baa0dabf671639de36882d33d8414`。因為 9ecedcf 的候選審閱缺少揭露檔列，不作為固定候選。

## 做了什麼

1. **重組審閱**：從 CI 公開 annotation 的「Candidate review metadata」以 `candidate_review.decode_parts` 重組 base（32 片）與 cpu（31 片），完整性、來源、profile 與 SHA-256 皆通過；Microsoft 探測以 `microsoft_runtime.decode_parts` 重組（2 片）。annotation 原始檔未保存，只保存重組後的 JSON。
2. **離線 replay**：`candidate_review.py --replay` 以 Git 樹 b17d51b 重算兩個 profile 的分類，與保存結果完全一致。
3. **揭露檔列核對（2a 第 1 點）**：base 審閱的 candidate_inventory.files 含三個隨包揭露檔列，`review_reasons` 為空，sha256 與 repo 內 `src/desktop_app/data/licenses/` 同名檔相同：
   - `known-gaps.json` 7000 bytes，`933165bf3485e9aea99f7608a64d0f0f4173dca56b9c9bce004e258b9399e3b7`
   - `known-gaps.md` 22878 bytes，`1b2bfcf35c82c98376dc404a042e963aa535fb2be0948be83956c9f4050362c1`
   - `test-build-limitations.md` 605 bytes，`76ed454b56dc458dd0e9498bc93668ce2333a1f1e231564953da97fde3dc8885`
4. **VC runtime 核對**：根目錄 `vcruntime140.dll`（`d5e4d9a3e835fa679450145d6a7d94e36573a509317111904d9b3712c30d9066`）與 `vcruntime140_1.dll`（`1f2d41c4aa5db0bc33ebf7b66d72943a817d7ce6cbe880502a9403823633093f`）與官方 Redist 同名檔的完整 sha256 相同（`matches_official=True`），PE 為 Microsoft Corporation 14.44.35211.0、簽章 Valid。numpy／pandas 的 msvcp140 改名複本（`a4c2229bdc2a…`）、PySide6／shiboken6 的 9 份 VC／MSVCP 複本與 A6 bytes 相同（`matches_a6=True`）。`terms: []`（與之前相同，見 A12 README 說明）。
5. **改綁**（見下節）。

## 新舊候選差異（A12 2555687 → b17d51b）

**base**

| 項目 | A12（2555687） | b17d51b |
| --- | --- | --- |
| 候選 Setup | 102438267 bytes，`c00435f3…` | 102443112 bytes，`b79b7597…` |
| 檔案數 | 1767 | 1770（+3，三個揭露檔） |
| inventory bytes | 263326495 | 263362685 |
| 原生檔 | 153（新增、移除皆 0） | 153；僅 vcruntime140.dll、vcruntime140_1.dll 的 bundled sha 與 origin 改變（system-native，官方 Redist） |
| 待審列 | 275 | 275（無新增、移除，無 reason 改變） |
| review_reasons | microsoft 14、source-owner-unresolved 264 | 相同 |
| unresolved／by_status | 264；confirmed 234、origin-known 30 | 相同 |
| by_category | microsoft-vc-redist 1、cpython-runtime 19 | microsoft-vc-redist 3、cpython-runtime 17（兩個根目錄 DLL 改由官方 Redist 對應） |
| 保留的無 reason 列 | 0 | 3（揭露檔，見上） |
| 同路徑但 bytes／sha 改變的保留列 | — | 23 列（RECORD、base_library.zip、build-profile.json、third-party.md、base-install-catalog.json 等，反映 bundle 內容變動；review_reasons 不變） |
| packages、python archive | — | 相同 |

原因：vcruntime 兩檔替換帶來原生檔與分類的變動；三個揭露檔因候選審閱保留規則（b17d51b 的 `DISCLOSURE_PATHS`）進入精簡列；bundle 的 RECORD 與相關清單因 DLL 替換而改 hash。

**cpu**

| 項目 | A12（2555687） | b17d51b |
| --- | --- | --- |
| 候選 zip | 92361577 bytes，`0c467903…` | 92373183 bytes，`1ed15ddb…` |
| descriptor sha256 | `05116cb3…` | `66fe8878…`（component 1.0.1 不變） |
| 檔案數 | 706 | 712（+6：worker-assets/licenses 三檔，以及 installed markitdown-desktop 下的同名三份複本） |
| 原生檔 | 61，bytes 全部不變 | 61，不變 |
| 待審列 | 300 | 303（+3：worker-assets/licenses 的三個揭露檔，reason source-owner-unresolved） |
| unresolved／by_status | 266；confirmed 238 | 269；confirmed 241 |
| review_reasons | source-owner-unresolved 266 | source-owner-unresolved 269（其餘 microsoft 6、flatbuffers 1、rapidocr 31 不變） |
| markitdown-desktop notices | 218 | 221（+3 揭露檔複本） |

## 改綁與 hash 同步清單

**登記表 `packaging/redistribution/obligations.json`**
- 兩個 profile 的 `source_commit` 改為 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（各 1 處）。
- 只更新 sha256 引用，其他欄位不變：
  - `packaging/embedded/base-windows.json`：舊 `c2fef24f…` → 新 `561e0a83…`，10 個條目（base-wheels-numpy、pandas、pillow、lxml、cryptography、onnxruntime、pypdfium2、cffi、charset-normalizer、psutil）。
  - `packaging/qt/6.12.0/thirdparty/catalog.json`：舊 `6e622a26…` → 新 `a4b2658c…`，1 處（base-qt）。
  - `packaging/microsoft/base-windows.json`：舊 `9186ee51…` → 新 `737d7fb0…`，1 處（base-microsoft）。
- 未改動：各條目 status、decision_source、accepted_gaps、requires_user_decision、required_evidence、review_reasons／native_files 選擇器。
- **stale selector：無。** 以不依賴 Microsoft 的 `coverage` 檢核：base 153 個原生檔、2 個 reason（microsoft 14、source-owner 264）全部恰好對到一個條目；cpu 61 個原生檔、4 個 reason 全部對到；摘要與列一致。
- 登記表結構 `validate_registry` 通過。
- 仍引用 A12 審閱的證據列未改（例如 base-source-attribution、base-cpython、base-archives、base-tesseract-models、base-own-mit-binding）。這些條目引用的是 A12 當時的 origin-known 與分類證據，檔案與 hash 都還在、內容未變，所以不強行改指（見疑點）。

**目錄**
- `packaging/embedded/base-windows.json`：`source_commit` → b17d51b；`source_review` 改指 `docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json`，sha256 `f65cdbc9a01d95391032fa991d6d4f0e5dfec10b317b983435ce79bfbeaed295`。
- `packaging/qt/6.12.0/thirdparty/catalog.json`：只改 `source_commit`。
- `packaging/microsoft/base-windows.json`：只改 `source_commit`；`basis` 與 `probe` 不變（見下節 BASIS）。

**腳本**
- `scripts/embedded_components.py`：`check_pin` 的 source_review 固定路徑改為 a13b。
- `scripts/known_gaps.py`：`DEFAULT_REPORT` 改為 a13b base 審閱。
- `scripts/microsoft_runtime.py`：`BASIS_PATH` 改為 a13b base 審閱（見下節）。

**測試輸入**（A12、A6 的歷史回歸輸入保留）
- `tests/test_redistribution_gates.py`：setUp 與 CLI 真實證據測試改為 a13b；a12b 快照測試改為比對 A12 候選審閱（快照釘在 2555687，見疑點）；無 reason 列測試改為不依賴重複的揭露列。註解的 source_commit 更新為 b17d51b。
- `tests/test_embedded_components.py`、`tests/test_embedded_runtime.py`、`tests/test_microsoft_runtime.py`、`tests/test_qt_components.py`：真實 base 審閱改為 a13b（embedded_runtime 暫存副本同時保留 A12 基準，因為 A12d 觀測綁定的是 A12 基準）。
- `tests/test_candidate_review.py`：`PreservedReplayTests` 名單加入 a13b base 與 cpu 的 replay。

## BASIS_PATH 的處理與影響

`scripts/microsoft_runtime.py` 的 `BASIS_PATH` 已改為 a13b base 審閱，讓之後在這個提交上執行的 Microsoft 探測以新候選為基準。

**本階段因此讓 base gates 失敗（exit 1）**，原因如下：
- `check_catalog` 要求目錄的 `basis.path` 等於 `BASIS_PATH`，而目錄仍指 A6；目前報 `Microsoft catalog source mismatch`。
- 探測檔 `windows-probe.json`（b17d51b 的 CI 結果）是以 A6 為基準產生的，其 `basis` 與 `a6_sha256` 都對應 A6。
- 即使不改 `BASIS_PATH`，在新候選上 `check_catalog` 也會因 vcruntime140.dll、vcruntime140_1.dll 的 `a6_sha256`（A6）與候選原生檔 sha 不同而拒絕（`Microsoft A6 file hash differs`）。這是 A13b 第一部分替換 DLL 的正確結果，不是缺陷。

因此 Microsoft 目錄、探測檔與 check_catalog 的放寬都必須在 2b 一起處理：以新 BASIS 在 b17d51b 之後的提交上重跑 Microsoft 探測，更新目錄的 basis 與 probe 引用，並收回放寬。2a 不做這些，也不偽造探測。

受影響的測試（都經過 base gates 或 Microsoft 目錄）：`test_embedded_components.GateIntegrationTests`、`test_known_gaps`（setUpClass，8 項未執行）、`test_microsoft_runtime`（目錄接線）、`test_redistribution_gates` 的 actual 系列、counts、CLI、existing_catalog 反例。它們都會在 2b 修正 Microsoft 目錄後通過，不是測試放寬。

## Gates 與測試結果

**gates**
- cpu：`python scripts/redistribution_gates.py --source-review docs/development-records/runs/a13b-fixed-review-2026-11-18/cpu-source-review.json --output …/cpu-gates.json` exit 0；`runtime_sbom_complete`、`redistribution_approved`、`release_ready`、`runtime_sbom_disclosed` 皆 false。輸出見 [cpu-gates.json](cpu-gates.json)。
- base：exit 1（`Microsoft catalog source mismatch`，見上節）。**沒有 base-gates.json 與 base-exit-report.json**，留待 2b。

**known_gaps**：`python scripts/known_gaps.py --check` 因需要 Microsoft 目錄推導而失敗（同一原因）。未重產 known-gaps.json；repo 內三檔 sha 與候選相同（已核對）。

**完整測試**：`python -m unittest discover -s tests`（環境同前，scratchpad venv，`PYTHONPATH=src:tests`、`QT_QPA_PLATFORM=offscreen` 等）：**Ran 914；failures 3、errors 6、expected failures 1（ONNX 繁中，既有）。**
- 6 個 ERROR 與 2 個 FAIL 為 Microsoft 目錄基準不一致（上節）；`test_known_gaps` 的 setUpClass 錯誤使該類 8 項未執行（922 − 914 = 8）。
- 1 個 FAIL 為 `test_history_index.test_repository_index_is_current`：新增證據目錄後索引過期，依協調者規則由協調者重建 `scripts/build_history_index.py`。
- `EXPECTED_TESTS` 維持 922，2a 沒有新增或移除測試，但目前無法在本機達到完整綠燈。

## 疑點與需要協調者決定

1. **2a 出口未通過 base gates**：本階段無法在不改 check_catalog、不偽造探測的前提下讓 base exit 0。建議：(a) 2a 提交接受 base 紅燈（僅 Microsoft 相關），由協調者在提交後重跑 Microsoft 探測，2b 再綁定；或 (b) 改由協調者決定 2a 與 2b 合併為一個提交。這點需要你的指示。
2. **仍引用 A12 審閱的證據列**：base-source-attribution、base-cpython、base-archives、base-tesseract-models、base-own-mit-binding 的 evidence 仍指 `a12-fixed-review-2026-11-18/base-source-review.json`（hash `9b9b2996…` 未變）。它們是 A12 當時的分類證據，目前內容未變，所以未改。若要統一改指 a13b，需要逐條判斷 evidence_complete 的語意是否仍成立，超出 hash 同步範圍，未做。
3. **a12b 快照測試**：`origin-known-review.json` 釘在 2555687，其列 sha 與新候選的 base_library.zip 等不同，因此測試改為比對 A12 審閱。快照本身未改。
4. **history index、progress.json、STATUS、CHANGELOG、docs/redistribution-gates.md 的 A12 指令與基準敘述**：未改，由協調者處理。
5. 解碼腳本與中間檔案在 `/tmp/claude-0/-home-user-MarkItDown-exe/4c4fa8db-71d4-5f78-b162-4bc8918c39ae/scratchpad/a13b2/`，不在 repo 中。

## 檔案

- [base-source-review.json](base-source-review.json)、[cpu-source-review.json](cpu-source-review.json)：b17d51b 候選審閱，離線 replay 通過。
- [windows-probe.json](windows-probe.json)：b17d51b CI 的 Microsoft 探測（以 A6 為基準）。
- [cpu-gates.json](cpu-gates.json)：cpu gates 輸出，exit 0、四旗標 false。
- [manifest.json](manifest.json)：日期、來源、結果、檔案雜湊與關鍵字。

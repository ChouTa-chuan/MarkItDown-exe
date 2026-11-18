# A13b 固定候選：來源審閱、Microsoft 探測與使用者決定寫入（b17d51b，2a＋2b）

A13b 第二部分：以 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（A13b 第一部分 9ecedcf，加上候選審閱保留揭露檔列的 b17d51b）作為固定候選，重組來源審閱、以該候選重跑 Microsoft 探測、收回 A12 的 check_catalog 放寬、把 A13 使用者決定寫入登記表，並產出 base／cpu gates 與 base 出口報告。不交付產品，不建 Release 或 tag。

**結果**：base gates 推導為 `runtime_sbom_complete` false、`runtime_sbom_disclosed` true、`redistribution_approved` true、`release_ready` false；cpu 四旗標皆 false。`release_ready` 仍為 false，因為 `base-clean-machine-manual` 需要大階段 C 的乾淨機與人工驗收。本結果不是乾淨機驗收。

## 候選與 run（只記錄，本環境未下載 artifact）

| 項目 | 內容 |
| --- | --- |
| 固定候選 | `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`，`workflow_dispatch`，`explicitly_pinned: true`，ref `refs/heads/claude/confident-ride-o38ls7`，run_attempt 1 |
| base | [run 44295039865](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295039865)，success；主 job 134770979765（OCR inputs job 134769787107）；Setup 102443112 bytes，sha256 `b79b75977b1d49589b3108d9363eb96016d2148f813db652468b2da7d7c075fe`；build_verified、validation、installer、upgrade、recovery 皆 accepted，clean_machine_accepted false |
| cpu | [run 44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417)，success；job 134769802426；`onnx-cpu-ocr-development.zip` 92373183 bytes，sha256 `1ed15ddb0a99c565509129c3ed83a7aaab4f7c11c0ba3712cc4b1742efd33bb5` |
| Microsoft 探測 | [run 44300296037](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44300296037)（head 7cf098e，即 2a 提交），job 134787974381，artifact microsoft-runtime-evidence-reports `sha256:6571a9d48778127beae91bd2a332b788515c5651912abf2fac48dccbc8341ed2`，到期 2026-11-25T12:05:37Z |

Artifact digest（只記錄）：

| 來源 | Artifact | digest | 期限 |
| --- | --- | --- | --- |
| base 主 job | windows-base-validation-reports | `sha256:caebc8c8ac24eb051ae346fb2e19220c2a026433f8b87c0c73c1c7b52d524490` | 2026-11-25T11:45:28Z |
| base 主 job | windows-native-build-reports | `sha256:1fcf3d5cc46fa06e4b670e9fd2d96c4576deea25d8da989480672113261b01d3` | 2026-11-25T11:30:54Z |
| base OCR job | windows-ocr-ci-inputs | `sha256:4f6756012d50890081940ce2c34c55ecf2a12ca842fd8dd5264eb42624bfbeeb` | 2026-11-19T11:30:45Z |
| cpu | windows-cpu-validation-reports | `sha256:8f38a60b9473ea915879d62adedd4dfc3b0a91ac9b1c5db3e7473ea51b89692e` | 2026-11-25T11:43:08Z |
| Microsoft 探測 | microsoft-runtime-evidence-reports | `sha256:6571a9d48778127beae91bd2a332b788515c5651912abf2fac48dccbc8341ed2` | 2026-11-25T12:05:37Z |

**前一個候選的紀錄（非固定候選）**：9ecedcf 的 base [run 44289885218](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289885218)、cpu [run 44289891259](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289891259)、Microsoft 證據 [run 44289896406](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44289896406)，皆 success。它是 VC runtime 替換的首次 CI 驗證。因為其審閱缺少揭露檔列，不作為固定候選。

## Microsoft 探測（2b 第 1 點）

探測存為 [microsoft-probe-7cf098e.json](microsoft-probe-7cf098e.json)，原樣保存 CI 解碼結果（sha256 `06ea54ffe310a80ef7b77364167dc8d52bd44c85d69764496056042386de8c3d`）。

- basis：`docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json`，source_commit `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`。
- scope：`installed-source-reconstruction`（與 9ecedcf 及 b17d51b 的 base 主 job 所用的 `built-bundle` 不同；候選 bytes 由 `a6_sha256` 與 bundle 觀測核對，見下表）。
- 14 檔齊。根目錄 `vcruntime140.dll`（`d5e4d9a3e835fa679450145d6a7d94e36573a509317111904d9b3712c30d9066`）與 `vcruntime140_1.dll`（`1f2d41c4aa5db0bc33ebf7b66d72943a817d7ce6cbe880502a9403823633093f`）與官方 Redist 同名檔完整 sha256 相同（`matches_official=True`）；其 `a6_sha256` 即為新候選 bytes（基準為 a13b 審閱）。
- 其他複本與 A6 相同（`matches_a6=True`）：PySide6 與 shiboken6 的 9 份 VC／MSVCP 複本、numpy 與 pandas 的改名 msvcp140 複本（`a4c2229bdc2a…`，改名 `renamed=True`）、根目錄 `msvcp140.dll`（與官方相同）。
- 簽章：14 份皆 Valid；PySide6／shiboken6 的 9 份 CompanyName 為 Microsoft Corporation，但簽署者為 The QT Company Oy（既有事實，列為 signature_review_files，不視為缺口）。
- `terms: []`：runner 的 VS2022 安裝目錄中沒有找到條款文字，與 A12 相同；目錄不以此欄位作依據。

**check_catalog 收回放寬**（2b 第 1 點）：探測的 `basis.source_commit` 必須等於目錄（登記表）的 `source_commit`，基準檔自身的 selection 也要相同。A12 的寬鬆規則已移除。反例：`test_probe_from_an_old_candidate_basis_is_rejected`（舊候選基準即使 hash 一致也被拒絕）、`test_probe_basis_source_must_equal_the_catalog_source`、`test_probe_basis_document_must_match_its_recorded_hash`。

## 使用者決定寫入（2b 第 2 點）

決定來源為 [docs/history/status/2026-11-18-a13-decisions.md](../../../history/status/2026-11-18-a13-decisions.md) D 節的 A13 逐條列（sha256 與 quote 由 gates 核對，quote 必須是存檔中的完整一行）。

| 條目 | 狀態 | 決定列 | accepted_gaps | 備註 |
| --- | --- | --- | --- | --- |
| base-microsoft | user_approved | A13-1 | 0 | 14 份複本；條款與再散布依據由使用者決定，EULA 與 REDIST 清單不能替代 |
| base-qt | user_approved | A13-2 | 85 | LGPL 動態連結做法；未知項目接受並揭露；揭露檔引用 |
| base-cpython | user_approved | A13-3 | 1（cpython/libffi） | libffi 僅建置宣告，揭露檔註明 |
| base-wheels-cffi | user_approved | A13-4 | 1（cffi/libffi） | 依 A13-4 列；libffi 同上 |
| base-wheels-numpy | user_approved | A13-4 | 2 | 版本未知元件接受並揭露 |
| base-wheels-pandas | user_approved | A13-4 | 1 | 同上 |
| base-wheels-pillow | user_approved | A13-4 | 3 | 同上 |
| base-wheels-lxml | user_approved | A13-4 | 3 | 同上 |
| base-wheels-cryptography | user_approved | A13-4 | 1 | 同上 |
| base-wheels-onnxruntime | user_approved | A13-4 | 1 | 同上 |
| base-wheels-pypdfium2 | user_approved | A13-4 | 10 | 同上 |
| base-tesseract-models | user_approved | A13-5 | 0 | 接受 CI 靜態建置的 tesseract.exe 5.5.3 與固定提交的四語 tessdata_fast |
| base-redistribution-decision | user_approved | A13-7 | 0 | evidence 為對應候選審閱與決定存檔；同意 B1 以 CI artifact 公開產出基本包測試版 |
| base-clean-machine-manual | **open** | — | — | A13-6 只確認限制文字；需大階段 C 的乾淨機與人工驗收證據 |

- 有未知元件的條目 `requires_user_decision` 為 true（A12c 規則）；八個 A13-4 條目原為 false，因使用者在 A13-4 作了決定而改為 true。
- `accepted_gaps` 合計 108 項，與 `known_gaps.py` 對本審閱推導的集合逐條相等（`known_gaps.py --check` 通過）。
- 揭露檔 `src/desktop_app/data/licenses/known-gaps.json`（sha256 `933165bf3485e9aea99f7608a64d0f0f4173dca56b9c9bce004e258b9399e3b7`）與候選中同名列相同，已作為 evidence 引用於有缺口的條目。
- `base-redistribution-decision` 原本沒有 evidence；依規則非 open 條目須有證據，故引用本審閱與決定存檔。

**未改動**：evidence_complete 的 base-source-attribution、base-own-mit-binding、base-archives、base-wheels-charset-normalizer、base-wheels-psutil；cpu 全部條目；A12 基準的歷史證據列。

## Gates 與出口報告（2b 第 3 點）

- [base-gates.json](base-gates.json)：exit 0；`runtime_sbom_complete` false（10 個條目仍有未知元件，阻擋清單見檔案）、`runtime_sbom_disclosed` true、`redistribution_approved` true、`release_ready` false。
- [cpu-gates.json](cpu-gates.json)：exit 0；四旗標皆 false。
- [base-exit-report.json](base-exit-report.json)：由登記表與 base gates 輸出推導（schema 2）；entries 含狀態、決定出處與 accepted_gaps 數量。分類：user_approved 14、evidence_complete 5、open 1（clean-machine-manual）。

## 本階段的其他改綁

- 登記表：兩 profile `source_commit` 為 b17d51b。`packaging/embedded/base-windows.json`、`packaging/qt/6.12.0/thirdparty/catalog.json`、`packaging/microsoft/base-windows.json` 的 sha256 引用已同步（base-microsoft 的目錄引用已隨 2b 更新）。
- `packaging/microsoft/base-windows.json`：`basis` 改指 a13b 審閱；`probe` 改指本目錄的 microsoft-probe-7cf098e.json；`files`、`references` 改為新探測值；`scope` 與 `limitations` 的過時敘述已更新。
- `scripts/microsoft_runtime.py`：`BASIS_PATH` 為 a13b 審閱；`check_catalog` 收回放寬。
- 測試：`tests/test_microsoft_runtime.py`、`tests/test_embedded_components.py`、`tests/test_embedded_runtime.py`、`tests/test_redistribution_gates.py` 的 actual 系列斷言改為決定後的狀態，並新增上述反例；embedded 測試傳入與 gates 相同的揭露 validator。`EXPECTED_TESTS` 為 929。

## 測試

`python -m unittest discover -s tests`（環境同前）：**Ran 929；failures 1、expected failures 1（ONNX 繁中，既有）**。唯一失敗為 `test_history_index.test_repository_index_is_current`：新增本證據目錄後索引過期，依協調者規則由協調者重建 `scripts/build_history_index.py`。

## 限制

- `release_ready` 為 false，需大階段 C（乾淨 Windows 10／11 實機、人工操作、四語與中文路徑、修復移除）。
- 本結果不是乾淨機驗收，也不是 GPU 實卡驗收。
- 決定列語意（是否真出自使用者、A13-6 文字是否足夠）仍需人工查驗；gates 只檢查格式與位置。
- 探測為 installed-source-reconstruction 觀測；候選 bytes 的一致性由 `a6_sha256` 與原生檔比對，不是 built-bundle 直接觀測。前一次 built-bundle 觀測（b17d51b 的 base 主 job）保存於 [windows-probe.json](windows-probe.json)，但其基準是 A6，只作歷史。
- 仍引用 A12 審閱的 evidence 列未改指（見 2a 報告的疑點）。
- ONNX 繁中缺口、RAM 軟性預算、Windows 實機／GPU 未驗收維持。
- 不交付安裝包，不建 Release 或 tag；B1 另行開始。

## 檔案

- [base-source-review.json](base-source-review.json)、[cpu-source-review.json](cpu-source-review.json)：b17d51b 候選審閱，離線 replay 通過。
- [microsoft-probe-7cf098e.json](microsoft-probe-7cf098e.json)：2b 使用的 Microsoft 探測。
- [windows-probe.json](windows-probe.json)：b17d51b base 主 job 的 built-bundle 探測（A6 基準，歷史）。
- [base-gates.json](base-gates.json)、[cpu-gates.json](cpu-gates.json)、[base-exit-report.json](base-exit-report.json)。
- [manifest.json](manifest.json)：日期、來源、結果、檔案雜湊與關鍵字。

## 已知過期的引用（Claude reviewer 指出，2026-11-18）

`base-source-attribution`、`base-archives`、`base-own-mit-binding` 三個 evidence_complete 條目仍引用 A12 審閱與 A12b 的 `origin-known-review.json`（綁 2555687）。A12 與本候選 b17d51b 的 30 個 origin-known 列中有 6 列 sha256 不同：`base_library.zip`、`native/manifest.json`、`python-modules.json`、`third-party.md`（建置產生檔，對照理由屬類別性，不受影響），以及根目錄 `vcruntime140.dll`、`vcruntime140_1.dll`。後兩列在 A12b 的理由寫「來自 CPython 3.12.10 官方安裝目錄、PE 14.42」，對本候選已不正確；本候選這兩個檔改為官方 Redist（PE 14.44），其 bytes 由 `packaging/microsoft/base-windows.json`（base-microsoft 的證據）逐檔涵蓋，A12b 該兩列的 remaining_obligation 原本也指向 base-microsoft。gates 不會偵測這種過期；後續編號應以本候選重產逐列對照並更新三條目的 evidence（見 STATUS.md C 節）。


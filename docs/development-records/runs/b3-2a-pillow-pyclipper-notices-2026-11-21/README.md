# B3-2a 原文補件 II：Pillow（libaom、dav1d、Raqm）與 pyclipper（Clipper 標頭、BSL-1.0）

2026-11-21（台北），2026-11-22 續作。從 origin/main `85c28dd`（含 B3-1，PR 57）新開 `claude/b3-2a-pillow-pyclipper-notices`。程式版本 0.19.1、架構 0.4 不變。**不重新固定候選**：`source_commit` 仍是 A13b 的 `b17d51b`，`packaging/redistribution/obligations.json` 的狀態、`requires_user_decision`、`decision_source`、`accepted_gaps` 都沒有改。只同步了必要的雜湊（見下節）。

**狀態：完成（依使用者決定，libyuv 的 PATENTS 不補）。** 續作時 googlesource 已開放，libaom 的 LICENSE 與 PATENTS 已補入，先前的阻擋已解除。

## 做了什麼

1. **確認 Pillow 13.0.0 Windows wheel 實際編入的函式庫。** 依固定標籤 `13.0.0`（commit `293218ad`）的 `winbuild/build_prepare.py`、`.github/dependencies.json`、`.github/workflows/wheels.yml`、`pyproject.toml` 的 `[tool.cibuildwheel] config-settings`、`setup.py`，以及 wheel 內 SBOM 與 `.pyd` 位元組核對。結論見下表「元件結論」。
2. **補入 6 份原文**（逐 byte 等於上游固定 commit 的檔案，雜湊與來源見下節），放在 `src/desktop_app/data/licenses/windows/supplemental/`：
   - `libaom.txt`（BSD-2-Clause，aom 標籤 `v3.14.1` 固定 commit `03087864` 的 LICENSE）。
   - `libaom-PATENTS.txt`（Alliance for Open Media Patent License 1.0，同一 commit 的 PATENTS）。
   - `dav1d.txt`（BSD-2-Clause，dav1d 1.5.3 的 COPYING）。
   - `raqm.txt`（MIT，libraqm 0.11.0 的 COPYING）。
   - `clipper-header.txt`（Clipper 6.4.2 的著作權與授權聲明，取自 pyclipper 固定標籤 `src/clipper.hpp` 的第 1–32 行，位元組未改寫）。
   - `bsl-1.0.txt`（Boost Software License 1.0 全文）。
3. **綁定擁有者**：`scripts/license_inventory.py` 的 `SUPPLEMENT_OWNERS` 新增 `libaom`、`libaom-PATENTS`、`dav1d`、`raqm` → `pillow`，`clipper-header`、`bsl-1.0` → `pyclipper`。`inventory.json` 的 pillow 列帶 dav1d、raqm、libaom、libaom-PATENTS；pyclipper 列帶 clipper-header、bsl-1.0。`scripts/prepare_worker_assets.py` 的 `WORKER_NOTICE_PINS` 新增 6 筆綁定（擁有者、版本、METADATA 雜湊、URL、sha256、大小）。
4. **目錄與登記**：`base-windows.json` 的 pillow 元件 `notices` 新增 dav1d、raqm、libaom、libaom-PATENTS（base 檢核接受 supplemental 路徑）。`cpu-windows.json` 的 pillow、pyclipper 元件**維持不變**：CPU 檢核只接受 `licenses/windows/<dist>/wheel/` 下的原文（`embedded_components.py`），因此 supplemental 只在 inventory 與閉包綁定，與 B3-1 的做法相同；B3-5 揭露檔會直接從 inventory 的 supplemental 列產生。
5. **閉包與索引**：`packaging/profiles/base-closure.json`（`scripts/packaging_profiles.py --generate`）與 `cpu-windows-closure.json`（`scripts/cpu_worker_profiles.py --generate`）重生。`src/desktop_app/data/licenses/index.html` 以 `license_inventory.py --verify --render` 重新渲染；`third-party.md` 沒有變動。
6. **反例與測試**：見「驗證」。

## 元件結論

| 元件 | 編入 wheel？ | 證據（分級） | 本次處理 |
| --- | --- | --- | --- |
| libaom 3.14.1（aom 標籤 `v3.14.1` → commit `03087864`） | **是**，靜態併入 `PIL/_avif.cp312-win_amd64.pyd`（字串 `libaom` 3 次、`aom_codec_` 10 次） | **Windows 執行期觀測**（runtime-observed）：A12d hosted Windows run 44270551031，`PIL._avif.codec_versions()` 回報 `aom 3.14.1`。上游建置設定：libavif v1.4.2 `cmake/Modules/LocalAom.cmake` 釘 `AVIF_AOM_GIT_TAG v3.14.1`，`GIT_REPOSITORY https://aomedia.googlesource.com/aom.git`。標籤解參照 commit `03087864`，與 googlesource 取回的 LICENSE、PATENTS 位元組相同。wheel 內 LICENSE 無 aom 段。 | **補 `libaom.txt` 與 `libaom-PATENTS.txt`**，綁 pillow。 |
| dav1d 1.5.3（commit `b546257f`） | **是**，靜態併入 `PIL/_avif.cp312-win_amd64.pyd` | 上游建置設定：libavif v1.4.2 `cmake/Modules/LocalDav1d.cmake` 釘 `AVIF_DAV1D_TAG 1.5.3`，Pillow 以 `AVIF_CODEC_DAV1D=LOCAL` 建置（`build_prepare.py`）。**Windows 執行期觀測**（runtime-observed）：A12d hosted Windows run 44270551031，`PIL._avif.codec_versions()` 回報 `dav1d 1.5.3-0-gb546257`，承載原生檔與 A12 候選同一位元組。tag `1.5.3` 的 peel commit 為 `b546257f`，與觀測字串一致。wheel 內 LICENSE 只有 `src/obu.c` 的 dav1d 歸屬段（2018–2019），不是完整 COPYING。 | **補 `dav1d.txt`**，綁 pillow。 |
| libyuv（commit `644251f2`） | **是**，libavif `AVIF_LIBYUV=LOCAL` 建置，`yuv` 靜態連結進 aom 與 avif（`_avif.pyd` 含 libyuv 字串 2 次） | 上游建置設定：`LocalLibyuv.cmake` 的 `AVIF_LIBYUV_TAG 644251f252a84bf8ce91ff0aca86a9b16b069ab8`（完整 commit）。版本只能到 commit，A12d 未取得版本 API，因此分級為 upstream-build-config。wheel 內 libavif-1.4.2 段含 `Files: third_party/libyuv/*` 的版權與 BSD 條文全文（與上游 LICENSE 正規化後逐段相符）。 | **不補 LICENSE**（wheel 已有條文全文）。**不補 PATENTS**，依使用者決定（2026-11-22），見下節。 |
| Raqm 0.11.0（libraqm `08ee1537`） | **是**，Pillow 內附 `src/thirdparty/raqm/raqm.c` 在 vendor 模式編入 `PIL/_imagingft.cp312-win_amd64.pyd`（`raqm_create`、`raqm_layout` 等符號字串） | 上游建置設定：`pyproject.toml` `[tool.cibuildwheel] config-settings = "raqm=enable raqm=vendor fribidi=vendor ..."`，適用 Windows；`setup.py` vendor 分支編入 `raqm.c` 與 harfbuzz。wheel SBOM 宣告 raqm 0.11.0 MIT，vendored `raqm.c` 的 sha256 `d3cb7309…` 與 SBOM 相符。Pillow 內附版本與上游 `src/raqm.c` 不同（77 bytes、Pillow 補丁，SBOM 標示）。A12d：`version_feature('raqm')` 為 None，無 Windows 版本值，**不以 runtime-observed 分級**。 | **補 `raqm.txt`**，綁 pillow。 |
| FriBiDi 1.0.17 | **否**。`_imagingft` 內的 `fribidi-shim` 執行期 `LoadLibrary` 動態載入 `libfribidi`；wheel 內沒有任何 DLL；`wheels.yml` 另外把 fribidi DLL 上傳為獨立成品，不入 wheel。SBOM 宣告 scope optional、LGPL-2.1-or-later。 | `build_prepare.py`（預設建置 fribidi）、`wheels.yml` 的 `Upload fribidi.dll` 與「Skip FriBiDi license, it is not included in the wheel」註解、wheel 檔案清單。 | **不補，也不需要 LGPL 決定**：沒有隨包的 FriBiDi 程式碼。 |
| Clipper 6.4.2（pyclipper 1.4.0 固定標籤） | **是**，`_pyclipper.cp312-win_amd64.pyd` 含 `Clipper` 字串 72 次、`Angus` 1 次。 | wheel METADATA 寫 `Clipper library (ver. 6.4.2)`（wheel-declared）；固定標籤 `src/clipper.hpp` 的 `CLIPPER_VERSION "6.4.2"` 與檔頭版本同。wheel 的 LICENSE 只有 pyclipper 自己的 MIT（不含 Clipper 與 BSL 聲明）。 | **補 `clipper-header.txt`（檔頭 1–32 行）與 `bsl-1.0.txt`**，綁 pyclipper。pyclipper 只在 CPU 版本。 |
| libimagequant、OpenCV、onnxruntime、NumPy | 不屬本階段 | libimagequant 由 `--no-imagequant`／`imagequant=disable` 排除。其餘為 B3-2b。 | 未處理。 |

## 原文清單（逐 byte 等於上游固定來源）

| 檔案（supplemental/） | 擁有者（版本） | 上游來源 | sha256 | bytes | 授權 | 版本依據（分級） |
| --- | --- | --- | --- | --- | --- | --- |
| `libaom.txt` | pillow（13.0.0） | `aomedia.googlesource.com/aom` `03087864cf4bea6abb0d28f95cf7843511413d8f` `LICENSE`（標籤 `v3.14.1`） | `4764a286d8b2faeaf42f4418e7d7a28d58fc8fd4d00a3d0a7f44b0a4099de7f2` | 1316 | BSD-2-Clause | runtime-observed（A12d run 44270551031），upstream build config（LocalAom.cmake）為佐證 |
| `libaom-PATENTS.txt` | pillow（13.0.0） | 同上 `PATENTS` | `661fb8e504744e95587b556b94a58343448300606a41bea8c7a9b97125696e61` | 5701 | Alliance for Open Media Patent License 1.0 | 同 libaom（同一 commit） |
| `dav1d.txt` | pillow（13.0.0） | `videolan/dav1d` `b546257f770768b2c88258c533da38b91a06f737` `COPYING` | `dd92c3c2247c5651606fc23a5e2d6a1ebc5ace9a3e49cbde0e12f05ad1cb1ee5` | 1317 | BSD-2-Clause | runtime-observed（A12d run 44270551031），upstream build config 為佐證 |
| `raqm.txt` | pillow（13.0.0） | `HOST-Oman/libraqm` `08ee1537e63f93bf926498e12b12ed15ee383216` `COPYING` | `f6baa5c872ed0c35cde377735f930d97a23e08065d87cf34d766b3aad5beed1e` | 1180 | MIT | wheel-declared（SBOM）與 upstream build config；Windows 無版本 API |
| `clipper-header.txt` | pyclipper（1.4.0） | `fonttools/pyclipper` `f998920369565dca56d346bb30c5741e273f0b9b` `src/clipper.hpp` 第 1–32 行 | `8fa62835d1b88be098193df53e921475d6a7119a3f3de8046eed81b9ffa23f67` | 2624 | BSL-1.0（Clipper 6.4.2 聲明） | wheel-declared（METADATA）與固定標籤檔頭 |
| `bsl-1.0.txt` | pyclipper（1.4.0） | `boostorg/boost` `1bed2b0712b2119f20d66c5053def9173c8462a5` `LICENSE_1_0.txt` | `c9bff75738922193e67fa726fa225535870d2aa1059f91452c411736284ad566` | 1338 | BSL-1.0 | 授權全文，跨版本固定 |

來源說明：

- aom、dav1d、libraqm、pyclipper、boost 的標籤以 `git ls-remote` 解析為上表 commit。dav1d 透過 GitHub 鏡像（code.videolan.org 本環境不可達），其 `1.5.3^{}` 即 `b546257f`。aom 的 LICENSE 與 PATENTS 直接從 `aomedia.googlesource.com` 以 `?format=TEXT`（base64）取得，解碼後與標籤 `v3.14.1` 取回的位元組相同。
- `clipper-header.txt` 不是整檔：`sources.json` 的 URL 指向 `clipper.hpp` 整檔（`734eba9d…`，15423 bytes），本檔是其第 1–32 行的位元組，`manifest.json` 記錄整檔雜湊與截取範圍。截取只為避免把整份標頭程式碼放進授權目錄。
- `bsl-1.0.txt` 的 canonical 位置是 boost.org，本環境只能取得 GitHub 上同一檔案的固定 commit 版本。
- `sources.json` 的 `url`、`sha256`、`bytes` 與上表一致。

## 使用者決定與未完成事項

1. **libyuv 的 PATENTS 不補（使用者決定，2026-11-22，協調者轉達）。** libyuv 的 BSD 條文已在 wheel 內全文出現，因此只保留 wheel 內的 BSD 原文。理由：BSD 只要求附授權文字，PATENTS 是額外的專利授權，不是散布義務。上游鏡像檔案 `4da84211…`（1387 bytes）保留在 manifest 中作為參照，未入 supplemental。
2. **登記表與已知缺口需協調者決定（本次未改）。** `packaging/redistribution/obligations.json` 的 `base-wheels-pillow` 仍有 `accepted_gaps: ["pillow/fribidi", "pillow/libyuv", "pillow/raqm"]`，`required_evidence` 仍寫 raqm、libyuv 版本未知；`src/desktop_app/data/licenses/known-gaps.json` 的 `base-wheels-pillow` 也列同樣三項。依指示沒有改狀態、`requires_user_decision`、`decision_source`、`accepted_gaps`。raqm 與 libaom、dav1d 已有原文與版本依據，libyuv 已有 commit 依據；這些項目是否關閉、改寫文字，待協調者與使用者決定。
3. **dav1d 的 COPYING 與 wheel 內 `src/obu.c` 段的差異**：年份不同（2018–2025 與 2018–2019）。本次補完整 COPYING，不改 wheel 內既有段落。
4. **Pillow 內附的 Raqm 原始碼與上游 v0.11.0 不同**（77 bytes 補丁）。授權條文以上游 MIT 原文為準；補丁本身的著作權歸屬不在本次範圍。

## 雜湊同步清單

| 檔案 | 舊 sha256 | 新 sha256 | 同步處 |
| --- | --- | --- | --- |
| `src/desktop_app/data/licenses/windows/inventory.json` | `27765d770a6b7fa370abd38c0d46124c4dfa3a28a1f49d57ff445be8aeda81ca` | `c479b78be51bdcd3b0cd00d6f945e15653c2d65fd12ee824dd78b03cafead50f` | `packaging/embedded/base-windows.json`、`cpu-windows.json` 的 `inventory.sha256`（已同步）；a12／a13b review 歷史快照保留 |
| `src/desktop_app/data/licenses/windows/supplemental/sources.json` | `a37099ae9783aa8ba050e04950b4e7dd501d7345d978238d750f60126d78e4f5` | `f2eb3c4acfc42984f5f7ce674875c6687f34193a5ffa631aa5cb037e9be1c781` | `inventory.json` 的 files 表（已同步）；a12／a13b review 歷史快照保留 |
| `packaging/embedded/base-windows.json` | `747316259c1d8246e61bbc83fcda0f46785d4297ce2e504a3e0fbbf275c8067f` | `ed8e42ab74169ac2363d3d038011e2ed33042051402bebcbcbe3505e5c89183d` | `packaging/redistribution/obligations.json` 10 處（已同步） |
| `packaging/embedded/cpu-windows.json` | `344b5ac3bbfc74e02399e3b285da35cc62e9e679c751e30ab48a4e806dcbd7e3` | `7c92f1c4ad769def10cb097c988ef54b12168985ebc4b232902ee8b83c00d6ac` | `packaging/redistribution/obligations.json` 2 處（已同步） |
| `src/desktop_app/data/licenses/index.html` | 見 B3-1 | 重新渲染 | 無外部引用（B3-1 歷史快照保留） |
| `packaging/profiles/base-closure.json`、`cpu-windows-closure.json` | 內容改變 | 見 manifest | 無外部引用 |

`cpu-windows-build.txt` 與 `base-windows-build.txt` 沒有變動（鎖檔不改）。`third-party.md` 沒有變動。

## base 與 CPU 各自受影響的檔案

- **base**（Pillow 同時在 base 與 CPU）：`packaging/embedded/base-windows.json`（pillow 元件 notices 新增 dav1d、raqm、libaom、libaom-PATENTS，`inventory.sha256`）、`packaging/profiles/base-closure.json`（pillow 列的 4 個 profile 各多 4 筆）、`inventory.json`、`index.html`。
- **CPU**：`packaging/embedded/cpu-windows.json`（只有 `inventory.sha256`；pillow 與 pyclipper 元件的 notices 依 CPU 檢核維持不變）、`packaging/profiles/cpu-windows-closure.json`（pillow 多 4 筆、pyclipper 多 2 筆）。
- **base 的 `base-windows.json` 與 CPU 的 `cpu-windows.json` 都因 inventory 雜湊改變而重算雜湊。** 下游的 `obligations.json` 已同步。

## 到 B3-9 必須重新核對的項目

1. 固定候選 `b17d51b` 的 source-review（a12、a13b）與現在的 inventory、supplemental 內容不同，這是預期的。B3-9 要重新固定候選並重產 source-review。
2. libaom 兩份原文的來源 commit、雜湊，以及 inventory、embedded、obligations 的同步。
3. libyuv PATENTS 不補是使用者決定；若 B3-9 或使用者改變主意，需比照 libaom 補入並同步雜湊。
4. Pillow 13.0.0 的 wheel 內容若換版，dav1d、libaom、Raqm 的版本依據與 `_avif.pyd`、`_imagingft.pyd` 位元組要重新觀測（A12d 的 run 只對應目前的 wheel）。
5. `packaging/redistribution/obligations.json` 的 `base-wheels-pillow` 與 `known-gaps.json` 仍列 raqm、libyuv 缺口與舊的 required_evidence 文字，待協調者決定是否關閉。
6. `pyclipper` 的 CPU notices 仍不含 supplemental（CPU 檢核限制），B3-5 揭露檔要從 inventory 產生。
7. FriBiDi 若未來改為隨包或改用系統 DLL，必須先停下，因為那會觸發 LGPL 原文與再散布義務。

## 驗證

測試與突變驗證的數字見 [docs/progress.json](../../../progress.json)（full_regression），這裡不重抄。

- 相關單元測試：`tests/test_bundle_provenance.py`、`tests/test_license_inventory.py` 全部通過（含新增子案例）。
- **測試函式**：只新增一個 `test_b3_2a_pins_match_the_recorded_evidence_manifest`（pins 與本目錄 manifest 一致，涵蓋 dav1d、raqm、libaom、libaom-PATENTS、clipper-header、bsl-1.0）。其餘為既有測試的子案例：`test_b3_1_owner_and_source_mutations_are_rejected_even_after_rehashing` 新增 6 個子案例（dav1d 錯綁、raqm 額外擁有者、Clipper 標頭額外 inventory 擁有者、BSL 來源 URL 被改、libaom 錯綁到 pyclipper、libaom-PATENTS 來源 URL 被改）；`test_supplement_owner_binding_is_checked_when_owner_present` 新增 6 個子案例；`test_worker_original_missing_or_changed_is_rejected_even_after_rehashing` 自動涵蓋 6 份新原文的缺檔、內容改變、同長度改動。
- **突變驗證**（每次只移除一個守衛，執行相關測試，然後還原；還原後的檔案雜湊與前後相同）：

  | 突變 | 位置 | 結果 |
  | --- | --- | --- |
  | M1 移除 inventory 唯一擁有者檢查（claims） | `prepare_worker_assets.py` | 失敗 2 個子案例（libyaml、clipper 額外擁有者） |
  | M2 移除 manifest 擁有者檢查 | `prepare_worker_assets.py` `verify_worker_notice_bindings` | 失敗 3 項（paddleocr、raqm 額外擁有者，以及 `test_worker_notice_rejects_…` 的 extra-owner） |
  | M3 移除 sources 記錄檢查 | `prepare_worker_assets.py` | 失敗 3 個子案例（paddleocr、bsl、libaom-PATENTS 來源 URL） |
  | M4 移除 license_inventory 擁有者綁定 | `license_inventory.py` `verify` | 失敗 `test_supplement_owner_binding…` |
  | M5 移除原文 SHA-256 檢查（只剩大小檢查） | `prepare_worker_assets.py` | 失敗 28 個子案例，包含 6 份新原文的同長度改動 |

- 其餘驗證（基線、回歸、gates、再生產物、索引、進度）見 `manifest.json` 的 `regression` 與 `gates` 欄位，以及 CHANGELOG「更新中」一行。

## 限制

- 只有 wheel 內位元組的字串計數與 zip 中繼資料，**沒有安裝、執行或 Windows 實機驗收**。`wheel-observation.json` 只作佐證，不是編入證明。
- 「編入」的判斷依賴上游建置設定（`build_prepare.py`、`setup.py`、`cibuildwheel` 設定、libavif 的 LOCAL cmake 模組）與 Pillow 自己宣告的 SBOM。這些是「建置設定」證據，不是逐檔連結圖。
- 沒有做法律審核；本文件不是最終再散布核准。
- 本次不擴大授權與再散布範圍，沒有建立 Release、tag，也沒有觸發 `windows-build.yml`。

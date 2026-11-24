# B3-2b 原文補件 II 後半：OpenCV（zlib、libpng）、onnxruntime、NumPy 查證

2026-11-23（台北）。從 origin/main `77f2d80`（含 B3-1、B3-2a、B3-3）新開 `claude/b3-2b-opencv-onnxruntime-numpy-notices`。程式版本 0.19.1、架構 0.4 不變。**不重新固定候選**：`source_commit` 仍是 A13b 的 `b17d51b`，`packaging/redistribution/obligations.json` 的狀態、`requires_user_decision`、`decision_source`、`accepted_gaps`、`required_evidence` 都沒有改，只同步了嵌入檔雜湊（見「雜湊同步」）。

**狀態：OpenCV 的 zlib、libpng 已補原文；onnxruntime、NumPy 查證後無可確認的缺口，未補；ITT 的雙授權選擇需使用者決定，未補。**

## 做了什麼

1. **下載並核對鎖定 wheel**：opencv-python 5.0.0.93、onnxruntime 1.31.1、numpy 2.5.4（cp312 win_amd64）的 sha256 與 `packaging/profiles/cpu-windows-build.txt`、`base-windows-build.txt` 一致；另下載 `packaging/requirements-windows.txt` 鎖定的全部 58 個 wheel 做完整重生比對（見「驗證」）。
2. **OpenCV 的 Windows 編入判定**：依固定上游 opencv-python 標籤 `93`（commit `b83046cd`，5.x 分支）、其 opencv 子模組 commit `40738fb1`（Release 5.0.0）的 `CMakeLists.txt`（`BUILD_ZLIB` 於 WIN32 預設 ON、`BUILD_PNG` 於 WIN32 預設 ON）、`3rdparty/zlib/zlib.h`（`ZLIB_VERSION "1.3.2"`）、`3rdparty/libpng/png.h`（`PNG_LIBPNG_VER_STRING "1.6.57"`）、`setup.py`（`BUILD_SHARED_LIBS=OFF`，只產出 `cv2.pyd`）與 wheel 的 PE 匯入表（`cv2.pyd` 不匯入任何 zlib／libpng DLL）核對。
3. **補入 2 份原文**（逐位元組等於上游固定 commit，並與 opencv 固定 commit 內的 3rdparty 副本 sha256 相同），見下節。
4. **綁定擁有者**：`scripts/license_inventory.py` 的 `SUPPLEMENT_OWNERS` 新增 `opencv-zlib`、`opencv-libpng` → `opencv-python`；`scripts/prepare_worker_assets.py` 的 `WORKER_NOTICE_PINS` 新增兩筆（owner `opencv-python`、版本 `5.0.0.93`、METADATA LF 正規化雜湊 `20749df4…`，與 pillow 既有 pin 的計算方式相同）。
5. **查證 onnxruntime 與 NumPy**：見「元件結論」與「涵蓋／缺口表」。

## 元件結論

### OpenCV 5.0.0.93（只在 CPU）

| 元件 | 編入 Windows cv2.pyd？ | 版本與依據（分級） | wheel 原文 | 本次處理 |
| --- | --- | --- | --- | --- |
| zlib 1.3.2 | **是，靜態**（BUILD_ZLIB；`cv2.pyd` 內 `deflate 1.3.2 Copyright 1995-2026` 字串；PE 匯入無 zlib DLL） | **Windows 執行期觀測**：hosted Windows 2022 run [44755140396](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44755140396)（B3c `cpu-native-observation.json`，`records['opencv-python/opencv'].build_declarations`）呼叫 `cv2.getBuildInformation()`，輸出 `ZLib: build (ver 1.3.2)`；該次觀測的 `cv2/cv2.pyd` sha256 `f1e76ab0…` 與本次 wheel 內 cv2.pyd 相同（已本地重算）。上游佐證：opencv 3rdparty/zlib 1.3.2。 | `cv2/LICENSE-3RD-PARTY.txt` 的 libz 段只寫「all opencv-python **Linux** packages」 | **補 `opencv-zlib.txt`**（madler/zlib v1.3.2 LICENSE） |
| libpng 1.6.57 | **是，靜態**（BUILD_PNG；`cv2.pyd` 內 `libpng version 1.6.57` 字串 2 次；PE 匯入無 png DLL） | **Windows 執行期觀測**：同 run，`PNG: build (ver 1.6.57)`，同一 cv2.pyd。上游佐證：opencv 3rdparty/libpng `PNG_LIBPNG_VER_STRING 1.6.57`。 | 段落只寫「all opencv-python **Linux and macOS** packages」 | **補 `opencv-libpng.txt`**（pnggroup/libpng v1.6.57 LICENSE） |
| libjpeg-turbo 3.1.2-70 | 是（`JPEG: build-libjpeg-turbo`） | 執行期觀測（同 run） | 段落「all opencv-python packages as build option」，涵蓋 Windows | 未補（已涵蓋） |
| libwebp（decoder 0x0210） | 是 | 執行期觀測（同 run） | 「all opencv-python packages」 | 未補（已涵蓋） |
| libtiff 4.7.1 | 是 | 執行期觀測（同 run，`TIFF: build (ver 42 - 4.7.1)`） | 「all opencv-python packages」 | 未補（已涵蓋） |
| OpenJPEG 2.5.3 | 是（JPEG 2000） | 執行期觀測（同 run） | 「all opencv-python packages」 | 未補（已涵蓋） |
| Protobuf 3.19.1 | 是 | 執行期觀測（同 run） | 「all opencv-python packages」 | 未補（已涵蓋） |
| Flatbuffers 25.9.23 | 是（builtin） | 建置宣告（`cv2.pyd` 字串 `Flatbuffers: builtin/3rdparty (25.9.23)`） | 「all opencv-python packages」 | 未補（已涵蓋） |
| CLapack（Windows） | 是（`Lapack: YES (Built-In libclapack)`） | 建置宣告 | 段落「for Windows」，涵蓋 | 未補（已涵蓋） |
| Intel IPP ICV（ippicv、ipphal、ippiw） | 是，靜態（`Custom HAL: ipp`、`Intel IPP: 2026.0.0`） | 建置宣告（字串）；版本 2026.0.0 未經執行期觀測 | 段落「Intel(R) IPP ICV library statically linked within x86 and x86_64 opencv-python packages」，但寫 **2021 Update 10**，與 2026.0.0 不一致 | 未補；**需 B3-9 核對原文涵蓋 2026.0.0**（見「到 B3-9 必須重新核對」） |
| Intel ITT（ittnotify 3.25.4） | 是，靜態（`cv2.pyd` 內 `__itt_` 符號 178 次、`ittnotify` 字串 2 次；`Trace: YES (with Intel ITT(3.25.4))`） | 建置宣告與二進位字串；版本未經執行期觀測 | **wheel 內無 ITT 原文** | **未補，停下回報**：上游 `3rdparty/ittnotify/src/ittnotify/ittnotify_static.c` SPDX 為 `GPL-2.0-only OR BSD-3-Clause`，opencv 自己以 `ocv_install_3rdparty_licenses` 安裝 BSD-3-Clause.txt 與 GPL-2.0-only.txt。選 BSD-3 或 GPL-2.0、或兩者並附，屬需使用者決定的授權選擇。 |
| Orbbec SDK | 未確認 | build 宣告 `Orbbec: YES`；`cv2.pyd` 內無 `OrbbecSDK` 字串；wheel 內無 Orbbec DLL；wheel 原文 Orbbec 段只寫 arm64 macOS 套件 | 只涵蓋 macOS arm64 | 未補、維持 unknown；**需 Windows 觀測**（見下節） |
| FFmpeg（`opencv_videoio_ffmpeg500_64.dll`，build 宣告 avcodec 61.19.100） | 獨立 DLL，不在 `cv2.pyd` | — | — | **依使用者 2026-11-13 決定排除**，本次未處理 |
| AVIF、OpenEXR、GStreamer | 未編入（build 宣告 NO） | — | — | 不適用 |

OpenCV 的 cpu unknown 共 8 項（`packaging/embedded/cpu-windows.json` 中 `version_basis` 為 unknown 的 zlib、libjpeg-turbo、libwebp、libpng、libtiff、openjpeg、protobuf、ipp-icv）。本次只有 zlib、libpng 的 Windows 歸屬有補原文，其餘 6 項涵蓋條文已在 wheel 內，版本仍無法由 wheel 文字判定，維持 unknown 不升級。`cpu-windows.json` 的 zlib 與 libpng 列也維持原樣（version null，見「雜湊同步」說明）。

### onnxruntime 1.31.1（base 與 CPU 共用）

**結論：查證無法確認缺口，未補原文。**

- 上游來源不可達：`microsoft/onnxruntime` 的 git 標籤查詢失敗（需認證），`raw.githubusercontent.com/microsoft/onnxruntime/{main,rel-…}/…` 的 README、ThirdPartyNotices、`cmake/deps.txt` 皆 404。因此無法取得固定 Windows CPU 建置的依賴清單，也無法做逐成員版本比對。
- wheel 內 `onnxruntime/ThirdPartyNotices.txt`（6369 行）與 `onnxruntime/LICENSE`（MIT）。以 `onnxruntime.dll`、`onnxruntime_pybind11_state.pyd` 的位元組字串計數，名稱層級可見 protobuf、abseil（absl）、re2、XNNPACK、cpuinfo、flatbuffers、safeint、Eigen、GSL、onnx、KleidiAI、MLAS 等，這些名稱在 ThirdPartyNotices 中都有對應段落。
- 逐成員版本、靜態併入範圍與「段落是否對應實際成員」無法確認。依規則，不能因為段落存在就補，也不能因為上游不可達就宣稱缺口。維持 unknown（cpu 1 項）。
- PE 匯入：`onnxruntime.dll` 匯入 `msvcp140.dll`、`vcruntime140*.dll`、`dbghelp.dll`、`setupapi.dll`、`dxgi.dll`，**不含 MinGW 或 libgomp**。MSVC runtime 屬 B3-4 的 Microsoft 再散布範圍，不在本階段。

### NumPy 2.5.4（base 與 CPU 共用）

**結論：涵蓋，無明確缺口，未補原文。**

- `numpy.libs/` 只有兩個 DLL：`libscipy_openblas64_-ed4f167a….dll`（OpenBLAS，二進位字串 `0.3.34`，PE 匯入僅 `kernel32` 與 `api-ms-win-crt-*`）與 `msvcp140-a4c2229b….dll`（改名複本，B3-4 範圍）。**沒有 MinGW／libgfortran／libgcc／libwinpthread 的獨立 DLL**。
- `libgfortran` 以靜態方式併入 OpenBLAS DLL（字串 `libgfortran/runtime/error.c` 等 3 次）。
- wheel 內 `numpy-2.5.4.dist-info/licenses/LICENSE.txt` 已含：OpenBLAS（BSD-3-Clause，`Copyright (c) 2011-2014, The OpenBLAS Project`）、LAPACK（BSD-3-Clause-Open-MPI 段）、「GCC runtime library」段（`GPL-3.0-or-later WITH GCC-exception-3.1`），以及 GCC Runtime Library Exception 3.1 與 GPL-3.0 全文。
- 未能由 wheel 確認的是 libgfortran 的精確版本（B3c 所列「精確版本及最終連結範圍」）。這不影響原文是否涵蓋：授權條文與例外全文都在 wheel 內。cpu unknown 共 2 項（`gcc-runtime-libgfortran`、`numpy-bundled-sources`）維持 unknown。

## 涵蓋／缺口表

| 套件 | 元件 | 結論 | 處理 |
| --- | --- | --- | --- |
| opencv-python | zlib 1.3.2 | 缺口（Windows 歸屬，wheel 原文只標 Linux） | 補 `opencv-zlib.txt` |
| opencv-python | libpng 1.6.57 | 缺口（wheel 原文只標 Linux/macOS） | 補 `opencv-libpng.txt` |
| opencv-python | libjpeg-turbo、libwebp、libtiff、OpenJPEG、Protobuf、Flatbuffers、CLapack | 涵蓋（段落標 all packages 或 Windows） | 不補 |
| opencv-python | Intel IPP ICV | 涵蓋，但段落版本 2021 U10 與 build 宣告 2026.0.0 不一致 | 不補；B3-9 核對 |
| opencv-python | Intel ITT（ittnotify） | 無 wheel 原文；雙授權（GPL-2.0 或 BSD-3） | **需使用者決定**，不補 |
| opencv-python | Orbbec SDK | 未確認 | 需 Windows 觀測 |
| onnxruntime | 全部第三方成員 | 無法確認（上游不可達） | 不補；需上游清單或 Windows 觀測 |
| numpy | OpenBLAS 0.3.34、LAPACK | 涵蓋 | 不補 |
| numpy | GCC runtime（libgfortran，靜態） | 涵蓋（GPL-3.0 WITH GCC-exception-3.1 全文在 wheel 內）；精確版本無法確認 | 不補 |

## 補了哪些原文

| 檔案（supplemental/） | 擁有者 | 上游來源（固定 commit） | sha256 | bytes | 授權 |
| --- | --- | --- | --- | --- | --- |
| `opencv-zlib.txt` | opencv-python 5.0.0.93 | `madler/zlib` tag `v1.3.2`（peel commit `da607da739fa6047df13e66a2af6b8bec7c2a498`）`LICENSE` | `e32ff4e00d9d94930537635291da39e7e612703334bf6fde8c7f1686fe8a45a2` | 1002 | Zlib |
| `opencv-libpng.txt` | opencv-python 5.0.0.93 | `pnggroup/libpng` tag `v1.6.57`（peel commit `95ab3fdca83ea294efd3b092e9a53c5a39886444`）`LICENSE` | `bdb0a645ea18c60507d0368379b1ac5474b92255fcc2d115e07486a7672ba526` | 5345 | PNG Reference Library License version 2 |

- 兩份原文都以 `git ls-remote --tags` 解析標籤、以 raw.githubusercontent.com 固定 commit 取得；與 opencv 固定 commit `40738fb1` 內 `3rdparty/zlib/LICENSE`、`3rdparty/libpng/LICENSE` 的 sha256 相同。
- `sources.json` 兩筆只留 `name/url/sha256/bytes`（與 pillow、pyclipper 既有記錄相同格式），版本與標籤資訊寫在本 manifest。

## 版本依據分級

| 元件 | 分級 | 依據 |
| --- | --- | --- |
| zlib 1.3.2 | Windows 執行期觀測 | hosted run 44755140396 的 `cv2.getBuildInformation()`，同一 cv2.pyd sha256 |
| libpng 1.6.57 | Windows 執行期觀測 | 同上 |
| zlib、libpng 編入 | 上游建置設定 + 二進位字串 + PE 匯入 | opencv 40738fb CMake 與 3rdparty；cv2.pyd 字串；匯入表無獨立 DLL |
| IPP 2026.0.0、ITT 3.25.4 | 建置宣告（字串） | cv2.pyd 內 getBuildInformation 字串，未執行期觀測 |
| onnxruntime 各成員 | 無法確認 | 上游不可達；僅名稱層級字串 |
| OpenBLAS 0.3.34 | wheel 二進位字串 | `libscipy_openblas64_…dll` 內字串 |

## 需要 hosted Windows 觀測的 API 清單（協調者安排）

本階段**未**在本機觸發 GitHub Actions，也未嘗試任何 Windows 執行。建議沿用 `scripts/cpu_native_observation.py` 的 `APIS` 與 `records` 模式（B3c 的 `cpu-evidence` job）擴充如下：

1. **opencv**：`cv2.getBuildInformation()` 已觀測（run 44755140396）。若要補 ITT 與 IPP 版本，需把 `Trace:` 與 `Intel IPP:` 兩行加入 `build_declarations` 的擷取（目前過濾只保留 12 行）。預期欄位：`Trace: YES (with Intel ITT(3.25.4))`、`Intel IPP: 2026.0.0 [2026.0.0]`、`Orbbec: YES`。
2. **opencv 的 Orbbec 靜態性**：`import cv2` 後以 psutil 列出進程載入模組，預期只有 `cv2.pyd`、`opencv_videoio_ffmpeg500_64.dll` 與系統 DLL，**沒有獨立的 OrbbecSDK DLL**。
3. **onnxruntime**：`onnxruntime.get_version_string()`、`onnxruntime.get_build_info()`（預期含 git commit 與建置字串）。無法得到逐成員版本，只能確認 build 身份。
4. **numpy**：`numpy.show_config(mode='dicts')` 的 `Build Dependencies` 區塊（預期 `blas` 名稱 `scipy-openblas`、`version: 0.3.34`），以及 `scipy_openblas64` 的版本函式（若存在）。預期欄位與 DLL 字串 `0.3.34` 對照。

## base 與 CPU 各自受影響的檔案

- **base**（numpy、onnxruntime 共用，但本次未改原文）：`packaging/embedded/base-windows.json`（`inventory.sha256`）、`packaging/redistribution/obligations.json`（10 處嵌入檔雜湊）。`packaging/profiles/base-closure.json` 重生後不變。
- **CPU**（opencv-python 只在 CPU）：`packaging/embedded/cpu-windows.json`（`inventory.sha256`）、`packaging/redistribution/obligations.json`（2 處）、`packaging/profiles/cpu-windows-closure.json`（opencv-python 列多 2 筆 supplemental）。

## 雜湊同步清單

| 檔案 | 舊 sha256 | 新 sha256 | 同步處 |
| --- | --- | --- | --- |
| `src/desktop_app/data/licenses/windows/inventory.json` | `c479b78b…` | `40cfea35…4f26cbc4f5e6` | `base-windows.json`、`cpu-windows.json` 的 `inventory.sha256` |
| `src/desktop_app/data/licenses/windows/supplemental/sources.json` | `f2eb3c4a…` | `8ecf9740…dddff0` | `inventory.json` files 表 |
| `packaging/embedded/base-windows.json` | `ed8e42ab…` | `f8c60552…fa41e8` | `obligations.json` 10 處 |
| `packaging/embedded/cpu-windows.json` | `7c92f1c4…` | `5572b8ad…e06273` | `obligations.json` 2 處 |
| `src/desktop_app/data/licenses/index.html` | 見 B3-2a | 重新渲染 | 無外部引用 |
| `packaging/profiles/cpu-windows-closure.json` | 內容改變 | 重生 | 無外部引用 |

`obligations.json` 的 diff 只有上述 12 行雜湊值，沒有改 `status`、`requires_user_decision`、`decision_source`、`accepted_gaps`、`required_evidence`。`cpu-windows.json` 的其他欄位（包括 zlib、OpenCV 列的 `version: null` 與 Linux 段落註記）沒有改，這是 B3-5／B3-9 的工作。`third-party.md`、`base-closure.json` 重生後沒有變動。

`inventory.json` 的 `files` 表順序與 `scripts/license_inventory.py` 生成順序不同（補件列寫在檔尾），因此位元組與生成結果不同；**語意上完全相同**（以 JSON 物件比較通過，見驗證）。

## 到 B3-9 必須重新核對的項目

1. 固定候選 `b17d51b` 的 source-review（a12、a13b）與現在的 inventory、supplemental 內容不同，B3-9 重新固定後要重產。
2. opencv zlib、libpng 的 Windows 版本依據來自 hosted run 44755140396；候選重新固定後，要重新觀測 `cv2.getBuildInformation()` 並確認 cv2.pyd sha256 未變。
3. ITT（ittnotify）的授權選擇（GPL-2.0、BSD-3 或兩者）需使用者決定後，補原文並同步雜湊。
4. Intel IPP 原文段落版本（2021 U10）與 build 宣告 2026.0.0 的涵蓋需確認。
5. onnxruntime 上游不可達；候選重固定時若取得 `microsoft/onnxruntime` 的 `cmake/deps.txt` 或等價清單，重做逐成員比對。
6. `packaging/redistribution/obligations.json` 的 `base-wheels-pillow` 與 `known-gaps.json` 仍列 raqm、libyuv 缺口（B3-2a 已記，本階段未改）。
7. `cpu-windows.json` 的 zlib 與 OpenCV 列仍為 version null 與 Linux 段註記；B3-5 或 B3-9 更新版本依據與註記。

## 使用者決定與未完成事項

- **ITT 雙授權（需使用者決定）**：cv2.pyd 靜態編入 Intel ITT，wheel 無原文，上游為 GPL-2.0-only OR BSD-3-Clause。依規則停下回報，未擅自選擇授權或補原文。
- **Orbbec 未確認**：需 Windows 觀測，未補。
- **onnxruntime 無法確認**：上游不可達，未補。

## 驗證

- 數字只寫在 [docs/progress.json](../../../progress.json)（full_regression）與下方 `manifest.json` 的 `regression` 欄位；兩者以最終執行為準。
- **完整重生比對**：以 `packaging/requirements-windows.txt` 鎖定的 58 個 wheel 重新執行 `scripts/license_inventory.py` 生成，語意上與修改後的 `inventory.json` 完全相同，`supplemental/sources.json` 與所有 notice 檔位元組相同（225 個 notice／metadata 檔）。在補件前的基線重生也與原 inventory 一致（僅 files 表順序不同）。
- `scripts/license_inventory.py --verify --render` 通過；`scripts/cpu_worker_profiles.py --generate`、`scripts/packaging_profiles.py --generate` 重生完成。
- 單元測試（`tests.test_bundle_provenance`、`tests.test_license_inventory`）：52 個測試通過；新增一個測試函式 `test_b3_2b_pins_match_the_recorded_evidence_manifest`，其餘為既有測試的新子案例（`test_b3_1_owner_and_source_mutations_are_rejected_even_after_rehashing` 新增 4 個子案例；`test_supplement_owner_binding_is_checked_when_owner_present` 新增 2 個子案例與固定表斷言）。
- **突變驗證**（每次只改一處守衛，執行兩個測試模組，然後以原位元組還原並核對 sha256）：

  | 突變 | 位置 | 結果 |
  | --- | --- | --- |
  | M1 移除 `opencv-zlib` 的固定擁有者綁定 | `license_inventory.py` | 初版未被偵測（測試漏洞），已補固定表斷言；補後失敗 1 項 |
  | M2 略過原文 SHA-256 檢查（只剩大小） | `prepare_worker_assets.py` | 失敗 34 項 |
  | M3 移除 inventory 唯一擁有者（claims）檢查 | `prepare_worker_assets.py` | 失敗 3 項 |
  | M4 移除 `opencv-libpng` 的 pin | `prepare_worker_assets.py` | 錯誤 42 項 |
  | M5 略過 sources.json 來源紀錄檢查 | `prepare_worker_assets.py` | 失敗 4 項 |

- 相關回歸與 gates 的數字見 `manifest.json` 的 `regression` 與 `gates` 欄位。

## 限制

- 只有 wheel 內位元組的字串計數、PE 匯入表與 zip 中繼資料，以及 B3c 已存在的 hosted Windows 觀測；**沒有在本機安裝或執行 Windows 元件**。`wheel-observation.json` 只作佐證，不是編入證明。
- zlib、libpng 的版本依據引用 B3c 的 hosted 觀測（run 44755140396，觀測程式與 cv2.pyd sha256 `f1e76ab0…` 已核對），不是本次新跑的觀測。
- 沒有做法律審核；本文件不是最終再散布核准。
- 本次不擴大授權與再散布範圍，沒有重新固定候選，沒有建立 Release、tag，也沒有觸發 `windows-build.yml`。
- 不改 STATUS.md、spec、鎖檔與既有證據檔。

# GEOS 授權與使用者替換

Windows CPU OCR worker 透過 Shapely 2.2.0 動態連結 GEOS 3.14.1。GEOS 使用 GNU LGPL 2.1，候選將 GEOS core 與 C API 保留為兩個獨立 DLL。CPU 元件內的原文位於 `_internal/worker-assets/installed/shapely/original/shapely-2.2.0.dist-info/licenses/LICENSE_GEOS`。[Shapely wheel 內的原文](windows/shapely/wheel/shapely-2.2.0.dist-info/licenses/LICENSE_GEOS)

The Windows CPU worker dynamically links GEOS 3.14.1 through Shapely. You can use a compatible build of both GEOS libraries through the user replacement directory described below.

## 放置或移除替換檔

1. 在使用者資料目錄（與本機 `settings.json` 同層，桌面版使用 Qt 的 `AppLocalDataLocation`）建立 `geos-replacement`。例如 `<settings.json 所在資料夾>\geos-replacement`。此目錄與受管 `component-state` 同層。
2. 放入支援的 Windows x64 GEOS 配對。目錄只接受下面兩個檔案的原樣檔名，兩個都必須是一般檔案。相對路徑、連結、junction、硬連結、其他檔名和不完整配對都會被拒絕。
3. 在支援此功能的主程式與 CPU worker 上重新執行健康檢查或 OCR。相容的配對會被標示「GEOS 使用者替換、未驗證」。健康結果、診斷與 Markdown 會記錄載入路徑與 SHA-256。
4. 要恢復受管版本，等目前工作結束後移除兩個替換檔。空目錄或缺少整個替換目錄時，下一次啟動使用受管版本。若檔案損壞、ABI 不相容或不符合目錄規則，當次請求會失敗並提示如何處理。受管 DLL 的逐檔驗證依原本規則執行。

| 元件 | 檔名 |
| --- | --- |
| GEOS core | `geos-bf067cd6ff74ee0ad5f3ff52c7ef08c9.dll` |
| GEOS C API | `geos_c-6dd9fd915eef8a7928285416bef1e666.dll` |

## 原始碼與相容建置

來源為 GEOS 3.14.1 的固定提交 `c389f532d25fe6228861d9b19339f9cb57ca4bdb`。使用 CMake 與 Visual Studio 2022 C++ x64 工具鏈，採 Release 與共用函式庫組態。[GEOS 固定原始碼](https://github.com/libgeos/geos/tree/c389f532d25fe6228861d9b19339f9cb57ca4bdb) · [GEOS 建置文件](https://github.com/libgeos/geos/blob/c389f532d25fe6228861d9b19339f9cb57ca4bdb/INSTALL.md) · [Shapely 固定 build 流程](https://github.com/shapely/shapely/blob/229c71f7128713b37201f3c77336d32b52467454/.github/workflows/release.yml)

以下示範在已取得固定提交的 GEOS 原始碼目錄內，讓 CMake 同時產出正確實體檔名與匯入函式庫名稱。

~~~powershell
@'
set_target_properties(geos PROPERTIES OUTPUT_NAME "geos-bf067cd6ff74ee0ad5f3ff52c7ef08c9")
set_target_properties(geos_c PROPERTIES OUTPUT_NAME "geos_c-6dd9fd915eef8a7928285416bef1e666")
'@ | Add-Content -LiteralPath CMakeLists.txt
cmake -S . -B out-geos -G "Visual Studio 17 2022" -A x64 -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=OFF -DBUILD_BENCHMARKS=OFF -DBUILD_DOCUMENTATION=OFF -DBUILD_GEOSOP=OFF
cmake --build out-geos --config Release --target geos_c --parallel 4
Get-ChildItem out-geos -Recurse -File -Filter 'geos*.dll'
~~~

Shapely 的 Windows wheel 對函式庫名稱做過 Delvewheel 改名。C API 的匯入名稱須對應到同組的改名 core，單純改磁碟檔名不能改寫相依名稱。替換版要保留 Windows x64、GEOS 3.14.1 及 C API ABI 1.20.5，符合 Shapely 所用的匯出。worker 會核對版本、載入路徑與基本幾何運算。SHA-256 用於記錄實際載入的檔案身分。

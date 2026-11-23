# GEOS 授權與使用者替換

Windows CPU OCR worker 透過 Shapely 2.2.0 動態連結 GEOS 3.14.1。GEOS 使用 GNU LGPL 2.1，候選將 GEOS core 與 C API 保留為兩個獨立 DLL。CPU 元件內的原文位於 `_internal/worker-assets/installed/shapely/original/shapely-2.2.0.dist-info/licenses/LICENSE_GEOS`。[Shapely wheel 內的原文](windows/shapely/wheel/shapely-2.2.0.dist-info/licenses/LICENSE_GEOS)

The Windows CPU worker dynamically links GEOS 3.14.1 through Shapely. To use a compatible build of both libraries, place them in the user replacement directory and explicitly enable the option.

## 啟用與停用

1. 在使用者資料目錄（與本機 `settings.json` 同層，桌面版使用 Qt 的 `AppLocalDataLocation`）建立 `geos-replacement`。例如 `<settings.json 所在資料夾>\geos-replacement`。此目錄與受管 `component-state` 同層。
2. 放入支援的 Windows x64 GEOS 配對。目錄只接受下面兩個檔案的原樣檔名，兩個都必須是一般檔案。相對路徑、連結、junction、硬連結、其他檔名和不完整配對都會被拒絕。
3. 到「選配元件管理」勾選「啟用 GEOS 使用者替換（進階，未驗證）」，閱讀警告後再執行健康檢查或受管 CPU OCR。成功時，健康結果、工作診斷與 Markdown 會標示「GEOS 使用者替換、未驗證」，並記下實際載入路徑與 SHA-256。
4. 取消勾選會立即儲存，下一次健康檢查或 OCR 使用受管版本，替換檔可留在原處。關閉時，若偵測到預期檔名，健康與工作診斷會提示「偵測到替換檔但未啟用」，仍照常執行。啟用時，空目錄、缺檔、損壞或不相容都會讓當次請求失敗，請補齊配對或停用後重試。

無介面時，將既有 `settings.json` 的 `geos_replacement_enabled` 設為 JSON 布林值 `true` 啟用，設為 `false` 停用。欄位缺少或型別錯誤時視為關閉。開發用命令列可以在既有 `--settings` 與受管 CPU OCR 選項之外，加上 `--geos-replacement` 或 `--no-geos-replacement`，只覆蓋當次執行的設定。

| 元件 | 檔名 |
| --- | --- |
| GEOS core | `geos-bf067cd6ff74ee0ad5f3ff52c7ef08c9.dll` |
| GEOS C API | `geos_c-6dd9fd915eef8a7928285416bef1e666.dll` |

## 使用替換檔前

替換的 DLL 會以目前使用者身分在 worker 程序中執行，只放你信任的檔案。程式在載入前檢查路徑、預期檔名及是否為一般檔案，但沒有雜湊白名單、簽章或 PE 檢查。Windows 在載入時就會執行 DLL 的 `DllMain`。確認實際載入模組的名稱、路徑和 ABI，以及試算幾何運算，都是載入後才做。程式不保證相容性或辨識品質，替換結果一律標示「GEOS 使用者替換、未驗證」。

開關預設關閉，可避免目錄裡意外出現的檔案被執行。能寫入你的使用者資料目錄與設定檔的惡意程式，也能放入 DLL 並改開關。這是明確同意的步驟，無法提供安全隔離。

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

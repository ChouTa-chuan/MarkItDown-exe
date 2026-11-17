# Qt／LGPL-3.0 說明

本說明隨基本安裝包附上，說明本程式如何使用 Qt。以下路徑以 Windows 安裝包為準。它不是法律意見，也不表示發佈審核已完成；其他尚未關閉的門檻見 third-party.md。

## 使用的元件與授權選擇

- PySide6-Essentials 6.12.0
- shiboken6 6.12.0
- 以上兩個套件內含的 Qt 6 程式庫（例如 Qt6Core.dll）與外掛

這兩個套件宣告的授權是「LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only」，wheel 內只附商業授權提示（LicenseRef-Qt-Commercial.txt）。本程式選擇依 **GNU LGPL 3.0** 使用 Qt。

English: This program uses Qt 6 (through PySide6-Essentials and shiboken6, both 6.12.0) under the terms of the GNU Lesser General Public License, version 3 (LGPL-3.0). Qt is dynamically linked; the Qt libraries are shipped as separate files that you can replace.

## 授權原文在安裝後的位置

以下路徑相對於安裝資料夾（內含 `_internal` 子資料夾的那一層）：

| 內容 | 路徑 |
| --- | --- |
| LGPL-3.0 原文 | `_internal\desktop_app\data\licenses\supplemental\qt-lgpl3.txt` |
| GPL-3.0 原文（LGPL-3.0 引用） | `_internal\desktop_app\data\licenses\supplemental\qt-gpl3.txt` |
| PySide6-Essentials wheel 內的 Qt 商業授權提示 | `_internal\desktop_app\data\licenses\installed\pyside6-essentials\original\pyside6_essentials-6.12.0.dist-info\licenses\LicenseRef-Qt-Commercial.txt` |
| shiboken6 wheel 內的 Qt 商業授權提示 | `_internal\desktop_app\data\licenses\installed\shiboken6\original\shiboken6-6.12.0.dist-info\licenses\LicenseRef-Qt-Commercial.txt` |
| 各套件的 METADATA | `_internal\desktop_app\data\licenses\installed\pyside6-essentials\METADATA`、`_internal\desktop_app\data\licenses\installed\shiboken6\METADATA` |
| 固定來源提交與本次建置 Qt 版本 | `_internal\desktop_app\data\licenses\qt-sources.json` |
| Qt 固定來源第三方宣告與原始授權（來源上位集合） | `_internal\desktop_app\data\licenses\qt-thirdparty\catalog.json` 與其中 `raw/` 路徑 |
| 完整第三方清單 | `_internal\desktop_app\data\third-party.md`（程式內「說明／第三方授權」可開啟） |

LGPL-3.0 與 GPL-3.0 原文取自 PySide 原始碼庫固定提交 `f50facb83fc3dc5f3240c854668c7a6dd93871b2` 的 `LICENSES/` 目錄：

- https://raw.githubusercontent.com/pyside/pyside-setup/f50facb83fc3dc5f3240c854668c7a6dd93871b2/LICENSES/LGPL-3.0-only.txt
- https://raw.githubusercontent.com/pyside/pyside-setup/f50facb83fc3dc5f3240c854668c7a6dd93871b2/LICENSES/GPL-3.0-only.txt

該提交原先只記錄授權原文來源；本輪另外查證它也是 PySide／shiboken 官方 `v6.12.0` tag 的提交。Qt 本體使用另一個來源庫，兩者分開列於下方，不能把 PySide 提交當作 Qt 本體提交。

## 對應原始碼的取得方式

目前來源對應版為 **Qt 6.12.0／PySide6-Essentials 6.12.0／shiboken6 6.12.0**。版本不是只按套件名稱推算：既有 hash 鎖定 Windows wheel 的 Qt DLL PE 版本經靜態檢查，建置時另用 `QtCore.qVersion()` 讀真正載入的 Qt 版本，並核對套件版本。每次基本包的觀測平台、Qt build 字串、Core extension 指紋與固定來源表記在上表的 `qt-sources.json`；觀測另含 `QLibraryInfo.version()`、`isSharedBuild()`、`isDebugBuild()`；build 字串不是完整編譯選項／CMake cache。建置解譯器觀測不等於 frozen 候選獨立執行驗證。

| 來源 | 官方發布 tag 與固定提交 | 取得來源 |
| --- | --- | --- |
| Qt 完整模組組合（supermodule） | `v6.12.0` → `ef25002ed292b132d1ed3246bfcee1d24a9cd966` | https://github.com/qt/qt5/tree/ef25002ed292b132d1ed3246bfcee1d24a9cd966 |
| Qt 本體 qtbase（Core／Gui／Widgets／Network 等） | `v6.12.0` → `025bdad181de241e81bf853c8a2d7bf3d19261a9`，也與上述 supermodule 的 qtbase gitlink 相同 | https://codeload.github.com/qt/qtbase/tar.gz/025bdad181de241e81bf853c8a2d7bf3d19261a9 |
| SVG 程式庫 qtsvg | 上述 supermodule 的 `883a58532078d003cefef0a549bfe9f885ce41f5` | https://codeload.github.com/qt/qtsvg/tar.gz/883a58532078d003cefef0a549bfe9f885ce41f5 |
| QML／Quick qtdeclarative | 上述 supermodule 的 `4332fbbb4c340463dc8cee36dda0c85d932122d8` | https://codeload.github.com/qt/qtdeclarative/tar.gz/4332fbbb4c340463dc8cee36dda0c85d932122d8 |
| Designer／UiTools／Help 等 qttools | 上述 supermodule 的 `613a6fbf0a7998010ab2fda260b64066d66a021d` | https://codeload.github.com/qt/qttools/tar.gz/613a6fbf0a7998010ab2fda260b64066d66a021d |
| PySide／shiboken 綁定與建置程式 | `v6.12.0` → `f50facb83fc3dc5f3240c854668c7a6dd93871b2` | https://codeload.github.com/pyside/pyside-setup/tar.gz/f50facb83fc3dc5f3240c854668c7a6dd93871b2 |

`qt-sources.json` 保存該官方 Qt 發布版完整的模組 gitlink、各模組固定提交及其來源下載連結；這是來源上位集合，不表示每個模組都被本應用程式打包或使用。各模組的原始授權、內含第三方來源與建置說明仍須依其原始碼處理。

也可以用 Git 取得同一組固定來源：

```text
git clone https://github.com/qt/qt5.git qt-6.12.0
cd qt-6.12.0
git checkout ef25002ed292b132d1ed3246bfcee1d24a9cd966
git submodule update --init --recursive
```

單獨下載 supermodule 的 ZIP／tarball 不會包含各 submodule 原始碼；請完成上面的 submodule 步驟，或依 `qt-sources.json` 逐一取得固定模組來源並保留目錄結構。PySide／shiboken 請另外取得表列的來源。套件 METADATA 指向的官方 Qt for Python 原始碼入口仍是 https://code.qt.io/cgit/pyside/pyside-setup.git/ ，本表使用官方 GitHub 鏡像的固定提交供下載與離線追溯。

此表確認官方發布來源位置與版本對應，**未宣稱二進位可逐位元組重建、已核實 wheel 所用完整建置修補與參數，或 LGPL／再散布義務已全部落實**。例如 qtbase 原始 `.cmake.conf` 另含 prerelease 預設欄位，保存原文不代表那就是官方 wheel 使用的完整 build 設定。固定候選仍是 A6，A12 尚未重新固定。建置修補／設定、第三方實際編入狀態與最終再散布仍待審閱。

## Qt 內含第三方的來源宣告

`qt-thirdparty/catalog.json` 列出固定 Qt 6.12.0 的 qtbase、qtsvg、qtimageformats 與 PySide 來源的宣告上位集合，排除 `tests/`、`examples/`、`cmake/`、`util/`、`src/testlib/`、`src/testinternal/` 目錄；也保留來源中屬其他平台的宣告，不聲稱它們都進入 Windows wheel。qtsvg 在該提交沒有 `qt_attribution.json`。其中名稱、版本、QtUsage、授權宣告與原始授權各可追溯到 `raw/` 的固定提交原文及 hash。

版本依據 `source-declared` 只指來源的 Version 欄位；未提供版本時記 `unknown`。這不是 wheel-declared，也不代表確認靜態編入。`compiled_into_windows_wheel` 保持 unverified，因為 `QLibraryInfo.build()` 不能證明完整編譯選項、system／bundled 選擇或上游修補；`opengl32sw.dll` 的 Mesa 精確版本及來源對應也仍未知。來源與原文取得不代表完整第三方閉包或 LGPL 做法已獲核准；是否足夠留待 A13 使用者決定。

## 如何替換 Qt 程式庫

Qt 以獨立檔案隨包提供，沒有靜態連結進本程式的執行檔。Qt 6 的 DLL（例如 `Qt6Core.dll`）位於安裝資料夾的 `_internal\PySide6\` 之下，外掛在其子資料夾。你可以：

1. 先關閉本程式，並備份原有的 `_internal\PySide6\` 資料夾。
2. 取得與 PySide6／shiboken6 6.12.0 二進位相容的 Qt 6 程式庫（自行建置或取自相容版本），以同名檔案取代。
3. 重新啟動本程式。

本專案的 A11 CI 使用不同 SHA-256 的 Qt6Core.dll，在可拋棄的基本包副本驗原版啟動、替換後啟動、移除 Core 的 loader 失敗，以及還原後啟動；同時讀取子程序實際載入路徑與 hash，避免誤用宿主 Qt。替換輸入為 PyPI PyQt6-Qt6 6.12.0 的 Core DLL，僅供測試，不隨產品提供；固定 URL、wheel 與 DLL hash 見專案 `packaging/qt/6.12.0/replacement-input.json`。實際 run 與結果以專案 A11 證據紀錄及 PR 為準。

這項測試只針對該組 DLL 在 hosted Windows runner 的相容性，不是實體機、乾淨機驗收，不保證任意使用者替換皆能成功，也不代替 A13 的 LGPL 做法決定。

## 其餘部分

本程式自有的部分採 MIT 授權，全文隨包保存在 `_internal\desktop_app\data\licenses\markitdown-desktop\LICENSE`。第三方元件完整清單見 third-party.md。

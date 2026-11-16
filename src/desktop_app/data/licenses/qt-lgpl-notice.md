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
| 完整第三方清單 | `_internal\desktop_app\data\third-party.md`（程式內「說明／第三方授權」可開啟） |

LGPL-3.0 與 GPL-3.0 原文取自 PySide 原始碼庫固定提交 `f50facb83fc3dc5f3240c854668c7a6dd93871b2` 的 `LICENSES/` 目錄：

- https://raw.githubusercontent.com/pyside/pyside-setup/f50facb83fc3dc5f3240c854668c7a6dd93871b2/LICENSES/LGPL-3.0-only.txt
- https://raw.githubusercontent.com/pyside/pyside-setup/f50facb83fc3dc5f3240c854668c7a6dd93871b2/LICENSES/GPL-3.0-only.txt

該提交只用於取得授權原文，不表示它是本包 Qt 的對應原始碼版本。

## 對應原始碼的取得方式

- PySide6／shiboken6 原始碼庫（依套件 METADATA 的 Repository 欄位）：https://code.qt.io/cgit/pyside/pyside-setup.git/
- PySide6 專案首頁（METADATA 的 Homepage 欄位）：https://pyside.org
- Qt 6 本身（qtbase 等模組）的對應原始碼位置與版本：**待補**。目前專案內沒有可作為依據的記錄，發佈前必須補上並確認與 6.12.0 相符；在此之前不宣稱已提供 Qt 本身的對應原始碼。

## 如何替換 Qt 程式庫

Qt 以獨立檔案隨包提供，沒有靜態連結進本程式的執行檔。Qt 6 的 DLL（例如 `Qt6Core.dll`）位於安裝資料夾的 `_internal\PySide6\` 之下，外掛在其子資料夾。你可以：

1. 先關閉本程式，並備份原有的 `_internal\PySide6\` 資料夾。
2. 取得與 PySide6／shiboken6 6.12.0 二進位相容的 Qt 6 程式庫（自行建置或取自相容版本），以同名檔案取代。
3. 重新啟動本程式。

替換後的相容性與運作由使用者自行負責；本專案不保證替換後的程式庫可以正常運作。

## 其餘部分

本程式自有的部分採 MIT 授權，全文隨包保存在 `_internal\desktop_app\data\licenses\markitdown-desktop\LICENSE`。第三方元件完整清單見 third-party.md。

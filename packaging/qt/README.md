# Qt 發布來源對應

`6.12.0/catalog.json` 固定官方 Qt supermodule、qtbase 及 PySide／shiboken 的 tag 解參照結果，列出完整模組 gitlink、Windows hash 鎖定 wheel 與原始來源檔 hash。`official-refs.json` 保留查詢所得的 tag／commit／Git tree 資料；`sources/` 保留原位元組，版本宣告與模板不混用。Qt for Python 真正版本來自其 `.cmake.conf`，`pyside_version.py`／`shiboken_version.py` 是生成模板。

`scripts/qt_sources.py` 在基本包準備資產時離線驗證這些資料，再實際呼叫 `QtCore.qVersion()` 與讀取已安裝的 PySide／shiboken 版本。不符就拒絕套用來源表。`licenses/qt-sources.json` 隨包保存模組來源 URL、固定提交、觀測平台、Qt build 字串及 Core extension 指紋；既有 build-profile 資產 manifest 覆蓋其 SHA-256。GitHub CI 另發 `Qt release sources` 公開摘要，Linux 觀測不能當 Windows 結果。

安裝後的中文取得方法見 [Qt／LGPL 說明](../../src/desktop_app/data/licenses/qt-lgpl-notice.md)。Qt supermodule 的一般 tarball 不含 submodule；須依固定 gitlink 取得各模組，PySide／shiboken 另取其來源。這是官方發布來源上位集合，不宣稱每個模組都被打包。

版本對應不證明二進位可逐位元組重建、官方 wheel 的完整建置修補與參數已核實，或 LGPL／再散布已全面完成。原始 qtbase `.cmake.conf` 的 prerelease 預設欄位也保持原樣，不能當實際 wheel build 設定。固定候選、其餘原生來源／授權、替換能力及最終審閱仍由 A6 等後續處理；所有產品門檻保持 false。

更新 Qt 版本時，先取得新的官方固定 tag／commit 與模組 gitlink，再保存真正版本宣告、核對鎖定 Windows wheel，更新明確支援版本及隨包說明。不得只重標 catalog。針對來源變異、實際載入版本不符與隨包 hash 跑測試，完成完整回歸及 Windows CI 後才採用；不修改現有原始授權全文。

A11 的 `6.12.0/thirdparty/catalog.json` 另列 qtbase／qtsvg／qtimageformats／PySide 的第三方來源宣告、原始授權、固定 URL／Git blob／SHA-256 及 A6 Qt 原生檔對應。`source-declared` 是固定發布來源的版本欄位，不是 wheel 宣告或實際編入的證明；無版本就記 `unknown`。每列 `compiled_into_windows_wheel: unverified` 保留 system／bundled 選項及其他平台宣告的界線。`opengl32sw.dll` 的 Mesa 精確版本與來源仍未知，完整編譯選項與上游修補也未取得。

`scripts/qt_components.py` 把這些原文放進基本包 `licenses/qt-thirdparty/` 並驗證；登記表只引用目錄的路徑與 SHA。QLibraryInfo 實際觀測另含 build 字串、library version、shared／debug 狀態，不代表完整 CMake cache。

`replacement-input.json` 只供 hosted Windows CI：PyPI 的 PyQt6-Qt6 6.12.0 wheel 與 Core DLL 各釘 SHA，從中只抽出不同 bytes 的 Qt6Core.dll 到可拋棄副本，不安裝 PyQt、不改產品依賴或鎖檔。`check_qt_replacement.py` 使用真正 frozen GUI，核對子程序實際載入路徑／hash，依序驗原版、替換、移除失敗與還原成功。wheel／DLL／副本均在報告 artifact 之外；只保存小型 JSON、日誌與本程式視窗截圖。這是 hosted runner，非實體機、乾淨機或再散布接受。

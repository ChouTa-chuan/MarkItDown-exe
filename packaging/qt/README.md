# Qt 發布來源對應

`6.12.0/catalog.json` 固定官方 Qt supermodule、qtbase 及 PySide／shiboken 的 tag 解參照結果，列出完整模組 gitlink、Windows hash 鎖定 wheel 與原始來源檔 hash。`official-refs.json` 保留查詢所得的 tag／commit／Git tree 資料；`sources/` 保留原位元組，版本宣告與模板不混用。Qt for Python 真正版本來自其 `.cmake.conf`，`pyside_version.py`／`shiboken_version.py` 是生成模板。

`scripts/qt_sources.py` 在基本包準備資產時離線驗證這些資料，再實際呼叫 `QtCore.qVersion()` 與讀取已安裝的 PySide／shiboken 版本。不符就拒絕套用來源表。`licenses/qt-sources.json` 隨包保存模組來源 URL、固定提交、觀測平台、Qt build 字串及 Core extension 指紋；既有 build-profile 資產 manifest 覆蓋其 SHA-256。GitHub CI 另發 `Qt release sources` 公開摘要，Linux 觀測不能當 Windows 結果。

安裝後的中文取得方法見 [Qt／LGPL 說明](../../src/desktop_app/data/licenses/qt-lgpl-notice.md)。Qt supermodule 的一般 tarball 不含 submodule；須依固定 gitlink 取得各模組，PySide／shiboken 另取其來源。這是官方發布來源上位集合，不宣稱每個模組都被打包。

版本對應不證明二進位可逐位元組重建、官方 wheel 的完整建置修補與參數已核實，或 LGPL／再散布已全面完成。原始 qtbase `.cmake.conf` 的 prerelease 預設欄位也保持原樣，不能當實際 wheel build 設定。固定候選、其餘原生來源／授權、替換能力及最終審閱仍由 A6 等後續處理；所有產品門檻保持 false。

更新 Qt 版本時，先取得新的官方固定 tag／commit 與模組 gitlink，再保存真正版本宣告、核對鎖定 Windows wheel，更新明確支援版本及隨包說明。不得只重標 catalog。針對來源變異、實際載入版本不符與隨包 hash 跑測試，完成完整回歸及 Windows CI 後才採用；不修改現有原始授權全文。

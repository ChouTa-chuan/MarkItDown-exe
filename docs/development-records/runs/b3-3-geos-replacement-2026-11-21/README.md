# B3-3：GEOS 使用者替換路徑

Windows CPU worker 只從和 `settings.json` 同層的固定 `geos-replacement` 目錄取得一組相容的 GEOS DLL。受管 `component-state` 仍走原先的租約、`_ready()` 與 `verify_tree()`。替換版本保留未驗證標記，健康結果、診斷與輸出的 Markdown 記載程序載入路徑及 SHA-256。[使用方式與 LGPL 說明](../../../../src/desktop_app/data/licenses/geos-lgpl-notice.md)

## Windows 可行性實驗

先在 hosted Windows 2022 的相同鎖定 Shapely 環境分別執行原版及替換版。替換版從固定 GEOS 3.14.1 原始碼提交 `c389f532` 以 Visual Studio 2022 x64 編譯，CMake 同時產生 wheel 的兩個 DLL basename 和相配的相依名稱。兩份 DLL 的 SHA-256 都和原版不同。Windows 程序模組清單只出現各一份，並確認兩份都從當次指定的路徑載入。Shapely 兩個矩形的交集面積均為 4，GEOS C API 為 1.20.5。[可行性結果](feasibility.json) · [run 44885924955](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44885924955)

## 測試證據

- 在 Linux 逐次突變路徑邊界、連結拒絕和協定證據檢查，三項的對應測試都確實失敗。各次突變僅替換記憶體中的函式，工作區與正式程式碼沒有改動。[突變結果](mutations.json)
- 完整混合與獨立模組回歸的數字以[進度資料](../../../progress.json)為準。固定候選的兩組 gates 依照原登記判定。

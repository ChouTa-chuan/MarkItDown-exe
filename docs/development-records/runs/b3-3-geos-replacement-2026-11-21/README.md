# B3-3：GEOS 使用者替換路徑

Windows CPU worker 只從和 `settings.json` 同層的固定 `geos-replacement` 目錄取得一組相容的 GEOS DLL。受管 `component-state` 仍走原先的租約、`_ready()` 與 `verify_tree()`。替換版本保留未驗證標記，健康結果、診斷與輸出的 Markdown 記載程序載入路徑及 SHA-256。[使用方式與 LGPL 說明](../../../../src/desktop_app/data/licenses/geos-lgpl-notice.md)

## Windows 可行性實驗

先在 hosted Windows 2022 的相同鎖定 Shapely 環境分別執行原版及替換版。替換版從固定 GEOS 3.14.1 原始碼提交 `c389f532` 以 Visual Studio 2022 x64 編譯，CMake 同時產生 wheel 的兩個 DLL basename 和相配的相依名稱。兩份 DLL 的 SHA-256 都和原版不同。Windows 程序模組清單只出現各一份，並確認兩份都從當次指定的路徑載入。Shapely 兩個矩形的交集面積均為 4，GEOS C API 為 1.20.5。[可行性結果](feasibility.json) · [run 44885924955](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44885924955)

## Windows 凍結 worker 驗收

用同一 spec 及依賴鎖在 hosted Windows 2022 建置凍結 worker，並以一次性測試簽章從空 PATH 的精簡控制端安裝與操作。在同一個受管版本測得下列結果。[凍結實測與載入指紋](frozen-worker.json) · [run 44887741340](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44887741340)

| 情境 | 驗收結果 |
| --- | --- |
| 正常受管 | 原本的幾何實驗、管理健康檢查、CPU provider 與固定英文 OCR 皆通過。 |
| 覆蓋受管 DLL | 受管租約拒絕 SHA 不符的 DLL。原樣還原後兩個 DLL 指紋相同，受管改檔期間文字轉 Markdown 仍通過。 |
| 使用者替換 | 兩個自建 DLL 的 SHA-256 均異於受管檔，實際程序模組位置在獨立替換目錄。Shapely 交集、frozen 健康與 OCR 通過，輸出與健康結果均有絕對路徑、雜湊與未驗證標記。 |
| 損壞與復原 | 將 C API 替換檔寫為無效 bytes，正式健康回呼及受管租約拒絕，未建立輸出。移除整組替換檔後辨識成功並恢復原版。 |

專項驗收先於 PR 57 原文補件合併，GEOS 載入程式於併入後相同。合併後以完整回歸與一般 Windows CI 重新驗證。驗收使用 hosted runner。實體 Windows 與乾淨機留在原規劃。一次性驗證 job 已還原。用 annotations 保存精簡結果，沒有上傳 Setup、worker、模型或另外建立 artifact。試跑 44886880410 因重啟正在調整的驗收方式而取消。試跑 44887094890 的診斷包裝器將預期的健康失敗轉成通用 RuntimeError，改由正式健康回呼後完成驗收。

## 測試證據

- 分別移除受管邊界判定、將檔案檢查改成跟隨連結，以及略過協定證據驗證，三項的對應測試都確實失敗。各次突變僅替換記憶體中的函式，工作區與正式程式碼沒有改動。[突變結果](mutations.json)
- 完整混合與獨立模組回歸的數字以[進度資料](../../../progress.json)為準。固定候選的兩組 gates 均 exit 0，flags 與原登記結果一致。CPU 的四項均為 false。

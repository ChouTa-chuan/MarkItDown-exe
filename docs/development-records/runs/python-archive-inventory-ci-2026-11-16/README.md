# Python 模組來源清單的首次 Windows CI 輸出

2026-11-16（台北）。[PR 5](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/5) head `c49c72922de07f5d3935783d7a326f7c0926288d`（程式 0.19.1／架構 0.4）。PR 流程以暫時合併提交 `9c5110a8c18e86f07b98ea84bc130651119328b7` 執行；這不是新的候選證據。資料取自 job 公開摘要，沒有下載 artifact。

| 流程 | run | 結果 |
| --- | --- | --- |
| Windows base validation | [43792126130](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43792126130) | Success；應用 10、安裝 6、跨版 11、續修 3 案全部接受 |
| Windows CPU component validation | [43792126123](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43792126123) | Success；功能 11、同版 8、跨版 8、恢復 6 全部接受 |
| Linux full regression | [43792126120](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43792126120) | Success |

## `python_archives` 摘要

| 項目 | 基本包 | CPU 元件 |
| --- | ---: | ---: |
| 純 Python 模組 | 1,715 | 562 |
| 標準庫 | 277 | 243 |
| 可對應到具體套件 | 1,384 | 307 |
| 自有程式 | 49 | 12 |
| 無法歸屬 | 5 | 0 |
| `base_library.zip` 成員 | 155 | 155 |

基本包無法歸屬的 5 個全部屬於 setuptools 隨附的子套件：`setuptools._distutils.compilers`、`.compilers.C`、`.compilers.platform`、`setuptools._vendor`、`setuptools._vendor.jaraco`。前述 namespace package 的修正已讓它們以明確原因標示，而不是讀檔錯誤；它們沒有對應的 RECORD 項目，因此歸為不明。是否需要隨包、授權歸屬（setuptools 為 MIT）待後續確認。

`excluded_binaries_absent` 仍為 true，簽章查詢沒有錯誤。

## 其他計數變化

與 PR 4 最後一次執行相比，基本包普通檔案 1,608→1,609、來源未對照 107→108、需審閱 145→146；CPU 元件 697→698、259→260、293→294。各多出的 1 個檔案是新加入的 `python-modules.json`：候選清單把它列為來源未對照，來源分類工具則會把它歸為「專案建置腳本產生」。`base_library.zip` 不再帶 `archive-members-not-enumerated`，但仍因「來源擁有者未對照」留在待審閱清單中。

## 限制

- 公開摘要在 job 記錄中完整出現，沒有截斷；GitHub 的 annotation 顯示是否截斷沒有另外檢查。
- 三個旗標維持 false；不是乾淨機或人工驗收；沒有 GPU。7/12、C04 2/4、C11 2/5 不變。沒有發布產物。

[返回歷史索引](../../../history-index.md)

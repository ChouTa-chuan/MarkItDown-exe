# 公開合成範例與歷史輸出

以下檔案為先前生成的示例，未在本次重新轉換。原始 PDF 與 Markdown 按位元組保存，供對照開發過程，不是一般文件準確率證明。

| 案例 | 原始來源 | 當時輸出／畫面 |
| --- | --- | --- |
| 對齊無框線表格與有框線同頁 | [生成 PDF](borderless-table-example.pdf) | [Markdown](borderless-table-example.md) |
| 跨頁候選續表 | [生成 PDF](continued-table-example.pdf) | [Markdown](continued-table-example.md)，保留兩頁表頭及原資料 |
| 合併儲存格 | [生成 PDF](merged-table-example.pdf) | [Markdown](merged-table-example.md)／[原頁畫面](../screenshots/merged-table-example.png) |
| 上游公開稀疏表格 | [固定提交測試 PDF](../../../tests/fixtures/upstream-sparse.pdf)／[來源資訊](../../../tests/fixtures/UPSTREAM.json) | [修正前輸出](upstream-borderless-result.md)／[修正後輸出](sparse-fixed.md) |

修正前稀疏表輸出保留當時結構不足，**不得列為表格結構通過**。修正後的逐格驗收另見 [版面矩陣](../../layout-acceptance.md)；以上只保存已存在的歷史產物。

合成 PDF 與範例源於專案測試；上游公開 PDF 來源與原授權維持既有 manifest，不包含使用者真實文件。

[返回開發紀錄](../README.md)

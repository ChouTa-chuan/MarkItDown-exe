# 里程碑 3：版面與表格驗收

本輪完成既有「複雜版面、跨頁／無框線表格驗收」的 Linux 代表性案例檢核，沒有刪減或新增進度分母。此階段驗收以內容、閱讀順序、欄列結構與歧義提示為目標；不是任意文件準確率、Windows 或正式發佈驗收。

## 驗收條件與證據

| 範圍 | 必須通過的斷言 | 證據 |
| --- | --- | --- |
| 雙欄及跨欄標題 | 各區先左後右；跨欄標題、區間標題及頁尾維持順序，各出現一次 | test_pdf_pipeline：純雙欄、兩個正文區塊與跨欄標題；frozen 標題／雙欄實測 |
| 合併與一般表格 | rowspan／colspan 有幾何依據；正文、空缺區註記及各儲存格不重複；HTML 跳脫 | test_tables、test_pdf_pipeline；frozen 合併表 |
| 對齊無框線表 | 兩／三欄及右對齊數字；有框線和無框線同頁均保留 | test_borderless；frozen 數值表 |
| 缺格及錯落列 | 六欄表頭；八列資料逐格正確，空格不補值；第二頁十列逐格正確 | 上游 sparse PDF；test_borderless、test_pdf_acceptance；frozen 公開樣本 |
| 跨頁表格 | 有框線、無框線及稀疏續表都保留各頁結構、重複表頭和資料；相符時提供來源關聯提示 | test_table_continuation；frozen 有框線及稀疏無框線續表 |
| 防誤判 | 新章節、空白頁、改表頭／欄位、多表、數值首列、雙欄文章及純文字稀疏列不誤接／強制表格化 | 各組正反例；公開維修單和收據反例 |
| 有界工作與取消 | 詞數、候選詞比對、版面分區、網格上限；取消清理及 OCR 最多兩次 | test_borderless、test_tables、test_pdf_pipeline |
| 內容與閱讀順序 | 四份固定提交公開樣本：字元守恆另加金額、頁面、正文順序及欄列斷言 | test_pdf_acceptance；來源及打包程式使用相同判準 |

來源驗收矩陣 **63/63 通過，零跳過、零預期失敗**：[逐項結果](layout-acceptance-results.json)。全專案 **148 項中 147 通過，1 項 ONNX 繁體品質預期失敗**；後者屬實驗性 OCR 模型缺口，沒有列為通過。

## 公開樣本

全部取自 Microsoft MarkItDown 固定提交 `7482c092d9c0074a89803c9fdb63a969e7fe17fc`。來源、MIT 授權位置及 SHA-256 記錄於 tests/fixtures/UPSTREAM.json 與 PUBLIC-PDFS.json，verify_upstream.py 可重驗。

| 原始樣本 | 頁數 | 正規化英數字元 | 額外判準 |
| --- | --- | --- | --- |
| SPARSE-2024-INV-1234_borderless_table.pdf | 2 | 1,397 | 兩表全部 18 列與空格逐格一致；章節順序；不同表不誤接 |
| REPAIR-2022-INV-001_multipage.pdf | 3 | 2,188 | 兩位姓名與各頁總額不混用；聲明保留；信頭合併格；無錯誤續表 |
| RECEIPT-2024-TXN-98765_retail_purchase.pdf | 1 | 905 | 商品、折扣負號、稅額、付款及退貨說明順序；總額一次 |
| test.pdf | 1 | 4,254 | 文章及兩個列點順序；不誤判表格 |

字元守恆以 PDF 原生字元與去除程式註記／提醒後的 Markdown 比較，解碼 HTML、NFKC 正規化並計算英數字元出現次數。**不計空白與標點，因此不能單獨證明排版、數字格式或結構正確**；表格與金額另有嚴格字串／儲存格判準。這些是上游公開測試文件，不是使用者真實文件。

視覺抽查稀疏報表第一頁及維修估價單第一頁，確認表格位置、空格和主要區塊；未宣稱四份所有頁面皆經人工逐頁複核。

## 重跑

先依鎖定依賴安裝專案及本機 Tesseract、eng／chi_tra 模型，並提供測試字型。以乾淨 venv 執行：

```bash
TESSDATA_PREFIX=/path/to/tessdata QT_QPA_PLATFORM=offscreen python scripts/check_layout_acceptance.py --report docs/layout-acceptance-results.json
TESSDATA_PREFIX=/path/to/tessdata QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
python scripts/verify_upstream.py
```

建置完成後才驗證打包產物：

```bash
python -m PyInstaller --noconfirm packaging/desktop.spec
python scripts/check_layout_acceptance.py --executable dist/MarkItDownDesktop/MarkItDownDesktop --report docs/layout-frozen-results.json
TESSDATA_PREFIX=/path/to/tessdata QT_QPA_PLATFORM=offscreen python scripts/smoke_frozen.py --crosscheck dist/MarkItDownDesktop/MarkItDownDesktop
```

打包公開樣本結果見 [frozen 結果](layout-frozen-results.json)；其他打包檢查摘要見 [驗證記錄](validation-results.json)。來源矩陣要求所有測試實際執行且通過，任何跳過或預期失敗都不算此矩陣完成。

## 保留的限制

- 跨頁處理是保留各頁表格與「可能續表」關聯，不輸出自動合併的長表、不刪重複表頭，也不自動補值。缺表頭、跨頁合併格及掃描續表尚未支援。
- 任意多欄中混排表格、旋轉、複雜換行、全為文字且無明確表頭的表格尚未完整辨識；不確定時保留原生文字，並不把這種回退計為結構驗收通過。
- 圖表視覺、標誌、公式及所有影像資產未完整重建。維修單部分不明幾何區域仍以原生文字保留並明示警告；該樣本僅驗證信頭合併格及內容／順序，沒有列為完整明細表結構通過。
- 固定樣本驗收不代表一般文件準確率。實際繁中／低品質文件資料集、Windows、GPU、負載及安裝包驗收仍待完成。

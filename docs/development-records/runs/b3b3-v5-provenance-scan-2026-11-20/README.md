# B3b3 PP-OCRv5 來源授權查證與模擬掃描複驗

日期：2026-11-20（台北）。本輪只新增證據，不改程式、打包、登記表、STATUS 或測試。

## 做了什麼

1. **v5 ONNX 來源與授權查證**（[v5-provenance.json](v5-provenance.json)）：B3b 實測的 `ch_PP-OCRv5_rec_mobile.onnx`（SHA-256 `5825fc7e…`，16,631,306 bytes）用多個來源核對雜湊，並以唯讀方式檢視 ONNX 檔頭與 metadata。查到 PaddleOCR 官方文件列有官方 PP-OCRv5 mobile ONNX（HF 與 BOS），但這兩個主機被擋，無法取得檔案比對。授權依證據分級，見下節。
2. **模擬掃描複驗**：以 B3b2 的 9 張固定合成圖為輸入，用固定參數與固定種子做 12 種劣化（旋轉、模糊、雜訊、對比、降解析度、JPEG），共 108 張輸出。產生腳本兩次執行 manifest 逐位元組相同。**這是模擬，不等於真實掃描機成像。**
3. **比較**：v4（rapidocr-onnxruntime 1.4.4 內附，固定 wheel 位元組）、v5 mobile、v6 small，沿用 B3b 的 `evaluate.measure()`（只換識別權重，偵測與方向分類固定）與 B3b2 的按語言字數加權計分。每個條件含原始合成圖對照，共 13 個條件 × 3 模型。
4. **真實公開掃描樣本**：未取得（見限制）。

## 結果

### 1. v5 ONNX 來源與授權分級

| 項目 | 結論 | 分級 |
| --- | --- | --- |
| 實測檔身分 | 三個獨立來源（RapidOCR v3.10.0 目錄、403323726 GitHub 鏡像、RapidOCR 登錄檔）SHA-256 相同；RapidOCR 的 ModelScope 原址被擋，未直接下載 | 雜湊已核對 |
| 轉檔者與工具版本 | 檔案內無 producer 資訊；無 RapidOCR 公開的 v5 轉檔紀錄。RapidAI 的 paddleocr_convert 工具寫入的 metadata 鍵與字表格式相符，但 ONNX 動態維度名為 `DynamicDimension.N`，與該工具改寫後的形式不同，故**不能認定**由該工具產生 | 查不到 |
| 官方 ONNX | PaddleOCR 官方 Android 部署文件（commit dab3fe3，與 B3b 固定提交 b03f464 皆含）列 `PaddlePaddle/PP-OCRv5_mobile_rec_onnx`（HF）與 BOS 官方 ONNX tar；**本環境無法取得，無法判定是否與實測檔為同一檔** | 存在但未驗證 |
| 原始 Paddle 權重授權 | PaddleOCR 專案 LICENSE 為 Apache-2.0（b03f464，SHA-256 `3840c5c0…`，與 B3b 原文相同）；官方模型列表列出 PP-OCRv5_mobile_rec 但不列個別授權；模型卡被擋 | **由專案整體授權推定** |
| ONNX 的授權宣告 | RapidOCR 的 `python/MODEL_LICENSES.md`（commit 1b9573d，2026-11-11）宣告登錄表內所有模型（含 PP-OCRv5 ONNX）為 Apache-2.0，並列出本檔所屬登錄路徑。這是 RapidOCR 的宣告，**不是 Baidu／PaddleOCR 權利人的授權文件**，且文件只對 PP-OCRv6 引用了 HF 模型卡 | **直接載明（僅第三方轉檔者宣告）** |
| 403323726 鏡像 | 無 LICENSE 檔，README 只寫「派生自 PaddleOCR，Apache 2.0」 | 查不到（僅 README 聲明） |
| 字表 | 內嵌 metadata 鍵 `character`，18,383 行；ONNX 輸出 18,385 類，多 2 類（推定為 CTC blank 與一個額外符號，未讀 RapidOCR postprocess 原始碼確認）。B3b 的 `measure()` 檢查輸出類別等於 postprocess 字表長度，本輪重跑時通過 | 與 1.4.4 相容有實測依據 |

**與使用者 2026-11-20 決定 A 的關係**：決定 A 只涵蓋 v4 與 v2 cls 三個既有模型，**不涵蓋 v5**。v5 的授權只能依 RapidOCR 宣告與專案整體授權推定，不足以視為已由 A 接受。

### 2. 模擬掃描：整體（12 個劣化條件彙總，按字數加權）

| 模型 | 繁中 | 簡中 | 英文 |
| --- | ---: | ---: | ---: |
| v4（現行） | 82.70%（980／5664 編輯） | 96.40%（203／5640） | 97.56%（328／13416） |
| v5 mobile | 93.91%（345） | 96.26%（211） | 97.54%（330） |
| v6 small | 95.43%（259） | 96.95%（172） | 97.77%（299） |

原始合成圖（對照，B3b2 同數值）：繁中 v4 86.23%、v5 98.52%、v6 98.52%；簡中 98.94%、99.15%、98.94%；英文 99.82%、100%、99.91%。

### 3. 模擬掃描：逐條件（簡中編輯錯誤數，v4／v5／v6）

| 條件 | v4 | v5 | v6 |
| --- | ---: | ---: | ---: |
| 原圖 | 5 | 4 | 5 |
| 旋轉 0.8° | 38 | 37 | 37 |
| 旋轉 2.0° | 78 | 77 | 77 |
| 模糊 0.8 | 4 | 4 | 5 |
| 模糊 1.5 | 4 | **5** | 4 |
| 雜訊 σ=10 | 4 | **11** | 6 |
| 雜訊 σ=20 | 6 | **8** | 4 |
| 對比 0.5 | 4 | 4 | 4 |
| 對比 0.3 | 4 | 4 | 4 |
| 降為 50% 再放大 | 9 | 8 | 4 |
| 降為 33% 再放大 | 40 | 37 | 13 |
| JPEG q30 | 6 | **10** | 9 |
| JPEG q12 | 6 | 6 | 5 |

簡中逐條件比較：v5 比 v4 多錯的條件有 4 個（模糊 1.5、雜訊 σ=10、雜訊 σ=20、JPEG q30），少錯的 4 個，其餘持平。v6 在簡中多數條件不差於 v4。

繁中：v5 在 12 個條件中全部不差於 v4；v6 在 4 個條件差於 v5（旋轉兩個、模糊 0.8、對比 0.5）。

英文：v5 比 v4 多錯 4 個條件（旋轉 0.8、模糊 0.8、降為 33%、JPEG q12）。

**v5 剩餘錯誤類型**：本輪只記數字，未逐字分類。繁中在旋轉條件下錯誤最集中；簡中的增量來自雜訊與 JPEG 條件下的少量字形誤讀。簡繁混淆、標點、罕見字的細分類需要更多樣本，**未做**。

### 4. 真實公開掃描樣本

**未取得。** 候選來源的主機全數被擋或不可用（見下節）。GitHub 上可取得的 OCR 測試圖（PaddleOCR、RapidOCR、Tesseract 專案）要不是非掃描文件，就是授權與來源無法確認，不符合本輪「授權清楚」的條件，故未使用。**未以合成圖冒充真實掃描。**

建議：使用者若要真實掃描複驗，可自行列印公開領域的繁中、簡中、英文文件並掃描，或由使用者提供已確認授權的樣本。

## 限制與未驗證

- 模擬掃描只有 3 份樣本／語言、1 次執行（ONNX 單執行緒推論為確定性，但仍是小樣本）。簡中 4 至 6 個編輯的差異屬小樣本範圍，不能當作統計顯著。
- 旋轉 0.8° 就讓所有模型（包括 v4）大幅下降，與掃描實務中的傾斜程度不一定相符，也可能是偵測框與閱讀順序的問題。本輪未分析原因，這個條件的數字應保守解讀。
- v6 small 的官方來源（HF 模型卡）與 v5 相同，皆被擋。RapidOCR 文件對 v6 引用了官方 HF 模型卡並宣告 Apache-2.0，**本輪未能驗證該引用**。
- 未跑 v3 繁中封存版的掃描條件（B3b2 已有原圖結果，本輪不擴充）。
- 未做 Windows 封裝、推論效能與記憶體比較。

## 被擋的主機

| 主機 | 用途 | 處理 |
| --- | --- | --- |
| www.modelscope.cn | RapidOCR v3.10.0 發布的 v5 ONNX 原址 | 改用 GitHub 鏡像，SHA 相同 |
| huggingface.co | 官方 PP-OCRv5 ONNX 與模型卡、v5 Paddle 模型卡 | 未取得，列為未驗證 |
| paddle-model-ecology.bj.bcebos.com | 官方 Paddle 權重與官方 ONNX tar | 未取得 |
| paddleocr.bj.bcebos.com | 繁中 v3 原始 Paddle 權重 | 未取得（B3b 已知） |
| commons.wikimedia.org、upload.wikimedia.org | 公有領域真實掃描 | 未取得 |
| zh／en.wikisource.org、gutenberg.org、archive.org、loc.gov、digital.ncl.edu.tw、dl.ndl.go.jp、data.gov.tw | 公有領域或公開文獻 | 探測皆被擋，未取得 |
| github.com 網頁與 api.github.com | 網頁 blob 頁 403；GitHub API 對非本專案 repo 未啟用 | 改用 raw.githubusercontent.com 與 git 協定讀取公開 repo；未繞過代理 |

完整的主機清單與用途寫在 [v5-provenance.json](v5-provenance.json) 的 `blocked_hosts`。

## 檔案

- [v5-provenance.json](v5-provenance.json)：v5 來源、雜湊、授權分級、被擋主機。
- [degrade_scan.py](degrade_scan.py)：固定參數與種子的模擬掃描產生器（只讀 B3b2 的 PNG）。
- [scan-degradation-manifest.json](scan-degradation-manifest.json)：12 個條件的參數、種子規則、來源樣本與 108 張輸出的 SHA-256。
- [run_scan_evaluation.py](run_scan_evaluation.py)：比較腳本，沿用 B3b 與 B3b2 的評分函式；輸入圖必須與 manifest 雜湊相符，否則停止。
- [scan-evaluation-results.json](scan-evaluation-results.json)：逐條件、逐樣本、逐模型的結果（含識別文字）。
- `samples/`：三張劣化示例（雜訊 σ=20 的簡中表格、33% 降解析度的繁中表格、JPEG q12 的繁中標題），僅供目視確認，不是評估輸入。

## 重跑

模型必須放在 repo 外，檔名與 B3b 的 `evaluation-inputs.json` 一致（`v5-rapid-mobile.onnx`、`v6-rapid-small.onnx`）。

```bash
RUN=docs/development-records/runs/b3b3-v5-provenance-scan-2026-11-20
python -I $RUN/degrade_scan.py --output-dir /tmp/b3b3-scan --manifest /tmp/b3b3-manifest.json
python -I $RUN/run_scan_evaluation.py --models /tmp/b3b3-models --degraded-dir /tmp/b3b3-scan --manifest /tmp/b3b3-manifest.json --output /tmp/b3b3-results.json
```

劣化輸出不放進 repo。若要逐位元組核對，比對 manifest 的 `outputs[].sha256`。

## 判斷

- v5 來源：**實測檔的身分已由多個來源核對，但授權只到「第三方宣告」等級。** 官方 ONNX 存在，但本環境無法比對，且 v5 不屬於使用者決定 A 的範圍。
- 模擬掃描：v5 相對 v4 在繁中明顯改善，英文持平，**簡中整體持平（96.26% 對 96.40%），但在雜訊與 JPEG 條件下出現 4 個增加的錯誤。** 依 2026-11-20 使用者決定「簡中能力不可移除或降低」，**目前證據不足以支撐在 B3 直接以 v5 取代 v4。**
- v6 small 在本輪模擬中整體最好（繁中 95.43%、簡中 96.95%），但其 ONNX 授權與來源證據也未在本環境驗證，且模型較大（21 MB）。
- 建議下一步：(a) 使用者提供或列印真實掃描樣本後再複驗；(b) 另查 v6 small 的官方 HF 模型卡；(c) 若要保留簡中不退步，v5 與 v6 都需要在更多簡中掃描樣本上證明。換模型的決定仍由使用者做。

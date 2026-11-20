# B3b5 以官方 PP-OCRv6 small／PP-OCRv5 mobile ONNX 重跑評估

日期：2026-11-20（台北）。開始時的 origin/main：`c42aa27`。本輪只新增本目錄與 CHANGELOG 一行，未改程式、打包、STATUS、登記表、測試或 CI，未改寫 B3b、B3b2、B3b3、B3b4 的任何證據檔。

## 做了什麼

1. **下載官方 ONNX**：以 B3b4 記錄的固定 commit 下載 `PaddlePaddle/PP-OCRv6_small_rec_onnx`（`b8f84f0b…`）與 `PaddlePaddle/PP-OCRv5_mobile_rec_onnx`（`ed152b8b…`）的 `inference.onnx`。兩檔的 SHA-256 與大小都與 B3b4 登錄值相同（見下表）。檔案放在 repo 外的 scratchpad，只用 onnxruntime 讀取。
2. **核對官方 inference.yml**：以固定 commit 的 raw 路徑取得，雜湊與 B3b4 記錄相同。
3. **字表**：官方 ONNX 沒有內嵌 metadata（沒有 `character`），因此 RapidOCR 1.4.4 無法從模型讀字表。改由 yml 的 `PostProcess.character_dict` 建立外部字表檔，經 `rec_keys_path` 傳入（見 [official_check.py](official_check.py)）。
4. **重生成劣化圖**：沿用 B3b3 的 `degrade_scan.py`（12 條件 × 9 張 = 108 張）與 B3b4 的 `degrade_expand.py`（2 條件 × 9 張 = 18 張）。兩份輸出圖的 SHA-256 與既有 manifest 逐張相同（0 不符）。
5. **評估**：135 張輸入（9 張原圖、108 張模擬劣化、18 張 expand 旋轉），沿用 B3b `normalized()`／`edit_distance()` 與 B3b2 `language_totals()`。比較 v4（現行）、v6 官方、v5 官方；v6 與 v5 的 RapidOCR 轉檔版引用 B3b3、B3b4 已記錄的結果，不重跑。
6. **一致性檢查**：本輪重跑的 v4 與 B3b3、B3b4 記錄值相比，135 張的逐樣本編輯數與辨識文字全部相同（0 差異）。這表示環境與 B3b 基準一致。
7. **官方與轉檔版比對**：在同一批 135 張輸入上比較辨識文字；另以隨機輸入比較 ONNX 輸出數值。
8. **粗略推論時間**（單執行緒，僅參考）。

## 檔案與雜湊

| 項目 | 官方（本輪下載，已核對） | RapidOCR 轉檔（B3b3／B3b4 實測） |
| --- | --- | --- |
| PP-OCRv6 small rec ONNX | `5435fd74…`，21,159,378 B（與 B3b4 登錄值相同） | `6f327246…`，21,234,383 B |
| PP-OCRv5 mobile rec ONNX | `da72dc72…`，16,534,782 B（與 B3b4 登錄值相同） | `5825fc7e…`，16,631,306 B |
| v6 inference.yml | `ab078671…`，150,579 B | 不適用 |
| v5 inference.yml | `5dfeb277…`，148,345 B | 不適用 |

官方 ONNX 本體與字表檔都不放進 repo（ONNX 約 21 MB、字表約 75 KB）。字表檔雜湊：v6 `b5f2bfe2…`（74,947 B，18,710 行含 blank 與空白）；v5 `d1979e9f…`（74,012 B，18,385 行）。

## 字表接法

- 字表檔由 [official_check.py](official_check.py) 從 yml 寫出：每行一字、UTF-8、以 `\n` 結尾。
- RapidOCR 讀入後會在最前加 `blank`、在最後加一個空白，所以字表長度 = yml 項數 + 2。
- 檢查結果（[official-onnx-check.json](official-onnx-check.json)）：

| 模型 | yml 項數 | ONNX CTC 輸出類別 | 字表長度（含 blank 與空白） | 回讀與 yml 相同 |
| --- | ---: | ---: | ---: | --- |
| v6 官方 | 18,708 | 18,710 | 18,710 | 是 |
| v5 官方 | 18,383 | 18,385 | 18,385 | 是 |

- yml 本身不含空白項，這與 B3b4 結論一致。
- 預處理：官方 yml 的 `RecResizeImg` 為 3×48×320，RapidOCR 的 `resize_norm_img` 也是 BGR、`(x/255−0.5)/0.5`，兩者一致，因此沒有改動預處理。
- 官方 ONNX 的輸入為動態寬度（`[N, 3, 48, W]`），與 RapidOCR 轉檔版相同。

## 結果

### 1. 三種口徑（按字數加權的字元正確率）

| 口徑 | 模型 | 繁中 | 簡中 | 英文 |
| --- | --- | ---: | ---: | ---: |
| 含舊旋轉（12 條件） | v4（現行，重跑） | 82.70%（980） | 96.40%（203） | 97.56%（328） |
| | v6 官方 | **95.43%**（259） | **96.95%**（172） | 97.77%（299） |
| | v6 轉檔（B3b3） | 95.43%（259） | 96.95%（172） | 97.77%（299） |
| | v5 官方 | 93.91%（345） | 96.26%（211） | 97.54%（330） |
| | v5 轉檔（B3b3） | 93.91%（345） | 96.26%（211） | 97.54%（330） |
| 排除舊旋轉（10 條件） | v4（現行，重跑） | 83.79%（765） | 98.15%（87） | 99.59%（46） |
| | v6 官方 | **96.97%**（143） | **98.77%**（58） | **99.85%**（17） |
| | v6 轉檔（B3b3） | 96.97%（143） | 98.77%（58） | 99.85%（17） |
| | v5 官方 | 95.11%（231） | 97.94%（97） | 99.58%（47） |
| | v5 轉檔（B3b3） | 95.11%（231） | 97.94%（97） | 99.58%（47） |
| 排除舊旋轉＋expand 旋轉（12 條件） | v4（現行，重跑） | 82.68%（981） | 96.40%（203） | 97.59%（323） |
| | v6 官方 | **95.43%**（259） | **96.95%**（172） | 97.83%（291） |
| | v6 轉檔（B3b4） | 95.43%（259） | 96.95%（172） | 97.83%（291） |
| | v5 官方 | 93.87%（347） | 96.24%（212） | 97.61%（321） |
| | v5 轉檔（B3b4） | 93.87%（347） | 96.24%（212） | 97.61%（321） |

括號內為總編輯數。

### 2. 簡中逐條件編輯數（越少越好）

| 條件 | v4 | v6 官方 | v5 官方 | 與 v4 相比（v6 官方） |
| --- | ---: | ---: | ---: | --- |
| 原圖（對照） | 5 | 5 | 4 | 持平 |
| 旋轉 0.8°（舊） | 38 | 37 | 37 | 較好 |
| 旋轉 2.0°（舊） | 78 | 77 | 77 | 較好 |
| 旋轉 0.8°（expand） | 38 | 37 | 38 | 較好 |
| 旋轉 2.0°（expand） | 78 | 77 | 77 | 較好 |
| 模糊 0.8 | 4 | **5** | 4 | **較差 +1** |
| 模糊 1.5 | 4 | 4 | 5 | 持平 |
| 雜訊 σ=10 | 4 | **6** | 11 | **較差 +2** |
| 雜訊 σ=20 | 6 | 4 | 8 | 較好 |
| 對比 0.5／0.3 | 4／4 | 4／4 | 4／4 | 持平 |
| 降為 50% 再放大 | 9 | 4 | 8 | 較好 |
| 降為 33% 再放大 | 40 | 13 | 37 | 較好 |
| JPEG q30 | 6 | **9** | 10 | **較差 +3** |
| JPEG q12 | 6 | 5 | 6 | 較好 |

**v6 官方在簡中相對 v4 較差的條件**：模糊 0.8（+1）、雜訊 σ=10（+2）、JPEG q30（+3），共 3 個條件、合計多 6 個編輯。其餘條件 v6 持平或較好，整體（三種口徑）簡中正確率仍高於 v4。

**較差的內容是什麼**（以字元比對檢視，[結果 JSON](official-evaluation-results.json) 內有原始辨識文字）：多數是**全形與半形標點**的差別，例如 `：`→`:`、`；`→`;`、`–`→`-`；另有一次多出一個拉丁字母 `W`（表格樣本）。沒有看到整字誤認。這些差異對閱讀影響有限，但仍是輸出上的差異，是否可接受交使用者判斷。

**v5 官方的簡中**：與 v4 相比在雜訊 σ=10（+7）、JPEG q30（+4）、雜訊 σ=20（+2）等條件較差，整體（排除舊旋轉）簡中為 97.94%，低於 v4 的 98.15%。這與 B3b3 結論一致，v5 不建議取代 v4。

### 3. 官方與轉檔版是否等價

- **辨識文字**：v6 官方與 v6 轉檔在 135 張輸入上**逐字完全相同**（135／135，差異 0）；v5 官方與 v5 轉檔同樣 135／135 相同。
- **數值**：以同一組隨機輸入（固定種子，形狀 2×3×48×320）比較 ONNX 輸出，v6 最大絕對差 1.9e-6、v5 為 8.9e-7，argmax 完全一致。差異僅為浮點誤差。
- 兩檔位元組不同（雜湊不同），但功能上等價。B3b3、B3b4 以轉檔版得到的數字，對官方檔同樣成立。

### 4. 推論時間（同環境、單執行緒、CPU，僅參考）

| 模型 | 權重大小 | 9 張總時間（三次中位數加總） | 每張平均 |
| --- | ---: | ---: | ---: |
| v4（現行） | 10,857,958 B | 14.9 s | 1.66 s |
| v6 官方 | 21,159,378 B | 12.4 s | 1.38 s |
| v5 官方 | 16,534,782 B | 14.9 s | 1.66 s |

數量級參考，不是效能基準。v6 檔案約為 v4 的 2 倍大，RAM 為軟性預算，這點尚未以實測量測。

## 判斷：B3 能否採用 v6 官方檔

**技術面**：官方檔已取得並核對雜湊；在本輪的 135 張輸入上，官方檔與 B3b4 使用的轉檔版辨識結果逐字相同，因此 B3b3、B3b4 的評估結論可以延用到官方檔。字表可由官方 yml 建立，與 RapidOCR 1.4.4 相容。

**仍待決定或補足的事項**：

1. **簡中**：整體不低於 v4，但在 3 個模擬條件較差（合計多 6 個編輯，多為標點全半形）。依「簡中能力不可降低」的決定，這點需要使用者判斷是否可接受。樣本每語言只有 3 張，屬小樣本。
2. **授權**：官方模型卡宣告 Apache-2.0，但模型卡連結的 `LICENSE` 在 repo 內不存在（`resolve/main/LICENSE` 回 404，與 B3b4 相同）。授權屬於模型卡的權利人宣告，不是獨立的授權文件。必要授權與再散布門檻仍未關閉，依 AGENTS.md 不對外上傳模型。
3. **打包**：官方 ONNX 沒有內嵌字表，若採用，打包時必須一併提供字表（外部檔，或寫入 ONNX metadata）。這是打包方式的決定，依 AGENTS.md 需要使用者同意，本輪未做。
4. **真實掃描樣本**：仍未取得（與 B3b3、B3b4 相同缺口）。
5. **官方 Paddle 權重**（`inference.pdiparams`）與 Paddle 推論：本輪未取得，只有 B3b4 的 LFS 雜湊。

**結論**：官方檔在技術上可以替代轉檔檔；是否採用，取決於（a）簡中三個模擬條件的標點差異是否可接受，與（b）授權與再散布門檻。在這兩件事由使用者決定前，不建議把 v6 官方檔放進 B3 的打包。v5 官方不建議採用。

## 限制與未驗證

- 全部為模擬掃描，不等於真實掃描機成像；每語言 3 張原圖，小樣本。
- 只在 CPU、單執行緒、rapidocr-onnxruntime 1.4.4 與 onnxruntime 1.31.1 的環境測試；Windows、GPU 未驗證。
- 官方檔的字表由 yml 外部提供；本輪未驗證打包後的載入流程。
- 未做記憶體測量。
- 英文在 expand 旋轉下的差異（B3b4 留下的未查明項）本輪未處理。
- 字表與官方 ONNX 本體未入 repo；repo 內只保留雜湊與結果。

## 被擋主機與本輪網路狀況

- 本輪 `huggingface.co` 與 `us.aws.cdn.hf.co` 可以正常下載，B3b4 記錄的 403 未再發生。
- 未嘗試 `paddle-model-ecology.bj.bcebos.com`，也未使用任何第三方 GitHub 映像。
- 未修改網路設定，未繞過代理。

## 重跑

```bash
RUN=docs/development-records/runs/b3b5-official-onnx-rerun-2026-11-20
B3B3=docs/development-records/runs/b3b3-v5-provenance-scan-2026-11-20
B3B4=docs/development-records/runs/b3b4-v6-official-provenance-2026-11-20
# 1. 核對官方檔並建立外部字表（下載目錄與字表目錄都放在 repo 外的新目錄）
python -I $RUN/official_check.py --onnx-v6 <v6 inference.onnx> --yml-v6 <v6 inference.yml> \
  --onnx-v5 <v5 inference.onnx> --yml-v5 <v5 inference.yml> --chars-dir <新字表目錄> --output <新 JSON>
# 2. 重生成劣化圖並與既有 manifest 核對
python -I $B3B3/degrade_scan.py --output-dir <新目錄>/scan --manifest <新目錄>/scan-manifest.json
python -I $B3B4/degrade_expand.py --output-dir <新目錄>/expand --manifest <新目錄>/expand-manifest.json
# 3. 評估（約 15 分鐘，CPU 單執行緒）
python -I $RUN/run_official_evaluation.py --official-v6 <v6 inference.onnx> --official-v5 <v5 inference.onnx> \
  --keys-v6 <新字表目錄>/v6-official-keys.txt --keys-v5 <新字表目錄>/v5-official-keys.txt \
  --check $RUN/official-onnx-check.json --scan-dir <新目錄>/scan --scan-manifest <新目錄>/scan-manifest.json \
  --expand-dir <新目錄>/expand --expand-manifest <新目錄>/expand-manifest.json --output <新 JSON>
```

執行環境為 `scratchpad/venv`，版本與 B3b 基準相同（rapidocr-onnxruntime 1.4.4、onnxruntime 1.31.1、numpy 2.5.4、opencv-python 5.0.0.93、pillow 13.0.0）。

## 檔案

- [official_check.py](official_check.py)：核對官方 ONNX 與 yml 雜湊，建立外部字表並回讀比對，檢查類別數。
- [run_official_evaluation.py](run_official_evaluation.py)：評估 v4（重跑）、v6 官方、v5 官方，彙總三種口徑並比對官方與轉檔版文字與推論時間。引用 B3b、B3b2 的計分函式，不改原檔。
- [official-onnx-check.json](official-onnx-check.json)：官方檔核對與字表檢查結果（含字表雜湊）。
- [official-evaluation-results.json](official-evaluation-results.json)：135 張輸入的逐條件、逐樣本結果（含辨識文字）、三種口徑彙總、簡中逐條件編輯數、文字比對與推論時間。
- [manifest.json](manifest.json)：日期、來源提交、結果摘要與各檔雜湊。

# B3b4 PP-OCRv6 small 官方來源、授權與旋轉條件補測

日期：2026-11-20（台北）。來源提交：origin/main `c0001b6`。本輪只新增本目錄與 CHANGELOG 一行，未改程式、打包、STATUS、登記表、測試或 CI。

## 做了什麼

1. **官方 v6 small 來源**：用 HF API 取得 `PaddlePaddle/PP-OCRv6_small_rec_onnx` 的 commit sha 與 LFS 雜湊（`inference.onnx`，`5435fd74…`，21,159,378 bytes）。模型卡以固定 commit 取得。同一 API 也取得官方 Paddle 權重 `PaddlePaddle/PP-OCRv6_small_rec` 的雜湊（`406e1e68…`）。
2. **與 B3b 實測檔比對**：B3b 的 v6 small 是 RapidOCR v3.10.0 的轉檔（`6f327246…`，21,234,383 bytes）。兩者**不是同一檔**（雜湊與大小都不同）。RapidOCR 的 `MODEL_LICENSES.md` 第 5 節也說明轉換檔不一定與 PaddlePaddle 託管的 ONNX 逐位元組相同。
3. **官方 v5 mobile 來源**（次要）：`PaddlePaddle/PP-OCRv5_mobile_rec_onnx`，`da72dc72…`，16,534,782 bytes。與 B3b 實測檔 `5825fc7e…`（16,631,306 bytes）**不同**。
4. **授權**：讀取官方模型卡的 YAML 與內文、RapidOCR 的 `MODEL_LICENSES.md`（v3.10.0）。摘錄見 [license-excerpts.md](license-excerpts.md)，全文另存 [RapidOCR-v3.10.0-MODEL_LICENSES.md](RapidOCR-v3.10.0-MODEL_LICENSES.md)。
5. **旋轉條件補測**：B3b3 查驗指出旋轉可能裁切內容。新增 `expand=True` 旋轉（0.8 度、2.0 度），沿用 B3b3 的評估腳本（只換識別權重）。
6. **粗略推論時間**（單執行緒，僅參考）。

## 結果

### 1. 來源與雜湊

| 項目 | 官方（HF，commit 固定） | B3b 實測候選（RapidOCR 轉檔） | 同一檔？ |
| --- | --- | --- | --- |
| PP-OCRv6 small rec ONNX | `5435fd74…`，21,159,378 B | `6f327246…`，21,234,383 B | 否 |
| PP-OCRv5 mobile rec ONNX | `da72dc72…`，16,534,782 B | `5825fc7e…`，16,631,306 B | 否 |

**官方 ONNX 位元組本輪未取得，故未能實測官方檔。** 雜湊來自 HF API 的 LFS 登錄，檔案本身沒有下載與核對。詳見「被擋主機」。

### 2. 授權分級

| 對象 | 分級 | 依據 |
| --- | --- | --- |
| 官方 v6 small ONNX 與 Paddle 權重（PaddlePaddle 組織） | **權利人直接載明** | 模型卡 YAML `license: apache-2.0`；徽章連結 `./LICENSE`，但該 repo 的檔案清單中**沒有** LICENSE 檔 |
| 官方 v5 mobile ONNX（PaddlePaddle 組織） | **權利人直接載明** | 模型卡 YAML `license: apache-2.0`；repo 中沒有 LICENSE 檔 |
| 專案整體 | 已保存 | PaddleOCR 專案 LICENSE（Apache-2.0，B3b 的 [PaddleOCR-v3.7.0-LICENSE.txt](../b3b-ppocr-model-review-2026-11-20/PaddleOCR-v3.7.0-LICENSE.txt)，SHA-256 `3840c5c0…`） |
| RapidOCR 轉檔的 v6／v5 檔（B3b 實測的 `6f327246…`、`5825fc7e…`） | **第三方宣告** | RapidOCR v3.10.0 `MODEL_LICENSES.md` 宣告 Apache-2.0，並說明它「不是權利人的授權文件」；轉檔紀錄（工具、版本、參數）未取得 |
| 字表 | 未核 | 官方 ONNX 本體與官方 `inference.yml` 都未取得；B3b 實測檔的內嵌字表授權另論 |

判斷依據的原文：官方模型卡的 YAML（逐字見 license-excerpts.md 第 1、2 節）與 RapidOCR 第 3 節（引用官方 v6 模型卡）、第 5 節（轉換檔可能非逐位元組相同）。

### 3. 評估（RapidOCR 轉檔候選，**非官方 ONNX**）

沿用 B3b3 的 `run_scan_evaluation.py` 與 `evaluate.measure()`。模型僅替換識別權重；偵測與方向分類固定。條件：B3b3 的 10 個非旋轉劣化、B3b3 的兩個舊旋轉（無 expand）、本輪的兩個 expand 旋轉。彙總方式為按字數加權。

| 口徑 | 模型 | 繁中 | 簡中 | 英文 |
| --- | --- | ---: | ---: | ---: |
| 含舊旋轉（B3b3 原口徑，12 條件） | v4（現行） | 82.70% | 96.40% | 97.56% |
| | v5 mobile | 93.91% | 96.26% | 97.54% |
| | v6 small | 95.43% | 96.95% | 97.77% |
| 排除舊旋轉（10 條件） | v4（現行） | 83.79% | 98.15% | 99.59% |
| | v5 mobile | 95.11% | 97.94% | 99.58% |
| | v6 small | 96.97% | 98.77% | 99.85% |
| 排除舊旋轉＋expand 旋轉（12 條件） | v4（現行） | 82.68% | 96.40% | 97.59% |
| | v5 mobile | 93.87% | 96.24% | 97.61% |
| | v6 small | 95.43% | 96.95% | 97.83% |

逐條件簡中編輯錯誤數（v4／v5／v6）：

| 條件 | v4 | v5 | v6 |
| --- | ---: | ---: | ---: |
| 原圖（對照） | 5 | 4 | 5 |
| 旋轉 0.8°（舊，無 expand） | 38 | 37 | 37 |
| 旋轉 0.8°（expand） | 38 | 38 | 37 |
| 旋轉 2.0°（舊，無 expand） | 78 | 77 | 77 |
| 旋轉 2.0°（expand） | 78 | 77 | 77 |
| 模糊 0.8 | 4 | 4 | **5** |
| 模糊 1.5 | 4 | 5 | 4 |
| 雜訊 σ=10 | 4 | 11 | **6** |
| 雜訊 σ=20 | 6 | 8 | 4 |
| 對比 0.5／0.3 | 4／4 | 4／4 | 4／4 |
| 降為 50% 再放大 | 9 | 8 | 4 |
| 降為 33% 再放大 | 40 | 37 | 13 |
| JPEG q30 | 6 | 10 | **9** |
| JPEG q12 | 6 | 6 | 5 |

**v6 在簡中是否比 v4 差？** 是，在 3 個條件中差 1 至 3 個編輯：模糊 0.8（5 比 4）、雜訊 σ=10（6 比 4）、JPEG q30（9 比 6）。其餘條件 v6 持平或較好。整體（排除旋轉）v6 仍較好（98.77% 比 98.15%）。

**旋轉問題的結論修正**：expand=True 與不 expand 的錯誤數幾乎相同（簡中 38／37／37、78／77／77 的模式不變），三個模型受影響的程度相近。這表示**旋轉的代價主要來自偵測與閱讀順序的管線，不是裁切**。B3b3 「可能是裁切」的推測被本輪推翻。仍然不應以旋轉條件判斷模型優劣，但原因不是裁切。英文在旋轉下各模型都大幅下降（例如 v6 旋轉 0.8° 為 102 個編輯，原圖為 1），這點在 B3b3 未單獨說明，需另查偵測器的角度處理。

### 4. 粗略推論時間（同一環境，單執行緒，CPUExecutionProvider，9 張原圖，每張取 3 次中位數）

| 模型 | 權重大小 | 9 張總時間 |
| --- | ---: | ---: |
| v4（現行 rec） | 10,857,958 B | 15.5 s |
| v5 mobile（RapidOCR 轉檔） | 16,631,306 B | 16.7 s |
| v6 small（RapidOCR 轉檔） | 21,234,383 B | 13.8 s |

三者差距很小，只能當作數量級參考，不是效能基準。模型體積 v6 最大。

### 5. 字表與 1.4.4 相容性

B3b3 已確認 RapidOCR 轉檔的 v5 與 v6 在 rapidocr-onnxruntime 1.4.4 下能推論，且 ONNX 的輸出類別數與 postprocess 字表長度相符（`evaluate.measure()` 檢查通過）。**官方 ONNX 的字表是否內嵌、是否與 RapidOCR 轉檔的字表相同，本輪無法確認。**

## 被擋主機與未取得的內容

| 主機 | 用途 | 結果 |
| --- | --- | --- |
| us.aws.cdn.hf.co | HF resolve 對官方 ONNX 的 302 轉址目標 | 代理回 403（no rule or network setting allows this host）。使用者清單中的 cas-bridge.xethub.hf.co、cdn-lfs.hf.co、cdn-lfs-us-1.hf.co 直接探測也都是 403，轉址沒有落在清單內 |
| paddle-model-ecology.bj.bcebos.com | 官方 Paddle 權重與官方 ONNX tar | 403 |
| 第三方 GitHub 映像（oaustegard/PP-OCRv6_small_rec_onnx） | 想取得與官方雜湊相同的位元組作為替代 | 這個下載被自動權限審查拒絕。本輪未重試，也沒有用它做評估。未用非官方來源代替官方檔 |

未修改網路設定，也未用其他方式繞過。若要取得官方 ONNX，需要使用者決定是否放行 `us.aws.cdn.hf.co`（或同一 xet 橋接主機），或另行提供已驗證雜湊的檔案。

## 判斷：能否在 B3 採用 v6 small

**目前證據不足以採用 v6 small。** 缺的項目：

1. **取得官方 ONNX 位元組**，核對 `5435fd74…` 與大小。目前只有 HF 的 LFS 登錄值，檔案本體未核。
2. **以官方 ONNX 重跑評估**。本輪的數字是 RapidOCR 轉檔候選，它與官方檔不是同一個檔案。
3. **官方字表與 1.4.4 相容性**，以及字表授權。
4. **授權的接受路徑**：官方模型卡是直接宣告，但模型卡連結的 LICENSE 不在 repo。RapidOCR 轉檔的檔案只有第三方宣告。若 B3 採用，應打包官方檔，而非 RapidOCR 轉檔檔（需使用者決定）。
5. **真實掃描樣本**（與 B3b3 相同的缺口）。
6. **使用者的決定**：AGENTS.md 規定換模型與打包變更須經使用者同意；必要授權門檻未關閉前不對外上傳模型。

v5 mobile 的判斷與 B3b3 相同：簡中在雜訊與 JPEG 條件較 v4 多錯 4 個編輯，不建議在目前證據下取代 v4。

## 限制與未驗證

- 模擬掃描，不等於真實掃描機成像。每個條件 3 份樣本、每語言小樣本，簡中差距（1 至 3 個編輯）屬小樣本範圍。
- 候選檔是 RapidOCR 轉檔，**不是官方 ONNX**。官方檔的推論結果未知。
- 官方權重 `PaddlePaddle/PP-OCRv6_small_rec` 的 `inference.pdiparams` 只取得 LFS 雜湊，未核對檔案本體。
- 模型卡 YAML 宣告 Apache-2.0，但未見 repo 內的 LICENSE 檔（連結失效）。
- 未核 v6 small 的字表授權、字型授權。
- 未做 Windows 封裝與記憶體測量。

## 重跑

候選檔放在 repo 外（與 B3b3 相同檔名）。命令見下，腳本在本目錄。

```bash
RUN=docs/development-records/runs/b3b4-v6-official-provenance-2026-11-20
B3B3=docs/development-records/runs/b3b3-v5-provenance-scan-2026-11-20
python -I $RUN/degrade_expand.py --output-dir /tmp/b3b4-scan/imgs --manifest /tmp/b3b4-scan/expand-manifest.json
python -I $B3B3/run_scan_evaluation.py --models /tmp/b3b4-models --degraded-dir /tmp/b3b4-scan/imgs --manifest /tmp/b3b4-scan/expand-manifest.json --output /tmp/b3b4-scan/expand-results.json
python -I $RUN/summarize.py /tmp/b3b4-scan/expand-results.json > /tmp/b3b4-scan/summary.json
python -I $RUN/timing.py --v4 <v4 rec onnx> --v5 /tmp/b3b4-models/v5-rapid-mobile.onnx --v6 /tmp/b3b4-models/v6-rapid-small.onnx --output /tmp/b3b4-scan/timing.json
```

`expand-manifest.json` 的輸出圖雜湊可核對重現；劣化圖與候選模型都不放進 repo。

## 檔案

- [sources.json](sources.json)：官方來源、commit sha、LFS 雜湊、授權分級、被擋主機。
- [license-excerpts.md](license-excerpts.md)：模型卡與 RapidOCR 授權宣告的逐字摘錄。
- [RapidOCR-v3.10.0-MODEL_LICENSES.md](RapidOCR-v3.10.0-MODEL_LICENSES.md)：RapidOCR 授權宣告全文（SHA-256 `c5fd0e86…`）。
- [degrade_expand.py](degrade_expand.py)：expand=True 旋轉劣化產生器（只讀 B3b2 PNG，不改 B3b3 腳本）。
- [expand-manifest.json](expand-manifest.json)：兩個 expand 條件的參數與 18 張圖（2 條件 × 9 樣本）的雜湊。
- [expand-results.json](expand-results.json)：逐條件、逐樣本、逐模型的結果（含識別文字）。
- [summarize.py](summarize.py)、[summary.json](summary.json)：三種口徑的彙總與逐條件編輯數。
- [timing.py](timing.py)、[timing.json](timing.json)：粗略推論時間。
- 既有證據未變更：B3b、B3b2、B3b3 目錄原地保留。

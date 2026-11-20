# B3b PP-OCR 模型來源、授權與辨識評估

本輪盤點 A13b 固定 CPU 候選 `b17d51b`（run [44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417)）的權重和設定，並在 Linux CPU 比較識別候選。正式設定仍使用原三個模型。登記表 `cpu-rapidocr-models` 維持 `open`，適用授權及模型選擇待使用者決定。

## 現有 worker 的來源

鎖定的 PyPI wheel 是 `rapidocr_onnxruntime-1.4.4-py3-none-any.whl`。下表四檔的大小與 SHA-256 同時符合 wheel 的 `RECORD` 及固定 Windows 候選。完整雜湊、原始 Paddle 模型 URL、RapidOCR 發布檔及 Paddle 鏡像逐項列在[現有模型對照](current-models.json)。

| 檔案 | Bytes | SHA-256 開頭 | 版本依據 |
| --- | ---: | --- | --- |
| `ch_PP-OCRv4_det_infer.onnx` | 4,745,517 | `d2a7720d` | PaddleOCR 官方索引的 PP-OCRv4 mobile 偵測模型。ONNX 與 RapidOCR 歷史發布 ZIP 逐 byte 相同。 |
| `ch_PP-OCRv4_rec_infer.onnx` | 10,857,958 | `48fc40f2` | PaddleOCR 官方索引的 PP-OCRv4 mobile 中文識別模型。ONNX 與同一發布 ZIP 逐 byte 相同。 |
| `ch_ppocr_mobile_v2.0_cls_infer.onnx` | 585,532 | `e47acedf` | PaddleOCR 官方索引的 PP-OCR mobile v2.0 方向分類模型。ONNX 與同一發布 ZIP 逐 byte 相同。 |
| `config.yaml` | 1,221 | `bf94a1da` | 與 RapidOCR `v1.4.4` 同版提交的 YAML 逐 byte 相同，內容指定模型路徑及前後處理參數。 |

RapidOCR 的 wheel 發布工作流會複製 GitHub asset `123276554` 裡的三個 ONNX，該 asset 由 SWHL 上傳。SWHL 在 2023-08-27 公告 v1.3.0 已支援 PP-OCRv4，已下載 v1.3.0 wheel 複驗，三檔完全一致。三檔也與 RapidOCR `v3.10.0` 目錄列出的 SHA-256 相同。PaddleOCR 官方索引給了原始推論模型名稱及連結，RapidOCR 另有同名 Paddle 封存，以及公開的 Paddle2ONNX 通用流程。三個 ONNX 沒有可核到的逐檔轉換紀錄，實際轉檔者、工具版本、參數及當時的輸入封存雜湊均未證實。Paddle 封存鏡像的雜湊只證明鏡像內容。[RapidOCR wheel 工作流](https://github.com/RapidAI/RapidOCR/blob/86ae3f5079df3422c1829cd84baf19bc8a7a9453/.github/workflows/gen_whl_to_pypi_rapidocr_ort.yml) · [RapidOCR v1.3.0 公告](https://github.com/RapidAI/RapidOCR/issues/111#issuecomment-1694652323) · [PaddleOCR 官方模型索引](https://github.com/PaddlePaddle/PaddleOCR/blob/07603421c20a96bb94bb87d0c4211032527ae706/paddleocr.py) · [RapidAI 的轉檔說明](https://github.com/RapidAI/PaddleOCRModelConvert/blob/66b51a48d57b4f17567a695d00c5682b1b08fd16/README.md)

## 授權及須決定的範圍

- **設定檔**可追到 RapidOCR `v1.4.4` 同版來源，其專案 Apache-2.0 原文已在 B3a 綁定。**三個模型**的上游原文是本輪保存的 PaddleOCR v2.9.1 專案 Apache-2.0 授權，包含原著作權行。現有 wheel、RapidOCR ONNX ZIP 和 Paddle 鏡像均未提供可逐一綁定到這些權重或轉檔的 LICENSE／NOTICE，其中 PaddleOCR 維護者已明確確認原始預訓練方向分類模型 `ch_ppocr_mobile_v2.0_cls` 為 Apache-2.0。兩個 v4 權重，以及三個 ONNX 的轉檔適用範圍仍待確認。[PaddleOCR v2.9.1 授權原文](PaddleOCR-v2.9.1-LICENSE.txt) · [方向分類權重授權回覆](https://github.com/PaddlePaddle/PaddleOCR/issues/8780#issuecomment-1371724255) · [RapidOCR B3a 原文證據](../b3a-cpu-original-notices-2026-11-20/worker-originals.json)
- 若確認 Apache-2.0 涵蓋對應權重及 ONNX，該條款第 4 節允許再散布，包括轉換後版本。交付時提供適用的完整 LICENSE、保留適用的著作權和歸屬，對修改檔標明變更。原作品有適用的 NOTICE 時，另附可讀的相關歸屬。現況可識別的兩份原文是 PaddleOCR 的 LICENSE 和 RapidOCR 的既有 LICENSE。隨包決定還應確認轉檔或上游是否有另需保留的 NOTICE。本輪保留原文與出處供審查。

## 只評估識別模型

偵測、方向分類、信心門檻及其餘設定固定為現有 wheel 的原始位元組，只替換測試程序的識別模型參數。固定繁中圖直接使用 `test_traditional_chinese_quality_known_gap` 的既有 PNG。新增固定簡中、英文合成圖，參考文字和指紋記於[輸入清單](evaluation-inputs.json)。

下表是 Python 3.12.14、Linux x86-64、`rapidocr-onnxruntime 1.4.4`、ONNX Runtime 1.31.1、CPU 單執行緒的實測。採 NFC、忽略空白，保留簡繁、大小寫及標點。括號為「字元編輯距離／參考長度」，正確率為 `max(0, 1 - 編輯距離 / 參考長度)`。單張樣本只反映本輪比較。[逐樣本輸出與環境](evaluation-results.json)

| 識別器與 ONNX 大小 | 繁中 | 簡中 | 英文 | 1.4.4 相容性 |
| --- | ---: | ---: | ---: | --- |
| 現有 PP-OCRv4 mobile，10,857,958 bytes | 88.24%（2/17） | 100%（0/17） | 100%（0/33） | 現有基線 |
| PP-OCRv5 mobile，16,631,306 bytes | 100%（0/17） | 100%（0/17） | 100%（0/33） | 原預處理、內嵌字表及 CTC 解碼實測通過 |
| PP-OCRv6 small，21,234,383 bytes | 100%（0/17） | 100%（0/17） | 100%（0/33） | 原預處理、內嵌字表及 CTC 解碼實測通過 |
| `chinese_cht_PP-OCRv3_rec`，UmiOCR 封存轉檔，11,169,672 bytes | 100%（0/17） | 29.41%（12/17） | 90.91%（3/33） | 能執行，簡中品質未達基線 |
| 繁中 v3，RapidOCR 目錄另版，11,152,536 bytes | 未實測 | 未實測 | 未實測 | 有目錄雜湊和 Git LFS 指標，下載端點被擋 |

| 候選 | ONNX 來源與授權查證 |
| --- | --- |
| v5 mobile | 實測版是 RapidOCR 目錄的 ONNX，同一 SHA-256 由固定 GitHub 鏡像取得。PaddleOCR 官方文件列出簡繁英等支援與原始 Paddle 下載。已取得 PaddleOCR v3.7.0 Apache-2.0 原文，實測 ONNX 的轉檔及授權適用範圍仍待確認。 |
| v6 small | 實測版同樣比對到 RapidOCR 目錄的 SHA-256。Paddle 官方另有 v6 small ONNX，其鏡像保留 Apache-2.0 和 NOTICE，SHA-256 與 RapidOCR 版不同。兩版的條款證據分開，實測 RapidOCR 版的適用範圍仍待確認。 |
| 繁中 v3 | PaddleOCR 舊版清單列出專用的 Paddle 推論權重。同家族的 UmiOCR 版 ONNX 用發布封存及成員雜湊核對，轉檔作者和權利範圍仍待確認。RapidOCR 目錄另版有不同 SHA-256。 |

原始模型 URL、實測封存來源、各候選完整雜湊及字數參考集中在輸入清單。三個實測候選均可由鎖定的 RapidOCR 1.4.4 執行。若將來採用，需要另行更新應用程式的模型驗證、安裝及授權資料。這次只有 Linux CPU 測量，未做新模型的 Windows 封裝驗收。[PaddleOCR 3.7.0 授權](PaddleOCR-v3.7.0-LICENSE.txt) · [PaddleOCR v5／v6 模型說明](https://github.com/PaddlePaddle/PaddleOCR/blob/b03f46425e8ff4442b268ce449e3eef758146cd4/docs/version3.x/module_usage/text_recognition.en.md) · [Paddle v6 ONNX 鏡像 NOTICE](https://github.com/oaustegard/PP-OCRv6_small_rec_onnx/blob/b8bf7284a7ae271ce31cec691ba9343d7ca3dbb8/NOTICE)

### 可選做法

1. **單一簡繁模型**。v5 mobile 和 v6 small 在目前三張圖同分。v5 檔案比 v6 小約 4.60 MB，可優先考慮 v5。若有更多文件樣本，再看 v6 是否有優勢。
2. **保留現有模型，加繁中選項**。仍以 v4 服務簡中及英文，讓使用者明確切換繁中。專用 v3 在本次簡中和英文退步，適用於明確選定的繁中輸入。新增選項會增加隨包模型、授權與管理成本。
3. **維持現況**。先把現有權重的授權範圍釐清。ONNX 繁中已知缺口維持現行揭露。

### 重跑

取回輸入清單中要跑的 ONNX 到 repo 以外的暫存目錄，解出 UmiOCR 封存指定成員，依其 `filename` 命名。在符合清單套件版號的 Python 環境執行下列程式。`--available-only` 會把缺檔標成未實測，SHA-256 或大小錯誤仍會停止。

```bash
python docs/development-records/runs/b3b-ppocr-model-review-2026-11-20/evaluate.py --models /tmp/ppocr-models --output /tmp/ppocr-results.json --available-only
```

B3a 的 pin、證據和兩份既有原文有新增一致性測試。兩個 profile 的 gates 均 exit 0，基本包旗標及阻擋清單維持原值，CPU 四旗標仍為 false。完整 Linux 回歸數見進度資料，既有 ONNX 繁中品質仍為預期失敗。[gates 摘要](gates-summary.json) · [回歸進度](../../../progress.json)

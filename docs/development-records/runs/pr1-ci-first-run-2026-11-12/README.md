# PR 1 上新 CI 入口的首次 GitHub 執行

2026-11-12（台北）。[PR 1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1) 的 head 為 `cd14fe7da32042859d9210a29c041b90f5af7e8b`（程式 0.19.1／架構 0.4）。這是 `linux-regression.yml` 以及兩條 Windows 驗證流程的 `pull_request` 觸發第一次在 GitHub Actions 實際執行，三者皆 Success。

| 流程 | run | 結果 | 報告 artifact（ID／SHA-256／到期） |
| --- | --- | --- | --- |
| Linux full regression | [43152427632](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43152427632) | Success | `linux-regression-reports`／13914003823／`38e9b4130ba48652556e46043bcdb138301a7309261013f334fbf3472bec1001`／14 天 |
| Windows base validation | [43152427580](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43152427580) | Success（Linux 原生輸入＋Windows 2022 建置與驗收兩個 job） | `windows-base-validation-reports`／13915870195／`275756533bb1d00103ab42244654eaec20a4f1da3dfb95815c2bc5b550169a27`／2026-11-19 |
| Windows CPU component validation | [43152427554](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43152427554) | Success | `windows-cpu-validation-reports`／13915590985／`b3041a83a827372b7447101f1d3da4a3b8c979874df760ba855750f40abc638e`／2026-11-19 |

## Linux 回歸的實際計數

取自保存的 [linux-regression-reports.zip](linux-regression-reports.zip)（原位元組，99 個成員，CRC 通過）內的 `mixed-result.json` 與 `isolated/summary.json`：

| 執行 | run | pass | failure | error | 載入錯誤 | skip | expected failure |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 混合程序 | 698 | 697 | 0 | 0 | 0 | 0 | 1 |
| 45 個獨立模組 | 698 | 697 | 0 | 0 | — | 0 | 1（全部 exit 0） |

Runner 環境：Ubuntu 24.04、setup-python 的 CPython 3.12.16、apt 的 Tesseract 5.3.4／Leptonica 1.82.0。唯一預期失敗仍是既有 ONNX 繁中品質缺口。

## 範圍與限制

- PR 觸發的流程以 GitHub 產生的**暫時 merge commit** 執行，Windows 報告內記錄的 commit 是該暫時提交，不是 `cd14fe7`。因此這兩次 Windows Success 只說明「此 PR 合併後的內容可在 hosted Windows 建置並通過既有自動驗收」，**不取代** source `cb8f24d` 的候選證據，也不是新的候選清單。
- 兩份 Windows 報告 artifact 沒有下載保存；需要時可在到期前取得。EXE／模型本體（`windows-ocr-ci-inputs`，保留一天）未下載。
- 沒有乾淨機、人工 UI 或 GPU 驗收；7/12、C04 2/4、C11 2/5 不變。沒有發布任何產物。

[返回開發紀錄](../../README.md)

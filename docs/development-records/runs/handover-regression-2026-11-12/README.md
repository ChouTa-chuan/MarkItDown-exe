# 接手環境的 Linux 完整回歸

2026-11-12（台北）。受測來源為 `2e066313f7a318fd5f9bde364794bceaccb46fa8`（程式 0.19.1／架構 0.4）；與最後功能來源 `cb8f24d` 相比，`src`、`tests`、`scripts`、`packaging`、`vendor`、`pyproject.toml` 無差異，只有文件與 Pages 流程不同。這是新接手 session 在全新雲端容器中的獨立執行，不沿用舊 venv 或模型。

## 結果

| 執行 | run | pass | failure | error | skip | expected failure | 程序 exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 首次（缺原生前置） | 653 | 639 | 3 | 6（皆為 `setUpClass` 載入錯誤） | 10 | 1 | 1 |
| 補齊後混合程序 | **684** | **683** | 0 | 0 | 0 | 1 | **0** |
| 補齊後 43 個獨立模組 | **684** | **683** | 0 | 0 | 0 | 1 | 全部 **0** |

- 唯一預期失敗仍是 `test_onnx_ocr.OnnxIntegrationTests.test_traditional_chinese_quality_known_gap`（ONNX 繁中品質已知缺口）；它不是品質通過。
- 首次執行不算回歸結果：容器缺 `libEGL.so.1`，6 個 Qt 測試類別在 `setUpClass` 失敗，其下 31 個測試方法沒有執行（684−653），另 3 個 Qt 生命週期測試因同一原因失敗；缺 Tesseract 使 10 項跳過。原始輸出保存在 [first-attempt-missing-prerequisites/](first-attempt-missing-prerequisites/mixed.log)。
- 補齊後的原始紀錄：[full-mixed.log](full-mixed.log)、[full-mixed-result.json](full-mixed-result.json)、[full-mixed-exit.json](full-mixed-exit.json)、[isolated/summary.json](isolated/summary.json)、[isolated-exit.json](isolated-exit.json)。exit code 取自外層真正程序，不是日誌字樣。

## 環境與基線的差異

環境指紋見 [preflight.json](preflight.json)。依賴以 `packaging/requirements-linux.txt` 雜湊鎖安裝（55 個第三方套件），`pip check` 無問題；四語模型用專案固定清單下載並驗證，五個檔案皆 `valid`。

| 項目 | 本次 | 既有基線 |
| --- | --- | --- |
| CPython | 3.12.3（Ubuntu 24.04 系統套件） | 3.12.14 |
| Tesseract | **5.3.4**（apt `5.3.4-1build5`），Leptonica 1.82.0 | 5.5.0 |
| 字型 | DejaVu Sans 2.37、NotoSansCJK-Bold（apt `fonts-noto-cjk 1:20230817`） | 同名字型，套件版本未比對 |
| libEGL | apt `libegl1 1.7.0` | 未記錄 |

因此本次是「不同 Tesseract／CPython 小版本下得到相同的 684 計數與相同的唯一預期失敗」，不是位元層級重現原基線環境。依賴鎖、模型來源與雜湊未改。

## 範圍

只驗 Linux 可攜核心與 offscreen Qt；沒有執行 Windows 建置、安裝、原生 worker、GPU 或人工 UI。C01–C12 的 7/12、C03 3/4、C04 2/4、C09 3/4、C11 2/5 不因本次改變。

[返回開發紀錄](../../README.md)

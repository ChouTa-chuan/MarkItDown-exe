# 新增分類工具與 CI 後的 Linux 完整回歸

2026-11-12（台北）。受測來源 `582458ef1c8454ca851fbc20beba7eac6630bdea`（程式 0.19.1／架構 0.4，工作分支 `claude/confident-ride-o38ls7`）。相對 `cb8f24d` 的程式差異只有新增的 `scripts/classify_unresolved_sources.py`、`scripts/run_mixed_regression.py` 與兩個測試模組；`src`、`vendor`、`packaging` 沒有變動。

| 執行 | run | pass | failure | error | 載入錯誤 | skip | expected failure | 程序 exit |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 混合程序（`run_mixed_regression.py --expected-count 698`） | **698** | **697** | 0 | 0 | 0 | 0 | 1 | **0** |
| 45 個獨立模組（`check_isolated_tests.py --expected-count 698`） | **698** | **697** | 0 | 0 | — | 0 | 1 | 全部 **0** |

- 測試數由 684 增為 698：`test_source_classification`（10 項）與 `test_regression_driver`（4 項）。模組數由 43 增為 45。
- 唯一預期失敗仍是 `test_onnx_ocr.OnnxIntegrationTests.test_traditional_chinese_quality_known_gap`，不是品質通過。
- 原始紀錄：[full-mixed.log](full-mixed.log)、[full-mixed-result.json](full-mixed-result.json)、[full-mixed-exit.json](full-mixed-exit.json)、[isolated/summary.json](isolated/summary.json)、[isolated-exit.json](isolated-exit.json)。
- 環境與[同日 684 項重跑](../handover-regression-2026-11-12/README.md)是同一個容器、venv、模型與系統套件（CPython 3.12.3、apt Tesseract 5.3.4），指紋見 [preflight.json](preflight.json)；與歷史基線（3.12.14／5.5.0）不同。

## 未在此驗證

- `linux-regression.yml` 與兩條 Windows 流程的新觸發條件只做了 YAML 解析與本機等效指令執行；因本 session 無法推送，**尚未在 GitHub Actions 實際執行**。
- 沒有 Windows 建置、安裝、原生 worker、GPU 或人工 UI。C01–C12 的 7/12、C04 2/4、C11 2/5 不變。

[返回開發紀錄](../../README.md)

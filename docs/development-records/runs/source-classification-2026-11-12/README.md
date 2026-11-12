# 未對照來源分類紀錄

2026-11-12（台北）。以 [scripts/classify_unresolved_sources.py](../../../../scripts/classify_unresolved_sources.py) 對[保存的 CI 完整報告](../ci-full-reports-2026-11-12/README.md)（source `cb8f24d`）執行，Git 樹取同一 commit。說明與結論見 [docs/source-classification.md](../../../source-classification.md)。

| 檔案 | 分類數／報告自述 | confirmed | origin-known | candidate | gap |
| --- | --- | ---: | ---: | ---: | ---: |
| [base-unresolved-classification.json](base-unresolved-classification.json) | 154／154 | 73 | 32 | 48 | 1 |
| [cpu-unresolved-classification.json](cpu-unresolved-classification.json) | 303／303 | 227 | 29 | 46 | 1 |

每份 JSON 記錄輸入 ZIP 與 `bundle-provenance.json` 的 SHA-256，以及逐檔的路徑、大小、雜湊、類別、status、證據與說明。兩份的 `accepted` 只表示分類數與報告相符；`runtime_sbom_complete`、`redistribution_approved`、`release_ready` 皆為 false。

本次沒有重新建置 Windows 候選，也沒有新增任何二進位檔。candidate 與 gap 共基本 49、CPU 47 個，仍需 Windows 端的簽章／版本資料或成員層級清單才能關閉。

[返回開發紀錄](../../README.md)

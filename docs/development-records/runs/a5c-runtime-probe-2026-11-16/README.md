# A5c：CPython runtime probe 驗收補強

2026-11-16（台北）。從 main `8993253cbecb56fe1c9794078a2059f3a1ccca63`（PR 1–10 已合併）另開 `codex/a5c-runtime-probe-20261116`，程式來源 `afb2062d4854234356faf2bb959aac634c40f89e`，獨立 [PR #11](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/11)，沒有推送其他 AI 的分支。

## 行為與反例

- 相對 A5 的 `probe_error` 或宣告-only 仍可被接受，Windows 適用清單現在由 `require_runtime_probes()` 強制每個已收集 OpenSSL／SQLite 檔案具備 `matched-runtime-probe`、觀測值及相符載入指紋。`probe_error` 一旦存在（含空字串）即拒絕，不讓成功列掩蓋整次探測失敗。
- 產生端先寫下原始診斷／來源清單再拋錯，原有診斷不被假值覆蓋；`verify_inventory()` 再強制相同條件，所以重新計算 sidecar／native manifest hash 也不能繞過 `check_bundle_provenance` 的拒絕。Windows 本機、GitHub Actions 及 Windows 清單離線重驗一致，不以環境旗標關閉門檻；Linux 不適用清單仍不冒充 Windows。
- 元件反例逐一移除 OpenSSL／SQLite 觀測、保留宣告；另驗來源不匹配、探測例外、已有匹配列卻插入 `probe_error`。audit／CLI 合成反例先證明有效 Windows fixture 可接受，再破壞四種探測條件並重綁 hash，在 CI 及非 CI 狀態均得到 exit 1／`accepted=false`。這只驗合成接線，不能當真實 Windows 執行。
- 補上刪除包內 `cpython-original/openssl.txt` 後 `verify_inventory` 拒絕的反例。libffi 不套用不存在的 runtime 查詢，保持 `build-declaration-only` 的既有限制；原文／固定版本／模型及 Qt 來源不改。
- [CPython README](../../../../packaging/cpython/README.md) 明列 `_ssl.pyd`、`_hashlib.pyd`、`_sqlite3.pyd` 的 `observed_version` 是所連結 OpenSSL／SQLite 的版本，不是該 extension 自身的 PE 檔案版本。未改 JSON schema 或藉此提高 SBOM／再散布旗標。

## 本機驗證

完整混合及獨立模組回歸均 exit 0；原始摘要見 [mixed-result.json](mixed-result.json)、[isolated-summary.json](isolated-summary.json)，現況計數唯一來源為 [progress.json](../../../progress.json)。只有既有 ONNX 繁中 expected failure，沒有 failure／error／skip。採 offscreen Qt、固定四語 TESSDATA_PREFIX、OMP／OpenBLAS／MKL 單執行緒，執行既有 run_mixed_regression.py／check_isolated_tests.py。較早相關測試的 unittest 摘要見 [targeted-summary.json](targeted-summary.json)；該獨立命令的 exit code 沒有另存，不能用後續 tail 的退出碼代替，完整 driver 的正常退出另外驗證。

上游／公開樣本、原始授權與兩平台 profiles 檢核通過。這次本機沒有失敗的完整回歸；原始日誌只留 `/tmp/markitdown-a5c-audit`，不保證更換環境後存在。

建立此紀錄時 A5c 原生 Windows CI 尚未執行；新驗收標準須由本 PR 全部 Windows CI 通過才可合併，後續另存原生實證，不改寫此本機來源。A5b 最終 CI／合併見 [PR #10](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/10)，不把它當本次 A5c 的驗證。

## 後續

本輪只完成 A5c 規格；下一個 A6 是固定來源候選、來源重分類與整體審閱。`runtime_sbom_complete`／`redistribution_approved`／`release_ready` 保持 false，原固定候選 `cb8f24d` 不替換，完整 build 修補／設定、Qt 義務與乾淨機／人工／GPU 仍待。程式0.19.1／架構0.4與產品里程碑不提高，沒有產品發行、Release 或 tag。

[返回歷史索引](../../../history-index.md)

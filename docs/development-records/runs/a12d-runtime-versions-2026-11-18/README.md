# A12d wheel 內含元件執行期版本觀測

2026-11-18（台北）。A12d 後半段：把基本包 Windows wheel 內含元件中，有版本 API 可讀的項目改為 `runtime-observed`，其餘維持 unknown。不改安裝包、spec、鎖檔，也不改任何條目的 status。

## 做了什麼

- 前半段（`scripts/embedded_runtime.py`、`scripts/embedded_components.py` 的 `runtime-observed` 分支、測試與 workflow）已在 fb4f510 推送並經 reviewer 查驗，本次沿用，沒有改動。
- 在 hosted Windows 上以 `microsoft-runtime-evidence.yml`（workflow_dispatch）執行 `scripts/embedded_runtime.py`，只讀實際載入模組的版本 API，並以原生檔 bytes 綁回 A12 固定候選。
- 把觀測結果寫入 `packaging/embedded/base-windows.json`，拆分 libxslt 與 libexslt，並在 `packaging/redistribution/obligations.json` 加入本目錄證據與共用 hash 同步。

## 結果

觀測來源：fb4f510844cbfb765bf1b5ffe19682da53c7638a（基準 A12 base-source-review，來源 2555687eafc931600f30265f7bd290331cd49a0f）。

| 元件 | 版本 | 承載原生檔 | 原生檔 sha256 與 A12 候選一致 |
| --- | --- | --- | --- |
| lxml／libxml2 | 2.11.9 | `lxml/etree.cp312-win_amd64.pyd` | 是 |
| lxml／libxslt | 1.1.45 | `lxml/etree.cp312-win_amd64.pyd` | 是 |
| pillow／libaom | 3.14.1 | `PIL/_avif.cp312-win_amd64.pyd` | 是 |
| pillow／dav1d | 1.5.3-0-gb546257 | `PIL/_avif.cp312-win_amd64.pyd` | 是 |
| numpy／LAPACK | 3.12.0 | `numpy.libs/libscipy_openblas64_-ed4f167a5330424524f45258e7ca2c8d.dll` | 是 |

- 報告 `accepted: true`，`redistribution_approved: false`。另有 19 項 not_probed 維持 unknown。
- 收據解回後與 `embedded-runtime-decoded.json` 完全相同（見下方 CI 紀錄）。

### 仍為 unknown 的項目與原因

- **pillow／raqm**：`PIL.features.version_feature('raqm')` 在 Windows 回傳 None，沒有版本值可綁定。
- **pillow／fribidi**：選配動態載入，DLL 不在 wheel 內，無法以 `_imagingft` 的 bytes 綁定。設計上保留 unknown，`scripts/embedded_runtime.py` 也明確拒絕以 Pillow 擴充模組綁定 FriBidi。
- **lxml／libexslt**：`LIBXSLT_VERSION` 只回報 libxslt 本體，libexslt 沒有取得版本的 API。
- **pillow／libyuv** 與其他 not_probed 項目：未取得觀測 API。

### 平台差異

Linux 環境的 libxml2 版本與 Windows 不同。目錄只採用 Windows 觀測（2.11.9），Linux 結果不作依據。

## CI 紀錄

- Run：44270551031（workflow_dispatch，head fb4f510，conclusion success），job 134685784045。
- 收據位於 annotation「embedded runtime observation」，內容為 gzip+base64。`annotations.json` 保存該 annotation 的原始 JSON（含同一 run 其他 annotation）。
- Artifact：`microsoft-runtime-evidence-reports`，digest `sha256:a9003fe466f6665ad66d42571d2733b41c3b863fad5396beb7cfaced1af79e62`，4224 bytes，到期 2026-11-25T08:52:51Z。artifact 只記錄、未下載。

## 限制

- 這是 Windows 執行期版本觀測，只說明「該 API 回報的版本」與「承載原生檔 bytes」的對應，不判斷原文是否充分，也不判斷散布義務。
- 不是實體使用者機驗收；GPU 與實機 Windows 驗收仍未做。
- 有五項版本綁定 A12 候選的 bytes；候選若變動，需以新的 workflow_dispatch 重新觀測。
- 證據 artifact 將於 2026-11-25 到期；本目錄保存的小型結果檔不受影響。

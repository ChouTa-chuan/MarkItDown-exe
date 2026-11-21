# B3-1 原文補件 I：LibYAML 0.2.5 與 PaddleOCR 授權原文

2026-11-21（台北）。從 origin/main `d91494c`（含 B3-0）開 `claude/b3-1-libyaml-paddleocr-notices`。程式版本 0.19.1、架構 0.4 不變。本次**不重新固定候選**，`source_commit` 仍是 A13b 的 `b17d51b`，登記表 `packaging/redistribution/obligations.json` 的狀態欄位都沒有改。

## 做了什麼

1. 新增兩份原文到 `src/desktop_app/data/licenses/windows/supplemental/`，都是固定上游 commit 的原始位元組，不改寫：
   - `libyaml.txt`：LibYAML 0.2.5 License，`https://raw.githubusercontent.com/yaml/libyaml/2c891fc7a770e8ba2fec34fc6b545c672beb37e6/License`，sha256 `c40112449f254b9753045925248313e9270efa36d226b22d82d4cc6c43c57f29`，1101 bytes，MIT。
   - `paddleocr.txt`：PaddleOCR v2.9.1 LICENSE，`https://raw.githubusercontent.com/PaddlePaddle/PaddleOCR/07603421c20a96bb94bb87d0c4211032527ae706/LICENSE`，sha256 `ff6311c56c1b22c9209c96cc8afc16da91c24ee55a15e14ebc46fe1960dbd856`，11438 bytes，Apache-2.0。與 B3b 證據目錄的 `PaddleOCR-v2.9.1-LICENSE.txt` 逐 byte 相同。
2. `sources.json` 新增上述兩筆（欄位：name、url、sha256、bytes）。
3. `inventory.json`：`pyyaml` 列綁 LibYAML；`rapidocr-onnxruntime` 列綁 RapidOCR 與 PaddleOCR 兩份原文；`files` 補兩份原文的雜湊並更新 `sources.json` 的雜湊。
4. `scripts/license_inventory.py`：新增 `SUPPLEMENT_OWNERS = {'libyaml': 'pyyaml', 'paddleocr': 'rapidocr-onnxruntime'}`。生成時依此表把原文掛到擁有者列；`verify` 在擁有者列存在時，要求該原文恰好由它宣告，否則拒絕。
5. `scripts/prepare_worker_assets.py`：worker 原文綁定改為「原文鍵 → 擁有者套件」（見下節）。
6. `packaging/profiles/cpu-windows-closure.json`：以 `scripts/cpu_worker_profiles.py --generate` 重生，只多出 `supplemental/libyaml.txt` 與 `supplemental/paddleocr.txt` 兩筆。`base-closure.json` 重生後不變（見「base 內容」）。
7. `src/desktop_app/data/licenses/index.html`：以 `license_inventory.py --verify --render` 重新渲染，只多出兩個原文連結。
8. `packaging/embedded/cpu-windows.json`：`libyaml` 元件的 note 更新說明原文已在登記清單綁定；`notices` 維持空陣列（見限制）。
9. 測試：`tests/test_bundle_provenance.py` 新增兩個測試，`tests/test_license_inventory.py` 新增一個測試；既有的 NOTICE_PACKAGES、pins 測試、原文缺失／被改測試改為依原文鍵迭代。`.github/workflows/linux-regression.yml` 的 `EXPECTED_TESTS` 由 970 改為 973。

## 原文綁定結構為何要改

舊結構的鍵是安裝套件名，一個鍵只能對應一份原文，且原文檔名、上游 URL 都假設等於套件名。LibYAML 沒有安裝的 `libyaml` 套件，PaddleOCR 也不是 wheel；rapidocr 列也需要兩份原文。因此改為：

- `WORKER_NOTICE_PINS` 的鍵是原文名；值是 `WorkerNoticePin(owner, version, metadata_sha256, url, sha256, size)`。
- `owner` 是實際安裝且持有原文的套件，`version` 與其 METADATA 雜湊都核對；`url` 含上游 commit，上游檔名取自 url 最後一段。
- 每份原文必須在 inventory 中恰好被一個列宣告（唯一擁有者），且該列必須是 `owner`。擁有者列的 `notice_files` 同樣只能含這份原文。
- 既有的 flatbuffers、rapidocr 行為不變弱：仍核對版本、METADATA、來源 URL、sha256，並新增原文大小檢查。既有反例（swapped、extra-owner、version、source、原文缺失或改動）全部保留，測試的 `first, second` 改取 `packages[1:3]`。

為何必要：PaddleOCR 授權涵蓋 rapidocr 內的 PP-OCR 模型，LibYAML 靜態併入 PyYAML 的 `.pyd`。兩者都不是獨立安裝套件，只能掛在擁有者列上。

## 版本依據分級

| 原文 | 依據 | 分級 | 說明 |
| --- | --- | --- | --- |
| LibYAML 0.2.5 | PyYAML 6.0.3 固定 commit `49790e73684bebad1df05ef8d828fa12f685bffb` 的 `.github/workflows/ci.yaml`：`LIBYAML_REF` 預設 0.2.5、`YAML_DECLARE_STATIC=1` | 上游建置設定（主要依據） | `_yaml.cp312-win_amd64.pyd`（sha `4fd0e84f…`）的 `0.2.5` 字串只是弱佐證。無 Windows 執行期觀測（`windows_runtime_observed: false`）。未升級任何 unknown 元件。 |
| PaddleOCR 原文 | v2.9.1，commit `07603421…`，與 PP-OCRv4 模型索引同一 commit | 同 commit 對應（原文與模型來源版本一致） | 授權條文屬實際模型來源的專案版本。模型本身的逐檔授權未逐一確認（B3b 已記錄，揭露檔屬 B3-5）。 |

**PaddleOCR 版本選擇**：協調者決定採 v2.9.1，不採 B3b 已取得的 v3.7.0（sha `3840c5c0…`）。v3.7.0 不隨包，之後若使用者改採 PP-OCRv6 模型，由 B3-6 再加入。兩份 Apache-2.0 條文相同，差別只在 v2.9.1 首行多了 `Copyright (c) 2016 PaddlePaddle Authors. All Rights Reserved`。

## base 內容

`packaging/profiles/base.json` 禁止 `pyyaml` 與 `rapidocr-onnxruntime`，基本包的 runtime 因此不含這兩個套件。`prepare_base_assets.py` 只複製實際 runtime 套件的 supplemental 原文，所以**基本包的檔案內容實際上不因本次變更而改變**。`base-closure.json` 重生後完全不變。協調者原本指示「base 也一併補」，此處與該指示不符，請協調者確認：若要基本包也附這兩份原文，需要先決定 base 是否收錄 pyyaml 與 rapidocr，這與現行 forbidden_packages 衝突，超出本階段範圍。

## 雜湊同步清單

| 檔案 | 舊 sha256 | 新 sha256 | 被引用處 |
| --- | --- | --- | --- |
| `windows/inventory.json` | `44fe23db…a217` | `27765d77…81ca` | `base-windows.json`、`cpu-windows.json`（已同步）；a12／a13b review、b3d `repo-notice-sources.json` 為歷史快照（保留） |
| `windows/supplemental/sources.json` | `6b5d97ed…79a` | `a37099ae…e4f5` | a12／a13b review 內的歷史快照（保留，不改） |
| `packaging/embedded/base-windows.json` | `561e0a83…03eb` | `74731625…8067f` | `obligations.json` 10 處（已同步） |
| `packaging/embedded/cpu-windows.json` | `66db0888…211c` | `b72120c6…cc77` | `obligations.json` 2 處（已同步）；b3c `notice-audit.json` 為歷史快照（保留） |
| `licenses/index.html` | `58077560…36c6` | `7809c3ac…61b1` | a12／a13b review 內的歷史快照（保留，不改） |
| `cpu-windows-closure.json`、`obligations.json` | 內容改變 | 見 manifest | 無外部引用 |

`docs/development-records/runs/b3c-cpu-native-review-2026-11-20/notice-audit.json` 仍記舊的 `cpu-windows.json` 雜湊。它是已存的證據快照，依規定保留原地。

## 驗證

- Gates：`redistribution_gates.py --source-review …/a13b-fixed-review-2026-11-18/{base,cpu}-source-review.json` 兩個 profile 皆 exit 0。與 origin/main 的輸出逐欄位相同。base：disclosed true、approved true、complete false、release_ready false。cpu：四個旗標皆 false。
- 完整回歸（venv Python 3.12，見 manifest）：`run_mixed_regression.py --expected-count 973`，結果記於 `docs/progress.json` 的 `full_regression`，數字以該檔為準。ONNX 繁中 known gap 仍是預期失敗。
- 基線：origin/main 單獨跑 `run_mixed_regression.py --expected-count 970`，結果 970 run、969 passed、1 expected failure，與 CI 一致。
- 突變驗證（M1–M4，見 manifest）：移除 inventory 唯一擁有者檢查、移除擁有者列檢查、移除原文 sha／大小檢查、移除 license_inventory 綁定檢查，各自都讓對應測試失敗；還原後回到綠燈。

## 到 B3-9 必須重新核對的項目

1. 固定候選 `b17d51b` 的 source-review（a12、a13b）與現在的 inventory、supplemental 內容不同，這是預期的。B3-9 要重新固定候選並重產 source-review。
2. `inventory.json`、`sources.json`、`index.html`、`base-windows.json`、`cpu-windows.json` 的雜湊，以及 `obligations.json` 內對應的 10 處與 2 處引用。
3. `cpu-windows-closure.json` 與 `cpu-windows-build.txt` 的重生結果。
4. `packaging/redistribution/obligations.json` 中的 `cpu-flatbuffers`、`cpu-rapidocr-models`、LibYAML 相關敘述（第 1186 行附近）與證據連結（`libyaml-gap.json`，仍記 `accepted: false`，屬歷史快照，未改）。
5. `b3c-libyaml-notice-gap-2026-11-20/libyaml-gap.json` 的「原文缺口」結論已被本次補件取代，但其內容保留為歷史證據。
6. `docs/development-records/runs/b3d-cpu-build-tools-2026-11-21/repo-notice-sources.json` 仍含舊 inventory 雜湊（歷史快照，保留）。

## 限制

- LibYAML 版本依據是上游建置設定，不是 Windows 執行期觀測。`packaging/embedded/cpu-windows.json` 的 `libyaml` 元件 `version_basis` 仍寫 `runtime-observed`，其依據是 B3c 的 `cpu-native-observation.json`，與 B3c 的結論（`windows_runtime_observed: false`）不完全一致。這是既有敘述，本次只更新 note，未改分級，請 B3-9 或協調者決定是否修正。
- `cpu-windows.json` 的 `notices` 只接受 `licenses/windows/<dist>/wheel/` 下的 wheel 原文（`embedded_components.py` 的 CPU 檢核），因此 LibYAML 原文不列入該元件的 notices，僅在 inventory 與登記清單綁定。
- PaddleOCR 原文綁在 rapidocr 列，只代表 PaddleOCR 授權的 Apache-2.0 文字已隨包。PP-OCR 模型的逐檔授權與轉檔來源仍未確認，屬 B3-5 揭露。
- inventory.json 以雜湊與既有生成器規則手動同步（生成器需要全部 wheel，離線無法重跑）。`license_inventory.py --verify` 與新增的 SUPPLEMENT_OWNERS 檢查確認其一致性。
- 不是 Windows 實機驗收，不是法律審核，不建 Release 或 tag。

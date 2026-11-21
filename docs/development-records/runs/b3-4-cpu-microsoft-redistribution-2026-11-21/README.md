# B3-4 CPU Microsoft 六檔再散布依據（只做證據）

2026-11-21（台北）。來源提交：CPU 候選 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（A13b 固定審閱），分支以 `origin/main` `b3a0e9c` 為基底。程式版號、打包內容、鎖檔、spec、`src/`、`scripts/` 與 `.github/` 均未改動。

本目錄只保存「依據」，不是核准。`packaging/microsoft/cpu-windows.json` 的 `legal_approval` 仍為 `false`，`obligations.json` 的 `cpu-microsoft` 仍為 `open`、`requires_user_decision: true`。是否接受、接受哪一條，由使用者在 B3-10 逐條決定。

## 做了什麼

1. **CPython 兩個根目錄 vcruntime（14.42.34438.0）**：確認來源是 CPU 候選 CPython 3.12.10 的 setup-python 工具快取（`C:\hostedtoolcache\windows\Python\3.12.10\x64`），不是 Visual Studio Redist。嘗試從 python.org 取得官方 3.12.10 安裝檔與 embeddable 包核對 bytes，**未成功**：`www.python.org` 經代理回 `CONNECT 403`，依代理說明不重試、不繞道。因此 bytes 與官方發行的同名檔相同與否**未能核對**。
2. **CPython 授權**：CPU 候選 `python-runtime/LICENSE.txt` 的 SHA-256 為 `e502c6b8…`（36874 bytes），候選 bytes 不在 repo 內，無法直接讀取。以 CPython 固定 commit `0cc81280…`（與 `packaging/cpython/windows-3.12.10/profile.json` 相同，`patchlevel.h` 為 3.12.10）的上游 `LICENSE` 與 `PC/crtlicense.txt` 比對（經 `raw.githubusercontent.com` 取得）。上游 `LICENSE` 的 SHA-256 為 `3b2f81fe…`，與 repo 既有 `c04-build` 的 `LICENSE.txt` 相同。上游 `LICENSE` 全文不含 Microsoft、vcruntime、CRT 字樣。`PC/crtlicense.txt` 則是 CPython 對 Windows 二進位內含 Microsoft Distributable Code 的宣告，已保存為 [cpython-PC-crtlicense.txt](cpython-PC-crtlicense.txt)。
3. **numpy 與 Shapely 的改名 msvcp140**：從 PyPI 下載鎖檔所列的 wheel 並核對 SHA-256。兩者都與 `packaging/profiles/cpu-windows-build.txt` 的 hash 相符。讀取 wheel 的 `RECORD`、`DELVEWHEEL`、`dist-info` 授權檔。用 `pefile` 2024.8.26 離線讀出 PE `FileVersion`（與既有 Windows 觀測相同）。
4. **官方 Redist 同名檔**：沿用 A13b 保存的 `microsoft-probe-7cf098e.json` 參照（`VS 2022 Enterprise 14.44.35112 x64 Microsoft.VC143.CRT`），未重做 Windows 探測。
5. **依據彙整**：六個 DLL 各一列寫入 [cpu-microsoft-basis.json](cpu-microsoft-basis.json)，並把 Shapely 的 `LICENSE_win32` 保存為 [shapely-LICENSE_win32.txt](shapely-LICENSE_win32.txt)。

## Microsoft 官方條款（權利人原文）

來源：A10 保存的 Microsoft Learn「Distributable Code for Visual Studio 2022」頁，[official-vs2022-redist.html](../a10-microsoft-runtime-2026-11-17/official-vs2022-redist.html)，SHA-256 `476af70cfdfc26a80338df8264bac5745a9e8b3a37dfd71decbaa56f301c9c22`。下列句子逐字摘錄（英文原文）：

- 「Visual C++ Runtime Files」段：「Subject to the License Terms for the software, you may copy and distribute with your program any of the files within the following folder and its subfolders except as noted below. You may not modify these files. [VisualStudioFolder]\VC\redist」
- 同段後：「Distribution of the Visual C++ Runtime Redistributable package, merge modules, and individual binaries obtained from those pages is limited to licensed Visual Studio users and is subject to its license terms.」
- debug_nonredist 與 onecore\debug_nonredist 的內容不得散布。

這段是 Microsoft 的直接條款，但只覆蓋**該資料夾內未修改的檔案**，並以「licensed Visual Studio users」為條件。它不涵蓋 CPython 或 wheel 自行複製的 DLL，除非位元組與資料夾內檔案相同。散布權利的適用由使用者判斷（A12b／A13 記錄使用者判斷適用 VS Community），本目錄不下結論。

## 逐檔依據（六列）

依據等級：權利人直接載明／專案整體推定／第三方宣告／查不到。詳細欄位與原始雜湊見 cpu-microsoft-basis.json。

| 候選檔（相對 `_internal`） | SHA-256（候選 bytes） | PE FileVersion | 來源 | 依據 | 等級 | 查不到／未決 |
| --- | --- | --- | --- | --- | --- | --- |
| `MSVCP140_1.dll` | `bfad5aef4c63a669e3c140655cdfdf395b6c979b400a447bd5dcb65ed8826c3d` | 14.44.35211.0 | VS 2022 Enterprise 14.44.35112 Redist 資料夾（與官方同名檔逐位元相同） | 上方 Microsoft 官方 REDIST 條款 | 權利人直接載明（條件：licensed VS 使用者） | 是否符合條件由使用者判斷（見 A13 D 節）；B3-10 逐條決定 |
| `msvcp140.dll` | `0f885b509a685d2bbfa652fed26b5fb31d88fbdab0a978c641d1c7b8aa460aa9` | 14.44.35211.0 | 同上（與官方同名檔逐位元相同） | 同上 | 權利人直接載明（條件同上） | 同上 |
| `vcruntime140.dll` | `052ad6a20d375957e82aa6a3c441ea548d89be0981516ca7eb306e063d5027f4` | 14.42.34438.0 | CPython 3.12.10 工具快取（python-runtime） | `PC/crtlicense.txt`（CPython 宣告，見上方檔案） | 第三方宣告（CPython）；Microsoft 直接條款：**查不到** | 與官方 Redist 14.44.35211.0 的 `vcruntime140.dll`（sha `d5e4d9a3…`）不同；python.org 同名檔未核對；14.42.34438.0 是否對應某官方 Redist 版本未核對 |
| `vcruntime140_1.dll` | `6a99bc0128e0c7d6cbbf615fcc26909565e17d4ca3451b97f8987f9c6acbc6c8` | 14.42.34438.0 | 同上 | 同上 | 第三方宣告（CPython）；Microsoft 直接條款：**查不到** | 同上（官方 `vcruntime140_1.dll` 為 14.44.35211.0，sha `1f2d41c4…`，與本檔不同） |
| `Shapely.libs/msvcp140-0fa7eb792d3fbcf2233e4ea47e9144b9.dll` | `0fa7eb792d3fbcf2233e4ea47e9144b9b1309ba8ed5d4731a72fffa8f4f556d6` | 14.44.35229.0（離線 pefile 核對） | shapely 2.2.0 wheel（`90895df6…`）內 `shapely.libs/`；RECORD 條目相符 | wheel 內 `licenses/LICENSE_win32`（SHA-256 `fdbb2abb8c598c8888755b52340bddcee38668a2def23e51e7d9e3f187bb8d51`，[原文](shapely-LICENSE_win32.txt)）：Shapely 上游宣告附帶 Microsoft Visual C++ Runtime Files，但引用 VS 2015（14.0）的條款網址，檔名寫 `msvcp140.dll` 與 VS 14.0 redist 路徑，未提及本改名複本 | 第三方宣告（Shapely 上游）；Microsoft 直接條款：**查不到** | VS 2015 條款網址未核對，不能直接套用於 VS 2022 位元組；宣告檔名與改名複本不一致；改名複本是否屬 Redist 散布範圍未決 |
| `numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll` | `a4c2229bdc2a2a630acdc095b4d86008e5c3e3bc7773174354f3da4f5beb9cde` | 14.40.33810.0（離線 pefile 核對） | numpy 2.5.4 wheel（`a7b1b635…`）內 `numpy.libs/`；RECORD 條目相符 | numpy wheel 的 `LICENSE.txt`（SHA-256 `a804dff0…`）與全部 dist-info、子目錄授權檔都沒有 Microsoft DLL 說明；只有 `DELVEWHEEL` 的 repair 參數與 METADATA 的平台分類 | **查不到** | 全部：上游沒有對此 DLL 的散布說明，Microsoft 直接條款也對不到本位元組（與官方 `msvcp140.dll` 不同，版本 14.40.33810.0 不屬 14.44.35112 Redist） |

### 版本比對

- 官方 Redist（VS 2022 Enterprise 14.44.35112）：`msvcp140.dll`、`MSVCP140_1.dll`、`vcruntime140.dll`、`vcruntime140_1.dll` 皆為 14.44.35211.0。
- CPU 候選根目錄 `vcruntime140*.dll` 為 14.42.34438.0，比官方 Redist 舊一個次版本。
- CPU 候選的根目錄 `msvcp140.dll`、`MSVCP140_1.dll` 與官方同名檔逐位元相同。
- numpy 的改名檔為 14.40.33810.0，比官方舊；Shapely 的改名檔為 14.44.35229.0，build 號比官方 14.44.35211.0 新。兩者都與官方同名檔的 bytes 不同。

## CPython 授權原文的結論

- 上游 `LICENSE`（固定 commit）：不含 Microsoft、vcruntime 或 CRT 字樣。
- 上游 `PC/crtlicense.txt`：宣告 Windows 二進位內含 Microsoft Distributable Code，散布者須遵守 Microsoft 的限制，且「see Microsoft's documentation」。這是 CPython 的宣告，不是 Microsoft 對特定 bytes 的授權。
- 候選 `LICENSE.txt`（36874 bytes，`e502c6b8…`）未能重現。依 `regen.targets` 的 `_LicenseSources`，正式建置應串接 `LICENSE`、`PC\crtlicense.txt`、bzip2、libffi、OpenSSL、SQLite，以及可能的 tcl／tk 授權。用可取得的來源（上游 LICENSE、crtlicense、bzip2 LICENSE 取自 `python/cpython-source-deps` 的 bzip2-1.0.8 分支，以及 repo 內 `packaging/cpython/windows-3.12.10/original/` 的 libffi、openssl、sqlite）依各種順序與換行組合試算，都未能得到候選的 SHA-256。上述來源全部相加為 30538 bytes，與候選的 36874 bytes 差約 6.3 KB，未能對上。tcl／tk 授權未取得，所以無法確認候選檔是否含 `crtlicense.txt` 段落。

## 查不到的明寫

- python.org 的官方 CPython 3.12.10 安裝檔與 embeddable 包：未取得（代理 403）。兩個根 vcruntime140 的 bytes 無法與官方發行對照。
- Microsoft 對 14.42.34438.0 的 `vcruntime140*.dll`、對 Shapely 的 14.44.35229.0 改名複本、對 numpy 的 14.40.33810.0 改名複本：沒有 Microsoft 直接條款能對到這些 bytes。
- numpy 上游沒有對 bundled msvcp140 的散布說明。
- Shapely 的 VS 2015 條款網址未核對內容。
- 候選 CPython `LICENSE.txt` 的 bytes 未能取得，也未能重現。

## 雜湊同步清單

無。本輪沒有修改 `packaging/microsoft/cpu-windows.json` 與 `packaging/redistribution/obligations.json`。`cpu-windows.json` 沒有適合放置新證據引用的欄位（只有 basis、redist_probe、observation 三個既有引用與 files 列）。新增引用需要改動登記表，本輪以「只新增證據、不動登記表」為優先，所以沒有需要同步的雜湊，也沒有需要新增的反例測試。若之後要把本目錄接上登記表，須另案處理，並同步測試與 `EXPECTED_TESTS`。

## 驗證

- `redistribution_gates.py --source-review …/a13b-fixed-review-2026-11-18/base-source-review.json`：exit 0。`accepted` true、`runtime_sbom_complete` false、`runtime_sbom_disclosed` true、`redistribution_approved` true、`release_ready` false。與 A13b 存檔 `base-gates.json` 的旗標及阻擋清單相同。
- `redistribution_gates.py --source-review …/a13b-fixed-review-2026-11-18/cpu-source-review.json`：exit 0。四旗標（`runtime_sbom_complete`、`runtime_sbom_disclosed`、`redistribution_approved`、`release_ready`）皆為 false。`redistribution_approved` 的阻擋清單比 A13b 存檔少 `cpu-flatbuffers`。這是 A13b 之後登記表的變動，不是本輪改動；本輪沒有改登記表。
- 測試：本輪沒有新增或移除測試，`EXPECTED_TESTS` 與 `docs/progress.json` 都不需要改，因此未執行完整回歸。
- `scripts/build_history_index.py` 與 `--check`：見 CHANGELOG 與索引。

## 限制與未驗證

- 所有 Windows 位元組都沒有在 Windows 上重新觀測。PE 版本與簽章沿用 `b3c-cpu-native-review-2026-11-20` 與 A13b 的 Windows 觀測；本輪只在 Linux 用 pefile 核對 numpy、Shapely 兩個 wheel 內檔案的 PE `FileVersion`，未重新驗證簽章。
- 根目錄 DLL 的 bytes 來自 A13b 固定審閱的 hash，本輪沒有取得檔案本身。
- 「權利人直接載明」只指 Microsoft 條款文字的存在與條件，不代表使用者符合條件；VS Community 與其他 VS 版本的適用性由使用者決定。
- 本目錄不改變任何狀態欄位，`cpu-microsoft` 仍 open，`legal_approval` 仍 false。
- Git clone（`python/cpython`）因代理的 worktree 隔離規則未執行，改以 raw 檔案 URL 取得上游 `LICENSE` 與 `PC/crtlicense.txt`。
- `cpython-PC-crtlicense.txt` 與 `shapely-LICENSE_win32.txt` 是第三方授權原文的位元組複本，來源與 SHA-256 已列於本 README 與 manifest。

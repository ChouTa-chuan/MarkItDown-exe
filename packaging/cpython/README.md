# Windows CPython 元件來源

此處保存對應 **實際 Windows CPython patch 版及 x64** 的官方建置宣告與原文。建置離線讀取 `windows-版本/profile.json`；沒有完全相同的已固定 profile 就失敗，不拿 Linux 或另一 patch 版代填。

`profile.json` 的每筆來源包含不可變 Git commit、來源路徑、SHA-256 及保存大小。`sources/` 保留官方 `python.props`、授權組合規則、外部相依選擇與 Windows 安裝配置的原位元組，用來核對宣告版本及原文來源；這些建置來源不隨應用程式複製。`original/` 才是隨包保存的原文：

- OpenSSL：取自該 CPython 外部二進位版本 x64 目錄的完整 `LICENSE.txt`。
- libffi：取自該 CPython 外部二進位版本的完整 `LICENSE`。
- SQLite：取自同版 CPython 外部來源 `sqlite3.h` 的第一個完整註記區塊，原樣保留。這是**位元組節錄**，不是整份標頭；來源整檔 hash、Git blob、節錄 offset／length 已記錄，不能改寫成自擬的授權摘要。

`scripts/cpython_components.py` 只為已由原生來源清單判為 `python-runtime` 的目標檔案建立關聯；同名 wheel／系統檔不認領。每個檔案的 source hash、PE `FileVersion`、官方建置宣告版本、與實際載入檔 hash 相符的 OpenSSL／SQLite 執行期版本分開保存。libffi 沒有本專案支援的執行期版本 API；缺少 PE 版本時只列官方宣告，不能把 `libffi-8.dll` 的 ABI 編號當成版本，也不宣稱二進位版本已獨立認證。

建置會在既有 native 資產目錄加入 `cpython-components.json` 與 `cpython-original/`，並保存實際安裝 CPython 的 `LICENSE.txt` 指紋；建置後重新驗證原文、原生檔覆蓋、版本宣告及 hash。候選清單把各檔連回對應原文，但不因此授予 owner 或把 `runtime_sbom_complete`／`redistribution_approved` 改成 true。Linux 只記不適用。

新增 profile 時先核對新的實際 CPython 版本，從官方固定 commit 取得建置設定與其真正相依原文，保留原始位元組及完整來源。以合成反例、完整回歸及 Windows CI 驗證後再採用；不可只改 JSON 版本或檔名。

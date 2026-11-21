# B3-4b：CPython 的兩個 vcruntime 與 python.org 官方發行包比對（2026-11-21）

## 做了什麼
B3-4（PR 55）當時 `www.python.org` 被這個環境擋住，無法核對 CPU worker 根目錄的兩個 `vcruntime` 是不是 CPython 官方發行的位元組。使用者 2026-11-21 開放 `www.python.org` 後，下載官方 Python 3.12.10 Windows embeddable package（64 位元），只用 Python 的 `zipfile` 讀取成員並計算雜湊，沒有執行或安裝任何內容，再和 CPU 候選的兩個檔案比對。

## 結果
| 檔案 | 候選 sha256 | 官方 embeddable 內的同名檔 | 結果 |
| --- | --- | --- | --- |
| `vcruntime140.dll`（14.42.34438.0，120,400 B） | `052ad6a2…27f4` | 相同 | **逐位元相同** |
| `vcruntime140_1.dll`（14.42.34438.0，49,776 B） | `6a99bc01…c6c8` | 相同 | **逐位元相同** |

- 完整雜湊：`052ad6a20d375957e82aa6a3c441ea548d89be0981516ca7eb306e063d5027f4`、`6a99bc0128e0c7d6cbbf615fcc26909565e17d4ca3451b97f8987f9c6acbc6c8`（與 `docs/development-records/runs/b3-4-cpu-microsoft-redistribution-2026-11-21/cpu-microsoft-basis.json` 記錄的候選值相同）。
- 下載檔：`https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip`，11,133,606 bytes，sha256 `4acbed6dd1c744b0376e3b1cf57ce906f9dc9e95e68824584c8099a63025a3c3`。
- 下載檔完整性：python.org 發行頁 `https://www.python.org/downloads/release/python-31210/` 公布的 Windows embeddable package（64-bit）MD5 為 `fe8ef205f2e9c3ba44d0cf9954e1abd3`，與我下載檔的 MD5 相同。
- 官方 embeddable 包內與 Microsoft 執行期有關的成員只有這兩個 `vcruntime`（沒有 `msvcp140*`）。

## 意義與限制
- 這證明 CPU worker 根目錄這兩個 `vcruntime` 就是 **CPython 官方發行包內的位元組**，不是別處取得的複本，這比 B3-4 時「只有 CPython 上游的宣告」的依據更具體。
- **仍然不是 Microsoft 對這些位元組的直接授權。** 它們的再散布依據仍是 CPython 的宣告（`PC/crtlicense.txt`，已保存於 B3-4 證據）：CPython 以「Microsoft Distributable Code」方式隨附，並要求下游遵守保護條款。這是否足夠，由使用者在 B3-10 決定，不代表已核准（`legal_approval` 仍為 false）。
- 只核對了 embeddable package，沒有下載 python.org 的完整安裝程式（.exe）；CPU 候選的 Python 來自 hosted runner 的 setup-python 工具快取，來源安裝程式未逐一核對，但兩個檔案的位元組與官方 embeddable 相同。
- 官方包的簽章（sigstore／GPG）未驗證，只核對了發行頁公布的 MD5。MD5 只能防誤傳，不能防惡意替換。
- 候選 CPython 的 `python-runtime/LICENSE.txt`（sha256 `e502c6b8…`）原位元組仍未取得，不在本次範圍。
- 下載檔放在 repo 外，沒有進 repo。

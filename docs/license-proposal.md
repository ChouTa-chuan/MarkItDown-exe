# 應用程式授權提案（自有程式授權已確認）

> **2026-11-13 更新：** 擁有者確認自有程式採 MIT，著作權人為「周大詮 (ChouTa-chuan)」；專案全部內容（含早期以 Codex 產生的提交）皆由擁有者主導開發、一併適用。根目錄已加入 `LICENSE`。下方第 1、2 節為當時的提案原文；第 3 節的第三方義務與缺口仍然有效，產品整體不是「全部採 MIT」。

2026-11-12（台北），程式 0.19.1／架構 0.4。**這是提案，尚未生效**：repo 根目錄目前沒有 `LICENSE`，在擁有者確認前不新增。本文件整理事實與缺口供審閱，不是法律意見；涉及對外散布時建議另請專業審閱。

## 1. 提案摘要

| 項目 | 提案 |
| --- | --- |
| 適用範圍 | 僅限**自有程式與文件**：`src/desktop_app`、`scripts`、`packaging` 內自有腳本與設定、`tests` 內自有測試、`docs` 與根目錄自有文件 |
| 授權 | MIT License |
| 不適用 | `vendor/markitdown`（上游 MIT，維持原文）、`src/desktop_app/data/licenses/**` 與 `packaging/native/minimal-notices/**`（第三方原文）、`tests/fixtures` 的上游樣本、任何建置產物中的第三方元件 |
| 產品整體 | **不是**「整個產品採 MIT」。Windows 基本包與選配元件是多個授權的集合，各元件依自己的條款，見第 3 節 |

選 MIT 的理由：與上游 MarkItDown 一致；與目前相依套件的宣告授權相容；自有程式透過 PySide6 的動態連結使用 Qt，LGPL 不要求應用程式本身採用 LGPL。

## 2. 需要擁有者決定或提供的事項

1. **是否採用 MIT**；若否，請指定其他授權。
2. **著作權人名稱與年份**。提案文字為 `Copyright (c) 2026 <著作權人>`，名稱【待確認】。
3. **早期提交的權利歸屬**。前 20 筆提交（2026-11-04～11-06）的作者欄是 `Codex Assistant`，為 AI 工具產生；是否由擁有者主張全部自有程式的權利，【待確認】。
4. 確認後要做的變更（屆時另行提交）：新增根目錄 `LICENSE`；在 `pyproject.toml` 宣告授權；更新 `THIRD_PARTY_NOTICES` 第一段；把自有 `markitdown-desktop` 的授權原文納入隨包通知，關閉報告中 25 項 `package-original-notice-pending:markitdown-desktop`。

MIT 草案文字（確認前不放進根目錄）：

```text
MIT License

Copyright (c) 2026 <著作權人>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 3. 第三方元件：義務與缺口

「宣告授權」取自套件 metadata 或 repo 保存的原文，「已有」指候選包或 repo 內查得到的證據（source `cb8f24d` 的[完整報告](development-records/runs/ci-full-reports-2026-11-12/README.md)與[來源分類](source-classification.md)）。「缺口」是散布前仍要補的事。

### 3.1 需要特別處理的元件

| 元件 | 所在 | 宣告授權 | 已有 | 缺口 |
| --- | --- | --- | --- | --- |
| Qt 6／PySide6-Essentials 6.12.0、shiboken6 | 基本包（`Qt6Core`／`Gui`／`Network`／`Svg`／`Widgets.dll` 與外掛） | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | 套件 metadata 與 wheel 內原文；repo 另存 LGPL-3 補充來源 | 選定以 LGPL-3.0 散布並隨包附 LGPL-3.0 與 GPL-3.0 全文；提供對應 Qt／PySide 原始碼的取得方式（固定版本連結或書面提供）；說明使用者可替換 Qt 程式庫（目前為獨立 DLL 的目錄式封裝，技術上可替換，但未寫成使用者說明、也未實測）；確認安裝條款不禁止為除錯而進行的逆向工程 |
| Microsoft Universal CRT／Visual C++ runtime | 兩個 profile（`api-ms-win-*`、`ucrtbase`、`msvcp140*`、`vcruntime140*`） | Microsoft 再散布條款 | 檔案雜湊；報告標記 30／21 項待審 | 檔案取自 runner 的系統路徑與 CPython 安裝，未記錄簽章與版本；需改用可追溯的官方 redistributable 來源，或在目標系統已內建 UCRT 時排除，再對照 Microsoft 的可再散布清單 |
| OpenSSL（`libcrypto-3-x64`／`libssl-3-x64.dll`） | 基本包 | 推測 Apache-2.0（OpenSSL 3） | 僅雜湊 | 來源為 runner 系統路徑、版本不明；推測由 Qt TLS 外掛引入。建議排除該外掛或改用固定來源，並附原文 |
| CPython 3.12.10 runtime | 兩個 profile | PSF-2.0，另含隨附第三方 | 建置直譯器的 `LICENSE.txt` 隨包 | 隨附的 OpenSSL、libffi、SQLite、Microsoft VC runtime 等未逐檔列版本；`base_library.zip` 與 PYZ 成員未列舉 |
| PyInstaller 6.22.3 啟動器 | 兩個 profile 的 EXE | GPL-2.0-or-later，附啟動器例外 | 原始 `COPYING.txt` 隨包並驗雜湊 | 無已知缺口；例外條款允許散布以其建置的程式，維持隨包原文即可 |
| Tesseract 5.5.3、Leptonica 1.87.0、libpng 1.6.59、zlib 1.4 | 基本包 `tesseract.exe`（靜態連結） | Apache-2.0、BSD-2-Clause、PNG Reference Library License、zlib | 固定原始碼封存與雜湊、原文隨包、`tesseract.exe` 與 payload 清單相符 | Apache-2.0 的 NOTICE 要求需確認上游是否有 NOTICE 檔；目前清單旗標 `redistribution_approved: false` |
| LLVM／MinGW-w64 執行期程式庫（compiler-rt、libc++、libc++abi、libunwind、winpthreads 等） | 靜態連結於 `tesseract.exe` | Apache-2.0 WITH LLVM-exception、MinGW-w64 各檔條款 | 原文隨包 | 確認實際連結進去的程式庫與隨包原文一一對應 |
| tessdata_fast 四語模型 | 基本包 | Apache-2.0 | 固定 commit、四檔 SHA-256 相符、官方 LICENSE 隨包 | 無已知缺口 |
| rapidocr-onnxruntime 1.4.4 與 PP-OCR 模型 | CPU 選配 | 套件宣告 Apache-2.0 | 模型雜湊檢查；報告 31 項待原文 | 模型本身的授權與來源聲明【待確認】；補齊隨包原文 |
| OpenCV 5.0.0.93 的 `opencv_videoio_ffmpeg500_64.dll` | CPU 選配 | 套件宣告 Apache 2.0；FFmpeg 另為 LGPL | 檔案在清單內 | FFmpeg 的 LGPL 義務（原文、對應原始碼取得方式）未處理；OCR 不需要影片 I/O，可評估排除 |
| Shapely 2.2.0 的 GEOS（`geos-*.dll`） | CPU 選配 | Shapely BSD-3-Clause；GEOS 為 LGPL-2.1 | Analysis 來源與雜湊 | GEOS 的 LGPL 原文與原始碼取得方式未列入 |
| pypdfium2 5.14.0／PDFium | 基本包 | BSD-3-Clause、Apache-2.0 與相依授權 | 套件原文 | PDFium 內含第三方的清單需確認已隨包 |
| certifi、tqdm | 基本包／CPU build 環境 | MPL-2.0 | 套件原文 | MPL 要求保留原文並提供該檔案原始碼的取得方式；tqdm 是否進入 runtime【待確認】 |

### 3.2 其餘套件

基本包其餘 runtime 套件的宣告授權為 MIT、BSD、Apache-2.0、PSF 或其組合（beautifulsoup4、cffi、charset-normalizer、click、cobble、cryptography、defusedxml、et-xmlfile、flatbuffers、idna、lxml、magika、mammoth、markdownify、numpy、onnxruntime、openpyxl、packaging、pandas、pdfminer-six、pdfplumber、pillow、protobuf、psutil、pycparser、python-dateutil、python-pptx、requests、six、soupsieve、typing-extensions、tzdata、urllib3、xlsxwriter）。主要義務是保留著作權與授權聲明，現有機制已把安裝套件的原文收進包內；逐一對照原生程式庫內含的第三方（例如 numpy、pillow、lxml、cryptography 的 wheel 內建程式庫）仍屬 runtime SBOM 的未完成部分。

CPU 選配的套件表描述的是**建置環境**（含 pyinstaller、pefile、setuptools、pip 等），不是 runtime 閉包；實際進入 worker 的套件需由成員層級清單確認。

## 4. 與交付的關係

- 這份提案與來源分類不阻擋 CI、報告保存或開發工作。
- 在第 2 節決定完成、且第 3.1 節的 Qt、Microsoft runtime、OpenSSL、FFmpeg／GEOS 缺口有具體處理之前，不對外上傳 Setup、worker 或模型，包含 CI artifact 形式的交付。
- 其中「排除 Qt TLS 外掛／OpenSSL」「排除 OpenCV 的 FFmpeg」「改用官方 VC runtime 來源」會改變打包內容，需擁有者同意後另行實作並以 Windows CI 驗證。

## 5. 建議的確認順序

1. 回覆第 2 節的三個問題。
2. 同意或否決第 4 節三項打包調整。
3. 之後由開發端：加入 `LICENSE`、補 Qt／LGPL 隨包說明與原始碼取得方式、在 Windows 建置時記錄系統 DLL 的來源路徑／簽章／版本、產生成員層級清單，再重新產生候選報告。

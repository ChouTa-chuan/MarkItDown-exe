# 第三方授權清單（開發預覽版）

已盤點 Windows Python 3.12 鎖定檔的 58 個套件，包含開發／建置相依的上位集合；不表示每個套件都會被打包。

原始 METADATA、wheel 內授權、官方補充原文、來源 URL 與 SHA-256 均保存在 licenses/windows。HTML 索引位於 licenses/index.html。

## 另列元件

- Microsoft MarkItDown 0.1.9：MIT；來源提交及原始 LICENSE 保留於 vendor/markitdown。
- CPython：實際建置直譯器的 LICENSE.txt 隨包保存在 licenses/python-runtime，不用其他版本文字代替。
- Tesseract 語言資料：固定提交 Apache-2.0，原文與來源在 licenses/models。Tesseract 執行檔尚未隨 Windows 包發佈。
- RapidOCR／PP-OCR 模型：屬固定版本套件，使用其 Apache-2.0 宣告，模型 SHA-256 在 onnx_ocr.py。
- 本應用程式尚未選定公開發佈的原始碼授權；不可自行假設它與上游相同。

## 特別注意

- Qt/PySide6/Shiboken：保留 wheel 商業授權提示，另附官方版本的 LGPLv3/GPLv3 原文；採用哪種授權及其義務須在發佈前落實。
- LGPL 路徑需保留動態函式庫替換能力、通知、對應來源取得方式及所需修改資訊；不可把單一封裝方式當成自動合規。
- Cobble：wheel 缺授權全文，保留官方 README 的 BSD-2-Clause 宣告、作者 metadata 及標準 BSD 文字；不代填未知著作權聲明。
- Magika 補充文件是固定官方來源的標準 Apache-2.0 原文，不宣稱該提交是本 wheel 的對應來源版本。
- 完整 Windows 二進位檔尚未建置，原生 DLL／MS runtime、Qt 義務及最終發佈授權審核仍是發佈門檻。這份清單不是法律認證。

## 鎖定套件

| 套件 | 版本 | 套件宣告（原文另附） |
| --- | --- | --- |
| altgraph | 0.17.5 | MIT |
| beautifulsoup4 | 4.15.0 | MIT License |
| certifi | 2026.10.23 | MPL-2.0 |
| cffi | 2.1.1 | MIT-0 |
| charset-normalizer | 3.5.2 | MIT |
| click | 8.5.0 | BSD-3-Clause |
| cobble | 0.1.4 | License :: OSI Approved :: BSD License |
| colorama | 0.4.6 | License :: OSI Approved :: BSD License |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause |
| defusedxml | 0.7.1 | PSFL |
| et-xmlfile | 2.0.0 | MIT |
| flatbuffers | 25.12.19 | Apache 2.0 |
| hatchling | 1.33.0 | MIT |
| idna | 3.20 | BSD-3-Clause |
| lxml | 6.1.3 | BSD-3-Clause |
| magika | 1.0.3 | Apache-2.0 |
| mammoth | 1.13.0 | BSD-2-Clause |
| markdownify | 1.2.3 | License :: OSI Approved :: MIT License |
| numpy | 2.5.4 | BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0 |
| onnxruntime | 1.31.1 | MIT License |
| opencv-python | 5.0.0.93 | Apache 2.0 |
| openpyxl | 3.1.5 | MIT |
| packaging | 26.3 | Apache-2.0 OR BSD-2-Clause |
| pandas | 3.1.0 | BSD-3-Clause |
| pathspec | 1.1.1 | License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0) |
| pdfminer-six | 20251230 | MIT |
| pdfplumber | 0.11.9 | License :: OSI Approved :: MIT License |
| pefile | 2024.8.26 | MIT |
| pillow | 13.0.0 | MIT-CMU |
| pluggy | 1.7.0 | MIT |
| protobuf | 7.36.2 | 3-Clause BSD License |
| psutil | 7.2.2 | BSD-3-Clause |
| pyclipper | 1.4.0 | MIT |
| pycparser | 3.12 | BSD-3-Clause |
| pyinstaller | 6.22.3 | GPLv2-or-later with a special exception which allows to use PyInstaller to build and distribute non-free programs (including commercial ones) |
| pyinstaller-hooks-contrib | 2026.9 | License :: OSI Approved :: Apache Software License; License :: OSI Approved :: GNU General Public License v2 (GPLv2) |
| pypdfium2 | 5.14.0 | BSD-3-Clause, Apache-2.0, dependency licenses |
| pyside6-essentials | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only |
| python-dateutil | 4.0.0 | BSD-3-Clause |
| python-docx | 1.2.0 | MIT |
| python-pptx | 1.0.2 | MIT |
| pywin32-ctypes | 0.2.3 | BSD-3-Clause |
| pyyaml | 6.0.3 | MIT |
| rapidocr-onnxruntime | 1.4.4 | Apache-2.0 |
| reportlab | 4.4.9 | BSD license (see license.txt for details), Copyright (c) 2000-2025, ReportLab Inc. |
| requests | 2.34.2 | Apache-2.0 |
| setuptools | 84.2.1 | MIT |
| shapely | 2.2.0 | BSD-3-Clause |
| shiboken6 | 6.12.0 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only |
| six | 1.17.0 | MIT |
| soupsieve | 4.0 | MIT |
| tomlkit | 0.15.2 | MIT |
| tqdm | 4.70.1 | MPL-2.0 AND MIT |
| trove-classifiers | 2026.9.21.13 | License :: OSI Approved :: Apache Software License |
| typing-extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.6 | Apache-2.0 |
| urllib3 | 2.8.0 | MIT |
| xlsxwriter | 3.3.1 | BSD-2-Clause |

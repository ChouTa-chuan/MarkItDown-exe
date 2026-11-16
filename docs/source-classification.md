# 候選包「來源未對照」檔案分類

2026-11-12（台北），程式 0.19.1／架構 0.4。對象是 source `cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1` 的 Windows 候選（run 42982427175／42982427186）。輸入為[保存的 CI 完整報告原檔](development-records/runs/ci-full-reports-2026-11-12/README.md)，逐檔結果在[分類紀錄](development-records/runs/source-classification-2026-11-12/README.md)。

這份文件回答交接 P0：基本包 154、CPU 選配 303 個 `source-owner-unresolved` 檔案各自是什麼、有什麼證據、還缺什麼。**分類不是授權核准**：`runtime_sbom_complete`、`redistribution_approved`、`release_ready` 仍為 false，C04 維持 2/4。

## 分類方法

[scripts/classify_unresolved_sources.py](../scripts/classify_unresolved_sources.py) 只讀 artifact ZIP 與 source commit 的 Git 樹，在 Linux 即可重跑，不需要重新建置。每個檔案依下列順序取第一個成立的證據：

| 順序 | 類別 | 證據 | status |
| --- | --- | --- | --- |
| 0 | `empty-file` | 零位元組，不以雜湊推定來源 | confirmed |
| 1 | `repo-blob` | 與 source commit 某個 repo 檔案位元組相同 | confirmed |
| 2 | `ci-artifact-member` | 與同次 CI artifact 成員位元組相同 | confirmed |
| 3 | `pinned-model` | SHA-256 等於固定四語模型清單 | confirmed |
| 4 | `project-native-payload` | SHA-256 等於同次 CI 的 native payload 清單 | confirmed |
| 5 | `cpython-runtime` | 報告標記自建置用 CPython 目錄收集，來源與收集後雜湊相同 | origin-known |
| 5 | `system-native` | 報告標記自建置機系統路徑收集；檔名只提供候選發行者 | candidate／gap |
| 6 | `installer-generated-record` | `*.dist-info/RECORD`，套件版號與報告套件表相符 | confirmed |
| 7 | `project-generated`、`cpython-license-text` | 專案建置腳本的固定輸出路徑 | origin-known |
| — | `archive-members-not-enumerated`、`unknown` | 無 | gap |

status 的意思：**confirmed**＝來源由雜湊或同次建置清單證明；**origin-known**＝知道從哪裡收集，上游版本與條款尚未逐檔核對；**candidate**＝只有檔名與收集位置；**gap**＝沒有證據。分類數必須等於報告自述的未對照數，否則工具以失敗結束。

## 結果

| | 基本包 | CPU 選配 |
| --- | ---: | ---: |
| 報告自述未對照 | 154 | 303 |
| 已分類 | 154 | 303 |
| confirmed | 73 | 227 |
| origin-known | 32 | 29 |
| candidate | 48 | 46 |
| gap | 1 | 1 |

| 類別 | 基本包 | CPU 選配 | 內容 |
| --- | ---: | ---: | --- |
| `repo-blob` | 24 | 220 | 基本包：自有 `THIRD_PARTY_NOTICES`、runtime 鎖、`packaging/native/minimal-notices` 的原生元件原文等。CPU：隨包的第三方授權原文／metadata 複本，與 `src/desktop_app/data/licenses` 內保存的原文位元組相同 |
| `empty-file` | 0 | 1 | 隨授權原文收集到的空 `__init__.py` |
| `ci-artifact-member` | 3 | 0 | `build-profile.json`、native `manifest.json`、`base-install-catalog.json`，皆為當次建置產物 |
| `pinned-model` | 4 | 0 | `chi_tra`／`eng`／`jpn`／`kor.traineddata`，等於 `ocr-four-languages.json`（tessdata_fast `8741641`） |
| `project-native-payload` | 2 | 0 | `tesseract.exe` 與原生來源紀錄 `source.json`，等於當次 native payload 清單；`tesseract.exe` 由固定原始碼在 CI 建置 |
| `installer-generated-record` | 40 | 6 | 各套件 `dist-info/RECORD` |
| `cpython-runtime` | 27 | 25 | `python312.dll`、`python3.dll`、標準庫 `.pyd`，以及 CPython 安裝隨附的 `libcrypto-3.dll`、`libssl-3.dll`、`libffi-8.dll`、`sqlite3.dll`、`vcruntime140.dll`、`vcruntime140_1.dll` |
| `cpython-license-text` | 1 | 1 | 建置用 CPython 3.12.10 的 `LICENSE.txt` 複本 |
| `project-generated` | 4 | 3 | 隨包原文／啟動器／原生來源的 manifest，基本包另有依 profile 重新產生的 `third-party.md` |
| `system-native` | 48 | 46 | 見下節 |
| `archive-members-not-enumerated` | 1 | 1 | `base_library.zip` |

## 2026-11-13 之後的變化

上面的數字是 source `cb8f24d` 候選的分類結果，保留作為當時的紀錄。之後的建置調整已改變候選包內容，以下數字取自 PR 3、PR 4 的 Windows CI 公開摘要（暫時合併提交上的驗證，不是新的候選證據；逐檔分類尚未對新候選重跑）。

| 項目 | `cb8f24d` 候選 | 調整後 |
| --- | ---: | ---: |
| 基本包來源未對照 | 154 | 107 |
| 基本包 Analysis 原生檔 | 201 | 153 |
| CPU 元件來源未對照 | 303 | 259 |
| CPU 元件 Analysis 原生檔 | 106 | 61 |

對應下節各項的現況：

- **第 1 項（系統路徑收集的 DLL）已處理。** CI 記錄的來源目錄顯示，這些檔案是 PyInstaller 沿 PATH 從 runner 上 Java JDK 的 `bin` 目錄收進來的複本。現在 Universal CRT（`api-ms-win-*`、`ucrtbase.dll`）不再隨包，由 Windows 10 以後的作業系統提供；`msvcp140*.dll` 改取自 Visual Studio 的可再散布目錄，數位簽章有效、簽署者為 Microsoft（[紀錄](development-records/runs/ms-runtime-official-source-ci-2026-11-13/README.md)、[簽章](development-records/runs/native-signatures-ci-2026-11-13/README.md)）。
- **第 2 項（基本包來源不明的 OpenSSL）已處理。** 排除 Qt 的 OpenSSL TLS 外掛與那兩個 DLL；CI 會在它們再度出現時直接失敗（[紀錄](development-records/runs/openssl-exclusion-ci-2026-11-13/README.md)）。「由 Qt TLS 外掛引入」仍是推測，但排除後兩個檔案確實不再被收集。
- **第 3 項（CPython 隨附元件）部分處理。** 來源目錄與簽章已記錄：基本包 27 個、CPU 元件 25 個檔案來自 python.org 發行的 CPython 3.12.10，簽章有效（Python Software Foundation 或 Microsoft）。逐檔列出隨附第三方（OpenSSL、libffi、SQLite）的版本與原文仍未做。
- **第 4 項（`base_library.zip`）進行中**，見 [STATUS.md](../STATUS.md)。
- **第 5 項不變。**
- CPU 元件另排除了 OpenCV 內附的 FFmpeg 影片外掛（[紀錄](development-records/runs/ffmpeg-exclusion-ci-2026-11-13/README.md)）。

## 仍未關閉的項目（`cb8f24d` 當時）

1. **系統路徑收集的 DLL（基本 48／CPU 46，candidate）。** `api-ms-win-*`（44／43 個）、`ucrtbase.dll`、`msvcp140.dll`、CPU 的 `MSVCP140_1.dll` 檔名符合 Microsoft Universal CRT／Visual C++ runtime，但報告沒有記錄來源路徑、數位簽章或版本資源，不能只靠檔名確認發行者。需要在 Windows 建置時補記這三項，再對照 Microsoft 再散布條款。
2. **基本包的 `libcrypto-3-x64.dll`、`libssl-3-x64.dll`（candidate）。** 這兩個檔案是從 hosted runner 的**系統路徑**收集，雜湊與大小都和 CPython 隨附的 `libcrypto-3.dll`／`libssl-3.dll` 不同（6,946,448 對 5,231,472 位元組）。也就是候選包帶了一份來源不明、隨 runner 映像變動的 OpenSSL。這是重現性與再散布風險：候選包同時含 Qt 的 `PySide6/plugins/tls/qopensslbackend.dll`，**推測**是這個 Qt TLS 外掛的相依讓 PyInstaller 從系統路徑收進 OpenSSL，尚未在 Windows 上以相依分析證實。應用程式本身不需要 Qt 網路 TLS 時，排除該外掛即可同時移除這兩個檔案。此項會更動打包內容，需要擁有者同意，尚未處理。
3. **CPython 隨附元件（基本 27／CPU 25，origin-known）。** 來源位置已確認，但 OpenSSL、libffi、SQLite、Microsoft VC runtime 各有自己的條款；隨包只有 CPython `LICENSE.txt`，尚未逐檔列出版本與原文，也未與 python.org 3.12.10 原文獨立比對。
4. **`base_library.zip`（各 1，gap）。** PyInstaller 產生的標準庫封存，成員未展開；與 PYZ 內的 Python 模組一樣，需要成員層級清單才算 runtime SBOM。
5. **專案產生的 manifest（基本 4／CPU 3，origin-known）。** 由固定腳本輸出，內容隨建置變動，無法逐位元對照；風險低，列出以求完整。

除「來源未對照」之外，報告的其他待審閱原因不在本次分類範圍，數量不變：

| 待審閱原因 | 基本包 | CPU 選配 |
| --- | ---: | ---: |
| `microsoft-native-redistribution-review` | 30 | 21 |
| `package-original-notice-pending`（自有 `markitdown-desktop`） | 25 | 0 |
| `package-original-notice-pending`（`rapidocr-onnxruntime`／`flatbuffers`） | 0 | 31／1 |
| `archive-members-not-enumerated` | 1 | 1 |
| `owner-outside-package-notice-table:setuptools` | 1 | 0 |

需審閱總數（含來源未對照）仍是基本 191、CPU 337。自有程式的 25 項待原文，取決於[應用程式授權提案](license-proposal.md)的決定。

## 重跑

```bash
python scripts/classify_unresolved_sources.py --profile base \
  --archive docs/development-records/runs/ci-full-reports-2026-11-12/windows-base-validation-reports.zip \
  --output /tmp/base-classification.json
python scripts/classify_unresolved_sources.py --profile cpu \
  --archive docs/development-records/runs/ci-full-reports-2026-11-12/windows-cpu-validation-reports.zip \
  --output /tmp/cpu-classification.json
```

輸出檔已存在時工具會拒絕覆寫。測試在 `tests/test_source_classification.py`，只用合成報告與臨時 Git 樹。

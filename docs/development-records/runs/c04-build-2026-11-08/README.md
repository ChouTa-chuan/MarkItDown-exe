# C04 基本核心打包與自檢開發紀錄

2026-11-08（台北），程式 **0.9.0**、架構 **0.4**。完成 C04 第二項子檢核（Linux 基本 profile PyInstaller／自檢），C04 **2/4**、整項未關閉，總數 **7/12**，既有 **19/25**。C03 原生 OCR、完整 C04／C09 及 Windows／GPU 尚待後續。

- [86 項結果](acceptance.json)／[日誌](component-tests.log)、[16 項新增測試](profile-tests.log)：profile／資產／診斷、閉包／授權／格式／核心／裝置／Qt 全過，0 跳過。合成 manifest／假轉換只驗自檢契約，實際 binary 驗收另列。
- [完整回歸](full-tests.log)：**440 項，439 通過、1 既有繁體品質預期失敗、0 跳過**，完整 Linux 開發 venv 的已安裝套件，63.791 秒為觀察；與下面基本 build 環境分開。
- [基本 build 安裝](build-install.log)、[本地專案安裝](local-install.log)、[實際版本](build-environment.txt)及[pip check](pip-check.log)。嚴格使用原 base Linux build 47 套件、兩個本地專案及 pip，不能拿完整開發 venv 假裝基本包。[資產準備](assets.log)與[最後建置](build.log)皆保留。
- [真正獨立程式七項](frozen/frozen-acceptance.json)／[日誌](frozen.log)：從專案以外的新工作目錄、空 PATH／TESSDATA_PREFIX／PYTHONPATH 執行，無外部 Python 或 OCR。六格式包含 UTF-8 文字／HTML／DOCX／XLSX／PPTX／原生 PDF；掃描缺 native OCR、明確選 ONNX 缺 RapidOCR 均失敗且沒有輸出。
- [core 自檢](frozen/core-self-test.json)四項通過；[full 自檢](frozen/full-self-test.json)的四項核心通過，第五項 `bundled_tesseract_bilingual` 因 C03 未整合而失敗、退出碼 1。兩者 `release_ready: false`／`full_c04_complete: false`；七項驗收驗證此拒絕行為，**不是把 OCR 失敗算成功或宣告完整基本版就緒**。
- [公開 PDF 五項](public-pdf.json)／[日誌](public-pdf.log)：四份原已固定來源 PDF，7 頁與 8,744 個正規化英數字元，另有逐格／金額／順序斷言。沿用已保存的公開來源與 hash；這組從測試控制端呼叫真 binary，空 PATH 的獨立證據在七項驗收，並非泛用準確率。
- 最終輸出保留 [文字](frozen/中文.txt.md)、[HTML](frozen/網頁.html.md)、[DOCX](frozen/文件.docx.md)、[XLSX](frozen/資料.xlsx.md)、[PPTX](frozen/簡報.pptx.md)、[原生 PDF](frozen/原生.pdf.md)及個別 stdout／stderr。合成來源沿用[前輪 fixture 清單](../c04-locks-2026-11-08/fixtures/fixtures.json)，執行前核對每檔 SHA-256，沒有使用者真實文件。
- [整包 1177 個檔案／連結及 hash](frozen/bundle-files.json)，檔案內容總大小 **352,814,293 bytes（約 336 MiB）**。binary 本體位於工作區 `/workspace/markitdown-c04-base-dist-complete/MarkItDownBaseCore`，不放 Git、未當成 Windows 安裝包發布；保留資料與來源可追溯實際建置，hash 不代表可從 Git 直接下載 binary。
- [內含 profile](bundled-data/build-profile.json)的 **235 份資產**完整逐位元組對照最終 bundle 後保存於 bundled-data；38 個 runtime 保留 Magika 的 CPU ONNX Runtime，無 RapidOCR OCR 模型／OpenCV／測試工具。包含[實際 40 個套件 METADATA／原文索引](bundled-data/licenses/installed/manifest.json)、99 份可取得的 wheel 原文、固定官方補充來源及實際 Python 授權；[256 筆 binary 來源與 75 套件系統 copyright](bundled-data/licenses/native/manifest.json)另存。
- 授權資料列出可取得的原文及來源，沒有推定尚未選定的主程式公開授權，亦不代表 Qt／全部再散布、原生 Tesseract 或最終 SBOM 審核完成。原 221 份第三方資產保持固定，本輪新增的是派生建置證據。
- [C04 2/4 與 C09 3/4 視覺](screenshots/components.png)、[窄版](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機里程碑](screenshots/mobile.png)及[瀏覽器日誌](browser.log)，總數仍 7/12。[上游](upstream.log)、[授權基線](licenses.log)、[完整性](integrity.json)與[本輪檔案 SHA-256](manifest.json)。新增[第十四份架構快照](../../../architecture/versions/v0.4-c04-frozen-core.md)。

過程紀錄：

- [初次沙箱安裝](initial-sandbox-install.log)未能取得套件，沿用相同代理／CA、固定版本與 hash 在核准執行環境成功，沒有改網路政策或升版。
- [第一次核心打包與七項](intermediate-core/frozen-acceptance.json)、[公開 PDF](intermediate-core/public-pdf.json)、該輪 build／自檢／輸出與[209 份早期資產清單](intermediate-core/bundled-data/build-profile.json)完整另存。這是授權目錄擷取加強前的版本，不冒充最後 235 份。
- 加強原生平台護欄重建時，[過早啟動程式檢查](initial-premature-executable-check.log)與[PDF 檢查](initial-premature-pdf-check.log)因 executable 尚未產生而失敗；等待建置成功後的[七項](intermediate-platform-check/frozen-acceptance.json)／[PDF](intermediate-platform-check/public-pdf.json)再驗證通過。當時 PDF 報告未成功寫出，不補造 JSON。
- 對照真正 wheel 後，發現 basename 檢索漏掉 licenses 目錄內 Apache-2.0.txt 等原文；改按完整路徑保存，補上具 hash／官方來源的原文，再重建。保存核對再發現 packaging/licenses 是 Python 子模組名稱，掃描把程式與兩份編譯快取也當成原文；排除 .py／.pyc／.pyo 與 __pycache__，新增反例後再重建。[235 份之前的 239 份觀察](intermediate-notice-scan/frozen-acceptance.json)只保留報告／輸出，不把快取寫入專案。主目錄 frozen／public-pdf／bundled-data 為最終結果，所有中間日誌與最後證據分開。

舊 `desktop.spec`／Windows workflow 保留，沒有執行 Windows、GPU、tag／Release 或手動發行；不是正式下載版。ONNX 繁體品質與 RAM 軟性預算限制保留；後續為 C03 原生引擎、完整 profile 及 C09。

[profile 指南](../../../packaging-profiles.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

# C04 基本版依賴拆分開發紀錄

2026-11-08（台北），程式 **0.8.1**、架構 **0.4**。完成基本 Python 依賴拆分子檢核，**完整 C04 未關閉，總數維持 7/12**，既有 **19/25**。原生 Tesseract／profile 打包自檢／Windows 與完整 C09 仍待後續。

- [52 項結果](acceptance.json)／[日誌](component-tests.log)：15 項新 profile 反例加原授權／格式／核心／裝置回歸，全部通過、0 跳過。新測試單獨的 [15 項日誌](profile-tests.log)另存。
- [完整回歸](full-tests.log)：**424 項，423 通過、1 既有繁體品質預期失敗、0 跳過**，已安裝套件的乾淨完整開發 venv，63.380 秒為本輪觀察；不是下列 38 套件基本 venv。
- [四份 profile 結果](profile-report.json)／[驗證日誌](profiles.log)：Linux／Windows runtime 各 38 套件，build 47／49，原版號及所有 hash 沿用。[來源規格、metadata 與 lock](../../../../packaging/profiles/README.md)另存專案，原上位清單不變。
- [乾淨基本環境六項](runtime/base-runtime-acceptance.json)／[日誌](base-runtime.log)、[pip check](runtime/pip-check.log)及[實際安裝版本](base-environment.txt)：38 個第三方套件、兩個本地專案、venv 自帶 pip，系統套件關閉；逐一比較 38 份已安裝 metadata 與鎖定快照，不含 RapidOCR／OpenCV／python-docx／reportlab 等選配或測試工具。
- 真正空 PATH／空 TESSDATA_PREFIX，六種格式走 spawn；[合成來源](fixtures/fixtures.json)附 hash，輸出保留 [文字](runtime/中文.txt.md)、[HTML](runtime/網頁.html.md)、[DOCX](runtime/文件.docx.md)、[XLSX](runtime/資料.xlsx.md)、[PPTX](runtime/簡報.pptx.md)及[原生 PDF](runtime/原生.pdf.md)。[掃描 PDF](fixtures/掃描.pdf)因缺原生 OCR 明確失敗、無輸出；這一項證明缺元件行為，不能列為 OCR 成功。
- 真正 Qt 在基本環境完成 DOCX／原生 PDF／文字批次，與各自輸出逐位元組比對；[實際視窗](runtime/desktop-base-profile.png)及 [GUI 輸出](runtime/gui/文件.docx.md)保存。圖內路徑為合成驗收資料，沒有使用者文件。
- 真正安裝的 [應用程式 wheel](local-wheels/markitdown_desktop-0.8.1-py3-none-any.whl)與 [vendor wheel](local-wheels/markitdown-0.1.9-py3-none-any.whl)、[建置](wheel-build.log)、[第三方 hash 安裝](runtime-install.log)及[本地 wheel 安裝](local-wheel-install.log)日誌保存；第三方 wheel 快取與 venv 不進 Git。這些是 Python 專案 wheel，非 Windows EXE 或完整原生安裝包。
- [進度元件與 C04 子檢核](screenshots/components.png)、[手機版](screenshots/components-mobile.png)、[既有里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機里程碑](screenshots/mobile.png)及[瀏覽器日誌](browser.log)。C04 1/4 子檢核、C09 3/4 子檢核，兩項整項均未關閉，總數 7/12。
- [上游](upstream.log)／[授權](licenses.log)、[舊紀錄完整性](integrity.json)與[本輪 SHA-256](manifest.json)。新增[第十三份架構快照](../../../architecture/versions/v0.4-c04-base-locks.md)，十二份舊圖及既有附件保持固定。

過程保存：

- [初次沙箱安裝](initial-sandbox-install.log)未取得套件，回傳無符合版本；使用相同版本／hash／代理與 CA 在核准執行環境重試成功，沒有改網路政策或升版。
- [版本整理前的 wheel 建置](initial-wheel-build.log)為過程紀錄，實際基本環境安裝使用最終 0.8.1 wheel；最終建置日誌與兩個 wheel 明確分開。
- [最初基本環境六項結果](intermediate-runtime/base-runtime-acceptance.json)／[日誌](intermediate-runtime/runtime.log)與輸出、視窗固定保留。之後增加 38 份安裝 metadata 對照與時間戳，主目錄 runtime 是再執行通過的最終結果。

Magika 檔案辨識需要 CPU ONNX Runtime，Excel／核心需要 NumPy，不能為了移除選配 OCR 而刪掉必要相依。profile 的原 Windows 授權引用不等於 Linux binary 授權／完整 SBOM／native 引擎再散布審核。舊 PyInstaller 與 Windows workflow 仍採完整開發包，diagnostics 尚未分 profile。

本輪沒有重建 frozen／native／Windows 安裝包、發布正式目錄或金鑰、建立 tag／Release 或執行手動發行。Windows／GPU、繁體品質與 RAM 軟預算限制保留；接續 profile 專用打包／自檢、C03 原生引擎與完整 C09。

[profile 指南](../../../packaging-profiles.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

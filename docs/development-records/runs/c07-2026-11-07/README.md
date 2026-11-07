# C07 開發紀錄

完成日期：**2026-11-07（台北）**。工作開始與部分執行環境原始 UTC 觀察為 2026-11-06，報告保留實際時間，不倒改原始日誌。程式 **0.5.0**、架構 **0.4**；新導入 **5/12（C01／C02／C05／C06／C07）**，既有 **19/25**。

- [元件逐項結果](acceptance.json)／[日誌](component-tests.log)：**115/115**，其中 C07 23 項、C05／C06 92 項回歸，0 跳過。協定／資源故障 fixture 與真正 native CPU 程序測試分開，並保留 11 次既有維護流程的實際程序退出觀察。
- [完整回歸](full-tests.log)：乾淨 Linux venv 的已安裝套件 **344 項，343 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。63.710 秒是本次觀察，不是效能承諾。
- [實際 frozen 驗收](frozen-acceptance.json)／[日誌](frozen-tests.log)：**10/10**，最小控制端沒有 ONNX／RapidOCR／NumPy／Pillow／Qt，PATH 留空完成簽章離線匯入、staging／正式健康、租約下 OCR、失敗隔離、後續成功、原生取消、RAM 拒絕、移除及主環境不變。
- 真正 worker 回報 frozen、Python 3.12.14／RapidOCR 1.4.4／ONNX Runtime 1.31.1／NumPy 2.5.4／OpenCV 5.0.0.93，三個實際 session 使用 CPU；[結果 JSON](frozen-worker-result.json)與[合成英文 Markdown](frozen-english-output.md)保留。健康原文 `WORKER HEALTH CHECK 12345`，不是繁體品質通過。
- [建置日誌](worker-build.log)／[資產準備](worker-assets.log)、[包檔量測](package-report.json)與[完整描述／逐檔雜湊](component.json)：814 檔、ZIP 202,741,436 bytes、解壓 536,330,062 bytes；包檔 SHA-256 `11c8e0e9ff648954c3e99a30630e47fd5f1fe6307fa813c5e062d374f3db6d18`。本機二進位 ZIP 保留在工作區外層，不加入 Git 或宣稱已發行，重建方法見 [C07 指南](../../../component-workers.md)。
- [控制端依賴安裝](controller-install.log)／[雜湊鎖定生成](controller-lock.log)：五項依賴來自原 Linux lock 的版本／雜湊子集，另有 venv 自帶 pip 及專案；這不是 C04 GUI 基本 profile 驗收。
- [實際套件原授權 manifest](installed-notices-manifest.json)記錄建置環境 58 套件、299 份 metadata／原授權；[原生來源 manifest](native-binaries-manifest.json)記錄 109 個 binary、13 個系統套件 copyright，[原生授權原文](native-notices/manifest.json)另存。包內另有 CPython 原授權與原 58／214 份依賴清單；最終再散布審查及專案授權仍待處理。
- [上游核對](upstream.log)／[既有授權核對](licenses.log)、[舊紀錄／快照／鎖定完整性](integrity.json)、[新附件 SHA-256](manifest.json)。前八份架構圖及所有先前工程附件保持固定，本輪另加第九份 [C07 架構圖](../../../architecture/versions/v0.4-c07-cpu-worker.md)。
- [瀏覽器日誌](browser.log)與[元件進度 5/12](screenshots/components.png)、[手機元件頁](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機版](screenshots/mobile.png)：測試篩選、鍵盤導覽、窄版與 JavaScript 錯誤。

開發過程與修正：

- [首次 frozen 退出 abort](intermediate-frozen-buffered-abort.log)：OCR 已完成，但 daemon 持有標準 stdin 的 buffered lock，CPython 結束失敗；改用 raw fd，正常退出也必須通過才提交正式輸出。
- [初始資源 fixture 失敗](intermediate-resource-fixture.log)：零 reserve 下零 available／extra 不構成超預算，修正為應用用量明確超過 budget；[後續 22 項中間通過](intermediate-workers.log)保留，未冒充最終 23 項。
- [全回歸的 BrokenPipe 收尾錯誤](intermediate-full-broken-pipe.log)：提前退出的 worker 關閉讀端，stdin.close 的 flush 偶爾回報 EPIPE。修正收尾不覆蓋工作結果，新增[兩項確定重現／提前退出回歸](pipe-regression.log)，再重跑上述完整最終結果。

未重建主程式 frozen 或 Windows 安裝包，未做 GPU／Windows／物理斷電驗證，RAM 仍是軟性預算；英文功能證據不關閉繁體品質 expectedFailure。沒有正式目錄、私鑰、tag 或 Release；下一段 C08 元件管理介面，再接 C09／C10，Windows 原生／profile 留原實機門檻。

[C07 設計與重建](../../../component-workers.md) · [完整架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

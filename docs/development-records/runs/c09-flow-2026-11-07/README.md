# C09 首次流程開發紀錄

2026-11-07（台北），程式 **0.7.0**、架構 **0.4**。完成三項流程子檢核；**完整 C09 仍未關閉，已驗收維持 6/12**，既有 **19/25**。基本包內含引擎／雙語模型仍缺 C03／C04，不能把本輪系統既有引擎當成全新基本包驗收。

- [94 項流程／設定／遷移／桌面／核心結果](acceptance.json)／[日誌](component-tests.log)：新增 22 項，全部通過、0 跳過；報告明列 `full_c09_complete: false`。Qt 與真實本機雙語探針，合成 fixture 另外標示。
- [完整回歸](full-tests.log)：**389 項，388 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，已安裝套件、乾淨 Linux venv，60.957 秒為本次觀察。之後補充手冊與其顯示斷言，最終 94 項另驗證新手冊。
- [真正 Qt／本機 CPU 流程九項](flow-acceptance.json)／[原始日誌](flow.log)：正式 QTimer 接點、RAM、真實繁中／英文健康、明確保存並略過選配、完成不重複、舊偏好、缺引擎文字功能與原模型不變。兩頁掃描 PDF 在**空 PATH／空 TESSDATA_PREFIX**下使用已保存的位置實際轉換。
- [實際合成 PDF](bilingual-scan.pdf)與[Markdown](bilingual-scan.md)一併保存；PDF SHA-256 記於九項報告。影像是既有英文及固定 17 字繁體目標，原文沒有放寬；合成健康不代表真實文件準確率。
- 新畫面：[RAM 與雙語健康](setup-ready.png)、[完成後掃描轉換](desktop-after-setup.png)、[缺引擎仍可繼續](setup-missing-engine.png)。圖內路徑均來自合成驗收暫存目錄，不是使用者文件。
- [元件進度與 C09 子檢核](screenshots/components.png)、[手機版](screenshots/components-mobile.png)、[原里程碑](screenshots/milestones.png)、[模組](screenshots/modules.png)、[手機里程碑](screenshots/mobile.png)，[瀏覽器日誌](browser.log)核對部分完成、展開子項、鍵盤／篩選／窄版／JavaScript。
- [上游](upstream.log)／[授權](licenses.log)、[舊附件／快照／鎖定／樣本完整性](integrity.json)及[本輪 SHA-256](manifest.json)。原十份圖及先前工程產物固定，新加[第十一份首次流程快照](../../../architecture/versions/v0.4-c09-first-run-flow.md)。

過程保留：

- [初始 22 項](initial-onboarding-tests.log)通過；[首輪真實流程](intermediate-flow/flow-acceptance.json)／[日誌](intermediate-flow/flow.log)及三張畫面／輸出保留，最終流程增加實際輸入 PDF 與雜湊保存。
- [首次子檢核瀏覽器檢查失敗](initial-browser-collapsed-details.log)：直接讀取摺疊 details 的 innerText，無法符合預期；改為先展開再核對可見內容，最終驗證通過。另讓摘要顯示「部分完成」，不把三個子項等同整項完成。

本輪模型在測試前由既有固定資料複製，原生引擎是系統 `/usr/bin/tesseract`。沒有自動下載、接管原資料、新增依賴、重建主程式 frozen／Windows 安裝包或宣稱內含 Tesseract。設定 schema v6、元件登錄及維護 schema 沿用；完成標記版本為 1，不保存永久 ready。

Windows／GPU／正式來源及基本包自帶 OCR 門檻保留，沒有 tag／Release 或手動 Windows 發行。可接續 C10 自動文件分析與元件協作，C09 全項待基本包證據。

[首次流程指南](../../../onboarding.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

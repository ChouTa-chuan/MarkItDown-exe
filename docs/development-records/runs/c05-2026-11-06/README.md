# C05 開發與驗收紀錄

日期：2026-11-06（台北），程式 **0.3.0**、架構 **0.4**。完成 C05「可信目錄與可恢復下載」，新導入 **3/12（C01／C02／C05）**，既有 **19/25** 另計。C03／C04 Windows OCR 與完整 profile 證據仍未完成，未以 Linux 準備工作替代。

- 最終 [41 項逐項驗收結果](acceptance.json)／[單元原始日誌](component-tests.log)：真實 Ed25519、磁碟與 SQLite；HTTP 回應、續傳、錯誤、取消、磁碟及撤銷／到期案例以注入回應驗證，0 跳過。
- 最終 [實際 HTTPS 六項結果](https-acceptance.json)／[日誌](https.log)：只從官方固定提交下載 11,358 bytes 的 LICENSE，核對 SHA-256、verified 登錄、快取零網路及離線匯入保留來源。一次性私鑰僅在記憶體，未作發行金鑰；不宣稱公開伺服器測過所有 Range 情境。
- 最終 [完整回歸日誌](full-tests.log)：**270 項，269 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，已安裝套件的乾淨 Linux venv。60.026 秒僅為本次觀察，不是效能承諾。
- [首次擴充測試的失敗](initial-regression.log)保留測試變數範圍錯誤；修正後的中間 [39 項結果](pre-final-acceptance.json)／[日誌](pre-final-component-tests.log)、[早期完整回歸](pre-final-full-tests.log)、[HTTPS 結果](pre-final-https-acceptance.json)／[日誌](pre-final-https.log)均為過程紀錄，最終驗收以上述檔案為準。
- [瀏覽器日誌](browser.log)與新畫面：[元件 3/12](screenshots/components.png)／[手機元件頁](screenshots/components-mobile.png)／[既有里程碑](screenshots/milestones.png)／[模組](screenshots/modules.png)／[手機版](screenshots/mobile.png)。
- [上游](upstream.log)／[授權](licenses.log)／[歷史附件、快照與依賴核對](integrity.json)。原 58 個鎖定套件、214 份授權原文不變，cryptography 現列為直接依賴；inventory 只更新鎖定摘要。
- [本輪附件清單與 SHA-256](manifest.json)獨立保存，原 75 份工程附件、C01／C02 產物與前六份圖保持原樣。

重跑：

```bash
python -m pip install --no-deps --no-build-isolation .
python scripts/check_component_acceptance.py --check C05 --report /tmp/c05-acceptance.json
python scripts/check_component_download_https.py --report /tmp/c05-https.json
TESSDATA_PREFIX=<verified model directory> QT_QPA_PLATFORM=offscreen python -m unittest discover -s tests -v
python scripts/build_progress.py
python scripts/check_progress_browser.py --screenshots /tmp/c05-progress
python scripts/verify_upstream.py
python scripts/license_inventory.py --verify
```

實際 HTTPS 需要網路且保持 proxy／CA／TLS 驗證；本輪沒有發布正式目錄、下載或執行 Windows／GPU 元件，也未重建 frozen、Windows 安裝包或觸發發行工作流程。下載只登錄 verified，不是 installed／ready；通用安裝、完整桌面管理與正式金鑰發行仍待各自工作。

[服務與信任邊界](../../../component-downloads.md) · [架構指引](../../../architecture-guide.md) · [開發紀錄](../../README.md)

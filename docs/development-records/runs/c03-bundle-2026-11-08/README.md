# C03 內含四語基本包開發紀錄

日期：2026-11-08（台北）。程式 **0.13.0**、架構 **0.4**。完成 C03 第三項的 **Linux 內含整包／離線自動解析與完整自檢**，C03 **3/4**；完整導入 **7/12**、既有 **19/25**，C04 **2/4**、C09 **3/4**，Windows／完整項未關閉。

| 保存內容 | 實際證據 |
| --- | --- |
| [acceptance.json](acceptance.json)／[日誌](acceptance.log) | 185/185：27 項新 payload／解析／故障／偏好反例，加原 build profile、四語、首次、設定／Qt／核心回歸 |
| [full-regression.log](full-regression.log) | 527 項：526 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過 |
| [frozen/frozen-acceptance.json](frozen/frozen-acceptance.json)／[driver](frozen-driver.log) | 真正 Linux frozen 12/12；空 PATH／模型環境、中文搬移、四語健康與掃描、原格式與日韓 CLI、設定原文、缺／損模型及引擎連結拒絕、文字隔離、缺選配與 library loader |
| [frozen](frozen/) | 實際 PDF／MD／文字、core 與 full 自檢、每次命令／loader 原始日誌、1260 筆 bundle 檔案／連結 hash、profile 與授權／binary 來源清單；binary 本體不入庫 |
| [qt/acceptance.json](qt/acceptance.json)／[driver](qt-driver.log)／[檢查程式](qt-check.py.txt) | 真正 source Qt／首次流程 3/3；內含模型只讀／禁止下載移除、四語健康、保存自動路徑與不重複完成；測試覆寫 asset root 指向真正 bundle，非 frozen GUI 或 Windows UI |
| [prepared-assets](prepared-assets/) | 最終實際準備的 283 份資產／profile 的可保存部分：40 套件 METADATA、99 份 wheel 原文、Python 原文、292 筆 binary 來源與 109 套件系統 copyright；排除引擎及四個 traineddata binary，只留 hash／來源 |
| [payloads](payloads/) | Windows 固定候選＋四語 28 檔／Linux 開發 8 檔的 manifest 與來源；Windows PE 沒有執行，兩個版本分開 |
| [cross-build](cross-build/) | 最後依序安裝、準備、PyInstaller 與離線組裝原始日誌；沒有把 pip 重裝與相同環境的測試並行 |
| [fixtures](fixtures/) | 重用先前固定 SHA 的公開合成文字／HTML／Office／原生與掃描 PDF；原檔保持，不含使用者文件 |
| [intermediate](intermediate/) | 初始匯入失敗、26 項／184 項／526 全回歸、前兩次建置／自檢、Leptonica soname 誤猜及實際 loader、Qt harness 類名錯誤；最後補自備模型偏好反例後才產生最終 185／527 與重新建置／12／3 驗收 |
| [screenshots](screenshots/)／progress-browser.log | 本輪里程碑／模組／元件分頁、手機、鍵盤與計數；真正模型視窗與桌面另在 qt/；初次長路徑裁切畫面另存 intermediate，擴大視窗後重建並重驗 |
| provenance.json／integrity.json／manifest.json | 新程式來源 hash、排除的 binary 範圍、舊資料保存與本目錄逐檔 bytes／SHA-256 |

Linux 實際入口為複製的 Tesseract **5.5.0**，Windows 固定最小候選是 **5.5.3**。四語均使用原固定模型 commit；Linux frozen 的 loader 已確認 Tesseract／Leptonica 從 bundle 內載入。Windows payload 的固定 EXE／模型／原文只靜態核對，沒有拿 Linux 成功冒充 Windows，也沒有執行 Windows OCR／中文路徑／安裝／乾淨機。

core 自檢通過不宣稱執行 OCR；full 只有實際四語健康與掃描通過才 `native_ocr_verified: true`。`release_ready`、完整 C03／C04／C09、Windows／GPU 均未關閉。明確自備路徑／選語保留，內含必需檔損毀時不靜默換引擎，但文字可繼續；內含模型只讀，不被受管模型服務移除。

沒有 binary、traineddata、wheel、venv、編譯快取或使用者真實文件入庫；`prepared-assets` 是來源／文字證據，並非可直接使用的完整安裝包。舊紀錄與十七份圖、七份 lock、原 221 份授權／模型清單及品質影像目標固定；既有產品資料僅離線手冊更新。ONNX 繁體缺口與 RAM 軟預算保留，未建立 tag／Release 或觸發手動 Windows 發行。

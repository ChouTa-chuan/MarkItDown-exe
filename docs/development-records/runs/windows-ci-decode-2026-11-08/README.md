# Windows 中文路徑診斷解碼修正

2026-11-08（台北），程式 0.14.0、架構 0.4。[CI #4](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42475049445)（d18e78b）Windows 原生基本包再次建置成功。UTF-8 manifest 已讓搬移後 native --list-langs 與四語清單通過；下一步 relocated full self-test 在 subprocess 讀取模型標頭時用 CP1252 解碼 UTF-8 中文，UnicodeDecodeError（byte 0x8f）而失敗。這次短 annotation 完整保留下實際錯誤，沒有再猜根因。

pdf_pipeline 的模型清單探針明確指定 UTF-8；errors=replace 僅用於診斷標頭／stderr。真正 OCR .txt 仍嚴格按 UTF-8 讀取，模型／品質目標沒有放寬。首次流程 native_command 原已以 bytes+UTF-8 讀取，這次補足 PDF OCR 路徑。

新回歸測試使用真正 Tesseract、固定 worker-health 影像及 eng 模型，複製到「中文程式 模型」路徑；強制預設 subprocess decoder=CP1252，先以真正 child 重現舊探針解碼錯誤，再驗修正版模型清單與實際 OCR 本文。這是 Linux 真實 child 的 locale 反例／功能測試，不當作新 Windows 成功。

舊安裝套件上先跑新回歸，抓到同型 UnicodeDecodeError；重新安裝修正版後相關 139/139、完整 553（552 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過）。相對 0.13.0 共新增 26 項。新 Windows CI 尚待執行，不增加完整 C03／C04／C09 或 7/12 進度。

保存公開頁、完整可讀的短診斷 JSON、初始與更正後回歸／重裝及畫面，沒有引擎／模型／使用者文件／憑證進 Git。Windows 完整 artifact／自身視窗截圖仍僅在原 CI artifact（七天），此處只封存已取得的公開證據；不宣稱已下載不可匿名讀取的附件。

基本包同時固定 Python UTF-8 mode，Windows core 會核對真正的 python_utf8_mode。最小 Linux frozen 用相同 PyInstaller option，在 LC_ALL=C、PYTHONUTF8=0、PYTHONCOERCECLOCALE=0 仍 flag=1／UTF-8，繁中／日文／韓文文字完整；僅驗包裝選項，不當作 Windows 或完整基本包驗收。保存原始 source／spec／log／JSON，binary 不入庫。

一次完整 unittest 雖印出全部檢核 OK，程序隨後 native teardown exit 139；這次不列為正式成功。啟用 faulthandler、無平行建置下隔離重跑 553／552＋1 預期失敗，實際 exit 0。初始／最新 log 與 exit metadata 分存；根因尚未定位，不把重跑通過當成修好，亦不推論 Windows 產品有同樣問題。

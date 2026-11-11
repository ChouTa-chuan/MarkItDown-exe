# 0.19.1完整回歸

2026-11-11（台北），程式0.19.1、架構0.4，測試來源ca5a296e84cdbfbfb9912f5d846df138f6fea801。Linux x86_64／Python3.12.14，獨立venv關閉system-site-packages；原Linux55套件hash鎖安裝，另以no-deps／no-build-isolation安裝本專案及固定vendor MarkItDown，pip check通過。沒有重新解析／升級鎖檔、修改vendor或模型。

完整混合程序645項：644通過、1項既有ONNX繁中品質預期失敗、0跳過、0錯誤／非預期失敗，程序正常exit0。41個模組分別建立獨立程序，總計仍645／644＋同一預期失敗，全部exit0；不是645×41項。summary.json與個別模組JSON／log完整保存。ONNX品質缺口仍未解決，預期失敗不是品質通過；GPU、乾淨Windows與人工操作均未在本輪執行。

四語Tesseract模型及LICENSE依固定commit／hash下載至本次獨立目錄，三個RapidOCR ONNX模型也驗hash；原模型資產不改。Tesseract為實際Linux系統5.5.0，字型、引擎及來源輸入hash與套件版號另記preflight.json，完整安裝集合另記all-installed-packages.json。這是來源整合回歸，不是重新建置Windows安裝包或Linux frozen包；四語模型完整不等同任意四語文件準確率。

初輪臨時mixed_runner.py缺少__main__保護，multiprocessing spawn子程序載入時重複執行suite，測試輸出交錯，該輪無效。父程序／命令列／工作目錄精確符合本次測試的執行器與其子程序已停止，exit-9屬主動清理無效啟動器，不列為產品崩潰。原driver／partial log／exit與原因保留invalid-harness；修正只在暫存測試啟動器，不改產品原始碼或測試斷言。最後受保護driver重跑全套及41模組均正常退出。

full-mixed-result.json由測試程序在teardown前寫入，因此process_exit_verified原值false保留不改；外層full-mixed-exit.json及regression-summary.json才確認實際exit0，避免僅看斷言通過而忽略原生退出異常。isolated/summary.json同樣逐案核對外層退出。

重現需先使用packaging/requirements-linux.txt的require-hashes安裝及兩份本地專案；模型路徑替換為已驗四語目錄，再於新輸出目錄執行。環境參數為QT_QPA_PLATFORM=offscreen、TESSDATA_PREFIX=<已驗四語目錄>、OMP_THREAD_LIMIT／OMP_NUM_THREADS／OPENBLAS_NUM_THREADS／MKL_NUM_THREADS=1、PYTHONFAULTHANDLER=1、PYTHONPATH=src:tests。隔離入口：python scripts/check_isolated_tests.py --expected-count 645 --output <新資料夾>。混合driver另存mixed_runner.py，main guard必須保留，內含本次固定工作／輸出路徑，重用時須換成新路徑並保留退出檢查。

視覺頁分頁／篩選／鍵盤／手機版及JavaScript檢查通過，五張實際截圖與browser.log保存。相對ca5a296的3124份既有紀錄／資產／鎖檔不變，50份run manifest共2680筆hash與28份架構快照核對通過；範圍見historical-integrity.json。

完整回歸基線由0.17.2的611更新為0.19.1的645，多34項既有新增測試；本次未新增產品測試或修改斷言。舊原始紀錄及先前162項相關測試不覆寫。C04仍2/4、C11仍2/5、導入7/12／歷史19/25。下一步候選基本包／CPU選配實物與原文、通知及版本核對，再準備可安裝測試產物／人工檢核表；無Setup／tag／Release或環境設定發布，RAM為軟性預算。

[返回開發紀錄](../../README.md) · [測試包準備](../../../windows-test-build-readiness.md)

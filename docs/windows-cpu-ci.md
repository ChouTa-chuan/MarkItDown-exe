# Windows CPU 選配元件驗證

2026-11-10，程式 **0.18.0**、架構 **0.4**。[Windows2022原生CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42791407466)（f0708d0）**11/11通過**；[公開原頁與驗證紀錄](development-records/runs/windows-cpu-ci-2026-11-10/README.md)已保存。

CPU選配獨立建置與打包，控制端不安裝NumPy、Pillow、ONNX、RapidOCR或Qt。兩者使用獨立venv，由既有Windows hash鎖及原始wheel METADATA產生依賴閉包，不重新選版本。建置24套件、控制端5鎖定依賴，後者另含pip及自有app。

| 模組 | 責任 |
| --- | --- |
| `scripts/cpu_worker_profiles.py` | 產生24／5依賴閉包，核對核心依賴範圍、父鎖及97／30份原notice或metadata |
| `packaging/profiles/cpu-windows-*.txt` | 兩份pip require-hashes獨立清單 |
| `scripts/run_windows_cpu_ci.py` | 真Windows x64 Python3.12門檻、兩個環境、PyInstaller／ZIP、原始步驟日誌及公開短摘要 |
| `scripts/check_cpu_worker_acceptance.py` | 真frozen健康／推論／隔離／取消／RAM／租約／移除及Windows EOF退出；Linux仍為原10項 |
| `src/desktop_app/component_workers/server.py` | 持有worker共享鎖後，先初始化Windows原生庫再開始背景reader，保留原RAM准入與期限 |
| `.github/workflows/windows-cpu-validation.yml` | main更新自動Windows2022驗證，只保存七天報告，不上傳worker／ZIP／模型或建立Release |

11項包括：臨時簽章離線匯入、staging與安裝後真CPU健康、受管真OCR租約、壞PNG隔離、後續OCR成功、原生取消不輸出、RAM不足啟動前拒絕、閒置移除、控制端環境不變，以及真正frozen父管道EOF退出72並釋放guard。健康／推論及EOF probe的PATH留空，沿用SystemRoot；三個實際provider皆為CPUExecutionProvider。

前四輪的原生匯入逾時與失敗候選保留：[第一輪](development-records/runs/windows-cpu-attempt1-2026-11-10/README.md)、[第二輪](development-records/runs/windows-cpu-attempt2-2026-11-10/README.md)、[第三輪](development-records/runs/windows-cpu-attempt3-2026-11-10/README.md)、[第四輪](development-records/runs/windows-cpu-attempt4-2026-11-10/README.md)。最後調整初始化順序後通過，沒有把CRT／DLL底層根因宣稱為完全證實。固定公開health樣本才開啟有界stdout／stderr／堆疊診斷；產品不保存文件stderr。

本地新15／相關143項在hash鎖定venv通過，完整本版回歸未執行，0.17.2的611項仍屬舊完整基線。公開原頁與完整短摘要已入專案；完整需登入報告artifact七天未下載，未聲稱永久保存原始native報告。

固定英文樣本僅驗功能；ONNX繁體已知缺口、日韓品質、GPU、無Python／離線乾淨Windows、各profile完整生命週期及最終原生再散布審查仍待。RAM仍為軟性預算。來源維持example.invalid，測試金鑰只在記憶體；沒有正式元件下載來源或Setup交付。C04仍2/4、C11仍2/5、導入7/12、歷史19/25；不能把CPU單一bundle通過當成所有profile完成。

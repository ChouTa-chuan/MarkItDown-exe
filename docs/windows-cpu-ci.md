# Windows CPU 選配元件驗證

2026-11-10，程式 **0.18.0**、架構 **0.4**。本地依賴／控制端檢核已備，真正 Windows 結果另記。

CPU 選配獨立建置與打包；控制端維持沒有 NumPy、Pillow、ONNX、RapidOCR 或 Qt 的環境。兩者各用獨立 venv，由既有 Windows hash 鎖及原始 wheel METADATA 產生依賴閉包，不另外選擇套件版本。

| 模組 | 責任 |
| --- | --- |
| `scripts/cpu_worker_profiles.py` | CPU 建置24套件／控制端5套件；97／30份原notice或metadata對照，驗證核心依賴範圍、父鎖與原文未變 |
| `packaging/profiles/cpu-windows-*.txt` | 兩份可實際以pip require-hashes安裝的獨立清單 |
| `scripts/run_windows_cpu_ci.py` | 真Windows x64 Python3.12門檻，建立兩個隔離環境、PyInstaller、元件ZIP、原始日誌及失敗摘要 |
| `scripts/check_cpu_worker_acceptance.py` | 同一套10項真正frozen推論、健康、取消、RAM、租約與移除檢核，保留平台歸屬 |
| `.github/workflows/windows-cpu-validation.yml` | main更新後自動在Windows2022執行；只保存七天報告，不上傳worker／ZIP／模型或建立Release |

十項範圍：臨時測試簽章的離線匯入、staging及安裝後實際CPU健康、受管OCR租約、壞PNG失敗隔離、後續推論成功、原生工作程序取消且不輸出、RAM不足啟動前拒絕、閒置元件移除、控制端套件環境不變。健康及推論時PATH留空，沿用SystemRoot與其他必要環境；控制端不能預先安裝OCR套件。只有實際frozen子程序及三個CPUExecutionProvider通過才接受。

固定英文樣本只作功能測試。ONNX繁中已知品質缺口、日韓品質、GPU、無Python乾淨Windows、完整各profile安裝生命週期與最終原生再散布審查仍待。來源URL維持example.invalid，測試金鑰只在記憶體；沒有正式選配下載來源或安裝包交付。原授權對照不等於最終再散布核准。

本地新8項與相關136項在鎖定依賴環境正常退出，Windows原生結果須另以實跑確認。[準備與紀錄](development-records/runs/windows-cpu-prep-2026-11-10/README.md)。完整C04仍2/4、C11仍2/5、導入7/12、歷史基線19/25；0.17.2的611項全回歸保留版本歸屬，本輪未冒充已跑完整623項。

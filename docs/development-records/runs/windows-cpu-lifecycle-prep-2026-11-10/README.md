# Windows CPU元件維護準備

2026-11-10（台北），程式0.18.1、架構0.4。前版0.18.0已完成Windows獨立CPU功能11項，本輪增加同版本維護8案，須真正Windows frozen再驗，不把Linux合成ZIP當成原生OCR通過。

新增scripts/cpu_lifecycle_acceptance.py：既有安裝重驗、不相容架構、活躍租約拒絕修復／移除、壞包、publish後取消回復、受管影像損壞與修復／真健康、未知檔案拒刪、移除保留合成文件／設定／快取後重裝。各案後均驗全payload hash、active／READY／交易收尾、原cache與合成資料，失敗保存已完成數與當前情境。臨時簽章金鑰仍只在記憶體，不寫入報告。

新4項採真ZIP／登錄／交易與核心鎖，涵蓋8案以及靜默成功不得計為拒絕、非預期例外不得吞掉、既有證據／合成文件拒覆寫；相關147項鎖定控制venv通過，退出0。初輪及最後一輪原始日誌保存；最後一輪對應source_hashes。本版完整回歸未執行，舊611屬0.17.2。closure只更新source_version，9份依賴鎖／模型／第三方原文不變。

本輪取消是維護fault callback在published後觸發Event，並非程序強制終止、斷電／重啟或跨版本升降級。C04仍2/4、C11仍2/5、導入7/12／歷史19/25；所有profile、乾淨機、人工UI、GPU及ONNX品質門檻仍保留，沒有Setup／Release。

[返回開發紀錄](../../README.md)

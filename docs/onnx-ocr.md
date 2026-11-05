# 實驗性 ONNX OCR

使用 rapidocr-onnxruntime 1.4.4，套件 metadata 宣告 Apache-2.0。套件附 PP-OCRv4 偵測／辨識及方向分類模型，載入前驗證版本與三個模型 SHA-256；無額外 Tesseract 執行檔需求。套件及模型再散布仍須納入完整授權審核。

## 品質界線

保留 Tesseract 為預設，ONNX 是手動選用的實驗性後端。乾淨英文掃描可用，但繁體中文合成樣本出現「會議紀錄」漏字及「換」字形錯誤；嚴格測試保留為 expectedFailure，與功能通過數分開呈現。不能用推論成功取代準確度驗收。

ocr-quality-sample.json 保存合成樣本對照及編輯距離／字元錯誤率，僅適用該張樣本，不是整體辨識率。scripts/evaluate_ocr_sample.py 可重現。分數低時提醒，但高分也不保證文字正確。

已知品質預期失敗使用 tests/fixtures/ocr-traditional-meeting.png 固定 NotoSansCJK-Bold 72px 影像，另有正常通過的 SHA-256／參考文字檢查。這避免 Windows 測試字型不同，意外改變同一品質目標；不代表缺口已修復。

## CPU／CUDA

桌面可選 ONNX 後端與 CPU 執行緒，CLI 支援 --ocr-backend onnx --device cpu。預設套件使用 CPU runtime；本環境只有 CPU，CUDA 選項仍不在桌面開放。程式中的 CUDA 路徑是待實機驗證的候選實作。

CUDA 需可查詢的單張 NVIDIA 卡、CUDAExecutionProvider、足夠可用 VRAM（預算另加 128 MiB 保留）。三個 session 分攤 gpu_mem_limit arena 預算，驗證各自第一個 provider 為 CUDA 並停用隱藏回退。本頁推論完成後才回報 CUDA 優先；部分算子仍可能由 CPU 執行。

CUDA arena 預算不是整張卡硬上限，不涵蓋所有函式庫配置。GPU 初始化、驅動、VRAM 峰值、OOM 及加速效果都仍需硬體實測。CPU／GPU runtime 不應混裝於同一環境；目前鎖定檔是 CPU 版本，未提供經驗證的 GPU 安裝鎖定檔，不可直接把候選路徑當成 GPU 安裝指南。

自動模式無 CUDA 准入就使用 CPU 並說明。初始化或推論失敗會釋放 session，在父程序 RAM checkpoint 通過後建立 CPU 後端；推論本頁最多回退重試一次。明確 --device gpu 失敗時報錯，不靜默改 CPU。取消不觸發回退。這些分支以模擬測試驗證，不是 GPU 實機測試。

## 設定與限制

schema v5 支援 OCR 後端及 VRAM arena 預算，讀取 v1–v4；CLI --vram-budget-mib 可覆寫。ONNX 任務預留較高的 RAM 估算，逐頁／推論前後仍透過父程序回壓。原生模型推論期間不能立即暫停；GPU 模型載入也不是硬性記憶體保證。

# 運算裝置與 CPU 資源

桌面提供自動／CPU，GPU 選項仍停用待硬體驗證。預設 Tesseract 只用 CPU；實驗性 ONNX 後端已能用 CPU 辨識，不需外部 Tesseract，但繁體品質未達標，不自動取代預設引擎。

ONNX 的候選 CUDA 路徑會查詢單張 NVIDIA 卡與可用顯示記憶體、建立三個 session 並驗證 provider，推論完成才回報 CUDA 優先。CLI 可指定 --ocr-backend onnx --device gpu 供受控驗證；目前 CPU 鎖定環境不能據此使用 GPU，尚無經驗證的 CUDA 安裝流程。詳見 onnx-ocr.md。

「裝置診斷」背景查詢 nvidia-smi 的名稱、UUID、總量／可用顯示記憶體及驅動，逾時五秒；失敗標未知，不代表其他廠牌硬體不存在。ONNX provider 清單是套件能力，不代表推論成功。本環境無觀測到 NVIDIA 卡，未執行 GPU 推論。

## 資源與回退

CPU 執行緒上限 1–256，預設一個，僅套用背景程序的 OpenMP／BLAS 與 Tesseract，不是整機 CPU 百分比硬限。ONNX 明確設定 intra／inter-op 執行緒；父程序與其他應用不受改寫。

ONNX 的 VRAM arena 預算由三個 CUDA session 分攤，不是整張卡硬限；准入另保留 128 MiB。自動模式 GPU 失敗會先釋放 session，再等待父程序 RAM checkpoint 後建立 CPU；明確 GPU 模式不靜默回退。推論回退最多一次，取消不回退。分支測試是模擬，不是 GPU 實機驗證。

設定 schema v5 保存裝置、CPU、OCR 後端及 VRAM 配置預算，讀取 v1–v4 並保留既有值，明確儲存前不改舊檔。Windows、GPU 真實峰值、OOM 與加速成效仍待實測。

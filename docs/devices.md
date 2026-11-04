# 運算裝置與 CPU 資源設定

桌面提供「自動／CPU／GPU」選項，目前 GPU 項目停用，因現有 Tesseract 只支援 CPU。自動模式明確顯示實際採用 CPU；CLI 可指定 --device。若明確要求 GPU 執行 PDF 精準流程，會在派送前失敗並說明原因，不假裝已加速或靜默改用 CPU。Office／文字的原生解析仍使用 CPU，會指出此步驟不使用 GPU。

「裝置診斷」使用背景執行緒查詢 nvidia-smi，顯示名稱、UUID、總量／當下可用顯示記憶體與驅動。命令逾時五秒，失敗標為未知；找不到工具不代表不存在其他廠牌顯卡。

ONNX provider 清單只表示套件提供的候選後端，不代表 CUDA 相依、特定模型或實際推論成功。此環境沒有觀測到 NVIDIA 卡，只有 AzureExecutionProvider／CPUExecutionProvider，未執行任何 GPU 推論，不列為顯卡支援驗收。

## CPU 執行緒

可設定 1–256，預設一個。每項任務在獨立工作程序設定 OMP_THREAD_LIMIT、OMP_NUM_THREADS、OPENBLAS_NUM_THREADS 與 MKL_NUM_THREADS，Tesseract 繼承上限；不更改父程序或其他程式環境。

這是支援這些設定的原生套件執行緒上限，不是整機 CPU 百分比硬上限，部分函式庫仍可能建立其他執行緒。RAM 預算與 CPU 設定互相獨立，現有低優先權策略保留。

schema v3 保存裝置及執行緒數，可讀取 v1／v2，保留既有 RAM 及 OCR 路徑。CLI --cpu-threads 可覆寫設定檔。明確儲存前不改寫舊設定。

## 待完成

需選定及整合真正支援 GPU 的模型後端、驗證 CUDA session 與模型輸出，再開放 GPU 選項。還需顯示記憶體預算、OOM 診斷、回退前 RAM 准入及真實 CPU／GPU 品質與效能比較。偵測到硬體或套件 provider 不能取代這些驗證。

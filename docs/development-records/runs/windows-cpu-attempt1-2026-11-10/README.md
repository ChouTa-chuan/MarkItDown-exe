# Windows CPU第一輪原生驗證

2026-11-10，程式0.18.0、架構0.4。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42783448673)（c2af2a7）已真正編譯獨立CPU包、產生元件ZIP並建立精簡控制端；但staging健康未通過，checks_passed=0，整輪不接受。

目前公開摘要僅得到LifecycleError「元件健康檢查未通過」，還不足以判定是loader、協定、原生推論或其他原因。產品WorkerRunner原本會排空而不保存可能含文件內容的stderr，因此這次只在固定公開health fixture的驗收CLI加有界4096 bytes擷取，原位元組照常返回排空執行緒，產品隱私／錯誤處理與健康門檻不改；健康觀察隨時寫入，失敗末行含實際binding訊息與fixture摘要。

新增2項確認診斷不改排空內容、上限與拒絕覆寫；相關138項在鎖定環境通過。這是診斷能力，不代表Windows原因已修復；下一輪仍須真正建置與跑原10項。完整621回歸未執行，原611仍屬0.17.2。C04 2/4、C11 2/5、導入7/12保留，沒有ZIP／Setup／Release發行；完整需登入CI artifact未下載。

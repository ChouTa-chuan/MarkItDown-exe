# Windows CPU第四輪：調整原生初始化順序

2026-11-10，程式0.18.0。[真正Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42788897192)（06543cf）完成建置，但ReadFile候選仍在ORT原生匯入逾時，checks0，不接受。公開短摘要與原頁保存；完整需登入artifact未下載。這輪證據否定先前候選已解決問題，不能宣稱已證實CRT鎖是根因。

下一候選移除該ReadFile實作，恢復raw stdin；持有worker自己的共享鎖後、啟動背景reader前，先初始化Windows原生套件。模型驗證與推論仍在收到有效工作後，父程序原有RAM准入與握手／總期限保留。固定公開health樣本診斷提前至7秒，以便取得握手10秒內的堆疊；產品仍不保存文件stderr。

新增3項涵蓋初始化時鎖與reader順序、精簡非frozen來源不假裝具OCR、真來源子程序EOF退出72及鎖釋放。移除失敗候選的6項專用測試；目前新15／相關143項鎖定venv正常退出，完整626未執行。另在真正Windows frozen驗收加入父管道EOF退出／鎖釋放，該平台預期11項，須下一輪結果確認。Linux來源EOF不是Windows實測。

C04仍2/4、C11仍2/5、導入7/12、歷史19/25；未通過的原生實跑不提高進度，品質／GPU／乾淨機與正式發行仍待。

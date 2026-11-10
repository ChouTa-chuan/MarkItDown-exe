# Windows CPU第三輪：原生匯入阻塞定位

2026-11-10，程式0.18.0。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42786526237)（eb3ed8f）編譯成功，健康仍逾時、checks0。公開短摘要確定已收到hello並到loading；45秒Python堆疊停在onnxruntime _pybind_state的原生匯入，尚未完成ready／推論。

依source可知背景執行緒此時以CRT讀stdin控制管道；候選修正讓Windows直接從借用的stdin HANDLE做ReadFile，避免在native loader初始化時持有CRT fd讀鎖。保留原reader並行處理、EOF退出72／共享鎖、pause／cancel與所有120秒期限，Linux仍走原raw FileIO。此為實測定位後的候選修正，須下一輪Windows結果確認；沒有以猜測宣稱底層DLL根因已證實。

新6項驗分段／合併UTF8與CRLF、超限／EOF截斷、非法讀取、Win32 API測試double不走CRT及真正非OCR子程序EOF退出／鎖釋放；相關146項鎖定venv通過。這不是Linux執行Win32 API成功，完整629未執行。固定公開fixture堆疊診斷仍是可選，產品控制端不保存文件stderr。

另保存固定1.31.1版本的官方參考來源：https://raw.githubusercontent.com/microsoft/onnxruntime/v1.31.1/onnxruntime/python/onnxruntime_pybind_state.cc 與 onnxruntime_pybind_module.cc；原bytes含MIT header。這兩份來源未找到直接_setmode呼叫，不把它當已證實原因，也不宣稱wheel binary精確建自該tag；只是native module初始化的參考，未修改vendor或第三方原文。

C04 2/4、C11 2/5、導入7/12／歷史19/25保持；健康未接受。需登入完整artifact未下載，未發行產品。

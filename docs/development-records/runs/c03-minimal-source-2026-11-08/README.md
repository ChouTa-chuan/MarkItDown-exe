# C03 最小原生來源準備開發紀錄

日期：2026-11-08（台北）。程式 **0.12.0**、架構 **0.4**。完成固定最小原生來源／必要相依與原授權文字準備，C03 **2/4**；完整導入仍 **7/12**、既有 **19/25**，C04 2/4、C09 3/4。沒有 Windows 執行或完整基本包驗收。

最終真實候選由固定四項原始碼與具官方發布 digest 的 LLVM-MinGW，從新目錄完全離線交叉建置。入口 **5,366,272 bytes**，SHA-256 `7d64177250b42f37fd3f8cf80ae440081a3e675e38d21e8932271dad7fb37342`，AMD64 PE32+；沒有第三方 DLL 靜態相依，仍需要 Windows 系統／UCRT。此 hash 記錄當次實際產物，未宣稱跨主機逐位元組重建一致。

| 保存內容 | 實際範圍 |
| --- | --- |
| [acceptance.json](acceptance.json)／[日誌](acceptance.log) | 86/86：22 項新來源／解包／linker／PE／設定反例，加原 native、profile、診斷與授權 64 項 |
| [full-regression.log](full-regression.log) | 全專案 500 項：499 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過 |
| [build-report.json](build-report.json)／[driver](build-driver.log)／[cross-build](cross-build/) | 最終新目錄、無人工介入的離線交叉建置；12 個 configure／build／install 日誌、strip、命令、工具鏈設定、實際 header／cache／link map |
| [actual-source.json](actual-source.json)／[日誌](actual-source.log)／[檢查程式](actual-source-check.py.txt) | 8/8 獨立真實來源／靜態檢查；四份 source＋工具 archive、PE、實際標頭、26 linker 輸入、21 份原文／來源文字、objdump、大小寫 import 別名、封裝阻擋 |
| [objdump.log](objdump.log) | 系統 objdump 的原始 PE 解析；14 個 import DLL 名稱與自有 parser 一致，沒有執行 EXE |
| [source-pages](source-pages/)／[host-tools](host-tools/) | 官方頁面、tag／commit、來源封存 SHA／bytes、工具官方 digest、wheel hash、下載／安裝／編譯器版本；皆為開發主機工具來源，非產品依賴 |
| [上游建置背景](upstream-context/) | 固定 Tesseract 提交的 nsis/build.sh 與 workflow；顯示舊 installer 為即時未鎖版 MSYS2，未觸發該 workflow |
| [prototype-failures](prototype-failures/) | 真正原型失敗：新 zlib 名稱、僅編 archive 的函式誤判、Windows TIFF try_run、libc++ 標頭與 Winsock 大小寫；修正寫入 recipe，沒有修改上游檔案 |
| [intermediate](intermediate/) | 初始 20 項／84 項／498 全回歸、原型 PE 手動補 Winsock 別名的中間建置、GNU trace 不支援及 verbose 成功、member／libpng 別名驗證失敗；不可當成最終成功或同一次測試 |
| license／upstream／profile verify 日誌 | 原 221 份授權、vendor／公開 PDF 與七份固定依賴鎖定不變；非 Windows 執行證據 |
| progress-browser.log／screenshots | 更新後里程碑／模組／元件分頁、手機、鍵盤與計數；沒有 Windows GUI 驗收 |
| integrity.json／manifest.json | 舊資料保存與本目錄逐檔 bytes／SHA-256 |

原授權與來源文字 21 份的固定位置為[最小原生 notices](../../../../packaging/native/minimal-notices/)，[來源契約](../../../../packaging/native/minimal-windows.json)逐檔記錄 hash；不重複放另一份可漂移清單。Tesseract／Leptonica／libpng／zlib 靜態庫及 LLVM／MinGW runtime／系統 import archives 共 26 個 linker 輸入已追溯，selected member 記錄也綁定原 archive。Leptonica 的 .dll 名稱實際是 ar 靜態庫；libpng 安裝別名和 Winsock 大小寫 import 別名都以實際 bytes 核對。

來源準備完成不等於核准再散布。`redistribution_approved`、`release_ready`、`native_ocr_bundled`、`windows_executed` 維持 false；舊候選 32 DLL 證據缺口及阻擋完整保留。沒有執行 Windows PE／OCR、驗中文路徑、整合四語模型到主 profile、建立 frozen／安裝包、GPU、tag／Release 或手動發行。

EXE／DLL／archive／object／wheel／模型、venv、快取與使用者文件均未入庫；保存公開文字、檢查程式文字、原始日誌與進度截圖。原品質影像／目標、舊圖與紀錄固定。下一步接四語基本包／離線設定與完整自檢，再在 Windows 實際建置及乾淨機驗收。

保存前的暫存區檢查發現，既有 `.gitignore` 的 `build/` 規則略過了本輪同名原始建置紀錄；改名為 `cross-build/` 後重建 manifest，並逐檔核對 Git 暫存內容。未提交缺少建置證據的版本。

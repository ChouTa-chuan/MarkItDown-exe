# 決策 0005：以固定最小原生來源取代未齊 DLL 證據的基本包候選

日期：2026-11-08（台北）。程式 0.12.0，架構 0.4。來源準備子檢核完成；Windows 執行與完整基本包未驗。

官方 installer 建置採未鎖版 MSYS2 套件，現存 32 DLL 的精確來源／原文證據仍未齊，維持原阻擋。基本 PDF OCR 的固定輸入是頁面 PNG，因此從固定 Tesseract、Leptonica、libpng、zlib 原始碼建立最小靜態 Windows 候選，減少整包依賴。

保留原始碼封存 hash、工具鏈發布 digest、runtime 原文／來源與真實 linker 輸入，使用隔離目錄離線交叉建置。Windows PE 沒有第三方 DLL 靜態相依；來源／原文準備與 Windows OCR、完整四語包、產品再散布各自保留證據門檻。舊 installer 契約不放寬，不因替代方案讓舊 DLL 缺口自動通過。

C03 來源準備為第二項，C03 2/4、C04 2/4、C09 3/4，完整導入仍 7/12。沒有把 Linux 交叉建置列為 Windows 執行通過，也沒有選擇或變更主程式公開授權。[建置契約與限制](../minimal-native-build.md)。

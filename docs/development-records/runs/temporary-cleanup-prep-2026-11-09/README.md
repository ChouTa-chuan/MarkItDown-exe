# 中斷測試暫存清理準備

2026-11-09（台北），程式 **0.17.2**、架構 **0.4**。新增可拋棄 Windows CI 對自身中斷產物的記憶體收據與原檔 handle 清理；本目錄只列準備狀態，Windows新機制必須另實跑。

- 14項本地清理契約涵蓋既有／未知／受管同名保護、改內容／同bytes替換、硬連結／symlink、不同root／重複／外部JSON收據、程序忙碌、第二檔失敗不先刪第一檔及預檢後替換；Windows刪除API沒有在Linux執行。安裝相關39項也通過。
- 全611項：610通過、1既有ONNX繁中品質預期失敗、0跳過，混合程序exit0，36個模組全部exit0。完整log與JSON保留；新版GUI生命週期回歸仍通過，RAM仍為軟性預算。
- Windows CI將真正重跑基本包、安裝／修復／移除、0.16→0.17.2跨版及三停點續修，每案app10項之後移除，再清自身精確收據。新增實際開檔鎖拒絕及未知同名／同bytes合成文件保留控制；至少清理1份真產物才可接受，不能把空集合當成功。
- 普通Setup沒有新增讀取外部收據或通配清理入口；這是控制端只清自己的CI產物。`temporary_cleanup_complete` 若後續為true，僅指 `ci-owned-fault-installer-artifacts`，不表示一般使用者完整安裝生命週期、斷電、全profile或正式發行已通過。

另保存前版0.17.1已完成的[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42594462484)公開原頁及完整短摘要：source c5f0c01，基本包／安裝後app各10、安裝6、跨版11、續修3案各10已接受，仍保留1份Inno暫存、cleanup=false。它是基線，不能作0.17.2新清理驗收。

[模組與邊界](../../../temporary-cleanup-ci.md)。完整C11仍2/5、導入7/12、歷史19/25；無Python乾淨機、人工UI、GPU、一般Setup暫存政策及ONNX品質另驗。沒有Setup／tag／Release。完整需登入CI artifacts未下載，不宣稱已保存。

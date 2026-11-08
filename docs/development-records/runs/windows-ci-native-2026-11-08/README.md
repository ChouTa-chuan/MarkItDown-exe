# Windows 原生建置、四語自檢與中文搬移修正

2026-11-08（台北），程式 0.14.0、架構 0.4。CI #2 的 Windows 依賴／本地專案安裝通過，固定 profile／lock 步驟失敗；原摘要被約 5 KB 截斷，不能據片段認定底層具體錯誤。換行保護後，實際 [CI #3](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42473518203) 已在 Windows 2022／Python 3.12.10 原生建置基本包，core 與完整四語健康／四份掃描 PDF 自檢通過；搬移中文空格路徑後，原生 --list-langs return 1，整體驗收仍失敗。

保存公開原頁、被截斷片段、完整可解碼的 windows-build JSON 與逐欄確定的 acceptance 觀察；不把不完整 JSON 補造為完整報告。失敗的 Windows 中文搬移是這次修正觸發條件。新摘要限制至公開頁門檻內，優先列真正失敗步驟，完整內容仍在原 artifact／summary。

第一方 windows-utf8.manifest 宣告 activeCodePage=UTF-8／asInvoker，在固定上游 CMake 之外以 RC／deferred target_sources 加到原生 EXE；四份上游 source／工具鏈／原文契約不變、不修改上游，也不改使用者系統地區。activeCodePage 需要 Windows 10 1903 以後（本 CI Windows 2022）。新 CI receipt 必須對應目前 manifest hash，預設歷史候選路徑保留。

本地真正重新 cross-build 完成，llvm-readobj 證明 RT_MANIFEST 24／ID 1、769 bytes，候選包含完整 XML；無第三方 DLL。新的四語 payload 組裝成功。第一次工具路徑填錯，錯誤 JSON 分存；重建後原 report 將 resource object 列入 Tesseract target，另以更正後的實際 linker 審核清楚分為 first-party-windows-manifest（原 report 固定、不重寫）。正式新 CI 會直接以新分類重建。

本地新增總數相對 0.13.0 為 25 項，相關 138/138；完整 552：551 通過、1 既有 ONNX 繁體品質預期失敗。UTF-8 候選目前僅 Linux cross-build／靜態，仍待新 Windows CI。C03 3/4、C04 2/4、C09 3/4、完整 7/12、既有 19/25 保留；沒有乾淨機、Setup、人工 UI、GPU 或發行驗收。引擎／模型／工具 archive／venv 不加入 Git。

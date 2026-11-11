# 隨包原文與原生來源追溯

2026-11-11，程式0.19.1、架構0.4。基本包及CPU建置新增實際PyInstaller原文、原生Analysis來源SHA-256／大小與可確認的distribution版號，原文不改寫。隨包檢查驗原文hash、METADATA版號及每個Analysis原生檔案存在性，來源與收集後指紋分列，不把經PyInstaller處理的binary冒稱位元相同。CPU套件表是build來源，不是最終runtime SBOM。

完整661項：660通過、1既有ONNX繁中品質預期失敗、0跳過；混合正常exit0，42個獨立模組均exit0。來源70f03f0，完整driver／stdout／退出與逐模組JSON另存。原固定55套件、四語／三ONNX模型、字型與Tesseract環境沿用[前次完整回歸指紋](../full-regression-0.19.1-2026-11-11/README.md)，未更新依賴。修正前660完整回歸另存pre-fix-regression，不冒稱最新來源。

首輪CPU42970949614在新增檢核拒絕Windows Analysis的反斜線，原頁與完整公開錯誤保留；基本包42970949611在後續提交觸發後取消，不算通過或失敗。修正清單產生器統一POSIX路徑，安全路徑檢查不放寬，新16項／相關65通過。首輪本地fixture錯誤與準備紀錄[原樣保留](../bundle-provenance-2026-11-11/README.md)。

[修正後Windows CPU42971219072](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42971219072)及[基本包42971218861](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42971218861)均Success，來源70f03f0。CPU公開root直接記錄provenance_accepted=true，功能11／同版8／跨版8／程序恢復6接受；基本包root overall_accepted=true，必要追溯子程序已正常退出，app10／安裝6／跨版11／續修3案接受。基本包摘要未單獨公開詳細追溯報告，依固定來源管線的必要步驟及最終接受判定，不補造套件／binary筆數或報告hash。原始完整CI報告保留七天；既有GitHub CLI API讀取回覆Forbidden，因此本紀錄保存公開頁／註記，不宣稱已永久下載登入報告。尚無Setup交付、tag或Release。

52份既有run manifest／2801筆hash核對通過，相對fa792b0的舊紀錄、原文／模型／9鎖／vendor及28圖均未改。技術追溯不等於再散布核准，完整候選清單、應用授權、Qt／Microsoft原生再散布及乾淨機／人工／GPU仍待；C04 2/4、C11 2/5、導入7/12保持。

[返回開發紀錄](../../README.md)

monitor.log為初版暫存監測器的空比對結果（run ID數字／字串不一致），已停止並修正；有效狀態見monitor-corrected.log及windows-run-status.json。公開頁補存時使用原生工作最終job ID。這些是紀錄工具問題，不列產品測試失敗。

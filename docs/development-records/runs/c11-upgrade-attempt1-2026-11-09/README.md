# 跨版 CI 第一次實測：Inno Script 編譯錯誤

2026-11-09（台北），程式0.16.0。公開run 42554509169，source 4e7057808fef921ea0b221d20706cac23aa69b10。原生輸入準備成功；Windows基本資料夾10/10已通過。安裝器在編譯時失敗，公開摘要保留真正compiler尾段：ExcludeTrailingBackslash不是Inno Script公開函式，尚未產生或執行新Setup，跨版安裝也未開始。這次不是升級／回復驗收通過，C11保持1/4、完整7/12。

修正只將父鏈走訪改用Inno官方函式RemoveBackslashUnlessRoot，根目錄保留、逐父層reparse檢查責任不變。API由官方issrc固定31ee6e35383c530cca8f047216045d3f61ca8be1之Projects/Src/Shared.ScriptFunc.pas宣告確認；不是假設Delphi所有函式均可在Inno Script呼叫。原25份架構圖與準備紀錄固定，下一次真正Windows結果另存，不覆寫失敗。完整登入artifact未下載、只在CI七天保留；無Setup發行。

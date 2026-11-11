# 首輪Windows恢復接受與公開摘要長度調整

2026-11-11（台北），程式0.19.1。Windows run42941852540／fc31d81的公開root接受true、功能11、同版8、跨版8，以及recovery接受true／Windows true／六案均直接見原始註記；driver僅在六案真frozen與環境檢查通過後才設root accepted。

GitHub公開註記在4096字元截斷，最後兩案明細及尾端全域欄位未完整顯示，完整JSON無法解析。此目錄保存原頁、未補字的4096字元prefix、可直接讀到的欄位與collector JSONDecodeError；不猜補缺少欄位、不稱永久保存完整原始報告。

新增public_summary：只壓縮公開副本，保留各驗收接受／計數／scope旗標及六案PID／exitcode／恢復後版號／frozen；完整cpu-build.json不改。新1項測最大Windows PID下完整JSON小於4000 bytes、原完整資料不變，以及長Unicode錯誤也須保留完整拒絕JSON。新增6／相關162項通過，原初輪負例失敗與161項準備紀錄不改。

將在既有Windows CI重跑驗證完整公開摘要。原生恢復程式與條件未變，C04 2/4、C11 2/5、導入7/12保持；本版完整回歸未跑，原生完整artifact七天未下載，無產品發行。

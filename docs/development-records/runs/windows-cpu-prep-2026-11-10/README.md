# Windows CPU 選配建置準備

2026-11-10（台北），程式0.18.0、架構0.4。新環境已連線，從已同步3e1d3d2接續，沒有重新套用或發布環境設定。

新增Windows CPU獨立profile：建置24套件、控制端5套件，各有97／30份原notice或METADATA hash對照。沿用原Windows父鎖與保存的wheel metadata，額外核對實際核心依賴範圍，不重新挑版。新增獨立Windows2022 CI，兩個venv、真正frozen worker、簽章離線匯入與10項原生驗收；只傳報告，模型／ZIP／EXE不入Git或Release。

新8項含範圍／hash／原文／父版號／核心依賴範圍／假發行／平台拒絕／child失敗不得冒充成功；相關136項（元件、生命週期、IPC、基礎與CPU profile）在獨立venv使用鎖定依賴全過，0跳過、正常退出。`related-tests.log` 是系統環境134項初驗（cryptography50.0.0）；`related-tests-locked.log` 才是最終136項（cryptography50.0.2）。第一輪沙箱pip連不到proxy的原始失敗保留，外層沿用proxy／CA及hash鎖後成功，不以此改網路設定。

此紀錄只列準備。真正Windows／四語或GPU品質不因本地測試而完成；ONNX繁中品質缺口保留，健康僅固定英文功能樣本。正式來源仍example.invalid、測試金鑰只在記憶體，RAM仍軟性預算。完整C04 2/4、C11 2/5、導入7/12／歷史19/25不提高。完整619項尚未執行；0.17.2全611項仍按原版保留，沒有改成0.18的完整回歸。

[模組與驗收範圍](../../../windows-cpu-ci.md)。Windows結果另存，不倒填此準備紀錄。

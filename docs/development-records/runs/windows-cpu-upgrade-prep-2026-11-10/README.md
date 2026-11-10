# CPU元件跨版本準備

2026-11-10（台北），程式0.19.0、架構0.4。CPU元件由1.0.0更新為1.0.1，協定維持1.0.0。控制端只接受明確列出的1.0.0／1.0.1；binding把租約描述的精確版號傳入runner，握手與結果均須相符，未知同major版也拒絕。

新增Windows跨版8案：安裝舊版並OCR、publish後取消升級保留舊版OCR、升級執行新版並記錄前版、固定舊版請求在新active時於健康前拒絕、明確回復執行舊worker、明確切回新版、移除舊版清除回復入口、移除新版保留合成文件與兩份快取。

CI另checkout固定fd69854ee19ba031362750072e22a92bf5463a7c（0.18.1／CPU1.0.0），檢查HEAD與工作區乾淨；前版與新版各用獨立build venv、原hash鎖與各自source／spec／packager真正建置，再由無OCR控制端呼叫。不能改描述、複製同個EXE或把合成ZIP當原生跨版。

新增9項：精確握手／binding傳值、未知版本拒絕、真子程序舊新選擇、握手後結果換版拒絕、舊來源dirty／錯誤SHA、Linux不得冒充Windows、真ZIP八案及錯誤回復部分失敗保存。相關156項鎖定venv通過，兩輪原始日誌保存；最後一輪對應source_hashes。本版完整回歸未跑，0.17.2的611仍為歷史完整基線。Windows跨版尚待實跑，交易案本地通過只標transaction_checks_accepted，accepted與windows_executed維持false。

closure只改來源版號；9份鎖、模型／第三方原文不改。C04仍2/4、C11仍2/5、導入7/12／歷史19/25；其他profile、強制中斷／斷電、乾淨機／人工／GPU與ONNX品質／RAM限制保留，無Setup／tag／Release。

[返回開發紀錄](../../README.md)

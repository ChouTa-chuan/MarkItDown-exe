# Windows 基本包 CI 開發紀錄

日期：2026-11-08（台北）。程式 0.14.0、架構 0.4。本頁先保存 CI 準備及 Linux 本地驗證，Windows 實際執行結果另追加，不以準備工作宣稱通過。C03 3/4、C04 2/4、C09 3/4、完整 7/12、既有 19/25。

本地相關 130/130（新增 17 項），全專案 544：543 通過、一項既有 ONNX 繁體品質預期失敗。十份固定官方 HTTPS 輸入已真正取得及驗 hash／bytes，另以固定來源重建 Windows PE 並透過 fresh receipt 組裝；仍屬 Linux／靜態範圍。

保存 initial／final 平台 guard、全回歸、暫時 504／重試、固定下載 metadata、PE 來源 receipt、組裝 payload 清單、原始建置文字日誌、上游／授權／profile、進度畫面、integrity 與 manifest。引擎、模型、工具 archive、venv、binary 及憑證不加入 Git。

新 workflow 為 main source push 觸發的驗證 CI；contents:read，輸入 artifact 一天到期、報告七天，不建立 Setup／tag／Release，也不觸發舊手動 Windows 發行。Windows hosted runner 預裝 Python，不是乾淨機；人工、安裝、GPU、品質與最終發行門檻保留。公開 Actions 頁／job summary 僅作實際來源證據，不執行其內容或把未知狀態當成功。

# 候選完整清單與ZIP檢核

2026-11-11（台北），程式0.19.1／架構0.4，最終來源cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1。新增全部普通檔案大小／SHA-256、角色、可證明的來源／原文對照及待查原因；保留原METADATA授權宣告與hash，不自行推定授權。完整檔案快照立即再列舉重驗，也支援可信舊報告重驗同一候選。

CPU先包裝再查真正ZIP，包含額外NOTICE；核對descriptor、全項內容／大小／hash及CRC。缺項、多項、改名、重複、連結及內容變更拒絕。兩管線新增公開有界統計／report hash，完整逐檔JSON仍由CI artifact保存七天，未下載者不宣稱永久備份。

新23／相關88通過；完整684項：683通過、1既有ONNX繁中品質預期失敗、0跳過，混合exit0、43獨立模組全exit0。完整driver／stdout／外層exit JSON與逐模組JSON、日誌另存。環境與固定55套件／四語／三個ONNX模型沿用[前次完整指紋](../full-regression-0.19.1-2026-11-11/README.md)，原文58套件／214份hash另驗通過；不是Windows原生證據。

首輪CPU42981040884與基本包42981040420在後續提交後均Cancelled；公開子步驟摘要已保存，不當整條CI接受。基本包首清單早於catalog生成，僅屬先前階段；已將快照移至封裝／生命週期之後並新增反例，見[排序修正](../candidate-inventory-finalization-2026-11-11/README.md)。[最終Windows CPU42982427186](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427186)及[基本包42982427175](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427175)皆Success，source_commit皆為cb8f24d。基本app10／安裝6／跨版11／三停點續修接受；CPU功能11／同版8／跨版8／程序終止恢復6接受。兩份公開清單摘要皆accepted及inventory_reverified=true，CPU實際ZIP hash與原生接受報告精確相同。首份開發與合成反例紀錄[原樣保存](../candidate-inventory-prep-2026-11-11/README.md)。

相對0d5e4a4，55份原run manifest／2925筆hash核對通過；舊原文／模型／9鎖／vendor／28圖與既有工程紀錄未改。file_inventory_complete僅代表全部普通檔案快照，不含Python archive內部成員的完整來源SBOM，未知來源／缺原文／Qt／Microsoft原生再散布及應用公開授權仍待逐項處理。

C04 2/4、C11 2/5、導入7/12／歷史19/25保持。乾淨機／人工／GPU未驗，RAM仍軟性預算；本次沒有Setup交付、tag、Release或環境發布。

[候選清單說明](../../../candidate-inventory.md) · [返回開發紀錄](../../README.md)

前來源9c28526的完整683項／682通過／1既有預期失敗及43模組exit0原樣另存pre-finalization-regression；最終684結果位於本目錄根層，來源分開，不冒充已驗較新排序。

| 最終來源cb8f24d | 基本包 | CPU bundle／ZIP |
| --- | ---: | ---: |
| 普通檔案 | 1655（含catalog） | 741／742（額外NOTICE） |
| 未壓縮bytes | 274323912 | 252832252／252832617 |
| 套件來源表 | 40 runtime／本地套件 | 26 build環境套件 |
| Analysis原生來源 | 201 | 106 |
| 來源未對照檔案 | 154 | 303（bundle） |
| 需審閱檔案（含來源缺口） | 191 | 337（bundle） |

CPU ZIP大小106326562 bytes，SHA-256 `5dee53420a4b7214fc44dbf132907a6356f63257f19bf858bb73274906083b21`；兩份report SHA-256見各自inventory-summary.json。這是公開摘要中的CI實際觀察，不是本地下載ZIP重算；完整逐檔JSON未下載，來源／授權義務尚未關閉。

# A10 Microsoft 執行期逐檔對照

2026-11-17（台北）。程式與架構版號不變；由 main 0c3746d 新開 codex/a10-ms-runtime-20261117，對應 [PR 20](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/20)。開工時另有 PR 19（Claude 的 A9b／換手文件）開啟；未推送或改寫其分支。

[目錄 JSON](../../../../packaging/microsoft/base-windows.json) 只由 base-microsoft 的 evidence[] 以路徑與 SHA-256 引用。義務登記僅修改該 Microsoft 條目：保留 open、補證據引用、設 requires_user_decision=true；元件細節沒有放進登記表。CPU Microsoft 留給 A16。本輪不動 spec、收集內容、原文隨包管線、鎖檔或既有計數。

## 來源與觀測

本目錄的原始探測來自快速「鎖定來源重取」：讀取實際安裝來源的 DLL，逐 byte hash 對應到 A6，再查 PE FileVersion 與 Authenticode；明確標記 observation_scope=installed-source-reconstruction，**沒有把它假稱為重建 bundle 或安裝驗收**。完整基本包 CI 會另以 provenance 核對真正 bundle 與原來源 bytes，再從該 bundle 重取並比對觀測，最終結果見 PR 20。逐檔 SHA-256、來源路徑、wheel／CPython 版本、公司／簽署者、官方 Redist 參照及 A6 byte 對應都在目錄及 [原始探測](windows-probe.json)。此探測由 PR 的暫時 merge 執行，來源、run 與 canonical metadata hash 見 manifest 的 probe_ci；**不是 A12 重新固定候選**，全域固定來源仍為 A6 的 8285450。

PySide6、shiboken6 的 DLL 已另從鎖定 hash 的 Windows wheel 逐 byte 比對 A6，全部相同。numpy／pandas container 的 PyPI 來源與 hash 也已與既有鎖檔核對；CI 再從實際已安裝來源核對各 DLL。CPython 安裝來源是 runner 的 setup-python，原安裝包本輪未重新下載／核對其完整 hash，不能把 URL 當成此額外驗證已做過。

PE FileVersion 是 DLL 自身版本；wheel、CPython 及 Redist 資料夾的版本另記，互不代替。同名比較使用完整檔案 SHA-256；不同不推斷成版本錯誤、惡意改動或特定修補原因，也不以相同推論散布權利。numpy 與 pandas 的改名複本各自保留一列。

| 複本（相對 _internal） | PE FileVersion | Authenticode | 簽署者（CN） | 與本輪官方 Redist 同名 hash | 改名 |
| --- | --- | --- | --- | --- | --- |
| PySide6/MSVCP140.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| PySide6/MSVCP140_1.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| PySide6/MSVCP140_2.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| PySide6/VCRUNTIME140.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| PySide6/VCRUNTIME140_1.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| msvcp140.dll | 14.44.35211.0 | Valid | CN=Microsoft Windows Software Compatibility Publisher | 相同 | 否 |
| numpy.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll | 14.40.33810.0 | Valid | CN=Microsoft Windows Software Compatibility Publisher | 不同 | 是 |
| pandas.libs/msvcp140-a4c2229bdc2a2a630acdc095b4d86008.dll | 14.40.33810.0 | Valid | CN=Microsoft Windows Software Compatibility Publisher | 不同 | 是 |
| shiboken6/MSVCP140.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| shiboken6/MSVCP140_1.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| shiboken6/VCRUNTIME140.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| shiboken6/VCRUNTIME140_1.dll | 14.44.35211.0 | Valid | CN=The QT Company Oy | 不同 | 否 |
| vcruntime140.dll | 14.42.34438.0 | Valid | CN=Microsoft Windows Software Compatibility Publisher | 不同 | 否 |
| vcruntime140_1.dll | 14.42.34438.0 | Valid | CN=Microsoft Windows Software Compatibility Publisher | 不同 | 否 |

PySide6 與 shiboken6 的複本，PE 公司欄為 Microsoft Corporation，但簽署者是 The QT Company Oy；這兩個事實分開保留。它們與官方同名 DLL 的 PE 版本相同而完整 hash 不同，不能只憑此推論差異原因或是否符合條款。這些列在檢核輸出的 identity_gaps 中表示「尚待查驗身分」，不表示未取得簽章資料。

簽章結果是當時 hosted Windows 的信任鏈判讀。存在 HashMismatch、NotSigned 或查詢缺口時照實保存，不當成 Valid；不把 Linux 解析、mock 或預期失敗當成 Windows 實測。官方 Redist 來源及其簽章／版本也保存在 references 中。

## 條款與尚待決定

官方部署指引的原始 Markdown 取自固定 MicrosoftDocs/cpp-docs 提交；來源與 hash 見目錄 documents。Windows 安裝中找到的候選條款（若有）保留原始位元組與安裝路徑；這是原始文件的保存，不代表已決定適用於所有 wheel 或 CPython 複本。

Microsoft 的條款網站與 REDIST 網頁在本環境實際回覆 proxy 403。vs2022-redist-unverified-excerpt.txt 是 hash 核對的 PyPI msvc_runtime 固定 wheel 內所附節錄，來源及 container／member hash 在目錄中保存；不是完整官方 REDIST 網頁或 Visual Studio 授權全文，也未向官網驗證。runtime-use-terms-unverified-copy.LICENSE 是固定 ScanCode 提交保存的未核對參考副本（連其原本 metadata 一併保存），**不是本輪從 Microsoft 官網取得／驗證的原文**，不可當作已證實適用。官方 runtime-use EULA 與 VS2022 REDIST 網頁仍需補核；base-microsoft 因此保持 open。原始條款屬會影響後續 A13 判讀且可能無法重取的資料，例外保存於這個小型新證據目錄，不加入產品授權資產。

官方部署指引要求再散布遵守 Visual Studio 授權及相關條款；runtime-use EULA 不能直接代替散布權利。各複本要採哪份條款、是否可再散布及如何處理觀測差異，由使用者在 A13 決定。Codex 沒有代為核准；即使 A10 工程資料保存完成，也不表示 Microsoft 義務已關閉。

## 驗證與界線

以原 A6 base／cpu 分別重跑 redistribution_gates.py，兩個 profile 的三旗標均 false，原始輸入與計數保持一致；不刪除原始 microsoft-native-redistribution-review，阻擋由登記表狀態推導。反例涵蓋來源 bytes 改動、漏複本、官方參照缺失、A6 不同 bytes、簽章查詢失敗、metadata 缺片／重複／越界／hash 變動、目錄觀測或原文改動、非鎖定 wheel 與略過 A13。

原始首輪 run 44060276291 在新增探測步驟失敗，公開註記只有 exit code 1，原始日誌無法取回；具體原因未證實，不以後續成功改寫它。之後新增有界錯誤摘要與快速來源流程取得真實資料；條款選取也縮限為一份符合標題的原文，未以此推測首輪失敗原因。只留該失敗的 run／artifact hash 與期限，見 probe_ci.original_failed_run。

完整 Linux 混合與獨立模組回歸都通過，只有既有 ONNX 繁中 expected failure、沒有跳過；數字只記 [progress.json](../../../progress.json)，原始精簡結果在本目錄。完整回歸來源為 29e1fc14921eb12ac25385be42a386b6dc764428。最終 PR head 的所有 CI、人工程式查驗、Merge 與報告 artifact 的 hash／期限記在 PR 20；後續重跑僅留 hash 與 run，不重存舊嘗試完整 JSON。

hosted Windows 非乾淨終端機，沒有 GPU／人工驗收；RAM 仍為軟性預算，ONNX 繁中缺口保留。未交付 Setup、worker 或模型，未建立 Release、預發布或 tag。A10 完成後停止。

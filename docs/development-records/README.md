# 開發紀錄

> **2026-11-13 起本頁不再追加。** 之後每個階段的經過記在 [STATUS.md](../../STATUS.md)，改寫前存檔到 `docs/history/status/`；所有紀錄可由[歷史索引](../history-index.md)查找。以下內容原樣保留。

**2026-11-12｜PR 1 上新CI入口首次執行皆通過**

- [PR 1](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/1)（head cd14fe7）觸發的Linux完整回歸43152427632、Windows基本包43152427580、Windows CPU選配43152427554皆Success。Linux在runner（CPython 3.12.16／Tesseract 5.3.4）為698 run／697 pass／1既有ONNX繁中預期失敗／0 skip，混合與45模組exit0；[報告原檔與說明](runs/pr1-ci-first-run-2026-11-12/README.md)保存。
- PR流程以暫時merge commit執行，Windows結果只證明合併後內容可建置並通過既有自動驗收，不取代cb8f24d的候選證據；兩份Windows報告未下載。7/12、C04 2/4、C11 2/5不變，無產物發布。

**2026-11-12｜新session接手：保存CI完整報告、分類未對照來源、補Linux CI與授權提案**

- 接手時先唯讀查證交接文件：版號、鎖定檔數、里程碑、CI run與證據檔皆相符。發現根目錄沒有LICENSE、Linux回歸不在CI、`THIRD_PARTY_NOTICES`仍稱Tesseract未內含，以及兩份完整報告artifact仍未過期（11-18到期）。
- 下載artifact時先被雲端環境網路政策拒絕（兩個GitHub artifact儲存主機CONNECT 403）；使用者核准加入允許清單後取得三份ZIP，雜湊與GitHub digest及公開摘要`report_sha256`相符，[原檔與核對腳本](runs/ci-full-reports-2026-11-12/README.md)保存。暫時簽章網址未入庫；EXE／模型本體未下載。
- 首次在新容器跑測試只執行653項：缺`libEGL.so.1`使6個Qt測試類別載入失敗、31個方法未執行，缺Tesseract使10項跳過。經使用者同意以apt補libEGL、Tesseract（實得5.3.4，非基線5.5.0）與CJK字型並下載固定四語模型後，[原684項重現](runs/handover-regression-2026-11-12/README.md)；首次輸出一併保存。
- 以[雜湊證據分類](../source-classification.md)基本154／CPU303個未對照檔案，[逐檔結果](runs/source-classification-2026-11-12/README.md)保存。檔名像Microsoft runtime的系統DLL只列candidate；另發現基本包帶有自runner系統路徑收集的OpenSSL，推測由Qt TLS外掛引入、尚未證實。零位元組檔不以雜湊推定來源，同雜湊多路徑時優先列最相近的repo路徑。
- 修正自有`THIRD_PARTY_NOTICES`、提出[授權提案](../license-proposal.md)待確認；新增Linux回歸CI與Windows驗證的PR／手動入口。新增14項測試後[全698項](runs/handover-ci-and-classification-2026-11-12/README.md)混合及45模組exit0。
- 過程中本session對repo的git push曾兩度回403（提示Claude GitHub App存取未連結），提交先留在本機分支；稍後重試成功，分支已推送。新CI流程在PR建立後才會首次於GitHub執行，結果另記。更動打包內容（排除Qt TLS外掛／FFmpeg、改用官方VC runtime來源）與授權決定待使用者同意。7/12、C04 2/4、C11 2/5不變。

**2026-11-12｜建立不依賴聊天紀錄的完整專案交接入口**

- 依使用者需求新增[專案說明與接手指南](../../PROJECT_HANDOFF.md)，從產品目的、已確認需求到程式責任、里程碑、最新證據與限制完整整理；提供新環境啟動／驗證、P0來源明細工作及完成條件，附可直接交給新AI的指令。
- 首頁／AGENTS與舊狀態／建置／架構文件加上入口及時序說明，區分當前HEAD、程式0.19.1與真正驗證來源cb8f24d；C04 2/4、C11 2/5及7/12不提高。
- 此輪是文件整理，核對狀態／數字、範例語法與相對連結，另實跑公開合成文字CLI範例；[交接整理驗證](runs/project-handoff-2026-11-12/README.md)保存。未重跑全功能／Windows／OCR，原始失敗、vendor／原文／模型／hash鎖／28張架構圖與舊run保留。

**2026-11-12｜GitHub Pages固定視覺進度網址已上線**

- 使用者完成來源設定後，[run43133764140](runs/progress-pages-live-2026-11-12/README.md)（bc5d601）建置／部署成功。公開網址https://chouta-chuan.github.io/MarkItDown-exe/ 由GitHub runner實際GET驗HTTP 200，精確SHA-256與目前產生器及前次Chromium互動／手機版HTML相同；公開原頁與驗證JSON已保存，首次未啟用的失敗紀錄不改寫。
- 首頁與[網站說明](../progress-pages.md)更新已上線狀態；進度資料同步main後自動部署，固定網址不變。程式0.19.1／架構0.4、684項功能基線與7/12維持，本次僅驗網站發布，沒有重跑或擴大Windows／GPU等驗收。

**2026-11-11｜準備GitHub Pages固定視覺進度網址**

- 依使用者指示新增[Pages自動部署流程](../../.github/workflows/progress-pages.yml)及[設定說明](../progress-pages.md)。固定網址為https://chouta-chuan.github.io/MarkItDown-exe/，首次部署狀態接續記錄；更新進度後自動發布，頁面重新整理載入最新快照。
- 只部署兩份同內容HTML與.nojekyll；本地建置／互動／手機版檢查通過。[首次run42986578102](runs/progress-pages-2026-11-11/first-deployment/README.md)建置成功、Pages站台Not Found，部署未成功，需管理員先啟用Source為GitHub Actions；原頁／錯誤另存，未當網站已上線。
- 網站更新不改功能里程碑、程式版本或Windows安裝包狀態。

**2026-11-11｜Windows最終候選清單與CPU ZIP接受，完整684項正常退出**

- [最終Windows基本42982427175／CPU42982427186](runs/candidate-inventory-ci-2026-11-11/README.md)同來源cb8f24d皆Success：基本封裝後1655檔（含catalog），CPU bundle741／ZIP742檔（含NOTICE），全檔大小／hash與快照重驗接受；CPU ZIP hash與11項原生接受精確相同。基本app10／安裝6／跨版11／續修三案、CPU功能11／同版8／跨版8／恢復6皆接受。
- 新23／相關88及全684：683通過、1既有ONNX繁中品質預期失敗、0跳過；混合及43獨立模組exit0。前來源683及首輪兩個Cancelled、已接受的清單子步驟原頁另存，不當整條CI接受；發現catalog新增後調整快照時點並補功能反例。
- 公開原頁／完整有界摘要、report hash、回歸原始日誌及視覺紀錄保存；完整逐檔登入artifact未下載、由CI暫存七天。55份既有manifest／2925筆hash、原文／模型／9鎖／vendor／28圖未改；基本154／CPU303個檔案的來源未對照，runtime SBOM／Qt／Microsoft再散布／應用授權仍待。
- 程式0.19.1／架構0.4，更新首頁、中文說明與視覺卡；C04 2/4、C11 2/5及導入7/12保持，乾淨機／人工／GPU接續，目前不用使用者安裝，無Setup交付或產品／環境發布。

**2026-11-11｜基本包清單改於封裝／生命週期完成後產生**

- 檢視發現安裝測試會新增catalog，逐檔快照移至最後，避免清單早於最終內容。新增真catalog產生的反例，新23／相關88通過；[排序修正紀錄](runs/candidate-inventory-finalization-2026-11-11/README.md)保存。前來源683全回歸保留，這次684與Windows接續；C04／C11及7/12不提高。

**2026-11-11｜候選包逐檔清單與CPU ZIP核對準備，程式0.19.1**

- [新22／相關87項](runs/candidate-inventory-prep-2026-11-11/README.md)通過：完整普通檔案大小／hash、可證明來源／原文對照、未知項待查及可信舊報告重驗；CPU ZIP包含額外NOTICE，逐項內容／CRC／descriptor皆核對。新增[中文檢核說明](../candidate-inventory.md)。
- 調整兩條CI的公開摘要轉送，方便保存實際檔案數與report hash；完整逐檔JSON仍由CI暫存。Windows及本次完整回歸待跑，原661基線不冒充新來源；原文／模型／9鎖／28圖不改，C04 2/4、C11 2/5、7/12保持。

**2026-11-11｜Windows兩包隨包原文與原生來源追溯通過，完整661項正常退出**

- [基本包42971218861與CPU42971219072](runs/bundle-provenance-ci-2026-11-11/README.md)均以70f03f0成功完成。基本包app10／安裝6／跨版11／續修三案接受；CPU追溯旗標true、功能11／同版8／跨版8／恢復6接受。隨包原文、METADATA、啟動器與Analysis所列原生來源／收集後指紋完成技術檢核；完整報告由CI暫存七天，本紀錄保存公開原頁／精簡結果，未下載登入artifact。
- 新16／相關65及全661：660通過、1既有ONNX繁中品質預期失敗、0跳過，混合及42獨立模組全exit0。首輪Windows反斜線拒絕後修正清單輸出，原失敗與被取消run保留；早期660來源另存，不冒充最新。52份舊manifest／2801筆hash與原文／模型／9鎖／vendor／28圖不改。
- 新增[追溯報告中文說明](../bundle-provenance.md)，視覺卡與測試基線更新。程式0.19.1／架構0.4；C04 2/4、C11 2/5及7/12保持。完整候選清單／再散布、乾淨機／人工與GPU接續，目前不用使用者安裝，無產品或環境發布。

**2026-11-11｜補齊基本包與CPU選配的啟動器原文／原生來源追溯**

- 建置檢查發現PyInstaller是build相依，先前未獨立保存其啟動器原文；新增實際安裝原文逐位元複製與hash。原生Analysis清單升為schema2，記錄來源指紋／大小及可確認套件版號；未知原生來源保持未知。
- 建置後驗隨包hash／METADATA／啟動器與每個原生收集檔，來源與收集後指紋分列，不能因PyInstaller處理後不同就冒稱位元相同。CPU套件表明列build來源範圍，缺wheel原文者保留待審。
- 新15／相關64項通過；首輪fixture改sys.platform影響sysconfig及誤打測試模組名稱，原失敗保留，修正測試後通過。Windows與完整回歸接續，程式0.19.1／架構0.4，C04 2/4、C11 2/5及7/12保持。[本次紀錄](runs/bundle-provenance-2026-11-11/README.md)。

**2026-11-11｜完成0.19.1完整回歸645項與41模組正常退出**

- 以獨立venv安裝原Linux55套件hash鎖、本專案與固定vendor，pip check通過；四語／三個ONNX模型hash及字型／Tesseract5.5.0觀察另存。[完整原始日誌與環境指紋](runs/full-regression-0.19.1-2026-11-11/README.md)保存。
- 全645：644通過、1既有ONNX繁中品質預期失敗、0跳過；混合程序正常exit0，41個獨立模組亦全exit0。首輪暫存測試driver漏main guard而無效，已停止自有程序並改正driver；原partial log／driver／主動終止-9留存，不列產品崩潰或有效回歸。產品原始碼與測試斷言不改。
- 進度頁測試基線由0.17.2的611更新為本版645，舊紀錄固定。候選包內容／原文、測試產物與乾淨機／人工接續；C04仍2/4、C11仍2/5、導入7/12／歷史19/25，ONNX品質／GPU／RAM軟性限制保留，無產品或環境發布。

**2026-11-11｜補存同版基本包CI並盤點第一版測試安裝包，0.19.1**

- [同來源ad7d227的Windows基本包CI](runs/windows-test-readiness-2026-11-11/README.md)公開原頁／摘要已保存：app10、安裝6、真0.16→0.19.1跨版11及續修3/3每案app10，CI自有清理3/3／清1剩0、鎖檔拒絕／未知檔保留均接受。並非本次重新建置；hosted仍非乾淨機。
- 離線profile／授權hash驗證通過，CPU24／5、基本runtime38／Windows build49、上位58套件與214份notice／metadata；不當最終再散布核准。新增[測試安裝包準備](../windows-test-build-readiness.md)，列本版完整回歸、候選內容／原文與交付、乾淨機／人工及GPU品質的缺口與順序；目前不用使用者安裝。
- 更新首頁／視覺卡與C11文字，清除過時的「CI清理未完成」描述；C11仍2/5、導入7/12、歷史19/25。本次僅驗文件／原文／閉包與瀏覽器，未重跑162或全回歸，無產品或環境發布。

**2026-11-11｜完成Windows CPU程序終止／獨立恢復六案，程式0.19.1**

- [真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42943978279)（ad7d227）恢復6/6、功能11/11、同版8/8、跨版8/8接受。升級／有效payload修復／移除六停點，自己spawn的安裝程序真kill，另一程序recover後驗精確版號／frozen／CPU及固定英文辨識；全hash、active、交易／staging收尾、重複恢復與合成資料／快取均符合預期。
- [公開原頁、完整精簡JSON、來源對照與視覺紀錄](runs/windows-cpu-recovery-ci-2026-11-11/README.md)保存；首輪4096字元截斷原文、初輪負例fixture失敗與本地162項日誌都保留，沒有補造缺字。完整登入報告七天未下載，本版完整回歸未跑。
- C04仍2/4、C11仍2/5、導入7/12；3073份既有紀錄／資產／鎖及28圖固定。其他profile、乾淨機／人工、斷電／OS重啟及GPU／品質仍待，無產品發行。

**2026-11-11｜首輪Windows六案接受，縮短公開摘要避免截斷，0.19.1**

- 首run42941852540（fc31d81）root與recovery接受true／六案已見公開註記，但GitHub在4096字元截斷，無法完整讀取後續明細。[原頁、原prefix與直接觀察欄位](runs/windows-cpu-recovery-summary-2026-11-11/README.md)保存，不猜補缺字。
- 公開副本改為精簡每案PID／exitcode／版號／frozen，完整原報告不改。新6／相關162項通過（含長Unicode錯誤／最大PID／原資料不變）；既有Windows CI將重跑，驗證完整公開JSON，本版全回歸未跑。

**2026-11-11｜CPU維護程序中斷／獨立程序恢復六案準備，0.19.0 → 0.19.1**

- 真spawn安裝程序抵達停點後，核對自有PID／token／操作／停點才kill；另一新程序恢復交易並驗OCR。升級、有效payload修復及移除各兩停點，分別驗未提交還原／已提交保留；活著時鎖拒絕、終止後journal／staging收尾、重複recover無動作及合成資料／快取保留。
- 新5／相關161本地通過，初輪負例fixture作用範圍過廣的失敗與後續通過均[保存](runs/windows-cpu-recovery-prep-2026-11-11/README.md)。Windows與本版完整回歸待驗；C04仍2/4、C11仍2/5、導入7/12，原資產／鎖／28圖固定，無產品發行。

**2026-11-10｜完成Windows CPU元件跨版8案，程式0.19.0**

- [真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42802066110)（db601e2）跨版8/8、原功能11/11、同版維護8/8通過。固定前版fd69854（app0.18.1／CPU1.0.0）與新版各自來源／venv建置，真frozen OCR版號序列1.0.0、1.0.0、1.0.1、1.0.0、1.0.1；精確版號與provider、全hash、active、合成資料／cache與環境不變均接受。
- [公開run／job原頁、完整短摘要與視覺紀錄](runs/windows-cpu-upgrade-ci-2026-11-10/README.md)保存；被取代首run最終Cancelled，不當失敗或成功。原156項準備與接續紀錄固定；完整登入報告七天未下載，原PDF／Qt與本版全回歸未重跑。
- C04仍2/4、C11仍2/5、導入7/12；28原圖與3044份既有紀錄／資產／鎖不改。下一步其他profile／完整故障恢復與乾淨機／人工，GPU／品質與RAM軟性限制保留，無產品發行。

**2026-11-10｜PDF／桌面驗收跟隨元件描述版號，程式0.19.0**

- 將舊驗收腳本的固定1.0.0要求、輸出來源及GUI偏好改讀本次descriptor版號，避免新1.0.1無法沿用原驗收入口。相關156項／語法編譯正常，[接續原始日誌與首run更新前快照](runs/windows-cpu-upgrade-followup-2026-11-10/README.md)保存；未重跑完整PDF／Qt或全專案。Windows將再驗最新版，原準備紀錄不改。

**2026-11-10｜CPU元件精確跨版相容與Windows驗收準備，0.18.1 → 0.19.0**

- 元件1.0.1與已驗1.0.0共用協定1.0.0；binding把租約版號交給runner，hello及結果都必須精確相符，未知版本拒絕。Windows另從乾淨固定fd69854來源與獨立venv建前版，新增升級／取消／固定請求／明確回復／退休及資料保留8案，不改描述冒充新版。
- 新9／相關156項本地通過，[準備原始日誌](runs/windows-cpu-upgrade-prep-2026-11-10/README.md)保存；Windows與本版完整回歸未跑，原CPU11／同版8仍屬0.18.1。C04 2/4、C11 2/5、導入7/12，9鎖／原文／模型與28圖保留。

**2026-11-10｜完成Windows CPU選配同版維護8案，程式0.18.1**

- [真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42794184827)（fd69854）功能11/11、維護8/8接受。重驗／租約鎖／架構拒絕、壞包、publish後取消回復、損壞修復、未知檔案及移除重裝，全hash／active／READY、合成文件／設定／快取與交易收尾均符合預期；控制端無OCR／Qt且環境不變。
- [公開原頁／完整短摘要／來源對照及視覺紀錄](runs/windows-cpu-lifecycle-ci-2026-11-10/README.md)保存；[147項準備日誌](runs/windows-cpu-lifecycle-prep-2026-11-10/README.md)固定。取消為Event停點，非強制終止、斷電、跨版或乾淨機；完整登入報告未下載，不冒充永久備份。
- 進度新增CPU同版維護已驗卡，C04仍2/4、C11仍2/5、導入7/12。3023份原紀錄／資產／鎖與28圖不改，本版完整回歸未跑；下一步元件跨版相容與其他profile，GPU／品質／乾淨機／人工仍待，無Setup／tag／Release。

**2026-11-10｜新增Windows CPU選配同版維護8案，0.18.0 → 0.18.1**

- 獨立驗收重驗、架構拒絕、租約鎖、壞包、publish後取消回復、損壞修復、未知資料拒刪、移除保留合成文件／設定／快取後重裝；每案驗hash、active／READY與交易收尾。原生功能11項保留，八案結果另外計，不合併成全profile或強制中斷驗收。
- 新4／相關147項正常退出；[準備原始日誌](runs/windows-cpu-lifecycle-prep-2026-11-10/README.md)保存，Windows待跑，完整本版回歸未執行。C04仍2/4、C11仍2/5、導入7/12；原9鎖／模型／第三方原文與28圖固定。

**2026-11-10｜完成Windows CPU選配原生11項驗收，程式0.18.0**

- [真正Windows2022 CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42791407466)（f0708d0）11/11通過：簽章離線匯入、兩位置健康／推論、壞檔隔離、取消、RAM啟動前拒絕、移除、控制端環境不變，以及frozen父管道EOF退出72／鎖釋放。三個provider均為CPU，控制端沒有OCR／Qt，無模型／ZIP／Setup發行。
- 在worker共享鎖內、reader前初始化Windows原生庫解決本次匯入等待；原RAM准入／期限保留，移除未奏效的ReadFile候選。[公開原頁／短摘要、143項日誌與來源對照](runs/windows-cpu-ci-2026-11-10/README.md)保存，前四輪失敗原樣保留；需登入完整報告artifact未下載。
- 更新視覺進度，C04仍2/4、C11仍2/5、導入7/12／歷史19/25；本版完整回歸未跑，舊611仍屬0.17.2。28張架構快照及原模型／第三方原文固定；下一步全profile生命週期與乾淨機／人工，ONNX繁體／日韓／GPU及RAM軟性預算限制保留。

**2026-11-10｜Windows CPU第四輪未通過，改為reader前初始化原生庫，0.18.0**

- [第四輪原頁與結果](runs/windows-cpu-attempt4-2026-11-10/README.md)保存；ReadFile候選仍在ORT匯入逾時，已退回raw輸入。新候選保留共享鎖／RAM／原期限，真正Windows另驗frozen EOF退出與鎖釋放，共預期11項；相關143項通過，完整626未執行，Windows待驗。

**2026-11-10｜Windows CPU定位原生匯入等待，加入Win32管道候選修正，0.18.0**

- [第三輪原頁與堆疊短摘要](runs/windows-cpu-attempt3-2026-11-10/README.md)顯示hello／loading後卡在ORT native import，仍未通過。Windows控制reader改用ReadFile避免CRT讀鎖，保留EOF／取消／資源及原期限，未提前宣稱修復。新6／相關146項通過，完整629尚未執行；參考ORT固定來源保存原bytes並標明未證實底層DLL呼叫。

**2026-11-10｜Windows CPU確認健康工作逾時，0.18.0**

- [第二輪原始結果](runs/windows-cpu-attempt2-2026-11-10/README.md)保存，錯誤為工作逾時、stderr空白，仍未接受。固定health驗收補協定進度與45秒堆疊，既有120秒驗收期限不變；新2／相關140項通過，未宣稱Windows修復或全623回歸通過。

**2026-11-10｜Windows CPU首輪編譯成功、staging健康失敗，0.18.0**

- 保存[原頁與短摘要](runs/windows-cpu-attempt1-2026-11-10/README.md)，原10項未通過、不提高進度。只對固定公開health fixture增加有界stderr與即時觀察，產品WorkerRunner仍排空且不保存文件診斷；新2／相關138通過，根因仍待下一輪實跑。

**2026-11-10｜新增Windows CPU選配獨立profile與原生驗證，程式0.17.2 → 0.18.0**

- 新環境連線恢復，核對GitHub main 3e1d3d2後續寫；不重新套用或發布環境設定。CPU建置24／精簡控制端5套件，原notice／metadata對照97／30筆，沿用原hash／版本與核心依賴範圍，保留原文。
- 獨立Windows2022 CI將真正建置frozen worker並以無OCR控制端跑原10項，包含中文路徑、空PATH、原生推論／取消、RAM拒絕與移除；臨時金鑰只在記憶體、只上傳七天報告，不提供產品ZIP／Setup。
- 新8項、相關136項在鎖定venv通過；134項初驗與proxy失敗也保存。[準備紀錄](runs/windows-cpu-prep-2026-11-10/README.md)／[範圍](../windows-cpu-ci.md)。Windows待實跑，本輪未執行完整619項；保留0.17.2的611基線、ONNX繁中／GPU／RAM與乾淨機門檻，C04仍2/4、C11仍2/5、完整7/12。


**2026-11-10｜完成CI自有中斷產物清理實測，程式0.17.2**

- [真正Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42599639656)（a40f438）接受三案：普通Setup續修各app10項、移除後只清本次記憶體收據產物，實際清1份／殘留0；真實sharing violation時拒絕，未知同類檔名／同bytes合成文件保持原內容。基本app10、安裝6、真跨版11及續修3案均通過。
- [公開原頁／完整短摘要／實測來源比較](runs/temporary-cleanup-ci-2026-11-10/README.md)與視覺進度保存；[準備14／39／611與前版Windows基線](runs/temporary-cleanup-prep-2026-11-09/README.md)不倒填。範圍僅ci-owned-fault-installer-artifacts，普通Setup沒有新增清理入口，不能當作一般使用者任意中斷自動清理。
- C11仍2/5、完整7/12、歷史19/25；28份架構圖與原紀錄固定。完整需登入artifact七天、未下載；全profile、乾淨機／人工／標準帳戶、一般Setup暫存政策、GPU／品質與RAM門檻保留，沒有Setup／tag／Release。


**2026-11-09｜新增CI中斷產物清理，程式0.17.1 → 0.17.2**

- 真正抓取前版0.17.1 Windows公開成功結果（42594462484／c5f0c01），保留原頁／完整短摘要；app10、安裝6、跨版11、續修3案各10，殘留1份且cleanup=false，未倒填新機制。
- 新清理限定本次自有PID、建立前不存在且已觀察的記憶體收據；整批預檢並以Windows原檔handle拒絕寫入／rename／delete分享，核對最終路徑後delete-on-close，沒有unlink後備／通配或外部JSON授權。新增真鎖檔拒絕與未知同名／同bytes保留的Windows CI控制，普通Setup未加入此清理入口。
- Linux14／相關39通過，全611（610＋1既有ONNX品質預期失敗、0跳過）混合及36模組正常exit0；Windows清理待另驗。[準備日誌與基線](runs/temporary-cleanup-prep-2026-11-09/README.md)／[說明](../temporary-cleanup-ci.md)。C11仍2/5、完整7/12、歷史19/25，28份架構圖不改，沒有Setup／tag／Release。


**2026-11-09｜修正Qt視窗生命週期，程式0.17.0 → 0.17.1**

- 原23項管理測試12輪中1輪exit-11；LLDB真正抓到PySide全域cleanup內QPushButton／QObject destructor SIGSEGV。入口設WA_DeleteOnClose、六組Qt測試負責關閉／等待／deferred delete，不跳過cleanup或強制殺程序。
- 新3案涵蓋主窗、元件子窗及忙碌QThread拒關／取消／收尾；前2案修前失敗、修後3案通過。管理23項12輪正常退出；全混合597 exit0、35模組全exit0，596通過＋1既有ONNX品質預期失敗、0跳過。[日誌／堆疊／前後對照](runs/qt-lifecycle-2026-11-09/README.md)／[設計](../qt-lifecycle.md)。首輪模型環境／closure未齊的失敗與跳過保留，補齊後完整重跑接受。
- 更新視覺進度與版本差異；本輪圖的結構未改，28份原架構快照不動。C11仍2/5、完整7/12、歷史19/25；Windows0.17.1、全profile、乾淨機／人工／GPU與Inno暫存清理另驗，沒有Setup／tag／Release發行。


記錄專案從規劃、實作、測試到調整方向的過程。之後每次開發在最上方追加日期、版本、做了什麼、遇到的問題與接下來要處理的事項，舊紀錄持續保留。

目前程式版本 **0.19.1**、架構版本 **0.4**。版本變更摘要另見 [CHANGELOG](../../CHANGELOG.md)。日期以台北時間記錄。

**2026-11-09｜完成Windows程序中斷後續修實測，程式0.17.0**

- [真實Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42578549106)（e3c0273）三停點3/3接受，taskkill自己握手後的PID樹，以一般匹配Setup明確續修，各10項app與全hash／舊metadata清理／移除及合成資料保留通過；未完成app入口退出3、不寫診斷，無確認及不同metadata拒絕。
- 原版0.16／990e600的controller／spec／generator獨立建置，另驗基本包與安裝後app各10、安裝6段、跨版11段。[原頁／完整短診斷／原文](runs/c11-recovery-2026-11-09/README.md)／[第二十八份圖](../architecture/versions/v0.4-base-recovery-ci.md)與進度保存，舊27圖與raw固定。完整登入artifact僅七天未下載，不假稱永久備份；無Setup發行。
- C11仍2/5／完整7/12，第三項各profile與更完整故障恢復尚待；非斷電／OS重啟或自動失敗回滾。Linux最新594回歸含Qt管理exit -11仍不接受，單獨23項exit0不代表修復，品質／GPU／RAM門檻保留。

**2026-11-09｜修正中斷後Inno暫存物收據，程式0.17.0**

- Windows基本包／安裝後app各10、安裝6段／跨版11段與第一個中斷續修案接受（1/3），第二案遇額外Inno暫存檔被完整性檢查拒絕。新增「既有已驗程式／Inno metadata精確hash」及「操作前不存在、自己停點已觀察、終止後續修前綁定path／hash／PID」收據；未知或變更檔不能憑.tmp名稱放行，檔案只保留、不直接刪除。完整暫存清理仍未驗收。[第二次原始紀錄與180相關／594斷言](runs/c11-recovery-attempt2-2026-11-09/README.md)保存，Windows待重驗，C11仍2/5／完整7/12；LinuxQt退出問題仍未修復。

**2026-11-09｜修正中斷續修Inno引入檔註解，程式0.17.0**

- Windows基本包10項通過，新Inno在引入檔第一行報BEGIN expected：[Code]內誤用分號註解，已改Pascal //。Setup與中斷測試尚未開始；[第一輪原始紀錄](runs/c11-recovery-attempt1-2026-11-09/README.md)保留，待重新實跑，不提高C11 2/5／完整7/12。Linux原591之Qt退出失敗仍追蹤。

**2026-11-09｜新增安裝程序中斷續修，程式0.16.0 → 0.17.0**

- 針對半套安裝卡在catalog／同版檢查的缺口，新增固定hash intent／暫存rename、原位置與匹配payload／明確續修、全hash後清標記及frozen入口阻擋。保留未知文件，沒有遞迴清除資料或宣稱自動回滾／斷電耐久。
- CI-only三個停點會真正終止自己程序樹，再以一般Setup續修及各10項app驗收；前版改固定0.16／990e600，原controller／spec／generator獨立建置。新增12／相關177；34模組591斷言（590＋1預期失敗），Qt管理23項斷言通過後exit -11，整輪不接受，Windows待實跑，C11仍2/5、完整7/12。[原始紀錄](runs/c11-recovery-prep-2026-11-09/README.md)／[指引](../base-recovery-ci.md)。26份舊圖與raw紀錄固定，完整C11／各profile／乾淨機與品質／GPU／RAM門檻保留。

**2026-11-09｜完成基本包跨版本升級／明確回復實測，程式0.16.0**

- [真正Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42557368030)（990e600）接受，獨立原0.15 source／installer初裝，升級0.16、拒未指定降版、相容installer回復真正前版、再升級與移除；跨版11/11，原版／升級後／回復後app各10項。改catalog／過期檔、未知新增檔衝突、真junction與改位置皆寫入前拒絕；全hash、過期空套件目錄移除、未知舊目錄內容拒絕、執行中app_version及合成資料／未知文件保留已驗。
- [原頁／完整短診斷與工具原文](runs/c11-upgrade-2026-11-09/README.md)、[第二十六份圖](../architecture/versions/v0.4-base-upgrade-ci.md)與進度保存，既有25份圖與原raw紀錄不動。完整需登入artifact七天保留、未下載不假稱已封存；Setup不發行。
- 完成的是基本profile之已知兩版跨版重裝／明確回復，原0.15 installer不具新保護，須用新相容installer回復。各profile、中斷自動回滾／乾淨機／人工UI及標準帳戶仍待，原C11第二項拆為基本包與各profile兩項（4→5），基本包完成、各profile待驗，現為2/5／完整7/12，Linux混合teardown、ONNX品質與GPU／RAM門檻保留。

**2026-11-09｜修正跨版自檢的空舊目錄與診斷保留，程式0.16.0**

- 第二輪Windows基本包／安裝後app各10項、安裝／同版修復／移除6段通過；跨版前6段含原版app、衝突／真junction／位置等控制通過，升級後app自檢失敗。公開診斷被cleanup空log蓋過，已固定failed_step優先保留原錯誤；不假稱已讀到Windows原例外。[第二次原始紀錄](runs/c11-upgrade-attempt2-2026-11-09/README.md)。
- 真importlib.metadata本地可重現空前版dist-info先列舉時遮蔽新版Version為None；新增已知空目錄移除、未知內容先拒絕及app前全hash／舊目錄檢查。這是候選原因與修正，Windows後續實跑另記；C11仍1/4、完整7/12，舊圖與日誌不倒填。

**2026-11-09｜修正跨版CI第一次Inno編譯失敗，程式0.16.0**

- Windows程式建置與基本包10/10通過；新安裝器在Inno編譯時指出ExcludeTrailingBackslash不支援，Setup與跨版安裝尚未開始。已改官方RemoveBackslashUnlessRoot，後續重新實跑；C11仍1/4、完整7/12。[第一次原始失敗](runs/c11-upgrade-attempt1-2026-11-09/README.md)及固定官方宣告保存，既有圖與raw日誌不倒填。

**2026-11-09｜新增基本包真跨版本升級／明確回復CI，程式0.15.0 → 0.16.0**

- 新增可信source catalog靜態規則、原位置／reparse保護、拒未指定降版與過期檔hash檢查，避免留下前版metadata或清除未知文件。回復使用新政策相容installer配真正0.15 payload；原0.15安裝器保持原樣，不能追溯加入保護，也不宣稱中斷自動回滾。
- 固定43cf811前版獨立建置，CI將測真正兩個版本與完整installed app10項、三類拒絕控制、再升級／移除與合成資料保留。本地新增9／相關163、33模組577（576＋1預期失敗）正常exit0；Windows待實跑，C11仍1/4／完整7/12。[原始紀錄](runs/c11-upgrade-prep-2026-11-09/README.md)／[指引](../base-upgrade-ci.md)。各profile、乾淨機、人工UI／標準帳戶、GPU／品質與Linux混合teardown仍追蹤，Setup不發行。

**2026-11-09｜完成 C11 hosted 安裝／同版修復／移除子檢核，程式0.15.0**

- [實際Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42542464205)（43cf811）已接受：基本資料夾10項、安裝後app10項及安裝生命週期6段。Inno真編譯／中文路徑安裝、1652檔catalog／registry／捷徑核對，刪入口及損模型後同版修復與四語自檢恢復；移除受管檔案／註冊／捷徑，未知文件及外部唯一合成哨兵保持原bytes。
- **C11 0/4 → 1/4**，整體仍7/12；跨版升級回復、無Python乾淨機／離線、人工UI與標準帳戶仍待，沒有把同版修復當升級。沒有Setup發行或tag／Release。[原頁／完整短診斷／hash與原文](runs/c11-installer-2026-11-09/README.md)、[第二十四份圖](../architecture/versions/v0.4-base-installer-ci.md)及視覺進度保存；完整artifact／截圖需登入、七天到期，未假稱已下載。
- compiler license從官方固定source取得，原SHA與runner完全相同；只標記授權原文來源，不假定compiler binary同一commit，也不取代再散布核准。Linux154／568隔離回歸及原品質／混合teardown限制保留。

**2026-11-09｜新增 C11 基本包安裝／修復／移除驗證，程式 0.14.0 → 0.15.0**

- 沿用0.14的 Windows 基本包10項驗證，新增獨立 per-user Inno基本包預覽安裝器與不同AppId，避免碰舊Desktop安裝；不使用遞迴刪除，catalog逐檔／版本驗證，修復只覆寫受管檔案。新CI會真安裝、刪入口／損模型、同版修復、重驗OCR、解除安裝並核對外部哨兵與未知文件保留，不冒充跨版升級／回復或乾淨機。
- 本地新增13項，相關154/154；新通用隔離runner明確核對總數與固定預期失敗ID，32模組568項（567通過、1既有預期失敗）各自正常退出。Inno UTF-16日誌也能正確摘要；尚無新Windows安裝結果，C11新子檢核先列待驗，不提高完整7/12。[準備與原始回歸](runs/c11-installer-prep-2026-11-09/README.md)及[第二十三份圖](../architecture/versions/v0.4-base-installer-preparation.md)保存。

**2026-11-09｜完成 Windows 基本包自動驗證，程式 0.14.0**

- [CI #7](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42539123115) 在固定 source 3384167 真正完成原生重建、Windows 基本包與 **10/10**：四語健康／掃描、中文搬移、UTF-8／CLI／偏好與故障保護、Qt 開窗及正常 exit 0（4 次正常關閉要求）。沒有略過 GUI 或用強制終止當成功。
- [實測原頁／完整短診斷／來源紀錄](runs/windows-base-ci-2026-11-09/README.md)、[第二十二份圖](../architecture/versions/v0.4-windows-base-ci.md)、中文封面與視覺進度同步；完整 authenticated artifact 及 Windows 截圖仍需登入、七天到期，此處不冒充已下載。
- Linux 31 模組隔離 555 項正常退出（554 通過、1 既有繁體品質預期失敗），原混合 teardown exit139 仍未定位；LLDB 下本次 target 正常 exit0、未重現而無 C stack，debugger exit1 是事後 backtrace 查詢已退出的 target。原始紀錄保留，不把未重現當修好。
- 完成的是基本包 hosted Windows CI 子檢核；乾淨機／安裝、人工 UI、各選配 profile 與 GPU 門檻保留。C03 3/4、C04 2/4、C09 3/4、完整 7/12、歷史 19/25，不建立 Setup／tag／Release。

**2026-11-09｜補下載早期診斷，保存隔離回歸，程式 0.14.0**

- 讀到 [CI #6](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42477745858)：下載固定來源失敗，原生編譯／Windows 均未執行，原早期日誌未保存而無法判定具體錯誤。增加 pip／fetch tee 日誌與 always 保存，明確 bash pipefail；實際合成失敗命令經 tee 仍 exit 1，不放寬 SHA／來源或驗收。
- 保存先前 11-08 已執行的逐模組回歸：31 個 child 正常 exit 0，555 項中 554 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過。混合 native teardown exit 139 根因仍待查，沒有把隔離當作修復。[原始日誌／JSON](runs/windows-ci-retry-2026-11-09/README.md)與視覺進度補存；Windows 仍九項通過、Qt待重驗，完整 7/12 保留。

**2026-11-08｜Windows 前九項通過，修正 Qt 關閉測試協定，程式 0.14.0**

- [CI #5](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42476509935) 已實測 Windows UTF-8 mode=true、四語健康／掃描、中文搬移／完整自檢、四語 CLI、設定保留及故障不回退，共 9 項通過；Qt 已開窗／自身截圖，但一次 WM_CLOSE 遇首次背景檢查收尾而暫緩關閉，工具等 25 秒後失敗。
- 工具在同一總期限內重新列舉自身 child PID 視窗並重送正常關閉，仍須真實 exit 0，非零／逾時不算通過，不以 kill／terminate 代替驗收。新增 2 項收尾協定反例，相關 141/141，仍待新 Windows GUI 實測。混合 555 項斷言完成後又 native teardown exit 139，保留 faulthandler／原始日誌且不列正式成功，另以逐模組正常 child 調查。[完整過程](runs/windows-ci-close-2026-11-08/README.md)及[第二十一份圖](../architecture/versions/v0.4-windows-cli-ci.md)保存；應用程式轉換碼／基本 spec 與 CI #5 相同，進度不提前增加。

**2026-11-08｜修正 Windows frozen 的中文診斷解碼，程式 0.14.0**

- [CI #4](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42475049445) 中新 UTF-8 引擎已在中文搬移路徑列出四語模型；接續 full 自檢遇到應用程式以 CP1252 讀原生 UTF-8 診斷的 UnicodeDecodeError。短摘要完整保留下根因，修正 PDF OCR 探針的明確解碼；辨識本文仍嚴格 UTF-8，模型及品質目標不變。基本包同時以 PyInstaller X utf8 固定 interpreter 模式，Windows core 驗實際旗標。最小 Linux frozen 在 LC_ALL=C／PYTHONUTF8=0／PYTHONCOERCECLOCALE=0 下仍 flag=1、UTF-8 四語輸出成功；只作 packaging option 證據，非 Windows 基本包成功。
- 真正 Tesseract＋固定影像／eng 模型＋中文路徑，強制預設 CP1252：先重現舊 child 解碼錯誤，再驗新探針與真實 OCR。舊已安裝套件先失敗，更正來源重裝後相關 139/139、最新完整 553（552 通過、1 既有預期失敗）且 exit 0；另一次 unittest 印 OK 後 native teardown exit 139，原始紀錄分存、根因待查，不把該次當正式成功。新增總數 26。[原始開發紀錄](runs/windows-ci-decode-2026-11-08/README.md)另存，修正版 Windows 結果仍待新 CI；完整 7/12 保留。

**2026-11-08｜Windows 原生基本包與四語自檢通過，中文搬移待修，程式 0.14.0**

- 讀到 CI #2 診斷，Windows 依賴／本地安裝成功，profile／lock 步驟失敗。換行保護後 [CI #3](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42473518203) 在 Windows 2022 真正原生打包成功，core 及四語健康／四份掃描 PDF 自檢通過；中文空格搬移後 native --list-langs 失敗，整體仍未驗收。
- 加入第一方 Windows UTF-8 manifest，不修改固定上游或系統地區，RC 接入 EXE並保存自己來源；新 receipt 要對應目前 XML，歷史固定候選保留。Linux 重建與實際 RT_MANIFEST 24／ID 1／原文及四語組裝通過，仍待新 Windows 結果。初始工具路徑錯誤、原 resource target 分類與補充正確 attribution 都分存。
- 公開摘要會截斷約 5 KB，改成短摘要優先失敗步驟；初始測試抓到異型 commands 處理，再補防守後通過。本輪新增總數 25、相關 138/138、完整 552（551 通過、1 既有預期失敗）；[原始 Windows／Linux 紀錄](runs/windows-ci-native-2026-11-08/README.md)與[第二十份快照](../architecture/versions/v0.4-windows-native-ci.md)另存。完整進度 7/12 保留，沒有乾淨機／安裝包／GPU 或正式發行。

**2026-11-08｜修正 Windows 自動換行破壞固定來源雜湊，程式 0.14.0**

- 在 Linux 實際使用 Git core.autocrlf=true checkout，重現固定 lock／來源 JSON／原始授權／舊 receipt 的原位元組被轉換；以 .gitattributes 保護 vendor、packaging、歷史證據與快照，自有文字固定 LF，原檔不重新格式化。另將屬性檔加入 CI 觸發條件。
- 新增暫存 Git repository 的真正 checkout 回歸，七類固定檔案全數 byte-identical；工具 21/21、相關 134/134。這是已重現的跨平台完整性問題，尚不宣稱就是首次 Windows job 的根因。[換行保護紀錄](runs/windows-ci-eol-2026-11-08/README.md)保存前後證據；GitHub 頁面持續 503／504，稍後讀到 CI #2 亦失敗，底層摘要仍待讀取，換行修正另待新 CI，進度不增加。

**2026-11-08｜首次 Windows CI 執行失敗，補足可讀取的診斷，程式 0.14.0**

- 正常推送 7815277 後，[CI #1](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42471909742) 真正啟動：Ubuntu 固定來源 native job 成功，Windows job 失敗。只能確認 Windows runner 已啟動，未取得應用程式建置／執行證據，不增加進度。
- GitHub 公開頁暫時 503，重試後保存狀態；Windows 日誌／附件及 summary 需要登入，現有 gh 憑證不可用。增加限量診斷 annotation，保留真實錯誤與尾段並跳脫指令字元，工具 20/20、相關 133/133、完整 547 項（546 通過、1 既有預期失敗），準備下一次執行以定位根因；沒有猜測成功或用 Linux 代替 Windows。[第一次執行紀錄](runs/windows-ci-attempt1-2026-11-08/README.md)另存。

**2026-11-08｜準備 Windows 基本包自動建置與驗證，程式 0.13.0 → 0.14.0**

- 使用者確認先採 Windows 虛擬機測試，目前 Linux 雲端沒有 Windows 執行器；既有 workflow 仍是手動舊 ONNX 開發／安裝流程。新增獨立 main push CI：Ubuntu 固定輸入重建 Windows 原生候選，再由 Windows 2022 原生建置基本包並驗四語、中文搬移／UTF-8、故障與 Qt；不觸發舊手動發行，不建立 Setup／Release。最小 contents:read，測試輸入 artifact 一天到期，報告七天。
- 新增有界固定來源下載、有限網路重試、可信建置管線 receipt 對應、Windows stdlib 控制端／驗收與公開 job summary。CI 會預備可用外部引擎／模型，確認故障時沒有誤回退；只有真正 Windows 才能執行驗收，Linux guard 不當作 Windows 成功。
- 初始 guard 抓出 platform.platform 會呼叫 uname，移到平台拒絕之後；最初全回歸因此一項失敗，原始日誌與更正後分存。工具鏈 HTTPS 首次遇 504，有限重試後固定十檔全部 hash／bytes 通過，完整性錯誤不重試。另以固定來源真正重建新 PE，因工作位置不同 hash 不強求逐位元一致，使用同次 receipt 逐項核對來源／工具／原文與新候選。
- 新增 **17 項**、相關 **130/130**；完整 **544 項：543 通過、1 既有 ONNX 繁體品質預期失敗**。[本輪準備紀錄](runs/windows-ci-2026-11-08/README.md)與[第十九份快照](../architecture/versions/v0.4-windows-ci-preparation.md)保存。此時 Windows 尚待實際 CI 結果；C03 3/4、C04 2/4、C09 3/4、完整 7/12、既有 19/25 保留。
- GitHub CLI 所帶 GH_TOKEN 回報不可用，沒有讀取或更改憑證；改用一般 git 推送觸發與公開 Actions 頁／job summary 查核。hosted runner 已有 Python，不當作乾淨機；安裝、人工 UI、GPU 與最終發行仍待後續，沒有把 workflow YAML／模擬當成通過。

**2026-11-08｜完成 C03 內含四語基本包 Linux 子檢核，程式 0.12.0 → 0.13.0**

- 接續固定 Windows 最小來源，離線組裝 5.5.3 EXE／四語模型／原文 28 檔＋manifest；同時明確以現有 Linux Tesseract 5.5.0 複本建立開發 payload。兩者平台與來源分開，不執行 PE，也不將 Linux 辨識當成 Windows 成功。新 schema 2 profile 只接受同平台 native assets，原生入口交由 PyInstaller 收相依與系統 copyright。
- 新增內含路徑唯讀解析，逐檔 hash／平台／PE 或 ELF／固定模型／未知檔案與連結檢查。桌面、CLI、首次流程共用；兩個路徑皆自動時檢查全部四語，明確自備引擎／目錄與選語保留。首次完成不保存內含絕對位置，搬移程式仍可用。模型視窗只讀顯示內含資料，不交由受管模型服務下載或移除。schema 7、舊三檔／四語目錄及品質目標保持。 視覺檢查發現長安裝路徑會裁切模型視窗文字，擴大顯示空間後重驗來源版 Qt 並重建最終 frozen。
- core 自檢只驗核心，full 真正跑四語健康及四份掃描 PDF；Linux 獨立程式從空 PATH／空模型環境、中文搬移路徑完成原格式與日韓 CLI。缺／損模型及替換主機引擎連結明確失敗、無部分輸出；缺 OCR 仍能轉文字。loader 的 calling init 路徑核對 Tesseract／Leptonica 從 bundle 載入，不只是同名檔案存在。
- 初始相關測試與 pip 重裝並行，造成 onboarding 模組暫時缺少；改為等重裝結束後再測。實際 frozen 驗收工具先誤猜 liblept.so.5，查看真實 loader 後改從 Analysis 取得 libleptonica.so.6；source Qt harness 又用錯 Window 類名，修正工具重跑。這些初始失敗分存，不列為產品 OCR 失敗或成功。另檢視發現自備模型目錄應保留所選單語，補反例與修正，再依序重裝／重建／回歸。
- 最終新增 **27 項**、相關 **185/185**；真正 Linux frozen **12/12**，source Qt／首次 **3/3**，完整 **527 項：526 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。source Qt 以測試覆寫指向真正 bundle 資產，未宣稱 frozen GUI 或 Windows UI；[原始日誌、清單、範例／輸出與畫面](runs/c03-bundle-2026-11-08/README.md)另存。
- **C03 2/4 → 3/4**，第三項範圍為 Linux 內含整包／離線流程；完整導入仍 **7/12**、既有 **19/25**，C04 2/4、C09 3/4 保留 Windows／各 profile 門檻。新增[第十八份快照](../architecture/versions/v0.4-c03-bundled-ocr.md)，前十七份與舊附件／七份 lock／原 221 份授權固定；更新的產品資料僅離線手冊，其餘既有資料／原品質影像目標不變。
- 未建立 Windows 安裝包、執行 Windows／GPU、一般品質驗收或核准再散布；沒有 tag／Release 或觸發手動 Windows 發行。引擎／模型／bundle binary、wheel、venv 不放 Git。下一步 Windows 原生基本包、四語實際 OCR／中文路徑與乾淨機，再完成 C04、完整 C09／C11；ONNX 繁體品質與 RAM 軟預算限制保留。

**2026-11-08｜完成 C03 最小原生來源準備，程式 0.11.0 → 0.12.0**

- 追查固定官方 `nsis/build.sh`，確認原 installer 依賴即時 MSYS2 套件，無法以現行最新原文推定那批 DLL 的確切來源。保留 32 DLL 缺口與舊候選阻擋，改為從四項固定官方原始碼建立最小原生候選；因既有 PDF OCR 先渲染 PNG，關閉其他外部編碼器、網路／封存、訓練、ScrollView 及 legacy engine。
- 固定 Tesseract 5.5.3、Leptonica 1.87.0、libpng 1.6.59、zlib 1.4 commit 封存 SHA／bytes；LLVM-MinGW 20261104 工具下載與官方發布 digest 一致。CMake 3.31.6／Ninja wheel 1.11.1.4 在獨立開發 venv，不增產品依賴。runtime 原文、作者及工具鏈來源 21 檔保存，沒有修改原 vendor／授權資產。
- 原型先遇 zlib 靜態庫新名稱、只編 archive 造成 `open_memstream` 誤判、Tesseract Windows TIFF try_run、libc++ 不再間接包含 string／cstdlib、Linux Winsock 大小寫等問題；依序寫入 recipe，保留真實失敗。TIFF 明確停用，交叉探針預置失敗值，不當成 Windows 執行成功；Winsock 只補相同 bytes 的 import archive 別名。Leptonica 名為 .dll 的輸出實際是 ar 靜態庫，最後連入 EXE。
- 第一份真實 PE 成功後，另做來源／linker 追蹤；GNU --trace 在該 driver 不支援，改用 -verbose。實際 member 名稱及 libpng 別名又揭露解析缺口，新增兩項回歸並修正；相關中間失敗與原型不列為最終無人介入成功。最終由新目錄離線自動建置，靜態 PE／設定／原文／26 linker 輸入及 objdump 獨立來源檢查 **8/8**。
- 新增 **22 項**，含 native／profile／診斷／授權回歸 **86/86**；完整 **500 項：499 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。早期 20 項／84 項與 498 全回歸、最終結果分存於[本輪紀錄](runs/c03-minimal-source-2026-11-08/README.md)，不混成同一次。
- **C03 來源／原文準備為第二項，1/4 → 2/4；完整導入維持 7/12，既有 19/25，C04 2/4、C09 3/4。** 新增[第十七份快照](../architecture/versions/v0.4-c03-minimal-source.md)、指引與進度；前十六份、舊紀錄、七份 lock、原 221 份授權及原繁體樣本固定。候選及工具／來源大型 archive 不放 Git。 保存前發現建置紀錄目錄被既有 build/ ignore 規則略過，改名 cross-build/ 後重建清單並逐檔核對暫存區；未提交缺少證據的版本。
- 這是 Linux 交叉建置與來源準備，沒有執行任何 Windows PE、掃描／中文路徑驗收、主 profile 內含整合、frozen／安裝包重建、GPU 或產品再散布核准；沒有 tag／Release 或手動發行。下一步接四語基本包與離線完整自檢，再於 Windows 實際建置及乾淨機驗收；ONNX 繁體品質與 RAM 軟預算限制保留。

**2026-11-08｜完成 C03 原生來源／DLL 靜態檢查機制，程式 0.10.0 → 0.11.0**

- 延續四語需求，先取得 UB-Mannheim 文件實際指向的官方 Tesseract 5.5.3 Windows 資產；核對發布 SHA-256、tag／原始碼提交與下載大小。只使用官方 7-Zip 解開 installer，不執行 Windows EXE；7-Zip 僅為檢查工具，不新增產品相依或把工具／原生 binary 放 Git。
- 新增固定候選清單、有界 PE32+／AMD64 普通及延遲匯入解析、DLL 閉包、檔案完整性／連結／大小寫保護、原文映射與封裝阻擋。真實來源共 56 PE，入口閉包 34、靜態未使用 22；來源中的 Tesseract Apache 原文只能證明已確認的主程式與主 DLL，其他 32 個可達 DLL 的逐檔來源／授權證據待補，不能因檔名或同包下載就推定完成。
- 初始實檔掃描發現 `libstdc++-6.dll` 含 `+` 被過窄正則拒絕，修正並增加反例；初始 20 項與 64 項回歸又發現底層連結拒絕冒出不同例外型別，正規化為原生來源錯誤後重裝與重跑。保留實際初次失敗／掃描與最終紀錄，沒有製造不存在的日誌。
- 最終機制 **64/64**，真實來源 **7/7**（發布 digest、原文、56 PE、閉包與 objdump 獨立比對）；要求再散布正確退出 1。報告 `accepted` 僅為靜態檢查成功，封裝／Windows／整包旗標維持 false，直接改旗標也無法取得封裝許可。完整 **478 項：477 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**，授權／上游／依賴 profile 核對另過。
- [官方頁面、三份原文、原始與最終日誌、來源及畫面](runs/c03-native-static-2026-11-08/README.md)保存；新增[第十六份快照](../architecture/versions/v0.4-c03-native-static.md)，視覺檢查另外發現發行目標橫幅仍寫雙語，改為四語後重驗與更新截圖，初次／最終瀏覽器紀錄分存；前十五份與舊附件／七份 lock／原 221 份授權固定。大型 installer、DLL、檢查工具與模型未加入 Git。
- **來源／授權子檢核仍未完成，C03 1/4、C04 2/4、C09 3/4，總數 7/12、既有 19/25。** 下一步取得確切逐 DLL 建置來源／原授權，或建立最小原生 build，再整合四語基本包與 Windows 實驗證。未重建 frozen／Windows 安裝包，未驗 Authenticode、動態載入／GPU，未建立 tag／Release 或觸發手動發行。ONNX 繁體品質與 RAM 軟預算限制保留。

**2026-11-08｜完成 C03 四語模型與語言選擇子檢核，程式 0.9.0 → 0.10.0**

- 依新增需求，基本包 OCR 目標擴充為繁中、英文、日文、韓文。維持架構 v0.4，新增四語固定清單與新受管目錄；不改舊繁中／英文三檔清單、收據或外部模型資料。日韓模型從同一官方固定提交以真正 HTTPS 取得並驗 SHA-256，新增約 4.15 MB，四語含授權約 10.6 MB，不把磁碟容量當 RAM。
- 新增語言契約與桌面／CLI 選項，單語、日＋英、韓＋英及四語混合均明確傳入 Tesseract。缺所選模型不換語言，日韓遇未驗 ONNX 不換後端；只在 OCR 頁處理語言，原生／空白頁沿用。混合使用共同解碼，不宣稱自動語言分類，輸出保留語言來源與混字提醒。
- 設定 v7 讀取 v1–v6，載入不寫檔、明確儲存前備份原始位元組；原引擎、目錄、RAM、品質、元件偏好、首次完成標記及相容預設都保留。新增固定日韓影像與字型來源 hash；原 17 字繁中樣本與 ONNX 品質預期失敗不變。首次檢查依所選模型做本機健康，不自動下載。
- 先跑既有 440 項：439 通過、一項既有品質預期失敗，再加入 18 項語言／資料保護／UI 檢查。最終子檢核 **138/138**、本機 Tesseract／CLI／Qt **10/10**，四種單語及這四頁混合都符合原文目標，樣本品質逐項另列。完整 **458 項：457 通過、1 既有繁體品質預期失敗、0 跳過**。
- 空 PATH／空 TESSDATA_PREFIX 下使用明確引擎與模型目錄，驗真正模型安裝／重用、健康、PDF、日韓 CLI、Qt 保存／轉換與模型視窗；缺模型、未驗後端失敗無輸出，受管移除保留未知資料。原生引擎為既有 Linux Tesseract，不能當成全新 Windows 已內含 OCR。
- [原始紀錄、PDF／MD、健康、實際畫面與來源](runs/c03-languages-2026-11-08/README.md)及[第十五份架構快照](../architecture/versions/v0.4-c03-four-languages.md)獨立保存，前十四份圖、舊附件、七份 lock 與原 221 份授權資產固定。模型 binary 不加入 Git，固定來源、大小及 hash 可追溯；沒有使用者真實文件。
- **C03 完成 1/4 子檢核，整項仍未關閉；總數 7/12，既有 19/25。** 無新增 Python 依賴，打包來源補新資產但沒有重建 frozen／Windows 安裝包，C04 0.9.0 Linux 核心包為歷史證據。後續固定 Windows 引擎／DLL／原授權與四語整包，完成 C03／C04／C09；Windows／GPU、繁體品質及 RAM 軟預算限制保留，沒有 tag／Release 或手動發行。

**2026-11-08｜完成 C04 基本核心打包／自檢子檢核，程式 0.8.1 → 0.9.0**

- 接續已拆分依賴，新增基本 PyInstaller spec 與獨立 build 環境資產準備器；核對套件集合、固定版本及目前專案，再產生 38 個 runtime 與兩個本地專案的內嵌 profile。只有 Linux 核心開發包，沒有把尚缺 Tesseract 的產物當成完整基本版。
- 依 profile 執行資產、固定 runtime、Unicode 文字與原生 PDF 四項 core 自檢；full 加驗必要原生 OCR，因 C03 未整合必須回報失敗，不借用 PATH／本機引擎。兩種範圍皆 release_ready false；來源及歷史開發包的原 ONNX 自檢沿用，損壞 profile 也保存失敗報告。
- 最初 frozen 核心 7 項與公開 PDF 5 項通過。加強平台護欄的重建途中曾過早啟動驗收，因 executable 尚未產生而失敗；等待建置成功後重跑全過，原錯誤日誌保存，不列為產品回歸。後續對照真正原文，發現僅檢索檔名會漏掉 licenses 目錄內的 Apache-2.0.txt 等檔案，改按完整路徑擷取，並加入既有具 hash 的官方補充來源，再重建與驗收。保存時再發現 Python 授權子模組／編譯快取混入，排除後新增反例、重建與重驗，未推送不完整結果。
- 最終保存 235 份內嵌資產、40 個套件 METADATA、99 份可取得 wheel 原文、Python 原授權、256 筆 binary 來源與 75 套件系統 copyright。這是來源證據，未宣稱完成主程式公開授權、Qt／所有再散布或 native OCR 審核；原 221 份資產與三個上位 lock 不變。
- 新增 16 項，子檢核含回歸 **86/86**；真正獨立程式 **7/7**、四份公開 PDF **5/5**。從新工作目錄、空 PATH／TESSDATA_PREFIX／PYTHONPATH 實際轉換六格式，缺原生或選配 OCR 明確失敗、不產生輸出。完整 **440 項：439 通過、1 既有繁體品質預期失敗、0 跳過**。
- **C04 為 2/4 子檢核，整項未關閉，總數維持 7/12，既有 19/25。** 約 336 MiB 的 Linux bundle 共 1177 個檔案／連結，hash 與實際資料另存[本輪原始紀錄](runs/c04-build-2026-11-08/README.md)，不把大型 binary／venv／快取放 Git。[第十四份架構快照](../architecture/versions/v0.4-c04-frozen-core.md)新增保存，前十三份圖與舊附件固定。
- 舊 Windows workflow 保留，沒有觸發發行、tag／Release、正式目錄或金鑰更新；下一步 C03 原生 Tesseract／雙語模型及完整 profile，C09、Windows／GPU、繁體品質與 RAM 軟預算門檻保留。

**2026-11-08｜完成 C04 基本版依賴拆分子檢核，程式 0.8.0 → 0.8.1**

- 檢視既有打包仍使用完整開發清單，本輪先拆基本 Python 閉包：runtime 38、Linux build 47／Windows build 49 套件，原版本與全部 hash 沿用。原上位鎖定與 221 份授權資產不變，Windows 授權按 profile 引用，不冒充 Linux native／原生引擎或完整再散布審核。
- 確認 Magika 為上游必要檔案辨識功能，仍需 ONNX Runtime；Excel／其他核心仍需 NumPy，沒有直接移除。基本版不含 RapidOCR、OpenCV 等 OCR 相依與 python-docx／reportlab 測試產生工具，上游原始碼保持固定。
- 新工具從兩份專案、extras、建置輸入與平台 metadata 追蹤閉包，遇到版本衝突、缺相依、marker／extras、改動 hash／授權或選配混入時拒絕。Windows marker 在 Linux 求值有專門反例，不把 metadata 分析列為 Windows 執行通過。
- 第一輪沙箱 pip 只得到找不到套件結果，沿用相同代理與 CA 在核准執行環境重試安裝成功，沒有改網路設定或升版。建立全新、不含系統套件的基本 venv，實際只含 38 個第三方套件、兩個本地專案與 pip；檢查安裝 metadata 與固定快照一致，pip check 通過。
- 新增 15 項，含原授權／格式／核心／裝置的 **52/52** 通過；空 PATH／空 TESSDATA_PREFIX 的基本環境 **6/6**，文字／HTML／DOCX／XLSX／PPTX／原生 PDF 與 Qt 批次實測，缺原生 OCR 明確失敗且無輸出。初次實測與加強安裝 metadata 核對後的最終結果分存。完整 **424 項：423 通過、1 既有繁體品質預期失敗、0 跳過**。
- **只完成 C04 的依賴拆分子檢核，完整 C04 未關閉，總數仍 7/12，既有 19/25。** 新增[樣本、輸出、實際視窗、wheel 與日誌](runs/c04-locks-2026-11-08/README.md)及[第十三份架構快照](../architecture/versions/v0.4-c04-base-locks.md)，前十二份圖與全部先前附件固定。
- 舊 PyInstaller／Windows workflow 尚未改成基本包，未重建 frozen、native／Windows 安裝包或發布 tag／Release。C03 Tesseract 原生檔／DLL／雙語模型與授權、profile 專用打包／自檢、完整 C09 及 Windows／GPU 仍待後續，正式來源、繁體品質及 RAM 軟預算限制保留。

**2026-11-07｜完成 C10 文件分析與受管 OCR 協作，程式 0.7.0 → 0.8.0**

- 將既有精準 PDF 的逐頁分析接上 C05–C08：只有 OCR 頁才驗來源、能力、啟用版本與真實健康，原生文字／表格及空白頁不依賴選配。整份文件含後續原生頁、輸出提交持有同一租約，OCR 前後及提交前重驗；撤回或實檔變動不提交部分 Markdown。
- 桌面與 CLI 加入明確受管 CPU 後端、元件／版號偏好；指定版本須先啟用，舊設定與其他偏好保留。缺來源、版本不符或健康失敗有具體提示，不自動下載、換版或換引擎，其他批次文件繼續。
- 接通完整應用程序樹 RAM、上層 permit／取消與巢狀等待狀態。模型准入延到 OCR，外層不重複加算已配置模型；修正等待 RAM 時主視窗可能仍顯示處理中的接線。取消能回收原生程序與租約，Outcome 及 Markdown 記錄有限的元件／版本／協定／CPU 證據，輸出增加懸空連結保護。
- 初始新測試重複傳入 health_check，修正 fixture 組裝後通過；舊裝置測試 mock 未接收新增 kwargs，改為保留並驗證取消／permit 接點。第一輪真實 RAM fixture 在零預留且零額外估計時本來允許執行，改用明確超預算情境；初始失敗與中間通過日誌都分開保存，不當成產品通過證據。
- 新增 20 項，C10 **242/242**（20 新接線＋152 元件／桌面＋63 版面＋7 裝置），完整 **409 項：408 通過、1 既有繁體品質預期失敗、0 跳過**。最終手冊及提示文字調整後再跑 242 項通過；原生 CPU／Qt **10/10**，空 PATH／空 TESSDATA_PREFIX 下沿用同一 C07 frozen 元件，混合 PDF／逐格表格、RAM 暫停、使用中移除拒絕、原生取消、提交前撤回及 GUI 批次隔離都有實測。
- 新導入 **7/12（C01／C02／C05／C06／C07／C08／C10）**，既有 **19/25**；C09 仍只有三項流程子檢核，完整項目待 C03／C04 基本包自帶 OCR。[新輸入／輸出、視窗與完整過程](runs/c10-2026-11-07/README.md)及[第十二份架構快照](../architecture/versions/v0.4-c10-managed-conversion.md)另存，十一份舊圖與所有先前附件保持固定。
- 無新增依賴、重建主程式 frozen／原生包／Windows 安裝包；正式來源與發行金鑰仍未提供，測試信任根只供隔離驗收，私鑰不保存。Windows／GPU、繁體品質與 RAM 軟預算限制保留，未建立 tag／Release；後續處理基本包與 profile、完整 C09 及平台實機驗收。

**2026-11-07｜完成 C09 首次流程／RAM 三項子檢核，程式 0.6.0 → 0.7.0**

- 新增首次設定介面與生產入口的 QTimer 提示，背景離線檢查基本 CPU／雙語模型、RAM 建議、略過選配與完成紀錄。已有設定兩個套用選項預設不勾，既有路徑、後端、品質與 GPU 偏好保留；找不到引擎也能繼續基本文字功能。
- 完成才寫入 onboarding_version 1，稍後／取消不留完成標記；完成後不每次重複，仍能手動再開。針對背景檢查期間其他視窗更新，新增設定原文與記憶體基線比對，拒絕過期覆寫，舊 schema v1–v5 的原文備份沿用。
- 使用固定英文與舊 17 字繁體影像做真實 Tesseract 健康，先驗 SHA-256，限制原生時間／輸出、CPU 1 執行緒與取消回收。繁體影像保持原來品質目標，沒有重畫或放寬 ONNX 的 expectedFailure。
- 新增 22 項首次檢查通過，94 項含設定／遷移／桌面／核心回歸全過；真實 Qt／本機流程九項通過，包括儲存後空 PATH／空 TESSDATA_PREFIX 的兩頁掃描 PDF OCR、舊偏好與缺引擎文字轉換。完整 389 項為 388 通過、1 既有品質預期失敗、0 跳過。
- 第一輪瀏覽器新子檢核讀取在摺疊 details 上直接用 innerText，斷言失敗；改為展開再核對可見內容，並讓部分完成有獨立標示。初始與最終日誌分開保存，進度仍區分整項與子檢核。
- **本輪完成 C09 三個流程子檢核，完整 C09 沒有關閉，仍為 6/12**。實測引擎來自既有系統，模型由驗收預置，不能當成基本包內含雙語 OCR；該項仍缺 C03／C04，既有 **19/25** 與 Windows／GPU 門檻保留。
- [新視窗、實際 PDF／輸出、原始與最終結果](runs/c09-flow-2026-11-07/README.md)及[第十一份架構圖](../architecture/versions/v0.4-c09-first-run-flow.md)另存，前十份圖及所有先前附件保持固定。沒有新增依賴或發行包，未建立 tag／Release；可接續 C10 自動路由與元件協作。

**2026-11-07｜完成 C08 背景元件管理，程式 0.5.0 → 0.6.0**

- 接續 C07，把可信目錄、可恢復下載、交易安裝與真實 CPU 健康接進同一個選配元件視窗。可看版本／容量／授權／來源／資源與啟用狀態，明確安裝／匯入、健康、修復、回復、授權查看與確認移除；原模型介面保留。
- 將磁碟、網路與健康工作放 QThread，下載進度限頻，動作與核心鎖互斥，取消後重新讀真實狀態。Esc、關閉與父視窗關閉都先等待背景收尾；基本批次時停用管理入口，選配失敗不關閉基本轉換。
- 第一輪 22 項有一項測試誤用不符合 C05 契約的空目錄，修正為仍含其他版本的有效撤回目錄，再補到期案例；23 項新測試通過。另檢視選檔讀取並拒絕 FIFO／特殊檔，避免背景讀取無法取消。
- 準備真實 GUI／frozen 健康驗收時檢視接點，發現取消需要傳回 Cancelled，否則能力解析會把主動取消視為不健康；在 binding 保留取消語意。增加 check_health，不因檢查舊版本改變 active，保留既有設定與資料 schema。
- 最終 C08 152 項含元件／桌面回歸全過；真實 Qt＋原 C07 frozen CPU 包九項通過，安裝期間 heartbeat 持續、空 PATH、真 CPU、原文授權、原生取消與退出、再次成功、移除及基本文字轉換皆有實測。完整 367 項為 366 通過、1 既有繁體品質預期失敗、0 跳過。
- 正式元件來源仍未發布，預設不配置信任根、清楚停用未核准下載；驗收只在暫存目錄注入短效測試政策，私鑰不保存。沒有新增依賴、重建 native 包、Windows 安裝包或發布 tag／Release，Windows／GPU／繁體品質與 RAM 限制保留。
- 新導入 **6/12（C01／C02／C05／C06／C07／C08）**，既有 **19/25**。[新紀錄與畫面](runs/c08-2026-11-07/README.md)與[第十份架構快照](../architecture/versions/v0.4-c08-component-ui.md)獨立保存，先前附件及九份圖不改；接續 C09 首次啟動與基本引擎設定，再接 C10 自動路由。

**2026-11-07｜完成 C07 獨立 CPU 選配 worker，程式 0.4.0 → 0.5.0**

- 延續 C06，完成真正 CPU OCR 元件、版本化 IPC 與可信 binding。以固定模型及三個實際 CPU session 推論；控制端只處理資源、通道及檔案，不匯入 OCR runtime，C08 介面與 C10 文件路由留待接續。
- 加入 RAM 載入前准入、回壓／遲滯、CPU 執行緒與低優先權、有界訊息、逾時／取消、輸出保護及失敗隔離。worker 自己持有共享 guard，父通道失聯退出；維護／恢復取得排他 guard，新目錄逐層 fsync，保留原資料結構與舊版本紀錄。
- 第一次真正 frozen OCR 已推論成功，但 daemon stdin 持有 BufferedReader 鎖導致程序退出 abort；改用 raw fd，完成訊息、結果雜湊及退出都通過才提交。資源測試的初始資料在零 reserve 下實際允許執行，修正為明確超預算情境，再驗證資源等待失敗原因。
- 全回歸再找到 worker 提前退出後，stdin.close 緩衝 flush 的 BrokenPipeError 會覆蓋原結果並中斷清理；補上確定重現的回歸，保留原失敗日誌後重跑。最終 C07 115 項全過（含 C05／C06 92 項），完整 344 項為 343 通過、1 既有繁體品質預期失敗、0 跳過。
- 實際 Linux frozen ZIP 經 C05／C06 離線安裝與真實健康，在只有五項鎖定測試依賴、沒有 OCR／Qt 的控制端，空 PATH 完成 10 項驗收；主環境不變。ZIP 約 193 MiB／解壓約 512 MiB，另保存實際授權與原生來源；這是功能證據，非繁體品質、正式產品或 Windows／GPU 驗收。
- 新導入 **5/12（C01／C02／C05／C06／C07）**，既有 **19/25**。新增[原始結果、建置／失敗日誌與新畫面](runs/c07-2026-11-07/README.md)、[C07 架構快照](../architecture/versions/v0.4-c07-cpu-worker.md)，前八份圖與既有附件不改寫。接續 C08 元件管理介面；Windows／GPU 及繁體品質限制保留。

**2026-11-06｜完成 C06 交易安裝與維護，程式 0.3.0 → 0.4.0**

- 接上 C05 的可信包檔，新增獨立 staging、健康前後驗檔、所有權與 active／前版，使用持久化日誌協調檔案及 SQLite。提交前中斷回復原狀，提交後中斷完成清理；沒有把未知資料當成可刪暫存。
- 以核心共享／排他鎖保護使用中元件，程序退出即可釋放，不靠 PID 或時間猜測。第一輪強制退出測試發現測試收尾仍存取被終止程序的同步事件而等待，改成有界收尾後重新驗證；保留當時中斷日誌。
- C05 原先以「鎖檔消失」檢查釋放，本輪改為持久空鎖檔與驗證核心鎖可重新取得；另保留初次舊斷言失敗紀錄。這避免刪檔後出現兩個 inode 鎖，也讓新鎖不因崩潰永久阻擋。
- 完成明確修復、版本回復、必要元件與依賴移除保護，補上共用 runtime 更新的反向相容性。快取加入發布前收據與配額；未知／改動檔、片段、無收據舊檔與不明舊鎖保留，不因空間不足擅自刪除。
- 最終 C06 92 項全過（含 C05 41 項回歸），11 次實際程序退出可逐項回看；完整 321 項為 320 通過、1 既有品質預期失敗、0 跳過。官方 HTTPS／快取／離線回歸六項通過，沒有冒充 Windows／GPU 或實際 OCR worker 驗收。
- 新導入 **4/12（C01／C02／C05／C06）**，既有 **19/25**。新[驗收與中間日誌](runs/c06-2026-11-06/README.md)、[架構快照](../architecture/versions/v0.4-c06-lifecycle.md)及進度畫面另存，舊附件保持原樣；後續接 C07 CPU worker，C03／C04 Windows 證據仍待執行器。

**2026-11-06｜完成 C05 可信目錄與下載，程式 0.2.1 → 0.3.0**

- 接續檢視 C03／C04，確認其 Windows 原生 OCR 與完整 profile 門檻仍需要 Windows 執行器；未用 Linux 模擬關閉，先完成可獨立驗收的 C05 傳輸服務。
- 新增真實 Ed25519 目錄驗證、固定信任根、金鑰撤銷／輪替政策、目錄到期／版次與來源白名單。正式發行金鑰與元件目錄尚未發布；測試私鑰只留在記憶體。
- 實作取消、限次重試、強 ETag／Range 續傳、失效重來與離線匯入；完整性通過才排他發布快取，登錄只到 verified，不直接當成能執行的元件。補上傳輸期間目錄到期或金鑰撤銷的拒絕檢查。
- 第一輪測試擴充時遇到一個測試函式變數範圍錯誤，修正後重跑；前後原始日誌分開保存，不以早期結果冒充最終驗收。最後 C05 41 項全過，另以官方固定 LICENSE 實際 HTTPS／快取／離線匯入六項通過。
- 完整回歸 270 項為 269 通過、保留 1 項既有品質預期失敗、0 跳過。新導入 **3/12（C01／C02／C05）**，既有 **19/25**；實際 HTTPS 與注入 HTTP 協定證據分開，不宣稱所有續傳情境都經公開伺服器實測。
- 明確使用原鎖定清單內 cryptography 50.0.2，套件版本／雜湊與授權原文不變。[本輪附件](runs/c05-2026-11-06/README.md)及[架構快照](../architecture/versions/v0.4-c05-downloads.md)另存，先前紀錄保留；接續 C06 交易安裝與維護，桌面完整管理留 C08。

**2026-11-06｜完成 C02 舊模型與設定遷移，程式 0.2.0 → 0.2.1**

- 延續 C01，讓舊模型管理透過 adapter 保存到新登錄，先接通既有視窗，再逐步接入完整元件服務。
- 檢視時發現舊視窗會對使用者選定的模型目錄直接提供下載／移除，因此改成舊／外部目錄只讀引用。新專用空目錄須明確下載才建立受管紀錄，不因資料放在程式目錄就接管；未知檔案保留。
- 設定升為 v6，保留 v1–v5 的資源、OCR 後端及路徑，新增品質與後續元件偏好。修正「載入未來設定失敗後仍可能按儲存覆蓋」的問題；未顯示在介面的欄位也不會因調整 RAM 被歸零。
- 舊設定在明確儲存時先備份原始位元組；登錄升級先保存 SQLite 一致性快照，再交易新增模型引用表。以故障注入驗證備份／替換／升級失敗時保留舊資料，並核對明確失效 OCR 路徑不會靜默回退。
- C02 61 項全過；完整 229 項為 228 通過、保留 1 項已知品質預期失敗、0 跳過。新導入 **2/12**，既有 **19/25** 不變，Windows／GPU 實機未列完成。
- [本輪驗收、原始日誌及新畫面](runs/c02-2026-11-06/README.md)與[架構快照](../architecture/versions/v0.4-c02-migration.md)另外保存，先前附件不改寫。程式有中文說明，無新增第三方套件；接續 C03／C04 Windows 基本 OCR 與 profile。

**2026-11-06｜完成 C01 元件基礎，程式 0.1.1 → 0.2.0**

- 按架構 v0.4 開始元件化：建立不可變描述、版本／平台／依賴契約、SQLite 登錄及能力解析，先讓後續模組有共同判斷依據。
- 處理「下載完成就誤判能使用」的問題：必須重驗檔案、相容性、依賴及可信健康探針；檔案被修改、依賴失效或新舊版本不合時，撤回可用狀態。探針期間的並行更新用世代號保護，損壞資料不自動清空。
- 使用真實暫存檔及 SQLite 驗收，C01 43 項全過；完整回歸 196 項中 195 通過、保留 1 項 ONNX 繁體品質預期失敗，沒有跳過。這些是 Linux 核心證據，未冒充 Windows 或 GPU 實測。
- 更新首頁中文架構、互動進度及[新增架構快照](../architecture/versions/v0.4-c01-foundation.md)，新導入到 **1/12**，既有 **19/25** 不變；舊快照、畫面與原始日誌維持原樣。
- 本輪[逐項驗收、完整測試日誌與新畫面](runs/c01-2026-11-06/README.md)另外保存並記錄雜湊。新程式附中文責任說明，無新增第三方套件。
- 接下來做 C02 舊模型轉接與設定遷移；目前桌面仍走原模型／設定流程，下載安裝、簽章信任與管理頁繼續按後續檢核開發。

**2026-11-06｜調整開發紀錄的呈現方式**

- 將這一頁改成持續更新的開發日誌，標題簡化為「開發紀錄」，以日期記下變化與處理過程。
- 過去保存的畫面、範例、日誌與架構圖繼續保留；之後的新紀錄也從這裡整理。
- 這次只調整文件，程式與架構版本不變。

**2026-11-06｜整理先前的開發附件**

- 將先前留在雲端工作區的截圖、合成表格範例、修正前後輸出及執行日誌放進專案，方便日後回看開發過程。
- 共整理 12 張畫面、8 份範例／輸出、53 份原始日誌及 2 份觀察／語法樹紀錄。早期失敗與當時畫面維持原樣，不改寫成最新成果。
- 附件：[畫面紀錄](screenshots/README.md)／[轉換範例](examples/README.md)／[原始日誌](logs/README.md)。

**2026-11-06｜保存舊版與新版架構圖**

- 將既有核心圖、新版對話主流程圖與首頁比較圖分別保存，補上中文說明與來源。
- 後續補齊「四、模組化架構與責任」的詳細圖及模組表，與對話簡圖分開記錄。
- 各版放在 [架構圖紀錄](../architecture/README.md)，未來更新時新增快照，保留前版。

**2026-11-05｜原始碼版本 0.1.0 → 0.1.1**

- 整理 GitHub 首頁，加入繁體中文產品說明、模組架構圖、功能狀態與文件入口。
- 新增版本更新紀錄，補記先前的 Git 開發歷史；自有程式與建置腳本補充中文註解。
- 確認註解未改變執行邏輯，重新執行 Linux 功能測試：153 項中 152 通過，保留 1 項 ONNX 繁體品質預期失敗。
- 將累積的開發歷史同步到 GitHub main。架構指引仍為 0.4，這次維護更新沒有新增轉換功能。

**2026-11-05｜採用基本安裝包＋選配元件管理**

- 因應希望免指令、免掛載、安裝後即可使用的需求，將架構指引從 0.3 更新為 0.4。
- 基本包目標內含執行環境、原生格式解析、Windows Tesseract 與繁中／英文 CPU OCR；額外語言、ONNX／GPU 與進階模型按需安裝。
- 保留現有核心與桌面，新增首次精靈、元件生命週期、能力解析、獨立選配工作程序及更新協調的規劃。
- 拆包時發現核心 Magika 也依賴 ONNX Runtime，因此選配 OCR 不能直接連同核心必要 runtime 一起移除。
- 新導入工作以 C01–C12 追蹤，目前 0/12；下一段先做 C01 元件／能力／版本契約與登錄、C02 舊模型轉接與設定遷移。詳見 [架構指引](../architecture-guide.md)。

**2026-11-05｜Windows 安裝與自動驗收流程**

- 增加 Inno Setup 每位使用者安裝來源、檔案清單、安裝／解除安裝與資料保留檢查流程。
- 加入打包程式內建自我檢查，使用生成文件測試中文路徑、背景程序、原生 PDF、ONNX CPU 掃描與授權資源。
- Linux 打包版在 PATH 不提供外部工具時通過五項自我檢查；PowerShell Linux 工具測試通過九組。
- Windows 安裝包編譯、乾淨 Windows、Tesseract 原生元件整合與 GPU 實機仍待執行。相關流程保存在 [Windows 開發說明](../windows-acceptance.md)。

**2026-11-05｜改善稀疏表格與複雜閱讀順序**

- 上游公開稀疏報表曾被錯判成單欄，先保留原文字，再以表頭位置分欄，還原六欄及缺格位置，不向下補值。
- 加入跨欄標題分區與雙欄閱讀順序，並讓無框線／稀疏表格也能提供相鄰頁續表提示。
- 以四份上游公開 PDF 及生成正反例檢查欄列、金額、順序與內容遺漏／重複，版面矩陣 63 項通過。
- 此階段完成 Linux 代表性驗收，既有檢核到 19/25；任意混排、掃描表格與續表自動合併仍需擴充。[修正前後輸出](examples/README.md)可回看當時差異。

**2026-11-05｜授權清單與離線手冊**

- 整理 Windows 鎖定依賴的 58 套件、214 份授權／metadata／補充文件，加入離線操作手冊與說明選單。
- 檢查一般安裝及打包程式能讀取文件，保留原文雜湊與實際 Python runtime 授權。
- 新版基本／選配包仍須加入各自的原生元件與模型授權，最終 Windows 再散布審核尚未完成。

**2026-11-05｜逐步補強表格結構**

- 合併表格改以實體儲存格幾何判斷 rowspan／colspan，保留外框內不屬於 cell 的註記，避免遺漏文字。
- 增加跨頁候選關聯，只在表頭、欄位與頁界條件相符時提示，保留重複表頭與原資料。
- 增加對齊數值型無框線表格推測，以文章、欄位漂移及數值首列等反例避免誤判；公開 PDF 測試資產按原位元組保存。

**2026-11-05｜ONNX OCR 與雙引擎核對**

- 整合固定版本 RapidOCR／ONNX CPU 推論、模型雜湊及候選 CUDA／CPU 回退策略，GPU 分支仍需實卡驗證。
- 發現繁體樣本漏字及字形錯誤，持續保留品質預期失敗，Tesseract 維持預設。
- 加入 Tesseract 與 ONNX 雙引擎核對，保留主要原文、候選及差異，不自動修字或繁簡轉換。
- 測試中也發現 Tesseract 對稀疏短行漏字，補上分頁模式判斷與嚴格雙行回歸。[品質比較](../ocr-quality-sample.json)保留當時輸出。

**2026-11-04｜模型管理、裝置診斷與設定**

- 加入固定繁中／英文模型下載、取消、完整性驗證與受管移除，儲存引擎和模型位置，減少手動環境變數設定。
- 加入裝置診斷與 CPU 執行緒上限，區分「查到顯卡／provider」與「模型已實際使用 GPU」。
- 設定採版本化讀寫；目前 schema v5 保存資源與 OCR 偏好，後續遷移需保留使用者明確選擇的路徑與後端。

**2026-11-04｜核心、桌面原型與 PDF 精準流程**

- 建立任務契約、文字串流輸出、spawn 背景程序、取消與 RAM 准入／回壓，避免單次失敗阻斷整批。
- 整合 Microsoft MarkItDown 官方來源及固定提交，加入 Office／HTML／PDF 轉換、Qt 拖放、批次與預覽原型。
- 因原生解析無法辨識掃描頁，加入逐頁原生／OCR／空白路由、繁中／英文 Tesseract、有界重試及品質提醒。
- 建立離線進度頁、依賴鎖定與打包來源，後續持續區分 Linux 核心驗證和 Windows／GPU 實機驗收。

相關資料：[版本更新](../../CHANGELOG.md) · [架構圖](../architecture/README.md) · [目前開發進度](../development-status.md) · [附件清單](manifest.json) · [早期提交索引](history.json)

[回專案首頁](../../README.md)

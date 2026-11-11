# 版本與更新紀錄

本檔記錄每次專案更新。**程式版本以 pyproject.toml 為準；架構指引版本獨立計算。** 原始碼版本不代表已發布 Windows 安裝包、Git tag 或 GitHub Release。

## 更新中

### 2026-11-11｜候選包完整逐檔清單與CPU ZIP核對

- 程式0.19.1／架構0.4不變。相對前次只查Analysis原生檔，新增全部普通檔案的大小／SHA-256、可確認的套件／原文對照、原METADATA授權宣告及未知來源待查表；新增同一候選的可信舊報告重驗。
- CPU先包裝再核對真正ZIP（含額外NOTICE），驗全項大小／hash／CRC及descriptor；兩條CI會公開有界清單摘要和report hash，完整逐檔報告仍留artifact。
- 新22／相關87項通過，涵蓋增刪改名／同大小變更、連結／junction／特殊檔、讀取失敗、限制、來源精確比對及ZIP反例。Windows及擴充完整回歸接續；舊完整661項仍是前次來源基線。
- 檔案清單完整與runtime SBOM／授權核准分開；應用授權、Qt／Microsoft再散布與未知來源、乾淨機／人工及GPU仍待，C04 2/4、C11 2/5及7/12保持。

### 2026-11-11｜補齊建置啟動器原文與原生來源追溯

- 程式0.19.1／架構0.4不變，改動自有建置與檢核工具。相對前次，基本包與CPU選配另存實際PyInstaller原始授權及hash；原生Analysis清單新增來源SHA-256／大小與可確認的distribution版號。
- 新增兩條Windows CI必要的隨包檢核，驗原文hash、METADATA版號、啟動器與Analysis所列原生收集檔案，來源與收集後指紋分列。CPU套件表屬build來源，技術追溯接受不等於完整SBOM或再散布核准。
- [Windows兩包接受及完整661項](docs/development-records/runs/bundle-provenance-ci-2026-11-11/README.md)：660通過／1既有ONNX繁中品質預期失敗／0跳過，混合及42獨立模組全exit0；CPU追溯及功能11／同版8／跨版8／恢復6、基本包app10／安裝6／跨版11／三停點續修均接受。新16／相關65通過。
- 首輪Windows反斜線路徑拒絕後修正清單輸出，原失敗、取消run與本地fixture問題保存；公開原頁／精簡結果已歸檔，詳細登入artifact未下載。新增中文說明、更新視覺進度；C04 2/4、C11 2/5及7/12保持。
- 完整候選清單／原文對照、Qt／Microsoft runtime再散布、應用授權、乾淨機／人工與GPU仍待，沒有交付Setup、建立tag／Release或發布環境設定。

後續變更先記在此區，完成版本整理時移入對應日期與版本。每筆需包含變更、與前版差異、驗證及尚未完成事項。

### 2026-11-06｜開發紀錄改為持續日誌

- 依使用者需求，將頁面標題簡化為「開發紀錄」，以日期記錄過去與後續的開發變化及處理過程。
- 移除主頁的一次性保存核對結論與報告式小節，整理既有開發歷程並保留附件；首頁與附件返回連結統一使用「開發紀錄」。
- 程式版本 **0.1.1**、架構版本 **0.4** 不變；只調整文件，檢查連結及原有附件／架構快照雜湊，未重跑功能測試。

### 2026-11-06｜開發紀錄保存核對與補存

- 核對截至 `3d0e005` 的 18 次提交及 GitHub 完整原始碼封存，逐一比對 374 個 Git blob；本地與遠端一致，Git 物件完整性檢查通過。
- 確認四份架構快照、版本／規劃／品質／授權及安裝來源均有保存；整理於 [開發紀錄](docs/development-records/README.md)。
- 補存仍在工作區的 75 份工程產物：12 張截圖、8 份範例／輸出、53 份日誌與 2 份觀察／AST 紀錄，各附雜湊；保留早期失敗，不重寫為通過。
- 本次只做保存核對，原始碼版本 **0.1.1**、架構 **0.4**、既有 19/25 與新增 0/12 不變，未重跑或擴大 Windows／GPU 驗收。
- 不把未匯出的聊天全文、無法取得的早期草稿或依賴快取宣稱為已完整備份；範圍與限制明列於保存核對文件。

### 2026-11-06｜補存第四節完整模組架構圖

- 補存 [「四、模組化架構與責任」的詳細圖與模組表](docs/architecture/versions/v0.4-modular-architecture.md)，從固定 Git 提交逐字抽出。
- 與前次的對話主流程簡圖分別列入索引；原三份快照及其雜湊保持不變。
- 新紀錄附來源提交、原節內容、圖與文件 SHA-256，並補上首頁入口。
- 程式版本仍為 **0.1.1**、架構版本仍為 **0.4**；僅補文件，檢查原文、雜湊與連結，沒有改動轉換邏輯或驗收進度。

### 2026-11-06｜架構圖保存紀錄

- 程式原始碼版本維持 **0.1.1**，架構指引維持 **0.4**；新增文件快照，未新增程式功能。
- 建立 [架構圖版本索引](docs/architecture/README.md)，保存既有核心回溯圖、使用者指定的新版對話原圖，以及當時首頁比較圖。
- 新版保留「模組架構會保留既有核心，增加元件管理層。」下方的原節點與連線；首頁比較圖直接從固定 Git 提交抽出。
- 各份快照附中文說明、保存日期、來源及 SHA-256；後續更新新增快照，不覆寫既有紀錄。
- 驗證範圍為來源圖一致性、文件雜湊、相對連結與程式版本未變；轉換程式未修改，未重跑功能測試或變更既有驗收進度。

## 0.19.1 — 2026-11-11

相對0.19.0新增CPU維護程序真實終止／獨立恢復六案，完成Windows接受與本版Linux完整回歸；架構0.4。

- Windows CPU原功能11／同版8／跨版8／程序恢復6接受，[完整公開摘要與原頁](docs/development-records/runs/windows-cpu-recovery-ci-2026-11-11/README.md)保存。公開副本縮短以避免4096字元截斷，原完整報告不改；首輪prefix、負例fixture失敗及先前162項相關紀錄保留。
- [0.19.1全645項](docs/development-records/runs/full-regression-0.19.1-2026-11-11/README.md)：644通過、1既有ONNX繁中品質預期失敗、0跳過。混合程序exit0，41獨立模組全exit0；55固定套件、四語與三個ONNX模型hash驗證。初輪暫存driver漏main guard的無效嘗試另存，修正driver後重跑接受，產品碼與測試斷言未改。
- 同來源Windows基本包app10／安裝6／跨版11／續修3案及CI自有清理結果已補存，視覺進度與[測試安裝包準備](docs/windows-test-build-readiness.md)已更新；9鎖／模型／第三方原文及28架構圖固定。
- C04 2/4、C11 2/5、導入7/12保持。候選再散布與包內容、其他profile、乾淨機／人工／GPU、ONNX品質與RAM軟性限制保留，無Setup／tag／Release或環境設定發布。

## 0.19.0 — 2026-11-10

相對0.18.1新增CPU元件跨版本控制與Windows驗收；架構0.4，Windows跨版8/8、原功能11/11與同版維護8/8已驗。

- 元件1.0.0→1.0.1、協定仍1.0.0。可信binding依租約描述固定版號，握手與結果精確核對；只接受已列出的舊新兩版，不因major相同自動接受未知引擎。
- 原PDF／Qt驗收入口改由包內描述讀取元件版號，精確請求／來源標記／GUI偏好跟隨該版，未冒充已重跑完整PDF／Qt。
- Windows CI已以固定舊提交fd69854、各自build venv與來源建置真正兩版，通過升級／取消／固定請求／明確回復／退休與資料保留8案；原功能11／同版維護8也重新通過。[公開原頁與結果](docs/development-records/runs/windows-cpu-upgrade-ci-2026-11-10/README.md)保存，首輪取消另存。只保留七天報告，不發行worker或Setup。
- 新9／相關156項本地通過，[準備與原始日誌](docs/development-records/runs/windows-cpu-upgrade-prep-2026-11-10/README.md)保存；本版完整回歸未跑，舊611屬0.17.2。9份鎖／模型／原文不變，C04 2/4、C11 2/5、導入7/12及品質／GPU／乾淨機門檻保留。

## 0.18.1 — 2026-11-10

相對0.18.0新增Windows CPU選配同版本維護驗收8案；架構0.4，真正Windows原生功能11/11與同版維護8/8已驗。

- 沿用原生CPU11項，增加重驗／架構拒絕、使用中鎖、壞包、publish後取消回復、損壞與修復、未知資料拒刪及保留合成資料／快取後重裝。各案後核對payload hash、active、READY與交易收尾；失敗保留部分結果，不吞非預期例外。
- [真正Windows結果與原頁](docs/development-records/runs/windows-cpu-lifecycle-ci-2026-11-10/README.md)保存：八案全過，原CPU11項也通過，控制端無OCR／Qt且環境不變。只保留七天報告、不上傳產品。
- 新4／相關147項本地通過，[準備原始日誌](docs/development-records/runs/windows-cpu-lifecycle-prep-2026-11-10/README.md)保存；完整本版回歸未執行，前版完整611仍屬0.17.2。closure只更新版號，9份鎖／模型／原文不改。
- 這是同版元件維護，非跨版、強制終止／斷電、乾淨機、所有profile或GPU驗收。C04 2/4、C11 2/5、導入7/12保留，無Setup／tag／Release。

## 0.18.0 — 2026-11-10

相對0.17.2新增Windows CPU選配的獨立依賴閉包與原生建置驗證；架構0.4，Windows CPU獨立選配11/11已驗。

- CPU建置24／精簡控制端5套件，沿用原hash／wheel METADATA、核對實際核心依賴與97／30份原notice或metadata；不混Qt／GPU與主轉換器。
- 獨立Windows2022 CI已以兩個venv通過真正frozen／簽章離線／空PATH的11項健康、推論、取消、RAM、移除與父管道EOF退出／鎖釋放。Windows原生庫在共享鎖內、背景reader前初始化，原期限／RAM准入保留；控制端無OCR且環境不變。[實跑原頁與紀錄](docs/development-records/runs/windows-cpu-ci-2026-11-10/README.md)，前四輪失敗另存。只上傳七天報告，不發行ZIP／模型／Setup。
- 新15、相關143項在鎖定venv正常退出；[原始準備紀錄](docs/development-records/runs/windows-cpu-prep-2026-11-10/README.md)。本輪完整回歸未執行，舊611保留0.17.2歸屬；全profile／GPU／品質與乾淨機另驗，C04 2/4、C11 2/5、完整7/12不提高，28份舊圖保持固定。

## 0.17.2 — 2026-11-09

2026-11-10更新Windows驗收紀錄。相對0.17.1完成可拋棄Windows CI自身中斷產物的受限清理，架構0.4；普通Setup未加入通配清理，C11仍2/5／完整7/12。

- Windows三案清理3/3，實際清1份／殘留0；真鎖檔拒絕，未知同類檔名／同bytes合成文件保持原bytes。原檔handle核對身分／hash、拒寫與rename後delete-on-close，不讀外部JSON授權。[Windows證據](docs/development-records/runs/temporary-cleanup-ci-2026-11-10/README.md)。
- 基本app10、安裝／修復／移除6、真跨版11及三停點續修各10亦通過。本地14／相關39；完整611（610通過、1既有ONNX品質預期失敗、0跳過）混合與36模組exit0，[準備紀錄](docs/development-records/runs/temporary-cleanup-prep-2026-11-09/README.md)保持原狀。
- closure只改來源版號，7鎖／模型／第三方原文與28份架構圖不改。清理只供CI自身產物；一般Setup暫存政策、全profile、乾淨機／人工／GPU及正式發行另驗，無Setup／tag／Release。

## 0.17.1 — 2026-11-09

相對0.17.0修正Qt視窗延留至全域cleanup的退出異常，架構0.4；功能導入仍7/12、C11仍2/5。

- 主GUI入口正常關閉時在Qt事件迴圈內釋放父子視窗；忙碌時仍先取消並等待收尾。六組Qt測試各自釋放視窗／等待執行緒，不依賴全域wrapper清理順序。
- 新3個真Qt子程序檢核，前2個修前失敗、修後全過；管理23項連續12輪exit0。混合597與35模組全exit0，596通過、1既有ONNX品質預期失敗、0跳過。[原始證據](docs/development-records/runs/qt-lifecycle-2026-11-09/README.md)／[說明](docs/qt-lifecycle.md)。首次模型路徑與closure未齊的失敗也保存。
- closure只更新來源版號，依賴鎖／模型／第三方原文不變；視覺進度同步。28份架構圖不變，Windows0.17.1待新CI，乾淨機／全profile／人工／GPU、Inno暫存與ONNX品質門檻保留，未建立正式Setup／tag／Release。

## 0.17.0 — 2026-11-09

相對0.16.0完成基本包程序中斷後明確續修，架構0.4；C11第三項仍待各profile，維持2/5／完整7/12／歷史19/25。

- [Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42578549106)真正終止自己Setup PID樹，在intent／第一檔／payload寫完但舊metadata未清三停點 **3/3**；以普通匹配Setup明確續修，各app **10/10**、受管hash／registry／移除與合成資料／未知文件保留通過。CI-only停點變體與一般恢復Setup分開，不是只改檔案假裝中斷。
- 固定source hash intent／完整暫存rename、原位置／匹配payload與明確續修、最終全hash後清標記、frozen入口未完成時退出3。拒靜默未確認續修及不同metadata；原版0.16固定990e600／原controller／spec／generator獨立建置，基本資料夾／安裝後app各10項、安裝6段與跨版11段也通過。
- 第一次Inno引入檔誤用主設定分號註解，已改Pascal //並以Windows重驗；[原始失敗](docs/development-records/runs/c11-recovery-attempt1-2026-11-09/README.md)保留，不改成通過。
- 第二輪中斷1案接受，第二案被Inno暫存物攔下；改精確hash及操作前／停點／自己PID建立收據，只保留，不通配忽略或刪除。最終仍保留1份，完整暫存清理未完成；[第二輪失敗及收據回歸](docs/development-records/runs/c11-recovery-attempt2-2026-11-09/README.md)保存。
- 新增15、相關180/180；全594斷言593＋1既有ONNX品質預期失敗，但Qt管理23項全過後exit -11，原整輪不接受；單獨補驗23正常exit0，根因仍待查。[180相關與594原始紀錄](docs/development-records/runs/c11-recovery-attempt2-2026-11-09/README.md)／[首次591與23項補驗](docs/development-records/runs/c11-recovery-prep-2026-11-09/README.md)／[Windows實測](docs/development-records/runs/c11-recovery-2026-11-09/README.md)／[指引](docs/base-recovery-ci.md)保存。
- 第二十八份架構圖與視覺進度同步，前27圖／歷史紀錄／7鎖／221授權／233資料固定。不是斷電／OS重啟、壞metadata、任意故障時點、自動回滾、全profile／乾淨機／人工UI或標準帳戶完成；完整artifact七天保留未下載，無Setup／tag／Release發行。

## 0.16.0 — 2026-11-09

相對0.15.0完成基本包真跨版本升級／明確回復CI，架構0.4；C11將跨版／profile合併項拆分，為2/5，完整7/12／歷史19/25。

- [Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42557368030)完成獨立前版43cf811原source／controller建置與原installer初裝 → 真升級0.16 → 明確回復真正0.15 payload → 再升級／移除，跨版 **11/11**；原版、升級後與回復後installed app各10項，基本包與同版安裝6段亦通過。
- 過期空dist-info目錄也精確移除，避免Python版本解析被遮蔽；若舊目錄內有未知內容先拒絕，並固定主要failed_step避免cleanup蓋過錯誤。[第二輪失敗及真實metadata負向控制](docs/development-records/runs/c11-upgrade-attempt2-2026-11-09/README.md)保存。
- 可信source catalog靜態規則、原位置／逐目標父鏈reparse保護、未指定降版／改catalog／改過期檔／新路徑未知檔衝突拒絕，真Windows junction不穿透；只刪精確hash未變的前版過期檔。實際app_version、全catalog／registry／捷徑與合成資料／未知文件保留已驗。
- 初次Inno編譯曾因ExcludeTrailingBackslash非公開函式失敗，已改官方RemoveBackslashUnlessRoot並重驗；[原始失敗](docs/development-records/runs/c11-upgrade-attempt1-2026-11-09/README.md)保留，不倒填為通過。
- 新增11項、相關165/165；33模組579隔離（578通過、1既有ONNX繁體品質預期失敗），最終165相關及579全隔離再驗。相容回復installer與原0.15 installer分開；這是明確跨版重裝，不是中斷自動回滾、全profile／乾淨機／人工UI或標準帳戶完成。
- [準備與回歸](docs/development-records/runs/c11-upgrade-prep-2026-11-09/README.md)、[Windows實測](docs/development-records/runs/c11-upgrade-2026-11-09/README.md)、[指引](docs/base-upgrade-ci.md)、第二十六份圖與視覺進度同步。前25份圖、既有紀錄／7鎖／221授權／233資料／vendor保持原bytes；完整artifact七天保留未下載，Setup不入Git／不發行，Linux混合teardown、品質／GPU／RAM限制保留。

## 0.15.0 — 2026-11-09

相對0.14.0，完成 **C11 hosted基本包安裝／同版修復／移除子檢核（1/4）**，架構0.4；完整導入仍7/12，歷史19/25。

- 獨立per-user Inno基本包預覽安裝器／不同AppId與版本化catalog，拒絕既有安裝、路徑別名／連結／未知檔案，信任同次建置來源而非可更改的安裝catalog；不遞迴刪除使用者資料，舊手動發行流程不動。
- [Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42542464205)真實通過：基本資料夾10項、安裝後app10項，以及安裝生命週期6段。中文路徑、1652受管檔／註冊／捷徑、刪入口與損模型後同版修復／四語自檢、移除及資料哨兵／未知文件保留皆驗證。
- 新增13項、本地154/154；32模組568隔離回歸（567通過、1既有ONNX繁體品質預期失敗）均正常exit0。可重用隔離runner、UTF-16 Inno日誌與分離的base／installer／overall旗標，防止基礎成功掩蓋安裝失敗。
- [準備](docs/development-records/runs/c11-installer-prep-2026-11-09/README.md)、[實測原始紀錄](docs/development-records/runs/c11-installer-2026-11-09/README.md)、[指引](docs/base-installer-ci.md)、[第二十四份圖](docs/architecture/versions/v0.4-base-installer-ci.md)及進度同步。Inno授權原文從官方固定source取得且SHA與runner一致，compiler／Setup／catalog hash保留；binary不入庫，不提供Setup發行／tag／Release。
- 仍待真升級／回復、各profile、無Python乾淨機離線、標準帳戶與人工UI；完整C11、C03／C04／C09未關閉。原23份圖、7份lock、221份授權與233份資料固定；Linux混合teardown、ONNX品質、GPU／RAM軟預算及最終再散布限制保留。

## 0.14.0 — 2026-11-08／2026-11-09

相對 **0.13.0** 新增可重跑的 Windows 基本包建置／驗證，架構 **0.4**。**2026-11-09 真正 Windows CI 10/10 通過**；完整導入仍 7/12（C03 3/4、C04 2/4、C09 3/4），歷史基線 19/25。

- 新獨立 main push CI，以固定來源／工具／四語模型、hash 與來源 receipt 重建原生候選，再由 Windows 2022 打包基本 app；contents:read，不觸發舊手動安裝包或建立 Release。
- 固定 Git checkout 原位元組、自有 Windows UTF-8 manifest／RC、Python frozen UTF-8 mode、PDF 原生診斷明確解碼；OCR 本文仍嚴格 UTF-8。Qt 驗收在背景收尾後重送正常關閉，25 秒總期限與 exit0 條件不放寬。
- [CI #7](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42539123115) 真正驗過四語健康／掃描、中文空格搬移、UTF-8 路徑／CLI／偏好、缺損模型／EXE 不回退及缺選配、Qt 視窗開啟及正常退出。下載曾於 #6 失敗、未進 Windows；補存早期日誌與 pipefail，本輪下載重建成功，不虛構舊失敗根因。
- 相對前版新增 **28 項**，相關 **141/141**；Linux 31 模組 **555 項：554 通過、1 既有 ONNX 繁體品質預期失敗**，各 child 正常 exit0。混合測試曾在斷言完成後 native teardown exit139；LLDB 下本輪正常退出、未重現，原因仍待查，不列已修復。
- 原始成功／失敗分存於[開發紀錄](docs/development-records/README.md)，補[第二十二份圖](docs/architecture/versions/v0.4-windows-base-ci.md)及視覺進度；[Windows 實測紀錄](docs/development-records/runs/windows-base-ci-2026-11-09/README.md)僅永久保存已取得的公開證據，未宣稱下載需登入的 artifact。
- hosted runner 已有 Python，不是乾淨機；完整安裝生命週期、人工 UI、各選配 profile、GPU、ONNX 繁體品質及 RAM 軟預算限制保留。沒有 Setup／tag／Release；既有來源、附件、21 份舊圖、7 份 lock、221 份授權及 233 份資料保持，binary／模型／憑證不入庫。

## 0.13.0 — 2026-11-08

相對 **0.12.0** 完成 C03 內含四語基本包／離線自動解析的 **Linux 子檢核**，架構 **0.4**；**C03 2/4 → 3/4**，完整項仍未關閉，總數 **7/12**、既有 **19/25**，C04 2/4、C09 3/4。

- 離線組裝固定 Windows 最小候選＋四語與原文，另明確準備 Linux 開發 payload；同平台才可接入 base assets／PyInstaller，原生入口走 BINARY dependency analysis 並保存實際相依來源。schema 2 profile 驗整包與固定模型，舊 core schema 1 行為保留。
- 桌面／CLI／首次設定自動解析內含路徑，搬移後不沿用舊絕對位置；明確自備引擎／模型與選語保留，內含模型只讀顯示。缺檔／篡改／平台錯誤／引擎替換連結拒絕，不借用 PATH；文字轉換仍可用。設定 schema 7 與原四語模型／品質樣本固定。
- full 自檢真正做四語健康與四份掃描 PDF，core 不宣稱執行 OCR；兩者仍 release_ready false。新增 **27 項**，相關回歸 **185/185**；真正 Linux frozen **12/12**，source Qt／首次 **3/3**，完整 **527 項：526 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。
- [本輪紀錄](docs/development-records/runs/c03-bundle-2026-11-08/README.md)保存初始測試與 pip 重裝並行造成的匯入失敗、驗收工具誤猜 Leptonica soname、Qt harness 類名錯誤及更正後的最終結果。另補自備模型只驗所選語言的反例後重裝／重建／回歸；視覺檢查再修正長路徑模型視窗裁切並重建／重驗，未混作同一次。更新[內含包指引](docs/bundled-base.md)、離線手冊、中文封面、[第十八份快照](docs/architecture/versions/v0.4-c03-bundled-ocr.md)與視覺進度。
- Linux 引擎 5.5.0 與 Windows 候選 5.5.3 分開；未執行 Windows PE／安裝包、GPU、tag／Release 或手動發行。舊圖、舊附件、七份 lock、原 221 份授權與繁體目標不變；沒有將 binary／模型／venv 入庫。下一步原生 Windows 與各 profile／完整首次流程驗收。

## 0.12.0 — 2026-11-08

相對 **0.11.0** 完成 C03 最小原生來源／授權原文準備子檢核，架構 **0.4**；**C03 1/4 → 2/4**，完整 C03／C04／C09 未關閉，總數仍 **7/12**、既有 **19/25**。

- 舊 installer 建置採未鎖版 MSYS2，32 DLL 證據缺口仍阻擋；另從固定 Tesseract 5.5.3、Leptonica 1.87.0、libpng 1.6.59、zlib 1.4 與具官方發布 digest 的 LLVM-MinGW 建立最小靜態 Windows x64 候選，無第三方 DLL 靜態相依，未執行 PE。
- 新增離線建置工具、來源契約及 21 份原文／工具鏈來源文字；有界解包、固定輸入、私有目錄、實際生成標頭、26 個 linker 輸入與 runtime 原文對應。處理靜態庫新檔名、交叉探針、libc++ 標頭、Winsock 大小寫與 linker archive／member 別名；不改上游或主程式 profile。
- 新增 **22 項**，含回歸 **86/86**；真實空目錄交叉建置及來源／靜態 **8/8**，完整 **500 項：499 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。初始失敗、手動中間產物與最終無人介入建置分存於[本輪紀錄](docs/development-records/runs/c03-minimal-source-2026-11-08/README.md)，不混列驗收。
- 更新[最小來源指引](docs/minimal-native-build.md)、決策、中文封面、[第十七份快照](docs/architecture/versions/v0.4-c03-minimal-source.md)與視覺進度；舊紀錄、十六份圖、七份 lock、原 221 份授權與品質基線固定。binary／工具／模型不放 Git；無新增產品依賴、Windows／GPU 執行、主 frozen／安裝包、tag／Release 或手動發行。後續整合四語基本包與 Windows，最終再散布審查仍待主包／平台。

## 0.11.0 — 2026-11-08

相對 **0.10.0** 完成 C03 Windows 原生來源／DLL **靜態檢查機制**，架構 **0.4**；來源／授權子檢核仍未完成，C03 **1/4**、C04 **2/4**、C09 **3/4**，總數 **7/12**、既有 **19/25**。

- 固定官方 Tesseract 5.5.3 Windows installer、發布 digest、56 個 AMD64 PE 及三份原文 hash；新增有界 import／delay-import、入口閉包、缺 DLL／連結／篡改拒絕，且不使用 PATH 補檔、不執行 EXE／DLL。
- 真實入口閉包 34 個、靜態未使用 22 個；32 DLL 尚缺逐檔來源／授權對應。Tesseract Apache 原文只映射已確認的兩檔，待審候選一律阻擋封裝，修改報告旗標不能核准；未加入基本包或驗證 Authenticode／動態載入。
- 新增 **20 項**，機制含回歸 **64/64**，實際來源靜態 **7/7**（含發布 digest 與 objdump），要求再散布正確退出 1。完整 **478 項：477 通過、1 既有繁體品質預期失敗、0 跳過**。實檔測試發現 MinGW DLL 名稱含 `+`、連結拒絕錯誤型別未正規化，修正後重驗；初始及最終[紀錄均保存](docs/development-records/runs/c03-native-static-2026-11-08/README.md)。
- 更新[來源指引](docs/windows-native-intake.md)、決策、中文封面、[第十六份架構快照](docs/architecture/versions/v0.4-c03-native-static.md)與互動進度，修正目標橫幅仍寫雙語的遺漏為四語；舊圖、紀錄、七份 lock、原 221 份授權資產與四語品質基線固定。沒有新增 Python 依賴、重建 frozen／Windows 包、執行 GPU 或發行 tag／Release；後續補 DLL 證據或最小原生建置，再驗四語整包與 Windows。

## 0.10.0 — 2026-11-08

相對 **0.9.0** 新增繁中／英文／日文／韓文模型與語言選擇，架構 **0.4**。依使用者需求擴充基本包語言目標；C03 完成四語本機子檢核 **1/4**，完整 Windows 原生整合仍未完成，總數 **7/12**，既有 **19/25**。

- 新增獨立四語固定清單、同一官方提交下的 jpn／kor 模型 hash，原三檔清單不變。四語模型／授權合計 10,639,763 bytes；使用新受管目錄與 manifest hash，不接管或修改舊／外部資料，移除保留未知檔案。
- 桌面及 CLI 支援單語／混合選擇，語言順序傳入 Tesseract，明確選語缺模型即失敗，OCR 頁附來源語言註記。四語混合不冒充自動分類；日韓搭配未驗 ONNX 後端時明確拒絕，不換引擎，原生頁不要求 OCR。
- 設定升至 v7，v1–v6 載入不寫檔，明確儲存前完整原文備份；舊相容預設、引擎／模型路徑、RAM、品質、元件偏好與首次標記保留。新增日韓固定健康樣本，所選模型各自健康，原繁中品質目標未變。
- 新增 **18 項**，語言／遷移／模型／桌面／首次／PDF／核心 **138/138**；真正本機 Tesseract／Qt／CLI **10/10**，四種單語與固定四頁混合原文符合。全專案 **458 項：457 通過、1 既有繁體品質預期失敗、0 跳過**，不當成一般文件準確率。
- 新增[四語指南](docs/four-language-ocr.md)、[需求決策](docs/decisions/0003-four-language-ocr.md)、[第十五份架構快照](docs/architecture/versions/v0.4-c03-four-languages.md)與[樣本／輸出／實際視窗／來源紀錄](docs/development-records/runs/c03-languages-2026-11-08/README.md)，中文封面與視覺進度同步。原十四份圖、舊紀錄、上位鎖定與原授權資產不變。
- 無新增 Python 依賴；打包來源補四語目錄與新健康資產，但未重建 frozen／Windows 安裝包。實測使用既有 Linux Tesseract，未冒充 Windows 自帶引擎；完整 C03／C04／C09、Windows／GPU 與正式來源保留，沒有 tag／Release 或手動發行。

## 0.9.0 — 2026-11-08

相對 **0.8.1** 完成 C04 第二項子檢核：Linux 基本核心 PyInstaller／依 profile 自檢，架構 **0.4**。C04 **1/4 → 2/4**，完整 C04／C09 未關閉，總數仍 **7/12**，既有 **19/25**。

- 新增基本 `base.spec`、嚴格獨立 build 環境／版本驗證與資產準備器，內嵌 38 個固定 runtime、兩個本地專案及 235 份資產 hash；沒有 RapidOCR、OpenCV 或 OCR 模型，Magika 必要 ONNX Runtime 保留。
- 自檢分 core／full：基本核心四項通過，完整自檢因 C03 未整合原生 OCR 必須失敗，兩者皆 release_ready false。舊來源／開發包五項 ONNX 自檢沿用；損壞 profile 仍保存失敗報告，既有報告不覆寫。
- 保存實際 40 個 runtime／本地專案 METADATA、99 份 wheel 授權／原文、固定官方補充文字與 Python 原授權；另列 256 筆 binary 來源與 75 套件系統 copyright。缺少主程式公開授權、完整再散布／Qt／native 清單審核仍保留，不把原文存在當成發行核准。
- 新增 **16 項**，子檢核含診斷／依賴／授權／格式／核心／裝置／Qt **86/86**；真正 frozen 程式 **7/7**，空 PATH／新工作目錄的六格式、core／full 語意與缺 OCR 拒絕，另有公開 PDF **5/5**。全專案 **440 項：439 通過、1 既有繁體品質預期失敗、0 跳過**。
- 檢視實際授權後修正只看檔名而漏掉 licenses 目錄內原文的擷取，補官方固定來源再重建。保存時再發現 Python 授權子模組／編譯快取混入，排除後新增反例、重建與重驗，未推送不完整結果。最終 bundle 約 336 MiB，1177 個檔案／連結列 hash；binary 本體保留工作區、不放 Git。過早啟動驗收的編排錯誤、早期 7／5 通過及最終結果分開保存於[本輪紀錄](docs/development-records/runs/c04-build-2026-11-08/README.md)。
- 更新中文封面、[第十四份快照](docs/architecture/versions/v0.4-c04-frozen-core.md)、[profile 指南](docs/packaging-profiles.md)與視覺進度。原十三份圖、上位 lock、第三方原資產與舊紀錄保持固定；原 Windows 開發 workflow 未切換，沒有 Windows／GPU、tag／Release 或手動發行。

## 0.8.1 — 2026-11-08

相對 **0.8.0** 完成 C04 的基本版 Python 依賴拆分子檢核，架構 **0.4**。完整 C04／C09 仍待原生基本包／profile／Windows，已驗收維持 **7/12**，既有 **19/25**。

- 新增 base runtime／build 規格、Linux／Windows marker 與 metadata 快照、四份雜湊鎖定及離線驗證工具。runtime 各 38 套件，Linux build 47、Windows build 49；原 55／58 套件上位鎖定、版號與 SHA-256 不變。
- 保留 Magika 必要 ONNX Runtime／NumPy，拆除 RapidOCR 及 OCR 相依、測試產生工具；不修改上游或把檔案辨識 runtime 當成 OCR 可用。分開列出原 Windows 授權引用，非 Linux binary／原生引擎／最終 SBOM 驗收。
- 新增 **15 項** extras／平台／閉包／衝突／證據反例，子檢核加原授權／格式／核心／裝置 **52/52**；乾淨基本 venv **6/6**，核對 38 套件及安裝 metadata、pip check、空 PATH 六格式與 Qt 批次，缺 native OCR 明確拒絕。全專案 **424 項：423 通過、1 既有繁體品質預期失敗、0 跳過**。
- 新增[profile 指南](docs/packaging-profiles.md)、[第十三份架構快照](docs/architecture/versions/v0.4-c04-base-locks.md)、C04 部分完成視覺與[原始紀錄／樣本／本地 wheel](docs/development-records/runs/c04-locks-2026-11-08/README.md)。最初沙箱安裝未取得套件，沿用原代理於核准執行環境重試成功，前後日誌分存；初次輪與後續 metadata 加強的實際驗收都保留。
- 未改舊 Windows 建置入口，未重建 frozen／native／Windows 安裝包，沒有 tag／Release、正式目錄或手動發行。Windows／GPU、繁體品質與 RAM 軟預算限制保留；下一段接 profile 打包／自檢與 C03 原生引擎。

## 0.8.0 — 2026-11-07

相對 **0.7.0** 完成 C10 自動分析與受管元件協作，架構 **0.4**。新導入 **6/12 → 7/12（C01／C02／C05／C06／C07／C08／C10）**，既有 **19/25**；完整 C09 仍待 C03／C04 基本包自帶雙語 OCR。

- 精準 PDF 只在 OCR 頁取得可信能力及啟用版本，原生／空白頁沿用原流程。文件與輸出提交全程固定 C06 租約，OCR 前後及提交前重驗目錄／實檔；撤回、版本不符及失敗不留下部分輸出。
- 桌面與 CLI 新增明確的受管 CPU OCR、元件 ID／版號偏好，版本須先啟用，不自行換版、下載或更換後端。舊 Tesseract 預設、設定 schema v6 與其他偏好保留；單份文件失敗不阻擋其餘批次。
- C07 接回上層 permit／取消及整棵應用程序樹 RAM，模型需求延後到 OCR 准入，避免執行中重複估算。健康與頁面的等待資源狀態回傳主視窗；Outcome 與 Markdown 保存有界元件來源證據。新增既有／懸空輸出連結保護。
- 新增 **20 項**接線／資源／版本／提交／桌面測試；C10 **242/242**（含原元件／桌面、63 項版面及裝置回歸），真實 frozen CPU／Qt **10/10**。全專案 **409 項：408 通過、1 既有繁體品質預期失敗、0 跳過**；手冊文字更新後另重跑 242 項全過。
- 真正驗收沿用相同 C07 元件 1.0.0／協定 1.0.0，在空 PATH／空 TESSDATA_PREFIX 下完成混合 PDF、表格、RAM 暫停與維護拒絕、原生取消、提交前撤回及 GUI 批次隔離。初始測試 fixture／舊 mock 失敗與中間結果另存於[本輪紀錄](docs/development-records/runs/c10-2026-11-07/README.md)。
- 更新中文架構、[第十二份快照](docs/architecture/versions/v0.4-c10-managed-conversion.md)、[接線指南](docs/managed-conversion.md)、離線手冊與互動進度；十一份舊圖、既有附件、依賴鎖定與授權保持固定。無新增依賴或重建原生／主程式 frozen／Windows 包。
- 正式目錄與發行金鑰尚未發布，預設來源仍未配置；驗收私鑰僅在記憶體。Windows／GPU、繁體品質與 RAM 軟性預算限制保留；沒有 tag／Release 或手動 Windows 發行。後續接 C03／C04 基本包、完整 C09 及平台驗收。

## 0.7.0 — 2026-11-07

相對 **0.6.0** 完成 C09 首次流程的三項子檢核，架構 **0.4**。**完整 C09 仍待 C03／C04 的基本包內含雙語 OCR，已驗收維持 6/12**，既有 **19/25**。

- 新增首次設定介面與主入口 QTimer：背景離線檢查、RAM 建議、保留既有偏好、明確完成才儲存版本 1、略過選配與已完成不重複；可稍後或手動重開。
- 使用明確路徑或本機 PATH，只讀模型候選；版本／語言及真實繁中／英文合成健康、原生逾時／輸出界限與取消。缺引擎不冒充 ready，仍能完成流程並使用基本文字轉換，不自動下載或啟用 GPU。
- 設定 schema v6 不變，新增 expected_raw 與視窗基線比對，保護檢查期間的新偏好；原 v1–v5 備份沿用，已指定路徑與後端不被替換。新增的繁體健康影像與舊固定品質樣本逐位元組相同。
- 新增 **22 項**，流程／設定／遷移／桌面／核心 **94/94**；真正 Qt／系統 Tesseract 流程 **9/9**，包含空 PATH／空 TESSDATA_PREFIX 的兩頁掃描 OCR、偏好保留與缺引擎文字功能。全專案 **389 項，388 通過、1 既有繁體品質預期失敗、0 跳過**。
- 真實流程明列使用既有系統引擎與驗收預備模型，`full_c09_complete: false`；不把流程完成標記當成基本包已自帶 OCR。無新增依賴，未重建主程式 frozen、原生包或 Windows 安裝包，Windows／GPU 與正式來源門檻保留。
- 更新首頁中文架構、[第十一份快照](docs/architecture/versions/v0.4-c09-first-run-flow.md)、[首次流程指南](docs/onboarding.md)、離線手冊及[本輪紀錄](docs/development-records/runs/c09-flow-2026-11-07/README.md)。進度頁可展開子檢核，完整 C09 保持未完成；保存初次對摺疊元素直接讀取的瀏覽器檢查失敗，改成展開後驗證。
- 未建立 tag／Release 或觸發手動 Windows 發行。下一段可接 C10 自動文件分析／元件協作，C09 全項待基本包證據。

## 0.6.0 — 2026-11-07

相對 **0.5.0** 完成 C08 背景元件管理介面；架構 **0.4**。新導入 **5/12 → 6/12（C01／C02／C05／C06／C07／C08）**，既有 **19/25**。

- 主視窗新增「選配元件管理」：版本、必要／選配、容量、來源、授權、資源與健康狀態；明確匯入／更新目錄、下載／離線安裝、健康、修復、啟用／回復、授權原文、確認移除及維護恢復。
- `components.management` 橋接 C05–C07，QThread 背景操作、下載進度限頻、管理核心鎖、失敗後實況更新、取消與視窗關閉等待收尾；目錄有界讀取並拒絕連結／FIFO，授權核對後純文字顯示。
- 新增不切 active 的 `check_health()`；修正原生健康取消被當成不健康的語意，取消傳回 Cancelled。設定 v6／登錄 schema 2／維護 schema 1 保留；主程式 spec 補 metadata，未重建主程式 frozen／Windows 安裝包。
- C08 **152/152**（23 項新服務／Qt＋115 項 C05–C07＋14 項桌面／說明）；真正 Qt／frozen CPU **9/9**，空 PATH 下安裝／健康、授權、原生取消與退出、恢復成功、移除及基本文字轉換。全專案 **367 項：366 通過、1 既有繁體品質預期失敗、0 跳過**。
- 初始測試用了 C05 不允許的空目錄，改成有效撤回情境，補到期／特殊檔反例；[原始與最終日誌／視窗](docs/development-records/runs/c08-2026-11-07/README.md)另存。首頁中文架構、[第十份快照](docs/architecture/versions/v0.4-c08-component-ui.md)、視覺進度與離線手冊同步更新，九份舊圖及先前附件保持固定。
- 正式目錄／發行金鑰尚未提供；預設來源未配置，不內建測試金鑰或開放任意信任來源。無新增依賴，沿用同一 C07 開發 ZIP 與原鎖定／授權；Windows／GPU、繁體品質與 RAM 軟預算限制保留。接續 C09 首次啟動與基本引擎設定，文件自動路由留 C10；未建立 tag／Release 或啟動手動 Windows 發行。

## 0.5.0 — 2026-11-07

相對 **0.4.0** 完成 C07 獨立 CPU 選配 worker；架構仍 **0.4**。新導入 **4/12 → 5/12（C01／C02／C05／C06／C07）**，既有 **19/25**。

- 新增 `component_workers`：v1 有界 JSON-lines、可信固定入口、CPU／模型與結果雜湊驗證、正常退出檢查、RAM 准入／回壓／遲滯、執行緒、逾時／取消及程序樹清理。每工作一個獨立 runtime，不改主程式套件。
- C06 接上 worker 自己持有的共享 guard；維護／恢復／切換取得排他 guard，父程序失聯後不刪改仍在使用的元件。新增目錄逐層 fsync；登錄 schema 2、設定 v6 不變。
- 新增真正 PyInstaller CPU worker、C01 ZIP／描述工具、原始授權／實際 binary 來源證據及最小控制端測試 lock；無新增 runtime 依賴，原 58 套件／214 份授權原文與鎖定不變。開發 ZIP 約 193 MiB／解壓約 512 MiB，原生 ZIP 不加入 Git。
- C07 **115/115**（23 項新 worker＋92 項 C05／C06 回歸）；另於無 ONNX／RapidOCR／NumPy／Pillow／Qt 的控制端，空 PATH 實際 frozen 驗收 **10/10**，三個 session 使用 CPU、環境前後不變。
- 完整 **344 項：343 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。修正 daemon stdin 在退出時持有 buffered lock 導致 abort，以及已退出程序收尾的 `BrokenPipeError`；保留失敗過程與新增回歸證據於[本輪紀錄](docs/development-records/runs/c07-2026-11-07/README.md)。
- 更新首頁中文架構、獨立新快照、里程碑／模組視覺化與開發日誌。C08 元件介面、C09 精靈與 C10 自動路由仍待後續；C03／C04 Windows profile 及 Windows／GPU／物理斷電未實測。英文健康通過不代表繁體品質達標，RAM 仍是軟性預算。
- 只同步原始碼及證據；未重建主程式 frozen 或 Windows 安裝包，沒有正式目錄／發行金鑰、tag 或 Release。原生再散布、專案授權與包體積縮減仍待處理。

## 0.4.0 — 2026-11-06

相對 **0.3.0** 完成 C06 交易維護 API；架構仍 **0.4**。新導入 **3/12 → 4/12（C01／C02／C05／C06）**，既有 **19/25**，C03／C04 Windows 門檻保留。

- 新增受限 ZIP32 staging、檔案清單／大小／SHA-256 與健康檢查、journal 協調恢復、所有權及 active／前版原子切換；失敗保留原版本，可重新驗證後回復版本。
- 新增程序生命週期的共享使用租約／排他維護鎖，修復、必要元件／依賴移除保護、反向相容性及取消；未知檔案／目錄不接管或遞迴刪除。維護日誌獨立 schema 1，原登錄 schema 2／設定 v6 保留。
- C05 下載改採持久核心鎖，加入發布前快取收據、使用租約與 8 GiB 預設配額，只回收可確認所有權且未修改的完整包。舊不明鎖、片段、未知及改動資料不自動刪除。
- C06 **92/92**（51 項新檢核＋41 項 C05 回歸），記錄 **11 次真實子程序退出**；完整 **321 項，320 通過、1 既有品質預期失敗、0 跳過**，官方 HTTPS 回歸 **6/6**。原始與中間日誌、進度截圖及 SHA-256 存於 [本輪紀錄](docs/development-records/runs/c06-2026-11-06/README.md)。
- 更新中文責任說明、首頁模組圖與新固定快照，先前快照／附件保留。無新增依賴，未建置 frozen／Windows、未驗收物理斷電或 GPU；實際 worker、GUI／轉換租約接線待 C07／C08／C10，不建立 tag、Release 或觸發發行工作流程。

## 0.3.0 — 2026-11-06

相對 **0.2.1** 完成 C05 傳輸服務；架構 **0.4**，新導入 **2/12 → 3/12**，完成項為 C01／C02／C05。C03／C04 Windows 門檻保留，既有 **19/25** 不變。

- 新增 Ed25519 可信目錄、應用程式固定公鑰／撤銷／最低版本政策、到期與同版內容保護，以及 HTTPS 來源／重新導向白名單。
- 新增取消、限次重試、固定緩衝與大小／磁碟限制、強 ETag／Range 續傳、失效重來、離線匯入及完整快取重驗；傳輸期間目錄失效亦不發布包檔。
- 下載僅接入 C01 登錄的 verified 狀態，不解壓或執行；安裝生命週期及桌面元件管理仍待 C06／C08。正式目錄／發行金鑰未發布，驗收使用一次性記憶體測試金鑰。
- 明確宣告已鎖定的 cryptography 50.0.2 為簽章依賴；Linux／Windows 套件版本與雜湊不變，58 套件及 214 份授權原文保留，更新 inventory 鎖定摘要。
- C05 **41/41**、實際官方 HTTPS／快取／離線匯入 **6/6**；完整 Linux 回歸 **270 項，269 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。原始日誌與視覺頁截圖附 SHA-256 保存於 [本輪紀錄](docs/development-records/runs/c05-2026-11-06/README.md)；注入協定與實際網路證據分開。
- 更新中文責任說明、首頁模組圖、固定架構快照與進度。未重建 frozen／Windows 產物、觸發發行工作流程、建立 tag 或 Release；Windows／GPU 及已知品質限制保留。

## 0.2.1 — 2026-11-06

相對 **0.2.0** 完成 C02；架構仍 **0.4**，新導入 **1/12 → 2/12**，既有 **19/25** 不變。

- 舊模型以 adapter 接入登錄與既有 GUI：外部／舊目錄只讀引用，不因位於程式目錄就接管。新專用空目錄明確下載才建立受管紀錄，沿用原下載、取消、快取與完整性保護；只移除受管且未修改的已知模型，未知檔案保留。
- 設定 **v5 → v6**，讀取 v1–v5、保留資源／OCR／路徑，保存品質與後續元件／精靈／更新偏好；GUI／CLI 不重設未顯示欄位，CLI 明確品質參數優先。
- 舊設定儲存前備份原始位元組，未來或損壞設定不能被預設值覆蓋；SQLite **schema 1 → 2** 先建立一致性快照，再交易新增引用表，失敗不重設原資料。
- C02 **61/61**；完整 Linux 回歸 **229 項，228 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。新增 [C02 開發與驗收附件](docs/development-records/runs/c02-2026-11-06/README.md)，含合成 Qt 畫面、進度截圖與 SHA-256；前版附件／架構圖不覆寫。
- 程式、中文註解、離線手冊、首頁模組圖及進度同步更新，無新增第三方依賴。模型驗證不代表引擎 ready；通用可信下載、交易安裝、獨立 worker 與完整管理頁仍待後續，下一段 C03／C04。未重建 frozen／Windows 產物或驗收 GPU；來源同步不等於正式安裝包發行。

## 0.2.0 — 2026-11-06

架構版本維持 **0.4**。相對 **0.1.1**，新增 C01 元件基礎函式庫；不是 Windows 安裝包發行。

- 新增嚴格元件／能力／穩定版本契約：平台、依賴、app／worker 相容範圍、來源／授權、完整檔案清單、容量、資源估計與簽章資料欄位。
- 新增 SQLite 登錄、串流 SHA-256、安裝內容驗證及世代比對；不可變 ID／版本描述，未知或損壞登錄明確失敗，不清空原資料。
- 能力解析每次重驗相容性、依賴、實檔與可信探針；下載／安裝不等於 ready，遭修改或失效的元件撤回可用性，明確指定引擎不改選其他引擎。
- 新模組與重要流程附中文說明。首頁、視覺進度、架構指引與開發日誌更新，新導入 **0/12 → 1/12**；舊架構快照保留，新增 C01 狀態圖。
- C01 **43/43**；完整 Linux 回歸 **196 項，195 通過、1 既有品質預期失敗、0 跳過**。驗收報告、原始日誌、進度截圖與 SHA-256 存於 [本輪紀錄](docs/development-records/runs/c01-2026-11-06/README.md)。
- 既有 **19/25**、設定 schema v5、預設 OCR 與轉換流程保持原基線；本輪沒有新增第三方依賴。後續 C02 轉接模型／遷移設定；可信簽章／下載、交易安裝、獨立 worker、GUI 及分析接線仍待各自檢核。未重建 frozen／Windows 產物；Windows、GPU 實機及 ONNX 繁體品質缺口保留。

## 0.1.1 — 2026-11-05

狀態：原始碼維護版；架構指引維持 **0.4**。本次從程式 **0.1.0 → 0.1.1**。

### 新增與調整

- 整理 GitHub 首頁 README：繁體中文產品說明、模組架構圖、既有／規劃能力、進度及文件入口。
- 新增本更新紀錄及 AGENTS.md 維護約定，後續持續記錄版本差異、驗證與同步狀態。
- 自有 Python、Windows 建置／驗收腳本及打包入口補充中文責任說明與關鍵流程註解；修正過時的「尚未整合」文字。
- 將累積的本地開發歷史首次同步至使用者指定的 GitHub 儲存庫 main。

### 相對 0.1.0 的差異

- 維護文件、版本辨識與程式閱讀性改善；轉換邏輯、預設 OCR、設定 schema v5 及架構指引 0.4 的功能範圍不變。
- 新版基本包／選配元件管理仍依 C01–C12 待實作，本次不提高其驗收進度。

### 驗證與限制

- 以移除說明字串後的 Python AST 比對，確認自有程式的執行語法樹未因中文註解改變；另執行來源、授權及適當回歸檢查。
- 本次 Linux 完整檢查 153 項：152 通過、1 項 ONNX 繁體品質預期失敗、0 跳過；PowerShell 工具 9 組及進度頁瀏覽器驗證通過。結果另記於 docs/validation-results.json。
- 未建立 Windows 正式安裝包、tag 或 Release；Windows／GPU 實機驗收仍待完成。

## 0.1.0 — 累積開發基線，2026-11-04～2026-11-05

以下依已存在的本地 Git 提交補記。當時套件版本皆為 0.1.0，**未另編造 0.1.x 發行紀錄**。

| 日期 | 提交 | 更新內容與前次差異 |
| --- | --- | --- |
| 11-05 | `dfdb8e8` | 架構指引升至 0.4：採基本安裝包＋選配元件管理；新增 C01–C12 導入規劃與視覺分頁。程式仍 0.1.0。 |
| 11-05 | `b5b706e` | 新增 Windows Inno Setup 來源、安裝／解除安裝驗收、內建離線自我檢查、固定繁體品質影像。尚未執行 Windows 建置。 |
| 11-05 | `8ec991b` | 修復稀疏表格、跨欄標題／雙欄閱讀順序及無框線續表；完成 Linux 代表性版面驗收，既有基線到 19/25。 |
| 11-05 | `f26a8ea` | 完成 58 套件、214 文件授權清單與離線手冊基線；不等於最終 Windows 再散布審核。 |
| 11-05 | `6dc8355` | 固定 PDF 測試資產為二進位，保存原始位元組與雜湊。 |
| 11-05 | `98f28d5` | 增加對齊數值型無框線表格推測；當時稀疏結構仍列為品質缺口。 |
| 11-05 | `c70419b` | 新增保守跨頁續表提示，保留各頁表頭與資料，不自動合併。 |
| 11-05 | `d506f99` | 依實體 cell 幾何輸出 rowspan／colspan，保留表格外框內非 cell 文字。 |
| 11-05 | `3033e10` | 新增雙引擎核對與多樣本品質記錄；保留主要原文與候選，不自動修字。 |
| 11-05 | `3de9029` | 整合實驗性 ONNX CPU／候選 CUDA，記錄繁體品質缺口並改善 Tesseract 稀疏文字辨識。 |
| 11-04 | `3280e00` | 新增裝置診斷與 CPU 執行緒設定，區分硬體偵測與實際 GPU 推論。 |
| 11-04 | `06f2a4b` | 新增固定模型下載／驗證／取消／移除，以及引擎與模型路徑持久化。 |
| 11-04 | `60444c0` | 新增逐頁 PDF OCR、精準路由及可重建的打包腳本。 |
| 11-04 | `1255c58` | 整合官方上游、格式轉換、Qt 桌面原型與離線視覺進度頁。 |
| 11-04 | `2010561` | 建立任務契約、文字輸出、spawn 背景工作與 RAM 調度核心。 |

## 版本規則

- 程式版本：不相容變更、功能與修正依版本差異說明；維護變更也可使用修補版號，但需明示未提供新功能。
- 架構版本：需求、模組責任、導入範圍變更另在架構指引記錄；例如 0.3 → 0.4 不等於程式版本同步升至 0.4。
- 驗證版本：報告保留平台、模型／元件與當次結果；未執行的 Windows／GPU 不用新版本號代替驗收。
- 本檔只記實際變更。未來功能放在更新中或開發規劃，不預先列為已交付。

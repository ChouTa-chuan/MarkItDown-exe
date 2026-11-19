# 版本與更新紀錄

本檔記錄每次專案更新。**程式版本以 pyproject.toml 為準；架構指引版本獨立計算。** 原始碼版本不代表已發布 Windows 安裝包、Git tag 或 GitHub Release。

## 更新中

- B1a：新增固定 b17d51b 基本包的報告式組裝流程與反例測試；只允許指定文字報告上傳，產品上傳明確停用，尚未執行 hosted Windows 試跑。

- 2026-11-19：依使用者決定重新排程：A14–A17 移入大階段 B 改編號 B3a–B3d；B1 拆為 B1a（準備試跑，不公開）與 B1b（planner 複查大階段 A 後公開產出，artifact 保留 30 天）；A13c 與 B1a 交給 Codex。

### 2026-11-18｜A13b 依使用者決定調整並重新固定候選

- 變更：基本包根目錄 vcruntime140／_1 改用 Visual Studio 官方 Redist（A13-1 b，使用者同意的打包變更）；新增隨包 known-gaps.json／known-gaps.md／test-build-limitations.md；候選審閱固定保留揭露檔列；以固定候選 b17d51b 重綁登記表與目錄，Microsoft 探測改以新候選為基準並收回 check_catalog 放寬；依 A13 決定存檔逐條寫入 decision_source 與 accepted_gaps（108），13 條 user_approved。
- 相對前版：基本包 `runtime_sbom_disclosed` 與 `redistribution_approved` 首次推導為 true；`runtime_sbom_complete`、`release_ready` 仍 false；CPU 全 false。
- 驗證：Windows CI 基本包建置、驗收、安裝、升級、恢復通過；gates 推導與證據一致；reviewer 特別查驗無必須修正（人工核對決定列對應，合成攻擊皆被拒）；完整 Linux 混合與獨立模組回歸通過，數字見 progress.json。
- 未完成：A13c 重產逐列來源對照（三個 evidence_complete 條目仍引用 A12 對照，6 列 hash 已變）；B1；大階段 C；CPU A14–A17。

### 2026-11-18｜A12d wheel 內含元件執行期版本觀測

- 變更：Codex 新增 `scripts/embedded_runtime.py`、反例與 workflow 觀測（fb4f510，run 44270551031）後中斷；Claude 接續把 libxml2、libxslt、numpy-lapack、libaom、dav1d 改為 runtime-observed，拆出 libexslt（unknown），新增證據目錄，登記表只做必要 hash 同步與證據引用，並改寫三條 required_evidence 描述。
- 相對前版：基本包 wheel 內含未知元件 26→22；A13b 揭露清單相應縮短。
- 驗證：觀測收據與證據檔逐位元組一致，承載原生檔 sha256 與 A12 候選相同；gates 兩 profile 四旗標皆 false；完整 Linux 混合與獨立模組回歸通過，數字見 progress.json。reviewer 查驗無必須修正。
- 未完成：raqm、fribidi、libyuv 等仍 unknown；A13b、B1。

- 2026-11-18：A12d 加入有界 Windows 版本 API 觀測、A12 原生檔 bytes 綁定及反例；先於 hosted Windows 蒐集觀測，未取得證據者不提升版本依據、不改安裝包。

- 2026-11-18：記錄使用者 A13 各項決定：A13-1 選 b（根目錄 2 份 VC runtime 換官方 Redist，其餘揭露）、A13-2／A13-3／A13-5 接受、A13-4 選 b（先做 A12d）、A13-6 同意限制說明草稿、A13-7 同意公開產出測試版；A12d、A13b 交給 Codex。本次不改條目狀態。

- 2026-11-18：修正進度頁「全階段規劃」版面：標題含長英文字（如 A12c 的 runtime_sbom_disclosed）時狀態標籤被擠出卡片；改為標題可斷行、標籤不縮小。

### 2026-11-18｜A12c 揭露式關閉規則

- 登記 schema 升為 3，每項加入空 accepted_gaps，現有狀態、選擇器、來源及證據引用不變。runtime_sbom_complete 保持嚴格；新增 runtime_sbom_disclosed，redistribution_approved 改依完整揭露及原再散布決定判定，release_ready 仍受大階段 C 限制。
- 未知／僅建置宣告的 wheel、CPython、Qt 缺口逐項對到 id；關閉須 user_approved、requires_user_decision=true、有效固定使用者決定、精確缺口集合及同 hash 候選隨包揭露。embedded 的 open-only 限制改由同一 gates 規則驗證；移除已存在目錄引用不能隱藏缺口；沒有獨立原生檔的 open 內含元件也不能靠省略來源 gate 繞過 disclosed。
- 補 base／cpu 合成正例與錯誤清單、決定、揭露內容／路徑／候選 hash 等反例；不建立真實揭露檔、不代作 A13，實際 A12 base／cpu 原三旗標與新增 disclosed 仍 false，coverage／原始計數不變。完整回歸及最終 CI 見本輪證據與 PR。
- A12b 已在 PR 26 一般 Merge（4f30196），五條 CI、Windows metadata replay、Qt 替換及 Pages 來源／hash 查驗通過；本輪從此最新 main 另開自己的 A12c 分支。A12c 完成後停止，不改 spec、鎖檔或打包內容，不交付產品、Release 或 tag。




### 2026-11-18｜A12b 既有證據接線與 Community 原文

- 把 A12 來源／封存／MIT 證據接進登記表，逐列評估 origin-known 而不改原始分類；只完成三個工程條目，CPython／Tesseract 原文引用補齊但維持 open，CPython 依使用者決定改為需 A13 決定。既有 requires_user_decision=true 條目的狀態全不改。
- 官方 VS2022 Community DOCX 保存來源網址、取得日期及 SHA，摘要只陳述使用資格、可散布程式碼與要求／限制，不判斷使用者、CI 或 DLL 的適用性，不核准再散布。
- 修正 cryptography 的過時 openssl 未知需求、MIT 候選描述、m5 與測試名稱；Microsoft 目錄只改 limitations 敘述，原生檔事實不動，base-microsoft 的目錄引用 SHA 同步。其他既有條目僅 hash 同步：無。
- 依使用者 C 節明確指定，只補註舊 A12 base-exit-report 的 base-clean-machine-manual 到大階段 C 才能關閉，對應 manifest 機械刷新該 SHA；原版 commit／blob／SHA 記在新證據，不重複存舊完整 JSON。A12 原始狀態、數字、來源與其他原始證據不變。
- 新證據 hash 變異與逐列對照反例、完整混合與獨立模組回歸通過；數字／來源見 progress.json。gates base／cpu 三旗標 false，原 coverage 與 inventory_summary 不變；解除與剩餘阻擋見新證據及 PR 26。spec、鎖檔、打包內容與固定候選不改。
- STATUS 先存檔再更新，D 節原文保留，補記使用者指定的 A12c 停止點；進度與歷史索引同步。A12b Merge 後才另開 A12c 分支；不交付產品、不建 Release 或 tag，既有 ONNX／RAM／實機限制維持。

- 2026-11-18：進度頁「全階段規劃」把原本的「需使用者」分成「需使用者決定」（A12d、A13、D1、D2，回答問題即可）與「需使用者實機測試」（B4、C1–C3）；`build_progress.py` 保留舊值 user 以相容。

- 2026-11-18：Claude planner 完成大階段 A 第二次複查：A8–A12 通過，但現行旗標規則使含版本未知元件的條目永遠無法關閉，B1 無法進入。使用者同意插入 A12b（證據接線，並把 base-cpython 改為需使用者決定）與 A12c（揭露式關閉規則），A13 拆為 A13-0～A13-7（A13-0 已同意）；A12b、A12c 交給 Codex。

### 2026-11-18｜A12 重新固定候選與基本包出口報告

- 變更：以 workflow_dispatch 在 main 指定 2555687（含 A7–A11）建置固定候選（base run 44217813413、CPU run 44217816852），重組 source-review 並離線 replay；登記表與 embedded／qt／microsoft 目錄改綁新候選，必要 hash 同步只動 sha256 引用；產出基本包出口報告與 A13 待決清單；progress.json 的 25 個 `previous_` 鍵原樣搬到 docs/history/progress-previous.json。
- 相對前版：固定候選由 A6 的 8285450 改為 2555687；原生檔 bytes 不變，新增 151 個隨包原文檔；`microsoft_runtime.check_catalog` 改為探測基準等於基準檔自身 selection（A10 探測仍以 A6 為基準），候選綁定仍逐檔比對。測試固定輸入改為 A12，A6 保留為 Microsoft 基準的歷史輸入。
- 驗證：新候選兩份輸入三旗標皆 false；完整 Linux 混合與獨立模組回歸通過，數字見 progress.json。reviewer 查驗無必須修正。
- 未完成：A13 使用者確認門檻、A14–A17（CPU，B1 之後）、大階段 B／C。


### 2026-11-18｜A11 Qt 第三方、建置資訊與可替換驗收

- 相對 A9b：新增固定 Qt 來源的 qt_attribution／原始授權目錄，以獨立 evidence 路徑及 SHA 綁定；準備資產與最終 bundle 都驗原文。版本 source-declared 不代表 wheel 宣告或確認編入，無版本與 Mesa 來源缺口保持 unknown。
- 真正 Windows QLibraryInfo 觀測補 library version／shared／debug；hosted Windows frozen GUI 驗不同 bytes Core 替換、移除 loader 失敗與還原成功，核對實際載入路徑及 hash。測試 wheel／DLL／副本在 reports 外，不上傳產品，不改正式 bundle。
- 只改 base-qt：evidence 更新、requires_user_decision=true、status 仍 open；LGPL 做法留 A13 決定。其他僅 hash 同步條目：無。spec、鎖檔、原文來源位元組、計數口徑與 A6 固定來源不改；base／cpu gates 三旗標 false。
- 首輪 Windows run 44153547178 在隔離環境安裝 app 前過早匯入而失敗；已重現、改延後匯入並加無 site-packages 的控制端啟動反例。失敗 run／註記 hash 保存，不重複存完整舊嘗試 JSON；後續失敗也公開小型結果。
- 缺檔／改原文／錯誤版本分級／錯誤載入 DLL／缺驗收階段及不當提高旗標反例、完整混合與獨立模組回歸通過，來源與數字見 progress.json。真正 Windows 首次成功證據、manifest、限制已保存；最終 head 全 CI／查驗／Merge 見 PR 22。
- STATUS 先保存再更新，使用者 D 節決定逐筆保留；視覺進度及索引同步。沒有產品交付、Release 或 tag；實體機／乾淨機／GPU 未驗收，ONNX 繁中與 RAM 軟性預算限制維持。本輪到 A11 停止，不做 A12。

### 2026-11-18｜A9b OpenSSL 原文隨包

- 新增固定 OpenSSL 4.0.3 tag／commit 的 LICENSE 原文與 cryptography 補充來源，接既有 supplemental_sources 管線；準備資產與最終 bundle 重新核對原文、套件綁定、實際 cryptography OpenSSL API 及 `_rust` bytes。
- 沿用 runtime-observed 分級，Linux 與 Windows 分別記錄；Windows API 觀測已取回並與 A6 bytes 核對後才更新目錄。Windows API 觀測與 A6 bytes 已核對；缺檔／改內容／錯綁、runtime 或來源不符反例及完整混合／獨立模組回歸通過。最終 CI／Merge 見 PR 21。
- 首輪 Linux／CPU CI 因 cpu-windows-closure.json 未重建而失敗，已由舊產生器同步授權索引；套件集合／鎖檔不變，失敗來源與 run 已保存。
- 依使用者明確授權，其他 wheel 條目只機械刷新共用目錄 hash，狀態、選擇器、required_evidence、requires_user_decision 均不變；僅 hash 同步條目：`base-wheels-numpy`, `base-wheels-pandas`, `base-wheels-pillow`, `base-wheels-lxml`, `base-wheels-onnxruntime`, `base-wheels-pypdfium2`, `base-wheels-cffi`, `base-wheels-charset-normalizer`, `base-wheels-psutil`。spec／鎖檔與既有計數程式不變，三旗標維持 false。


- 2026-11-17：記錄使用者決定：補上 cryptography 靜態併入的 OpenSSL 授權原文（新增 A9b），A10 換手 Codex（已於 PR 20 完成）。

### 2026-11-17｜A10 Microsoft 執行期逐檔證據

- 相對 A9：補上 Microsoft 複本的 Windows PE 版本、簽章及官方 Redist 同名 SHA-256 比較；保留改名複本，來源容器符合原鎖檔。目錄與原始探測／條款位於 packaging/microsoft 及本輪小型證據目錄，以 evidence 路徑加 hash 綁定。
- 查驗時把「簽署者不同的已知事實」與「查詢缺資料」分開，前者列 signature_review_files，不以簽署者必須是 Microsoft 的硬規則取代 A13；有完整資料仍須使用者決定。
- 登記只改 base-microsoft，標 requires_user_decision=true，維持 open；先前代理拒絕問題在使用者發布網域後解除；補存官方 Runtime、VS2022 Enterprise／Professional 原始 DOCX 與 REDIST 全頁，path／hash 引用，舊轉載標記保留，不把原文取得當成散布權利。適用性及許可留待 A13，CPU Microsoft 留給 A16。
- 相關正反例與完整 Linux 混合／獨立模組回歸通過；原 A6 base／cpu 再跑三旗標均 false，數字與原始 review_reason 不改。數字、來源與新證據見 progress.json；最終 head CI／Merge 及報告 hash／期限見 PR 20。
- 未動 spec、打包內容、鎖檔與既有計數口徑，未交付 Setup／worker／模型、Release 或 tag。A10 完成後先停；Windows／GPU 實機、RAM 軟性預算與 ONNX 繁中限制保留。


### 2026-11-17｜A9 基本包 wheel 內含第三方元件目錄

- 變更：新增 `packaging/embedded/base-windows.json` 與 `scripts/embedded_components.py`（由 `redistribution_gates.py` 呼叫），記錄基本包 10 個 wheel 的內含元件、版本依據分級、來源與既有授權原文 hash；`base-wheels` 拆成 10 條，只有 charset-normalizer、psutil 為 evidence_complete；依 STATUS C 節把 `base-tesseract-models` 改為需使用者決定（A13）。
- 相對前版：A8b 時所有 wheel 原生檔歸在單一 `base-wheels` 條目，現在逐 wheel 對應內含元件並可檢核。
- 驗證：A6 兩份輸入三旗標皆 false；完整 Linux 混合與獨立模組回歸通過，數字見 progress.json。reviewer 第一輪指出 Pillow 的 `.pyd` 字串顯示內含 raqm、fribidi、libaom、dav1d、libyuv（LICENSE 未列），Pillow 退回 open；第二輪無必須修正。
- 未完成：cryptography 靜態併入的 OpenSSL（`OpenSSL 4.0.3` 字串）沒有隨附原文，補原文需使用者決定；PE 匯入表、Windows 實機載入行為與 upstream 網址未驗證；A10–A17。

- 2026-11-17：線上視覺進度頁新增「全階段規劃」分頁（大階段 A–E 各編號的狀態與 PR，資料在 progress.json 的 `stage_plan`，build_progress.py 驗證狀態值域與已完成項目須有 PR 號）。並依現況更新：m0 打包可行性改為已完成（hosted Windows 建置與安裝已驗）、m5 改列 hosted 建置、門檻、交付、乾淨機各項；更新模組與元件卡片中過時的版本與測試數字；限制改為現行七條（舊版逐輪數字留在 Git 歷史）。C01–C12 維持 7/12。

### 2026-11-17｜A8b 義務登記檢核補強

- 變更：`redistribution_gates.py` 的使用者決定出處只接受 `docs/history/status/` 固定存檔 D 節內完整的使用者決定列（日期有效、程式碼區塊與 `## Data` 類標題不算）；新增 stale selector 反向檢查；`*-clean-machine-manual` 關閉須有 `stage-c-` 證據，release_ready 在大階段 C 前不可能為 true；登記表鍵集合封閉、schema 升為 2（obligations.json 只改版本號）。
- 相對前版：A8 時「證據指向 LICENSE、quote='M'」即可讓三旗標全為 true，現已拒絕；腳本仍不檢查決定列與條目的語意對應，文件已寫明須人工審查。
- 驗證：A6 兩份輸入實跑三旗標皆 false（base 153／3、cpu 61／4）；完整 Linux 混合與獨立模組回歸通過，數字見 progress.json。Windows CI 見本輪 PR。
- 流程：Claude coder 實作、reviewer 查驗無必須修正項目，協調者補小修正。也整理了 CHANGELOG A8 小節後重複的兩條。
- 未完成：A9–A17、門檻確認（A13）與大階段 B／C。

- 2026-11-17：依使用者決定調整 Claude 角色模型：planner 改 Opus 5.5、coder 改 Haiku 5.5、reviewer 改 Sonnet 5.5，推理強度維持中（`.claude/agents/`、`CLAUDE.md`；只影響 Claude）。

### 2026-11-17｜A8 義務登記與旗標判定

- 首個提交 fec86c9 先完成 A7 查驗小問題；核心僅新增單一 obligations.json 與一支 redistribution_gates.py，base／cpu 分開對應原生檔與 review_reason，並按證據／決定狀態推導三旗標及列出阻擋條目。
- 未知／重複對應、無決定出處的使用者核准及證據 hash／quote 不符拒絕；正例證明旗標可依條件變動，實際 A6 輸入的三旗標仍全 false。原始 unresolved_files 等計數不改，規則定義詳見 docs/redistribution-gates.md。
- 相關反例與完整混合／獨立模組回歸通過，現況數字只記 progress.json；精簡新證據與來源已保存，STATUS 先封存後更新、重建進度頁及索引。最終 head 全 CI／查驗通過才一般 Merge。
- 只依 C 節勘誤兩句說明並重產 Markdown；未動 spec、套件收集、依賴或原始授權。A8 完成後停止，不展開 A9–A17，產品核准門檻未關閉。

- `full_regression.baseline_environment_identical` 在 A7 移除：舊布林值未附完整環境清單比較的依據，不能據此宣稱兩輪環境相同或不同。目前保留實測 Python／Tesseract、來源提交與回歸結果，舊欄位仍可由 Git 歷史追溯；本輪不還原沒有比較證據的布林值。

- 2026-11-17：PR 13（A7）合併後 Windows 基本包與 CPU 驗證成功。Claude planner 完成大階段 A 整體複查：A1–A7 達成，但三旗標仍 false；依使用者決定續編 A8–A17，門檻確認前移為 A13，A12 不做打包減量並整理 progress.json，CPU 排在 B1 之後（STATUS C、D 節）。

### 2026-11-17｜A7 自有 MIT 對照、工作流來源傳遞與分片反例

- 首個提交修正 A6 合併現況、原排隊 run 最終成功且只有報告 artifact，並以 8285450 成功 run 作基本包審閱依據；A6 attempts.json 不變，原文／模型／架構快照保留。
- 兩條 Windows 工作流以獨立提交改 step env EXPECTED_SOURCE，pwsh 先驗 SHA；缺片與越界反例使用真正多片資料。基本包自有 MIT 綁入套件原文表，產生／audit 核對來源，重算 hash 仍拒絕缺檔、改內容與錯誤綁定。
- 完整混合／獨立模組回歸及 Windows 基本包分支驗收通過，數字只見 progress.json；[精簡證據、來源與期限](docs/development-records/runs/a7-mit-binding-2026-11-17/README.md)已保存，不重複複製舊嘗試完整 JSON。STATUS 先封存後更新，視覺進度及索引同步。
- 程式／架構版號與全套固定候選不改，完整 SBOM／再散布及產品門檻不提高；最終 PR 全 CI／查驗通過後才一般 Merge。A7 完成後停止，剩餘義務整體複查及重新規劃交 Claude planner。

- 2026-11-17：A7 將既有自有 MIT 路徑綁入基本包套件原文表，產生與 audit 兩端核對固定來源的原始位元組，拒絕缺檔／改 hash／少綁／重複綁定及錯綁第三方套件；補重算資產 hash 後仍拒絕的反例。安裝路徑及第三方原文不變，CPU 清單與產品核准旗標不提高。

- 2026-11-17：A7 在既有分片 broken 清單加入少一片與 part 編號越界反例；fixture 先確保產生多片，避免缺片只測到空清單。測試方法數不變。

- 2026-11-17：A7 獨立修正兩條 Windows 工作流的來源傳遞：每個使用來源的 pwsh step 設 EXPECTED_SOURCE，先驗完整 SHA 格式及長度，再經環境變數傳給 Python；expression 不再插入命令列。

- 2026-11-17：A7 首個提交修正 PR 12 已合併（7b787d3）、合併後 CI 全綠及下一步；STATUS／A6 README 追加原排隊 run 最終成功且僅報告 artifact 的補註，attempts.json 不變。基本包審閱改以 8285450 成功 run 為準，保存舊資料 hash，不複製舊完整 JSON；A7 完成後停止，後續規劃交 Claude planner。

### 2026-11-17｜A6 固定基本包／CPU 候選與整體工程審閱完成

- 兩種候選以同一個完整來源提交 8285450 執行 Windows 驗證，既有功能及新增審閱 metadata 均通過；精簡資料完整取回後以固定 Git 樹離線重跑，來源 gap／candidate 列已消除，原 inventory 待審／未對照計數維持原值。
- CPU 實際完整 provenance 超過前版精簡入口容量，分離上限後成功；原始預檢／審閱失敗、排程異常、前輪基本包實證與修正後結果一併保存，[證據與期限](docs/development-records/runs/a6-fixed-review-2026-11-17/README.md)可追溯。完整回歸數字只見 progress.json。
- [整體審閱](docs/a6-source-review.md)明列自有 MIT 套件對照、wheel 內含第三方、Microsoft／Qt 與 CPU 原文／模型／GEOS 等待辦；A6 工程審閱完成，完整 SBOM／再散布與 release_ready 仍 false，產品里程碑不提高。
- STATUS 先封存後更新，D 原文保留，視覺進度與索引同步；最終文件 head 仍依 PR 全 CI／查驗後一般 Merge，下一個 A7 另開分支處理自有 MIT 表對照。程式／架構版號不變，沒有產品發行。

### 2026-11-17｜A6 首批檢核、基本包固定候選與 CPU 排程阻擋

- 相對前版只有 PR 暫時合併驗證，本輪新增固定完整來源 SHA 的 Windows 候選檢查、候選 hash 與可離線重跑的精簡來源審閱資料；CPython 元件觀測／原文及官方 VC 身分證據納入分類，原 inventory 計數與產品核准旗標不改。
- 第一個提交完成指定的 main 已合併 PR 1–11 現況、A5b／A5c 最終 CI run 與 D 節規則；保留所有使用者決定、歷史證據、上游原文與架構快照。
- 完整 Linux 混合及獨立模組回歸通過，Windows 基本包固定候選與離線分類已驗；[原始結果、失敗紀錄、來源及期限](docs/development-records/runs/a6-fixed-review-2026-11-17/README.md)已保存，現況數字只記 progress.json，進度頁與索引同步。
- A6 尚未整體完成：CPU 固定候選長時間 queued 且沒有 jobs，重送已開始執行，原請求取消 API／CLI 回覆矛盾；新版 CPU metadata 與整體審閱、PR 全 CI 仍待。A7 自有 MIT 套件對照先列後續，不提前合併或提高 SBOM／再散布門檻，沒有產品發行。

- 2026-11-17：A6 第二輪基本包實證通過；CPU 既有驗收通過後，新增審閱入口以精簡 metadata 上限讀取大型完整 provenance 而拒絕。完整來源報告改用獨立有界容量、公開 metadata 上限不放寬，補容量分離反例與公開錯誤摘要；需重新固定同一來源的兩種候選。

- 2026-11-17：A6 首輪固定來源檢查正確拒絕未提交的 CI out 目錄，但既有流程本來就在此存前版 checkout；新增根目錄 /out/ 的建置暫存忽略規則，來源檢查仍拒絕其他未提交檔。首次失敗保留，重新選定 SHA 後再驗。

- 2026-11-17：A6 新增固定來源候選檢查、候選 hash／來源重分類與精簡可重跑審閱 metadata；Windows 工作流只保存報告，不上傳產品。CPython 原文／runtime 與官方 VC 身分證據納入分類，產品核准旗標維持 false；完整回歸及原生固定候選待驗。

- 2026-11-17：A6 第一個提交依使用者指定更新 STATUS A／C 與進度 headline／next 為 main 已合併 PR 1–11，補齊 A5b／A5c 最終 head 的 CI run；記錄兩階段 Claude reviewer 通過。D 節新增前不得重複原文摘要，既有使用者決定不刪不併；A6 候選與分類尚未執行。

### 2026-11-16｜A5c 原生 Windows 新接受條件查驗完成（PR #11）

- 相對前次只有本機反例，Windows 基本包與 CPU 現在都以 A5c 新 policy 建置並通過既有驗收；實際 CPython 摘要中 OpenSSL／SQLite 皆有匹配 runtime 觀測，libffi 僅建置宣告限制保留。拒絕缺口的合成反例與原生正常建置實證分開，不宣稱做過 Windows 故障注入。
- Linux、Windows 基本包、CPU 及索引首輪 CI 全通過，[head／暫時 merge、公開原始摘要、artifact digest／期限](docs/development-records/runs/a5c-pr11-ci-2026-11-16/README.md)另存，最終文件 head 仍須全 CI 通過才 Merge。數字只記 progress.json，清除發行準備描述中的舊回歸計數，不提高里程碑勾選。
- 現況先封存再更新，D 節使用者決定逐筆保留，視覺進度與歷史索引同步；下一個 A6 先固定來源候選，再重跑分類及整體審閱。程式／架構版號、原候選及產品門檻不提高，沒有產品發行。

### 2026-11-16｜A5c：CPython 探測接受條件及反例

- 程式0.19.1／架構0.4不變；相對前版 Windows 清單探測失敗僅保留缺口，本輪要求已收集 OpenSSL／SQLite 皆為匹配來源的 runtime probe，存在 probe_error（含空字串）就拒絕。產生端先保存診斷再失敗，重驗端再強制一次，不因重算 sidecar／native manifest hash 通過 audit／CLI。Windows 本機、CI 與 Windows 清單離線重驗一致。
- 補齊各元件、錯誤欄位、刪除 OpenSSL 原文與 hash 重綁的 audit／CLI 反例；README 說明 extension observed_version 是所連結元件版本。libffi 僅建置宣告及 Linux 不適用範圍保留，沒有改 schema、固定相依或原文。
- 相關測試及完整混合／獨立模組回歸通過，數字只記 progress.json；[來源與原始結果](docs/development-records/runs/a5c-runtime-probe-2026-11-16/README.md)已保存。STATUS 先封存後更新，main 基線為已合併 PR 1–10，A5b 合併及最終 CI 來源補入現況資料，D 節使用者直接決定逐筆保留。
- 新接受條件尚待本 PR 原生 Windows CI，全部通過且查驗完成後才 Merge；A6 固定候選、完整來源／再散布及實機仍待。原固定候選、產品里程碑與發行旗標不提高，沒有產品發行、Release 或 tag。

- 2026-11-16：A5c 強制 Windows 適用清單的 OpenSSL／SQLite runtime probe 完整且匹配，產生與重驗兩端皆拒絕缺口／probe_error，保留失敗診斷；補齊 hash 重綁後 audit／CLI 不接受及缺失 OpenSSL 原文反例，明列 extension observed_version 的元件語意。libffi 與 Linux 不適用範圍保留，完整回歸／Windows CI 待驗。

### 2026-11-16｜A5b 原生 Windows Qt 查驗完成（PR #10）

- 相對前次只有本機與 Windows wheel 靜態證據，現在取得真正 Windows Qt／PySide／shiboken 版本、Qt build 字串、固定來源 catalog 及 Core extension 指紋；實際載入的綁定擴充檔與鎖定 Windows wheel 相符。controller 報告轉存及公開 annotation 接線已驗。
- Linux、Windows 基本包、CPU 與索引首輪 CI 全部通過，[精確 head／暫時 merge、原始公開摘要、artifact digest／期限](docs/development-records/runs/a5b-pr10-ci-2026-11-16/README.md)另存。最終文件 head 仍須相同全 CI 通過後一般 Merge；數字只記 progress.json。STATUS 先封存後更新，重建視覺進度與歷史索引，D 節使用者決定原文完整保留。
- 下一個為 A5c 獨立 PR，三項 CPython 驗收補強本輪未實作；A6 固定候選與完整 build 修補／參數、LGPL／SBOM／再散布仍待。程式／架構與產品里程碑不提高，既有固定候選保留，沒有產品發行。

- 2026-11-16：Qt CI 摘要接線修正後完整混合／獨立回歸通過，保存新的來源與原始結果；現況計數及 CI EXPECTED_TESTS 已同步，原有較早結果維持來源不改寫。

- 2026-11-16：A5b 自我查驗發現基本包控制端會擷取子程序 stdout，補上 Qt JSON 報告轉存與 annotation 重送，新增接線測試；保留一般 CLI 行為與原始日誌，不牽涉 A5c。

- 2026-11-16：A5b 已建立 PR #10，STATUS 與進度連回即時查驗入口，原生 Windows CI 執行中。

### 2026-11-16｜A5b Qt 發布來源與實際版本對應

- 相對前版 Qt 本體來源「待補」，現在固定官方發布 tag、supermodule／qtbase／PySide 提交、完整模組 gitlink、原始版本宣告與來源 hash；基本包隨附 qt-sources.json，離線查驗來源後核對真正載入的 Qt 及套件版本，CI 有獨立摘要。中文取得方法明列 supermodule tarball 不含子模組、各固定來源下載與限制。
- 第一個提交已依使用者要求恢復原始使用者決定並新增不得因精簡合併／刪除的規則；main／next 改為 PR 1–9，A5 最終四條 run 追加至指定 README（原版先另存、原始 JSON 不變）。A5c 三項列獨立 PR 待辦，本輪未改其驗收標準。
- 完整混合與獨立模組回歸通過、上游／原始授權／profiles 與來源變異反例通過；數字只記 progress.json，[原始結果及靜態 Windows wheel 證據](docs/development-records/runs/a5b-qt-source-2026-11-16/README.md)已保存。來源探索／呼叫錯誤照實記錄。A5b 原生 Windows 觀測尚待 PR CI。
- 程式0.19.1／架構0.4與產品里程碑不提高；發布來源對應不等於完整 build 修補／參數、可重建二進位或完成 LGPL／SBOM／再散布。原始授權、模型、固定相依、既有圖及固定候選保留，沒有產品發行。

- 2026-11-16：A5b 新增官方 Qt／PySide 固定發布來源、完整模組 gitlink 與原始版本宣告；基本包隨附 qt-sources.json 並核對實際載入版本，更新 Qt／LGPL 說明及產生範本。相關測試通過；完整回歸與 Windows CI 待執行，來源對應不視為完整建置修補／再散布審核。A5c 保留獨立待辦。

- 2026-11-16：A5b 第一個提交依使用者要求恢復 STATUS D 節歷史使用者決定原文，維護規則明列不因精簡合併或刪除；main／next 更新為已合併 PR 1–9，A5 CI README 補最終 head 的四條 run（先另存原版，原始 JSON 不變）。A5c 三項列為獨立 PR 待辦，本輪不實作。

### 2026-11-16｜A5 Windows 實證完成（PR #9）

- 相對前次只有 Linux 本機結果，Windows 基本包與 CPU 已通過既有驗收及新增逐檔來源／原文查驗；OpenSSL／SQLite 觀測與官方建置版本相符，libffi 仍明列僅建置宣告。實際 source hash 對應建置程序載入的來源檔，不冒充 frozen 候選獨立二進位認證。
- Linux、Windows 基本包、CPU、索引首輪 CI 全部通過；[原始公開摘要、精確 head／暫時 merge、artifact digest／期限](docs/development-records/runs/a5-pr9-ci-2026-11-16/README.md)另存，最終文件提交仍須全 CI 通過後一般 Merge。現況計數只見 progress.json；新增清單及原文不會自動消除未對照 owner。
- 現況封存後更新 STATUS、視覺進度與歷史索引，下一個為 A5b Qt 原始碼對應。A4 完成／main 已合併 PR 1–8 與指定 109 基準補註已保留；完整逐檔基準未保存。程式／架構版號、產品里程碑與再散布門檻不提高，無產品發行。

### 2026-11-16｜A5：逐檔 CPython 元件版本與原文；修正 A4 現況及 109 說明

- 程式0.19.1／架構0.4不變；從已合併 PR 1–8 的 main `e87de4b` 開自己的 A5 分支。相對前版僅有總體 CPython 原授權，現在新增逐檔來源 hash、PE 檔案版本、官方建置宣告、匹配載入檔的 OpenSSL／SQLite 執行期版本，以及每檔對應原文。
- 固定 Windows CPython patch 版／x64 的官方來源與原文 hash；`patchlevel.h` 防止換標代填，完整 OpenSSL／libffi 原文與 SQLite 原始標頭註記節錄隨包。libffi 只有宣告時不冒充二進位版本認證；來源不符、改原文、改版本或漏檔均有反例。
- 依使用者要求明列 A4 完成（PR #8、Claude reviewer 已查驗），main 已合併 PR 1–8，next 改為 A5／A5b。A4 README 補註實體檔案與 PYZ 分開計數；找到並保存 PR #6 的 109 基準，完整逐檔基準未保存。原版 README／manifest 先另存，原始 CI JSON 不變。
- 驗證：完整 Linux 混合與獨立程序回歸通過，現況計數只見 progress.json；索引過期的首次失敗與修正後結果均保存。上游／授權／profiles 檢核通過，Windows 實際版本及隨包原文仍待本 PR CI。SBOM／再散布與產品里程碑不提高，未發布產品。

### 2026-11-16｜A4 Windows CI 補齊；API 阻擋解除

- PR #8 的 Linux、Windows 基本包、Windows CPU 元件與歷史索引首輪 CI 全部通過；相對前次只有 Linux 本機證據，現在有真正 Windows setuptools 排除與既有安裝／跨版／恢復驗收實證。
- Windows 基本包已沒有原 setuptools namespace，`build_only_modules_absent=true`；CPU 元件維持既有清單。公開摘要、精確 head／暫時 merge、artifact digest／期限存於[本輪紀錄](docs/development-records/runs/a4-pr8-ci-2026-11-16/README.md)，計數只見 progress.json。
- STATUS 先封存再更新，重建進度頁與歷史索引；最後文件 head 仍須經 CI 才 Merge。A5 接續以實際 Windows CPython patch 版及安裝原文逐檔盤點；不以另一版本的根目錄 LICENSE 或建置 props 代填。
- 原候選與原始本機證據維持來源，不把 PR 暫時 merge 當可交付新候選。完整 SBOM、Qt 原始碼、再散布及實機驗收仍待；應用／架構版號及產品里程碑不變，沒有產品發行。

- 2026-11-16：使用者發布允許 GitHub API 的新環境後，連線與 PR 建立已恢復；建立 A4 PR #8，更新 STATUS 與進度為 CI 執行中，既有 Linux 證據維持原來源，尚未關閉 A4。

### 2026-11-16｜A4：查明 setuptools namespace 並排除基本包的建置工具

- 程式／架構版號不變；`codex/a4-setuptools-audit-20261116` 承接 PR 6，並以 merge 納入已合併 PR 6／7 的最新 main，保留另一 AI 的設定與歷史。
- 實際 Linux 匯入圖重現 urllib3 的選用 backports 匯入經 PyInstaller 別名帶入 setuptools 父套件與編譯工具；相對前版，基本包排除 setuptools，不再只把無來源檔的 namespace 留作 unknown，也不把它們按名稱改列已知套件。建置環境、固定相依、第三方原文與 CPU 元件不變。
- spec 及隨包來源檢核拒絕 setuptools 根／子模組重新出現，基本包的公開小結新增 `python_archives.build_only_modules_absent`。反例涵蓋 namespace、套件邊界、重算資產 hash 及 CPU 不受影響；修改檔案內的分號敘述一併拆開。
- 驗證：Linux 隔離基本包真正建置、檢查 EXE 內嵌 PYZ 並執行 frozen core／格式驗收；完整混合及獨立模組回歸通過，計數只見 [progress.json](docs/progress.json)，[小型證據與失敗紀錄](docs/development-records/runs/a4-setuptools-audit-2026-11-16/README.md)已保存。現況封存後更新 STATUS 與自動歷史索引，重建視覺進度頁。
- 未完成：本環境 GitHub CLI 被拒，A4 PR 尚未建立、Windows CI 未執行、尚未合併；A4 未正式關閉。Qt 本體原始碼、CPython 隨附元件、再散布與實機驗收仍待，沒有提高里程碑或發布產品。

- 2026-11-16：PR 6（A3）合併。依使用者決定，Claude 的規劃者改為子代理 `planner`（Fable 5.2），主對話改為協調者並預設 Opus 5.5（`CLAUDE.md`、`.claude/`；只影響 Claude）。

### 2026-11-16｜A3：基本包隨附 Qt／LGPL 說明與自有程式 MIT 全文

- 程式0.19.1／架構0.4不變；分支`claude/qt-lgpl-notice`由main開出。
- 新增`licenses/qt-lgpl-notice.md`並隨基本包安裝：Qt（PySide6／shiboken6 6.12.0）以LGPL-3.0使用、授權原文位置、原始碼取得方式、替換方法。相對前版，Qt授權選擇不再是「待落實」。Qt本體原始碼位置repo內無依據，照實寫「待補」。
- 根目錄`LICENSE`複製進基本包（先前安裝包沒有自有程式的授權全文）；說明檔與LICENSE列為必要資產。third-party.md改由`license_inventory.py`的render()範本產生，並刪除「尚未選定原始碼授權」的過時說法。
- 三角色流程：reviewer第一輪找出兩項需修正（指向不存在的LICENSE、只改了產出檔），第二輪確認全部解決；說明檔路徑以11-12的Windows實際安裝清單核對。
- 驗證：Linux全741：740通過／1既有ONNX繁中品質預期失敗／0跳過，混合及50模組exit0；變異測試確認路徑或範本錯誤會被攔下。**新建置的實際檔案清單待本PR的Windows CI**。
- 未完成：Qt本體原始碼位置待補；A4、A5、A6。7/12、C04 2/4、C11 2/5不變。

- 2026-11-16：依使用者指示合併 PR 4、PR 5；規則改為每完成一個編號即可自行合併該 PR（CI 通過且查驗完成）。使用者已為 `main` 設定分支保護。

- 2026-11-16：PR 5 的 Windows CI 通過並首次輸出 Python 模組清單：基本包 1,715 個模組中 5 個無法歸屬（setuptools 隨附子套件），CPU 元件 562 個全部可歸屬（[紀錄](docs/development-records/runs/python-archive-inventory-ci-2026-11-16/README.md)）。

### 2026-11-16｜Python 模組來源清單與封存成員列舉；三角色分工啟用

- 程式0.19.1／架構0.4不變；分支`claude/python-archive-inventory`疊在PR 4之上，未合併main。
- 新增`scripts/python_archive_inventory.py`：建置時記錄每個純Python模組來自標準庫、哪個套件或自有程式，並列舉`base_library.zip`成員；隨包檢核把分類計數寫進CI公開摘要。相對前版，Python程式層級不再是完全沒有清單。
- 這是首次依三角色流程進行：coder實作、reviewer查驗（七項驗收條件通過，五項建議已修正）、規劃者跑完整回歸。reviewer以真實打包分析試跑：1,655個模組中6個無法歸屬。
- 文件：來源分類與授權文件補記微軟執行期、OpenSSL、FFmpeg的處理現況；使用說明註明需要64位元Windows 10／11。基本包簽章已確認：28個非wheel原生檔全部有效，自建`tesseract.exe`未簽章屬預期。
- 驗證：Linux全736：735通過／1既有ONNX繁中品質預期失敗／0跳過，混合及49模組exit0。**Windows上的清單輸出待本階段PR的CI**；未執行GPU或人工驗收。
- 未完成：Qt／LGPL隨包說明、CPython隨附元件逐檔清單；runtime SBOM旗標維持false。7/12、C04 2/4、C11 2/5不變。

- 2026-11-14：AGENTS.md 新增「多個 AI 輪替」：以 PR 為交棒單位、接手從最新工作分支開新分支、不推送他人分支、共用檔案衝突的處理方式。

- 2026-11-13：簽章查詢修正後，CPU 元件 27 個非 wheel 原生檔全部取得有效簽章（Microsoft 或 Python Software Foundation），原生檔與未對照來源各再少 44 個（[紀錄](docs/development-records/runs/native-signatures-ci-2026-11-13/README.md)）；基本包摘要待讀。

- 2026-11-13：微軟執行期調整通過 Windows CI：基本包原生檔與未對照來源各少 45 個，VC runtime 來自 Visual Studio 可再散布目錄（[紀錄](docs/development-records/runs/ms-runtime-official-source-ci-2026-11-13/README.md)）。簽章查詢因繼承的 PSModulePath 失敗，已修正待驗。Linux 全 719：718 通過／1 既有預期失敗／0 跳過。

- 2026-11-13：Windows CI 摘要顯示 46 個系統 DLL 實際來自 runner 上 Java JDK 的 bin 目錄（經 PATH 收集）。改為不隨包 Universal CRT、VC runtime 取自 Visual Studio 可再散布目錄，並把簽章查詢錯誤寫進公開摘要。Linux 全 718：717 通過／1 既有預期失敗／0 跳過；Windows 效果待 CI。

### 2026-11-13｜PR 1–3合併；CI自行檢查排除檔案並記錄原生檔來源與簽章

- 程式0.19.1／架構0.4不變。使用者指示合併PR 1、2、3（main為`747edba`），現行規則與現況檔已在main；本階段分支`claude/ci-self-check-and-ms-runtime`由main開出。
- 新增`scripts/native_identity.py`：建置時為CPython目錄與系統路徑收集的原生檔記錄來源目錄、PE版本資源與Windows數位簽章。相對前版，報告不再只有雜湊。
- 隨包檢核在公開摘要輸出分組後的來源／簽署者，並在候選包出現已排除的檔案時拒絕；不必下載artifact即可核對。
- 驗證：Linux全713：712通過／1既有ONNX繁中品質預期失敗／0跳過，混合及48模組exit0。**Windows上的實際輸出待本階段PR的CI**；未執行GPU或人工驗收。
- 未完成：微軟執行期改用官方來源、Python封存成員清單、Qt／LGPL隨包說明。7/12、C04 2/4、C11 2/5不變。

- 2026-11-13：PR 3 的 Windows CPU 元件 CI 通過，排除 FFmpeg 後既有驗收全部接受，元件 ZIP 由約 106 MB 降為約 93 MB；逐檔清單未核對（[紀錄](docs/development-records/runs/ffmpeg-exclusion-ci-2026-11-13/README.md)）。

- 2026-11-13：CPU 文字辨識元件排除 OpenCV 內附的 FFmpeg 影片外掛（Windows 效果待 CI）；新增輪替工作流 2.0 並在 AGENTS.md 要求接手時先看 PR。Linux 全 707：706 通過／1 既有預期失敗／0 跳過，混合及 47 模組 exit0。

- 2026-11-13：PR 3 的 Windows 基本包 CI 通過，排除來源不明 OpenSSL 後既有自動驗收全部接受；計數與排除三個檔案一致，逐檔清單因 artifact 主機被網路政策擋下而未核對（[紀錄](docs/development-records/runs/openssl-exclusion-ci-2026-11-13/README.md)）。

### 2026-11-13｜自有程式採MIT；基本包排除來源不明的OpenSSL

- 程式0.19.1／架構0.4不變；分支`claude/license-and-openssl-cleanup`疊在PR 2之上，未合併main。
- 新增`LICENSE`（MIT，周大詮 (ChouTa-chuan)）並在`pyproject.toml`宣告；相對前版，自有程式不再是未授權狀態。第三方元件各依原授權，產品整體不是全部MIT。
- `packaging/base.spec`經`scripts/bundle_filters.py`排除`qopensslbackend.dll`、`libssl-3-x64.dll`、`libcrypto-3-x64.dll`；保留Schannel後端與CPython的OpenSSL。
- 驗證：Linux全705：704通過／1既有ONNX繁中品質預期失敗／0跳過，混合及47模組exit0（CPython 3.12.3、Tesseract 5.3.4）。**Windows建置後的實際效果尚待PR的CI確認**；未執行GPU或人工驗收。
- 未完成：微軟執行期改用官方來源、Python封存成員清單、Qt／LGPL隨包說明；FFmpeg做法待確認。7/12、C04 2/4、C11 2/5不變。

- 2026-11-13：為 20 筆有失敗紀錄的舊證據新增補充關鍵字表 `docs/history/keywords.json` 並重新產生歷史索引；舊證據檔未改動。

### 2026-11-13｜現況檔、自動歷史索引與精簡維護規則

- 程式0.19.1／架構0.4不變；分支`claude/status-and-history-index`疊在PR 1之上，未合併main。
- 新增[STATUS.md](STATUS.md)作為唯一的現況入口，開工必讀由六份（約272 KB）減為AGENTS.md與STATUS.md（約10 KB）。相對前版，交接指南、開發紀錄、狀態頁改為背景與歷史，原樣保留但不再更新。
- 新增`scripts/build_history_index.py`與[歷史索引](docs/history-index.md)，由證據目錄、現況存檔與決策紀錄自動產生；測試與`history-index.yml`檢查是否過期。
- AGENTS.md改寫：數字只記在progress.json、階段完成才整體更新（小修只記一行）、新證據只留摘要與雜湊（舊證據原地保留）、指定未合併PR時讀該分支、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行。採納Codex交接方案的四組欄位與PR範本內容，做法改為單一現況檔。
- 首頁不再重抄數字；保存[成本診斷](docs/cost-diagnosis-2026-11-13.html)。
- 驗證：[全703：702通過／1既有ONNX繁中品質預期失敗／0跳過，混合及46模組exit0](docs/development-records/runs/status-and-index-2026-11-13/README.md)。未執行Windows建置／安裝、GPU或人工驗收。
- 未完成：授權與三項打包調整待決定；候選與無證據來源（基本49、CPU47）需Windows端資料；舊證據是否補關鍵字待決定。7/12、C04 2/4、C11 2/5不變。

### 2026-11-12｜接手：保存CI報告、來源分類、Linux CI與授權提案

- 程式0.19.1／架構0.4不變；工作在分支`claude/confident-ride-o38ls7`，尚未合併main。分支規則改為「工作分支＋PR，不直接推main」，AGENTS與交接文件同步修正。
- [保存Windows CI完整報告原檔](docs/development-records/runs/ci-full-reports-2026-11-12/README.md)：run 42982427175／42982427186（source cb8f24d）三份artifact ZIP原位元組保存，`bundle-provenance.json`雜湊與公開摘要`report_sha256`相符。相對前版，repo不再只有摘要；更早各run的完整報告仍未保存。
- 新增`scripts/classify_unresolved_sources.py`與[來源分類](docs/source-classification.md)：基本154／CPU303個未對照檔案依雜湊證據分類，confirmed 73／227、origin-known 32／29、candidate 48／46、gap 1／1。發現基本包含自runner系統路徑收集、來源不明的`libcrypto-3-x64`／`libssl-3-x64.dll`。
- 自有`THIRD_PARTY_NOTICES`改為分profile敘述，修正「Tesseract未內含」只適用舊development整包的過時說法；第三方原文未改。新增[授權提案](docs/license-proposal.md)（自有程式擬採MIT，待確認，未新增LICENSE）。
- 新增`linux-regression.yml`與`scripts/run_mixed_regression.py`；兩條Windows驗證流程加入`pull_request`與`workflow_dispatch`。[PR 1首次執行](docs/development-records/runs/pr1-ci-first-run-2026-11-12/README.md)三條皆Success（Linux 698／697／1預期失敗／0跳過）；PR流程使用暫時merge commit，不取代cb8f24d候選證據。
- 驗證：新容器先以原684項獨立重跑（[683通過／1預期失敗／0跳過，混合及43模組exit0](docs/development-records/runs/handover-regression-2026-11-12/README.md)）；新增14項測試後[全698：697通過／1既有ONNX繁中品質預期失敗／0跳過，混合及45模組exit0](docs/development-records/runs/handover-ci-and-classification-2026-11-12/README.md)。環境為CPython 3.12.3、apt Tesseract 5.3.4，與先前基線（3.12.14／5.5.0）不同。未執行Windows建置／安裝、GPU或人工驗收。
- 未完成：candidate／gap基本49、CPU47項需Windows端補來源路徑／簽章／版本與封存成員清單；runtime SBOM、再散布、授權決定、乾淨機／人工、GPU仍待。C04 2/4、C11 2/5及7/12不變；無Setup交付、tag／Release。

### 2026-11-12｜新增完整專案說明與接手指南

- 新增根目錄PROJECT_HANDOFF.md，整理需求／決策、實際模組、版本沿革、C01–C12狀態、684項與Windows／Pages證據、限制、可重現環境及下一步完成條件，文末附新AI接手指令。
- 首頁與AGENTS加入入口；舊狀態／建置／架構文件加上最新來源導引，保留歷史敘述與28份原圖，不倒填舊run。
- 程式0.19.1／架構0.4與7/12不變。本次只整理文件，核對來源／數字、指令／範例與連結，未重跑原生Windows／OCR或全功能回歸。

### 2026-11-12｜GitHub Pages視覺進度已上線

- 使用者完成Pages來源設定後，[部署43133764140](docs/development-records/runs/progress-pages-live-2026-11-12/README.md)成功；固定網址HTTP 200，內容SHA-256與目前產生器及前次瀏覽器驗證HTML完全一致。公開原頁與驗證JSON已保存。
- 專案首頁改為已上線固定連結；進度變更同步main後自動部署，重新整理載入最新快照。純說明整理不重複部署相同頁面。
- 保留首次未啟用的原始紀錄；程式0.19.1／架構0.4與684項功能基線不變，本次不重跑應用程式／Windows驗收。

### 2026-11-11｜視覺進度GitHub Pages自動部署

- 依使用者要求準備固定網址及Pages工作流程；進度JSON／模板／產生器更新後自動部署，保留離線HTML。
- 僅發布進度頁及別名，不複製完整docs或安裝產物；流程核對發布頁HTTP 200與建置SHA-256。首次Pages啟用涉及專案管理權限，實際部署狀態另存。
- 本地網站產生及Chromium互動／手機版通過；[首次Pages流程](docs/development-records/runs/progress-pages-2026-11-11/first-deployment/README.md)建置成功、部署因站台Not Found停止，尚未上線，需管理員先選GitHub Actions來源。
- 程式0.19.1／架構0.4、684項功能測試基線與7/12不變；本次驗證限網站產生與部署，未重跑Windows／OCR或發布應用程式。

### 2026-11-11｜候選包完整逐檔清單與CPU ZIP核對

- 程式0.19.1／架構0.4不變，僅改建置檢核。相對前次只查Analysis原生檔，新增全部普通檔案大小／SHA-256、可確認套件／原文對照、原METADATA授權宣告及未知來源待查；支援可信舊報告重驗同一候選。
- [Windows最終清單與ZIP接受](docs/development-records/runs/candidate-inventory-ci-2026-11-11/README.md)：基本1655檔（封裝後含catalog）、CPU bundle741／真正ZIP742檔（含NOTICE）；全項內容／CRC／descriptor與快照重驗接受，CPU ZIP hash與原生接受一致。公開有界統計與report hash保存，完整逐檔登入artifact未下載。
- 新23／相關88、全684：683通過／1既有ONNX繁中品質預期失敗／0跳過，混合與43獨立模組全exit0；基本app10／安裝6／跨版11／三停點續修、CPU功能11／同版8／跨版8／程序恢復6均接受。發現安裝會新增catalog後調整快照時點並補反例，前來源683與兩個Cancelled紀錄保留。
- 更新中文說明、首頁與視覺進度；55份舊manifest／2925筆hash及原文／模型／9鎖／28圖不改。基本154／CPU303個檔案來源未對照，完整runtime SBOM與再散布、應用授權、乾淨機／人工及GPU待查；C04 2/4、C11 2/5及7/12保持，無Setup交付、tag／Release或環境發布。

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

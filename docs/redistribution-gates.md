# 義務登記與完整／揭露／再散布判定（A12c）

核心只有 [obligations.json](../packaging/redistribution/obligations.json) 與 [redistribution_gates.py](../scripts/redistribution_gates.py)，沒有規則外掛、額外資料模型或發佈動作。以固定 A12 base／cpu source-review 為輸入，原始報告與計數不改寫。A12 出口報告須使用此腳本的推導結果；來源報告中的舊 false 保留作當時建置證據，不拿來代替本判定。

| 旗標 | 條件 |
| --- | --- |
| runtime_sbom_complete | 此 profile 所有影響來源盤點的義務皆完成證據審閱，並有可重驗的證據引用，且沒有任何未知／僅建置宣告缺口（接受缺口仍是 false）；不以套件宣告或外層 wheel 擁有權代替內含第三方盤點 |
| runtime_sbom_disclosed | 所有影響來源盤點的義務皆非 open；未知或僅有建置宣告的元件逐項經使用者接受，並有與候選 bytes 相同的隨包揭露。不要求再散布總決定或實機義務先關閉 |
| redistribution_approved | runtime_sbom_disclosed 為 true，所有再散布義務完成；需要使用者決定的條目必須 user_approved 且有決定原文引用。每個 profile 的 redistribution-decision 為必要門檻，協調者不能代為決定 |
| release_ready | redistribution_approved 為 true，加上 clean-machine-manual 必要條目完成並經使用者確認。hosted Windows CI 不代替大階段 C 的乾淨機與人工驗收 |

base 與 cpu 分開判定；CPU 尚未關閉不妨礙基本包依自己的證據完成。共用登記 JSON 本身仍須結構有效，任何標成使用者已核准而沒有有效決定出處的條目都拒絕。

## 精確覆蓋與計數

- `native_files` 是 A6 `classification_input.report.native_files` 的精確路徑列表，以 Windows 路徑不分大小寫的規則比對，不支援通配或兜底；每個原生檔須恰好對到一個條目。
- `review_reasons` 是另一個獨立對應軸。每個 reason 字串須恰好對到一個條目，所有帶該 reason 的檔案引用同一義務；摘要須與輸入列一致。未知 reason、未知原生檔或重複對應皆拒絕，沒有優先順序掩蓋重疊。
- `file_groups` 只描述人工審閱範圍，例如模型、PYZ／base_library，不是執行時通配規則。清單不宣稱已展開 wheel 內的隱藏元件，細部目錄由 A9 等後續階段處理。
- **unresolved_files 沿用原盤點「無 wheel 擁有者」的計數，不是要歸零的指標。** 合理的非 wheel 來源包括 CPython、自行產生檔案及模型。腳本保留輸入 summary，依義務／證據判定旗標，不降低或重新定義任何既有數字。

## 結構與決定出處（A8b，A12c 升為 schema 3）

- **封閉結構**：登記表 `schema_version` 為 3（只接受整數 3；A8b 當時為 2）。頂層、profile、每個條目、每個 evidence／decision_source 參照物件的鍵集合都是固定允許集合（條目的 `decision_source` 可省略或為 null），未知鍵拒絕。
- **決定出處格式**：`decision_source.path` 必須是 `docs/history/status/YYYY-MM-DD-<slug>.md` 固定存檔，不接受 STATUS.md 本身（它持續改動，hash 會失效）。`quote` 必須等於該存檔中**完整的一行**，該行位於 `## D` 標題之後、下一個 `## ` 標題之前，且符合 `| 日期 | 使用者… | 內容 |` 形式（來源欄以「使用者」開頭）。任意子字串、非 D 節的行、來源欄不是使用者的行都拒絕。這只限制出處的位置與格式，不證明該行真的出自使用者，仍須人工查驗。
- **反向檢查**：除了輸入每一項恰好對到一個條目，登記表該 profile 的每個 `native_files`、`review_reasons` 選擇器也必須真的出現在輸入中；否則以 stale selector 拒絕。
- **release_ready 綁定大階段 C**：`*-clean-machine-manual` 要關閉（非 open）時，`evidence` 須至少有一筆 path 以 `docs/development-records/runs/stage-c-` 開頭。這個前綴目前不存在，所以在大階段 C 的乾淨機與人工驗收完成之前，release_ready 不可能為 true。
- **仍須人工審查的部分**：腳本不檢查決定列與條目的語意是否對應，同一列使用者決定可以被多個條目引用；`stage-c-` 前綴也只是格式門檻，不證明驗收真的做過。D 節標題須為 `## D` 後接標點、空白或行尾，程式碼區塊（``` 圍欄）內的內容不算；日期須為有效日期；`schema_version` 須為整數 3。把條目改為 `evidence_complete` 或 `user_approved` 的提交，一律要逐條比對其引用的決定列與證據內容。
- **各 profile 分別評估**：反向檢查只涵蓋被評估的 profile，base 與 cpu 必須各跑一次。

## 狀態與證據

每項含 id、檔案／reason 對應、所需證據、狀態、旗標範圍與使用者決定出處。`open` 為未關閉；`evidence_complete` 表示所列證據已經人工審閱完成；`user_approved` 再加上使用者已作決定。工程證據完成可以關閉盤點義務，但不會自動滿足需要使用者決定的再散布或實機驗收義務。

非 open 狀態須有證據引用；引用使用 repo 相對路徑與 SHA-256，決定還須符合上節的出處格式（固定存檔 D 節中完整的一行使用者決定）。已核准卻無出處、引用不存在、hash 不符或 quote 不存在皆拒絕。required_evidence 是審閱清單，語意是否已滿足須由維護者依證據查驗；腳本驗證引用完整性與已記錄的狀態，不判定法律充分性、作者身分或自動產生使用者核准。

登記表綁定該 profile 的來源提交，避免把不同候選的確認直接帶過去。當前基準是 A12 的 2555687（main，含 A7–A11），候選審閱見 [A12 證據](development-records/runs/a12-fixed-review-2026-11-18/README.md)；A6 的 8285450 保留為歷史回歸輸入。A12b 已將來源逐列對照、封存與自有 MIT 綁定三項工程義務改為 evidence_complete；CPython、Microsoft、Qt、Tesseract 與其他未決條目仍維持原狀。A12c 只升 schema 及為每項加入空 accepted_gaps，不改實際狀態，**base／cpu 原三旗標與新增 disclosed 現況均為 false**。

## 內含元件目錄（A9）

`wheel` 內含的第三方元件（例如 numpy 的 OpenBLAS、Pillow 的 libjpeg-turbo）不寫進登記表，改由 [packaging/embedded/base-windows.json](../packaging/embedded/base-windows.json) 逐一列出：每個 wheel 的原生檔屬於哪個元件、元件版本與其依據、上游來源，以及授權原文的 repo 路徑與 hash。

- **版本依據分級**：`wheel-declared`（wheel 內文字檔或 METADATA 宣告）、`runtime-observed`（實際載入觀測；A9b 使用 cryptography 連結的 OpenSSL API，另記平台與 `_rust` SHA-256，Windows 觀測須對到 A6 檔案）、`unknown`（未知）。`unknown` 的版本欄位必須為 null；所屬條目保持 `open`，或依下節完整的使用者決定及隨包揭露條件關閉；不得把它改稱已知版本。
- **檢核範圍**：目錄綁定鎖檔的 wheel 名稱、版本與 sha256；原生檔必須與 A6 輸入一致，且與指定條目完全相同（不多、不少、不重複）；授權原文必須在 `src/desktop_app/data/licenses/windows` 內，hash 與 `inventory.json` 一致。檢核由 `scripts/embedded_components.py` 執行，並被 `redistribution_gates.py` 在組裝判定時呼叫。
- **不能驗證的部分**：`wheel-declared` 的 `version_source` 只記 wheel 內的檔案與欄位，repo 內沒有 wheel 本體，無法自動重驗宣告字串；元件清單是否完整、上游網址與授權判斷由人工審閱。這些必須以人工比對 wheel 內容的方式補上，不能因為腳本通過就視為已驗證。
- **限制**：目錄只是證據與檢核，不改變打包內容，也不代表使用者已同意再散布。

## A12c 揭露式關閉（schema 3）

`accepted_gaps` 是每個登記條目的必要字串陣列，實際登記目前一律為空。不可重複、不可用空白或控制字元冒充 id，也不可用任意 id 接受不存在的缺口。`runtime_sbom_disclosed` 是推導輸出，不是可手填的 entry gate；既有三個 gate 選擇器不變。輸出報告仍用 schema 1，另列 `registry_schema_version: 3`，不更動既有 source-review schema／分類計數。

缺口 id 直接從受 hash 綁定的目錄或固定候選取得，不塞完整元件資料進登記表：

- wheel：沿用目錄的 `distribution/component-id`；`version_basis=unknown` 逐項列入，不因外層 wheel 有版本而省略。
- CPython：`cpython/<component>`；原始列的 observed_version 為空、version_status 為 unknown 或 build-declaration-only 即是缺口。同一元件多份檔案去重，但每份檔案仍保留原生檔精確覆蓋。libffi 的建置宣告不是執行期版本觀測。
- Qt：沿用 attribution 原始 id。來源上位集合中 compiled_into_windows_wheel=unverified 的宣告也逐項列為建置／編入未證缺口，不能因 source-declared 有版本而稱完整；未知原生檔用 `qt-native/<file>`。這不是聲稱所有上位集合元件都已編入，也不提高 A11 的閉包／建置重現旗標。

含缺口的條目只准 open，或同時滿足以下條件後 user_approved：requires_user_decision 必須 true，decision_source 通過固定存檔 D 節及 hash／整行引用檢查，accepted_gaps 與該條目的全部缺口集合完全相同，並有有效隨包揭露。工程 evidence_complete 不能替代接受缺口。open 條目也不能先填 accepted_gaps 冒稱已接受。決定列的語意及是否真出自使用者，仍須人工逐項核對。

揭露檔契約是位於 `src/desktop_app/data/licenses/` 下的 JSON（以 evidence 路徑及 SHA 引用），閉合結構範例如下；可在同一檔逐項列多個義務，這只是合成格式，並非已作決定：

```json
{"schema_version": 1, "accepted_gaps": {"base-example": ["example/component"]}}
```

對應條目的清單必須與目錄缺口完全相同，JSON 本身亦拒絕重複鍵、未知頂層鍵及無效清單。一般 inventory JSON 或任意授權原文不能冒充揭露。base 候選中必須有 `_internal/desktop_app/data/licenses/<相對檔名>`，cpu 必須有 `_internal/worker-assets/licenses/<相對檔名>`，路徑與實際 prepare_worker_assets 佈局一致；其 SHA 必須等於 repo 揭露檔。同樣資料只留在 repo、未在候選 source-review 的 candidate_inventory.files 保存，不能關閉。來源提交也須等於登記表基準。若重定候選時精簡報告漏掉此檔，須先補齊證據，不使用其他檔案或舊候選 hash 兜底。

已存在的 embedded／Qt 目錄不可藉移除全部 evidence 引用來隱藏缺口。embedded_components 獨立呼叫而沒有 gates 的完整驗證回呼時，未知條目仍只能 open；經 gates 則依同一套規則檢查。CPU 的 CPython 缺口也使用相同接受與 worker 隨包證據規則；CPU wheel 詳細目錄仍由 A16 處理，本輪不擴充該目錄或關閉 CPU 義務。

「不得有 open」適用於影響來源盤點的條目。再散布總決定由 redistribution_approved 另外要求，clean-machine-manual 只屬 release_ready；因此完整揭露且經再散布決定後可以進 B1，但在大階段 C 完成之前仍 release_ready=false。所有來源條目關閉且沒有缺口時 complete／disclosed 都可為 true；有缺口被有效接受時 complete 仍 false、disclosed 才可 true。輸出分開列 unknown_components、accepted_gaps 與各旗標 blockers，不重寫原 input_inventory_summary 或 classification。

A12c 不新增實際隨包揭露檔、不寫 A13 決定、不修改現有條目狀態。真正揭露內容須待 A13 使用者決定，再由 A13b 加入包內並重新固定候選、驗證同 hash。本輪只有合成正反例證明規則，不能當成真實核准或實機證據。

## Microsoft 執行期目錄（A10）

基本包的 `base-microsoft.evidence[]` 以路徑與 SHA-256 引用 [packaging/microsoft/base-windows.json](../packaging/microsoft/base-windows.json)。版本、來源容器、逐檔身分、官方 Redist 比較與條款文件引用都放在目錄，不展開到義務登記表。CPU 的同類工作留給 A16。

- `scripts/microsoft_runtime.py` 在 hosted Windows 上唯讀核對已建置 bundle、原始來源及 VS 的 x64 CRT Redist。先確認 source／bundle 與 provenance 的 SHA-256 相同，再查 PE 版本資源及 Authenticode。每份複本各一列，numpy／pandas 改名複本不合併。
- `version_basis=pe-version-resource` 表示 DLL 自身的 `FileVersion`；wheel、Python 與 Redist 資料夾版本另記，不能互相代替。這是 A10 的 PE 證據分類，不改 A9 元件版本分級。
- 比較使用官方 Redist 同名 DLL 的**完整檔案** SHA-256；改名複本明記對照名稱。不同版本、簽章或任何位元組差異都會造成不相同；探測不猜測原因，不替換檔案。
- 目錄綁定 A6 輸入與 Windows 探測的原始結果；後者只有逐檔 bytes 與 A6 相同才可沿用身分觀測。另核對原鎖檔的 wheel container、證據原文的 repo 路徑與 hash；漏檔、觀測資料不同、hash 不符及移除 A13 決定要求都拒絕。
- 簽章、版本或 A6 對應缺口，以及尚未核對的條款，都不當成已關閉的工程證據；這類條目保持 `open`。具體觀測與限制見 [本輪證據](development-records/runs/a10-microsoft-runtime-2026-11-17/README.md)。Windows 的簽章查詢是當時該 runner 的信任判讀，不代表對軟體授權的核准。
- A6 原始 `microsoft-native-redistribution-review` 列及其數字保持原樣；判定器依對應條目的狀態列出有效阻擋，不從原盤點刪除 review_reason。`requires_user_decision: true` 保證工程證據齊全也不等於 A13 已同意。
- 條款原文只作開發證據；來源、標題與適用性分開記錄。未向官方網站驗證的轉載有明確標記，不能冒充本輪下載的官方原文。runtime-use EULA、Visual Studio 的散布權利與 REDIST 清單也不能互相代替；是否適用及允許再散布由使用者在 A13 決定。

## 執行與驗收

```bash
python scripts/redistribution_gates.py --source-review docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json
python scripts/redistribution_gates.py --source-review docs/development-records/runs/a12-fixed-review-2026-11-18/cpu-source-review.json
```

有效輸入輸出旗標、各旗標阻擋條目、相依關係與精確對應。exit 0 只表示登記／涵蓋性有效，交付流程必須另檢查對應旗標；未關閉時仍會列出 blockers。錯誤輸入非零退出，指定 `--output` 時只准寫新檔，驗證錯誤不留下部分成功報告。

測試含未知檔／reason、重複對應、缺少決定出處、改證據／決定原文、三旗標的分層與相依、base／cpu 獨立、保留原始計數與 CLI 不覆寫。全關閉的正例使用合成證據，只證明旗標不是常數，不代表實際授權或實機驗收已通過。

A12c 不動 spec、依賴、打包內容或計數口徑，不代做 A13、不交付產品、Release 或 tag；完成後先停。

## A9b OpenSSL 版本與原文的界線

沿用既有 runtime-observed，不新增版本分級。觀測須由實際安裝的 cryptography 呼叫它所連結的 OpenSSL 文字與數值版本 API，兩者一致才可綁定上游同版本 tag 的 LICENSE。二進位靜態字串不是 wheel-declared，CPython ssl 的版本也不能代替 cryptography。Linux 與 Windows 各自記錄；只有 Windows 的 `_rust.pyd` bytes 與 A6 相同才可把該觀測綁入基本包內含元件目錄。

新增原文透過既有 supplemental_sources 管線隨包，並在基本資產與最終 bundle 各驗缺檔、內容 hash 及 cryptography 套件對應。Rust 相依等未查明部分維持 unknown／open，原文補齊不等於核准再散布。

## A12 重新綁定候選（2555687）

登記表的 `source_commit` 改為 2555687，原生檔與 review_reason 仍各自精確對應；唯一的 stale selector 是 `base-own-mit-binding` 的 `package-original-notice-pending:markitdown-desktop`（A7 綁定後已不存在），僅移除該選擇器，A12 當時狀態維持 open；A12b 之後才依既有證據關閉三項工程義務。

目錄綁定的調整只限於綁定欄位，檔案 bytes 與身分事實不變：

- `packaging/embedded/base-windows.json`：`source_commit` 與 `source_review`（路徑、hash）改指 A12 的 base-source-review.json；`embedded_components.py` 的固定路徑同步。
- `packaging/qt/6.12.0/thirdparty/catalog.json`：只改 `source_commit`。
- `packaging/microsoft/base-windows.json`：只改 `source_commit`；`basis` 與 `probe` 不變，仍指 A6 基準與 A10 探測。原因是 CI 探測（A12 候選，見證據目錄）是在 A6 基準上比對的，無法在不重跑 CI 的情況下改成 A12 基準。`check_catalog` 因此改為：探測的基準必須與基準檔自身的 selection 一致；候選綁定仍由逐檔 `a6_sha256`、`origin`、`distributions` 與候選原生檔 bytes 比對完成。
- 三個目錄的 sha256 變動，只在登記表對應條目的 `evidence` 更新引用，條目的 status、選擇器、required_evidence 與 requires_user_decision 不變。

A12 的基本包出口報告見 [證據目錄](development-records/runs/a12-fixed-review-2026-11-18/README.md)；三旗標仍由 gates 推導為 false。

# 現況

更新：2026-11-20（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | PR 1–36 已合併（aab43c2）；A13c（PR 33）、B1a（PR 34）經 Claude reviewer 查驗無必須修正 |
| 本輪分支 | `codex/b2-stage-c-checklist`：B2 驗收表，等待 Claude reviewer；B1b 另有獨立分支 |
| 下一棒 | **Codex（GPT）**：B1b 與 B2 平行，各一個 PR，從最新 main 開新分支 |
| 固定來源 | A13b `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（base run 44295039865、cpu run 44295044417、Microsoft 探測 run 44300296037） |

## B. 這個階段完成了什麼

- **大階段 A 收尾**：Claude planner 2026-11-19 整體複查 A1–A13c 全部通過、無必須修正。gates 以 A13b 審閱實跑：base `runtime_sbom_disclosed`、`redistribution_approved` true，`runtime_sbom_complete`（10 條已接受缺口）與 `release_ready`（只差大階段 C 的 `base-clean-machine-manual`）false；cpu 四旗標 false。基本包每個檔案以「已知或經使用者接受並隨包揭露」說得出來源、版本與授權義務。
- 相關 10 個測試模組 176 項在 planner 環境通過（`test_qt_notice` 1 項因無 PySide6 未執行）；完整 941 項回歸本輪未重跑，沿用 progress.json 來源提交。
- run 44307725980（PR 31 合併後的 main push）Windows 失敗位於升級測試重建前一版 990e600 的驗收；同一棵樹在 PR head 與後續兩次 main push 都通過，判定為間歇性問題，不影響 B1b。根因因 artifact 主機被本環境擋下而未查明。
- 順帶修正過時敘述：progress.json m5、`docs/redistribution-gates.md` 的旗標現況、accepted_gaps 與 A16 編號。

## C. 未完成、阻擋與下一步

**整體規劃**（每個編號一個 PR，CI 通過且查驗完成即合併）

| 大階段 | 編號與任務 | 狀態 |
| --- | --- | --- |
| A 關閉來源與再散布缺口 | A1–A7（PR 5、6、8–13） | 完成 |
| | A8 義務登記表與旗標判定規則：新增 `packaging/redistribution/obligations.json`（分 base／cpu，每項含 id、對應的 review_reason 或檔案群、所需證據、狀態、使用者決定出處）、`scripts/redistribution_gates.py`、測試與 `docs/redistribution-gates.md`（三旗標定義；寫明 `unresolved_files` 是「無 wheel 擁有者」的計數，不是要歸零的指標）。旗標改由條目推導，不再只是常數。順帶修正 `scripts/license_inventory.py` render() 兩句過時文字（「Tesseract 執行檔尚未隨 Windows 包發佈」「完整 Windows 二進位檔尚未建置」）並重產 `third-party.md`。驗收：以 A6 的 base／cpu source-review 為輸入，每個原生檔與 review_reason 各對到恰好一個條目，未對到者拒絕；標「使用者已核准」卻無決定出處者拒絕；現況輸出三旗標皆 false 並列出未關閉條目；不動 spec、打包內容與既有計數口徑；限制為單一 JSON 加一支檢核腳本，避免過度設計 | 完成（PR 15） |
| | A8b 義務登記檢核補強：決定出處限固定存檔 D 節的使用者決定列、反向檢查 stale selector、release_ready 綁定 `stage-c-` 證據、結構封閉與 schema 2（使用者決定插入於 A9 之前） | 完成（PR 16） |
| | A9 基本包 wheel 內含第三方元件目錄（非 Qt、非 Microsoft）：元件名稱、版本、版本依據分級、來源與隨包原文；未知者保持 open | 完成（PR 18） |
| | A9b cryptography 內含 OpenSSL 原文隨包：A9 查得 `cryptography/hazmat/bindings/_rust.pyd` 有 `OpenSSL 4.0.3` 字串（靜態併入），wheel 未附原文。使用者已同意補：以固定上游來源（OpenSSL 對應版本標籤的 LICENSE 原文，記來源網址、版本依據與 sha256）加入隨包授權資料，接到既有原文管線與目錄（`packaging/embedded/base-windows.json` 的 openssl 元件），補缺檔／改內容反例；版本仍須有依據，不能只憑字串就標成 wheel-declared（可新增分級需先說明）。會改變安裝包內容（使用者已同意） | 完成（PR 21，9360a54）；六項 CI 與查驗通過 |
| | A10 Microsoft 執行期逐檔對照（基本包 14 檔：根目錄 3、PySide6 5、shiboken6 4、numpy.libs 與 pandas.libs 各 1 個改名的 msvcp140）：收集來源、PE 版本、簽章、與官方 Redist 同名檔雜湊比對、適用條款文件；改名複本單獨標示；review_reason 改由登記表狀態控制。條款是否允許由使用者在 A13 決定 | 完成（PR 20）；Microsoft 條款已由 A13 使用者決定，A13b 已接線 |
| | A11 Qt 內含第三方（qt_attribution）、建置資訊（`QLibraryInfo.build()` 等）與「可替換 Qt」驗收（hosted Windows CI：替換 DLL 後可啟動、移除 Qt6Core 後啟動失敗，標明非實體機）；更新 `qt-lgpl-notice.md`。LGPL 做法是否足夠由使用者在 A13 決定 | 完成工程與 hosted Windows 驗證（PR 22）；LGPL 做法已由 A13 使用者接受，A13b 已接線 |
| | A12 以 A8–A11 完成後的 main 重新固定候選，產出基本包出口報告；`runtime_sbom_complete` 依 A8 定義推導，不得人工改寫。**順帶整理 `docs/progress.json`**：把 `previous_*` 等舊紀錄鍵搬到 `docs/history/`（搬移，不刪除內容；使用者已同意）。**不做打包減量**（使用者決定） | 完成（PR 23） |
| | **A12b 證據接線**（使用者已同意）：把已存在的證據接進 `obligations.json`，不改安裝包。(1) `base-source-attribution`、`base-archives`、`base-own-mit-binding` 以既有證據改為 evidence_complete，每條 evidence 用路徑加 hash 引用；30 個 origin-known 列（A12 base-source-review 的 classification）各寫對照理由，存於新證據目錄 `docs/development-records/runs/a12b-evidence-wiring-*/`。(2) `base-cpython`、`base-tesseract-models` 補上 evidence 引用（後者引用 `packaging/native/minimal-windows.json`、minimal-notices、`src/desktop_app/data/ocr-four-languages.json`、A12 classification），狀態維持 open。(3) **`base-cpython` 改為 `requires_user_decision: true`**（使用者同意，供 A13-3）。(4) 從微軟官方取回 **VS2022 Community 授權原文**（記來源網址、取得日期、sha256），存入證據目錄，並寫白話摘要標出與再散布有關的段落（可散布程式碼、使用資格）；只陳述條文，不判斷是否適用。(5) 順帶修正：`base-wheels-cryptography` required_evidence 裡已過時的 openssl 字樣、progress.json m5 描述、`packaging/microsoft/base-windows.json` limitations 的「fixed A6 source」敘述（只改敘述，事實欄位不動並同步 hash）、`base-exit-report.json` 註明 `base-clean-machine-manual` 要到大階段 C、測試名稱 `test_actual_a6_profiles_have_exact_coverage_and_false_flags` 改成符合實際輸入。驗收：gates 重跑 base／cpu exit 0、三旗標 false，runtime_sbom 阻擋清單由 14 條減少並在 PR 列出；改 evidence hash 的反例被拒；完整回歸與 EXPECTED_TESTS 同步；不動 spec、打包內容、鎖檔、既有計數，以及任何已是 `requires_user_decision: true` 條目的狀態 | 完成並 Merge（PR 26，4f30196）；五條 CI 與查驗通過 |
| | **A12c 揭露式關閉規則**（使用者已同意，A13-0）：`runtime_sbom_complete` 維持嚴格（有任何未知元件就是 false）。新增推導旗標 `runtime_sbom_disclosed`：不得有 open 條目；凡含 unknown 或僅建置宣告的條目，必須是 `user_approved`，並且有 `decision_source`、`requires_user_decision: true`、新鍵 `accepted_gaps`（逐一列出被接受的元件 id，必須與目錄的 unknown 清單完全相等），evidence 至少一筆指向隨包揭露檔（例如 `src/desktop_app/data/licenses/known-gaps.json`），且該檔以相同 hash 出現在候選 source-review 中。`redistribution_approved` 的前提由 `runtime_sbom_complete` 改為 `runtime_sbom_disclosed`；gates 輸出列出 accepted_gaps。`embedded_components` 的「unknown 必須 open」改為「open，或符合上述條件的 user_approved」。schema 升為 3、結構仍封閉；規則同時適用 cpu。驗收：合成反例（accepted_gaps 與 unknown 不等、缺 decision_source、缺揭露檔、揭露檔不在候選或 hash 不同）皆拒絕；合成全揭露正例 `runtime_sbom_complete` false、`runtime_sbom_disclosed` 與 `redistribution_approved` true；實際 A12 輸入三旗標仍 false；現有條目狀態不改 | 規則及回歸完成（PR 27）；最終整合見 PR，完成後停止 |
| | **A12d wheel 內含元件執行期版本觀測**（使用者 A13-4 選 b）：對有版本 API 的元件（例如 lxml 的 libxml2／libxslt、Pillow 的 raqm／fribidi，coder 先查哪些真的有 API）以 hosted Windows CI 觀測，比照 A9b 以 bytes 綁回 A12 原生檔，改為 runtime-observed；查不到者維持 unknown。不改安裝包。驗收：每個改為 runtime-observed 的元件都有 Windows 觀測且對應 .pyd／.dll 的 sha256 等於 A12 原生檔；反例（bytes 不符、未觀測卻標已知）被拒；gates 兩 profile exit 0、三旗標 false | 完成（PR 30） |
| | A13 使用者確認基本包門檻：A13-0～A13-7 **已由使用者決定（2026-11-18，見 D 節逐條）**。各條目已於 A13b 依決定接線 | 決定已記錄並由 A13b 實作 |
| | **A13b 依決定調整並重新固定候選**（使用者已同意以下打包變更）：(1) 根目錄 `vcruntime140.dll`、`vcruntime140_1.dll` 改用 Visual Studio 官方 Redist 版本（A13-1 b），在 CI 驗證程式仍正常執行；numpy／pandas 改名複本與 Qt 9 份照現狀揭露。(2) 新增隨包揭露檔 `src/desktop_app/data/licenses/known-gaps.json`：依 A12c 規格逐條列出被接受的未知元件（A12d 之後的 wheel unknown、libffi 建置宣告、Qt 85 個未知 attribution 等），並新增測試版限制說明（A13-6 草稿，見 D 節）。(3) 依 D 節決定列寫入各條目的 `decision_source`（引用本輪存檔）、`accepted_gaps`，改為 `user_approved`；每個條目各引用一列，查驗時人工比對條目 id 與範圍。(4) 以 workflow_dispatch 重新固定候選、重組 source-review；在新候選上重跑 Microsoft 探測，把 A12 放寬的 `check_catalog` 收回為「探測基準等於登記表來源」並補反例。(5) gates：base `runtime_sbom_disclosed` 與 `redistribution_approved` 推導為 true（cpu 仍 false），`runtime_sbom_complete` 仍 false，`release_ready` 仍 false（需大階段 C）。不做 B1 上傳 | 完成（PR 31） |
| | **A13c 以 A13b 候選重產逐列來源對照**（reviewer 建議）：`base-source-attribution`、`base-archives`、`base-own-mit-binding` 本輪前引用 A12 審閱與 A12b `origin-known-review.json`；本候選 30 個 origin-known 列中 6 列 sha256 已變（4 個建置產生檔、2 個根目錄 vcruntime——後兩列 A12b 的理由「來自 CPython、PE 14.42」已不正確，實際 bytes 由 base-microsoft 目錄涵蓋）。以 b17d51b 審閱重產逐列對照並更新三條 evidence；不改條目狀態與旗標。gates 不會偵測此類過期 | 完成（PR 33）；大階段 A 經 planner 複查無必須修正，2026-11-19 收尾 |
| B 測試版安裝包 | **B1a 測試版產出準備**：寫好以 CI artifact 產出基本包測試版的流程，來源固定為 A13b 候選 b17d51b，產物附提交、版本、安裝包 sha256、隨包授權原文清單、`known-gaps`、測試版限制說明；artifact 保留 **30 天**（使用者決定）。以 workflow_dispatch 試跑驗證產物內容，**試跑不上傳安裝包**（只上傳報告），不建 Release 或 tag | 完成（PR 34）；公開上傳仍停用 |
| | **B1b 測試版公開產出**（交 Codex）：以 B1a 流程從 main 產出並公開上傳安裝包 artifact（保留 30 天）。驗收（planner 建議、使用者 2026-11-19 同意做法）：(1) **逐檔對照**：下載 run 44295039865 `windows-base-validation-reports` 的 `bundle-provenance.json`（sha256 `b7fa49e6df55…`，即 base-source-review.json 的 `provenance_report_sha256`；**2026-11-25T11:45Z 到期**），先核 sha，再與重建 bundle 的 inventory 比對：路徑集合相等、明列且附理由的生成檔例外外 bytes 全同、`pure_modules_sha256` 相同；多檔、少檔、改檔、清單外生成檔、provenance sha 不符皆拒絕並有反例測試。結果寫 `CONTENT-EQUIVALENCE.json` 放進產品與報告，BUILD-INFO 引用其 sha。來不及在到期前完成時，改用 repo 內較弱依據（264 列分類、153 原生檔、原文、模組雜湊、檔案數），並在公開說明寫明（使用者已接受此退路）。(2) 公開上傳只在 `github.ref == refs/heads/main`、`PUBLIC_UPLOAD_ENABLED=True`、gates 四旗標等於預期、逐檔對照通過、lifecycle 安裝包 sha 等於上傳安裝包時執行；腳本同步檢查 `GITHUB_REF`；非 main 要求公開被拒並有反例。(3) 產品含 Setup、BUILD-INFO（含 `byte_identical_installer_to_original` 與對照摘要 sha）、CONTENT-EQUIVALENCE.json、LICENSE-FILES.json、known-gaps.json／.md、test-build-limitations.md、SHA256SUMS.txt 與中文 README（測試版非正式版、需登入 GitHub 下載且 30 天到期、`certutil -hashfile … SHA256` 核對、未簽章與 SmartScreen、安裝與移除、授權與已知缺口位置、Issues 連結、安裝程式由同一固定來源重建且容器與審閱時不同）。(4) 報告 artifact 寫明 SHA256SUMS 對應產品目錄。(5) 合併後從 main dispatch 一次：記錄 artifact 名稱、digest、大小、到期日；API 核對只有預期兩份 artifact。dispatch 前先跑一般驗證取得當天有效的 OCR 輸入（只保留 1 天）。(6) **公開後立即另開小 PR 把 `PUBLIC_UPLOAD_ENABLED` 改回 False**，並更新 STATUS。(7) 完整回歸、EXPECTED_TESTS 與 progress.json 同步；PR CI 全過、reviewer 無必須修正。不動 spec、鎖檔、登記表狀態、gates 規則與固定候選，不碰 `windows-build.yml`，不建 Release 或 tag | 下一步（Codex；2026-11-25 前） |
| | **B2 驗收表**（交 Codex，與 B1b 平行，獨立 PR）：依 C1–C3 逐項列乾淨 Windows 10／11 安裝、離線首次啟動、四語 OCR、中文路徑、修復、移除與人工操作的勾選表；每項有預期結果與證據格式，填寫結果放 `docs/development-records/runs/stage-c-…/`（符合 `base-clean-machine-manual` 前綴）。依使用者決定，大階段 C 用 **B3 後的新版本**，表格以「待填安裝包 SHA」欄位綁定，不寫死 B1b 的 SHA。只改文件，不改程式 | [驗收表已備妥](docs/stage-c-acceptance.md)，待 Claude reviewer；大階段 C 等 B3 後的新包 |
| | B3a CPU：flatbuffers、rapidocr 原文綁定（接線 `prepare_worker_assets.py`；錯綁與缺檔反例）（原 A14） | 待開始（B1b 之後） |
| | B3b CPU：PP-OCR 模型來源、版本、雜湊與授權原文（不以套件的 Apache 宣告代替）；授權範圍需使用者確認（原 A15）。**另評估改用繁體中文識別模型以解決 ONNX 繁中已知缺口**（`tests/test_onnx_ocr.py` 的 `test_traditional_chinese_quality_known_gap` 預期失敗）：候選為 PP-OCRv5、PP-OCRv6 的繁中能力與專用 chinese_cht_PP-OCRv3_rec（需查證授權、ONNX 可用性與大小），以該固定繁中測試圖比較準確度；台灣聯發科 Breeze2 屬 3B／8B 多模態大型語言模型（Llama 社群授權），不適合 CPU 選配元件，若要採用改列大階段 E 或另立 GPU 選配元件。換模型屬更換模型與打包內容，需使用者同意；評估結果列表交使用者選擇 | 待開始（B1b 之後） |
| | B3c CPU：Shapely／GEOS（LGPL）與 CPU wheel 內含元件（沿用 A9 格式），CPU Microsoft 6 檔（沿用 A10）；LGPL 做法需使用者確認（原 A16） | 待開始（B1b 之後） |
| | B3d CPU：查明 setuptools、pip、pyinstaller 等建置工具是否真的進了 worker；若要排除屬打包變更，需使用者同意（原 A17） | 待開始（B1b 之後） |
| | B3 CPU 元件重新定版（需 B3a–B3d 完成並經使用者確認）。會改動共用 `source_commit`，範圍含 base 重新審閱與 gates 重建，並以此新候選產出大階段 C 驗收用的新測試版 | 待開始 |
| | B4 使用者確認測試版結果（綁定所測安裝包的 SHA，並在其 artifact 30 天期限內完成，否則重新產出） | 需使用者實機測試 |
| C 乾淨機與人工驗收 | C1 乾淨 Windows 10／11 安裝與離線首次啟動；C2 四語、中文路徑、修復移除；C3 人工操作 | 需使用者或實體 Windows |
| D 功能擴充 | D1 圖片檔走本機 OCR；D2 影音獨立選配元件 | 等使用者決定 |
| E GPU | 實卡驗收 | 延後 |

**執行順序**：大階段 A 已收尾 → **B1b 與 B2 平行（Codex，下一步）** → B3a–B3d（CPU，原 A14–A17；B3b 換繁中模型會牽動 known-gaps 與限制文字的 ONNX 繁中缺口一行）→ B3 → B4 → 大階段 C。各編號一個 PR。

**大階段 B 的進入條件**

- B1b：條件已全部達成（gates 推導 base `redistribution_approved` true、A13c 完成、planner 2026-11-19 複查無必須修正）。CPU 不必先關閉。
- B3：B3a–B3d（原 A14–A17）完成並經使用者確認。
- `release_ready` 在大階段 C 的乾淨機與人工驗收之前維持 false。

**A7 查驗留下的小問題**（已在 A8 第一個提交處理）：兩個 Windows workflow 的 pwsh 預檢共 14 處改用 `-cmatch '^[0-9a-f]{40}\z'`（`-match` 不分大小寫，`$` 允許結尾換行；後面的 Python 檢查會擋，沒有安全缺口）；`tests/test_candidate_review.py` 再加一個「只有越界」的反例（保留其餘各片、把最後一片改成 part=N+1）；`progress.json` 的 m5 描述與 `a7_mit_notice.status` 更新；CHANGELOG 補一句 `full_regression.baseline_environment_identical` 欄位移除的原因（或還原）。

**A9、A10、A11 共同注意事項**（A8 查驗提出）：三者平行修改 `packaging/redistribution/obligations.json` 的不同條目。各自的 PR 要把要在 A13 由使用者決定的條目改為 `requires_user_decision: true`（base：`base-microsoft`、`base-qt`、`base-tesseract-models`；cpu 的 GEOS 與 rapidocr 模型條目留給 A15、A16）。元件細節（名稱、版本、版本依據分級、來源、隨包原文）放在另一個由 `evidence[]` 以路徑加 hash 引用的目錄 JSON，不塞進登記表；原生檔仍只對到一個條目。合併順序依完成先後，後合併者先把 main 合併進自己的分支並重跑 `redistribution_gates.py` 兩個 profile 再合併。

**補充換手來源**

- 使用者已同意補 cryptography 內含 OpenSSL 原文，列為 A9b（見上表）；A9b 已於 PR 21 完成原文隨包。
- A10 的 Microsoft 條款適用與再散布許可仍由使用者在 A13 決定；官方候選原始檔與 REDIST 全頁已取得；不把原文取得、簽章有效或 hash 相同當成已核准。

**有期限的資料**：PR 上的 Windows 報告保留七天，以暫時合併提交執行，不是候選證據。artifact 儲存主機常被本環境網路政策擋下，需要的資料請讓 CI 寫進公開摘要。

**既有限制**：ONNX 繁中缺口、RAM 軟性預算、Windows 實機／GPU 未驗收；沒有產品交付、Release 或 tag。

## D. 新增規則與決定

使用者親自做的決定逐筆保留，不因精簡而合併或刪除；工具專用設定的適用範圍說明不能取代原決定。以下恢復原文自 [A4 現況存檔](docs/history/status/2026-11-16-a4-before-a5.md)。

| 日期 | 來源 | 內容 |
| --- | --- | --- |
| 2026-11-16 | 使用者本輪指示 | API 存取恢復後完成 A4 PR、Windows CI 與合併等阻擋項目，再依現況接續；沿用既有查驗與 Merge 條件，沒有新增產品發行授權 |
| 2026-11-16 | 使用者本輪接手指示 | Codex 從 C 節 A4 開始；更新 STATUS、推送自己的新分支、開 PR；CI 通過即可依 AGENTS 的查驗條件 Merge。不直接推 main、不推別人分支。A4 任務內排除已驗證非必要的 setuptools，不擴及其他打包調整 |
| 2026-11-12 | 使用者指示 | 工作分支＋PR，不直接推 main；不強制推送；門檻未關閉前不對外交付安裝包（含 CI artifact）；暫不建立 Release 或 tag |
| 2026-11-13 | 使用者同意 | 現況與歷史分開、自動索引、數字單一來源、階段完成才整體更新、新證據移出 repo（舊證據原地保留）、暫緩擴充元件系統、動到的檔案順手拆開壓縮的程式行 |
| 2026-11-13 | 使用者決定 | 自有程式採 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 使用者同意 | 排除 Qt TLS 外掛與來源不明的 OpenSSL；從 CPU 文字辨識元件排除 OpenCV 內附的 FFmpeg，影音日後另做獨立選配元件；微軟執行期改用官方來源 |
| 2026-11-14 | 使用者指示 | 專案由 Claude 與 Codex 輪流進行，每個 AI 至少完成一個小階段（PR）才換手；規則見 AGENTS.md「多個 AI 輪替」 |
| 2026-11-16 | 使用者指示 | A3 完成後 Claude 暫停，換手給 Codex（GPT）從 A4 繼續 |
| 2026-11-16 | 使用者指示 | 合併 PR 4、PR 5；之後每完成一個編號（如 A4、A5）視為小階段完成即可合併；`main` 已由使用者設定分支保護 |
| 2026-11-14 | 使用者指示 | Claude 採三角色分工：規劃者（主對話）、編程者 `coder`、查驗者 `reviewer`，流程見 CLAUDE.md；主對話推理強度為中 |
| 2026-11-16 | 使用者決定 | 規劃者改為子代理 `planner`（`claude-fable-5-2`），只在大階段開始前寫計畫、完成後整體複查；主對話改為不屬於角色的協調者，預設模型 `claude-opus-5-5`。原因：主對話會隨工作階段切換模型，角色模型應固定在子代理定義檔 |
| 2026-11-16 | 使用者本輪指示 | A4 已由 Claude reviewer 查驗通過；開始 A5，並在同一 PR 修正 A4 完成／main 已合併 PR 1–8 的現況與 next；補充 A4 unresolved_files=109 的計數口徑與基準，找不到寫未保存 |
| 2026-11-16 | 本輪明確授權的保存補註 | 僅對指定 A4 證據 README 追加說明；先保存原版 README／manifest，再更新該 README 的 hash。其他舊證據及原始 CI JSON 不變，不擴大成任意改寫歷史的授權 |
| 2026-11-16 | 既有使用者指示／AGENTS | 各編號一個 PR，全部 CI 與查驗通過即可一般 Merge；不直接推 main、不推別人分支、不 force push 或刪分支 |
| 2026-11-13 | 已確認授權決定 | 自有程式 MIT，著作權人「周大詮 (ChouTa-chuan)」，涵蓋以不同 AI 工具產生的全部自有內容 |
| 2026-11-13 | 已確認打包決定 | 排除 Qt TLS／來源不明 OpenSSL、CPU OCR 的 OpenCV FFmpeg；VC runtime 取官方來源，影音另行規劃 |
| 2026-11-13–16 | 已確認維護方式 | 現況／歷史分開，數字單一來源，階段完成才整體更新，原文／模型／圖及原始失敗保留；優先基本包，暫緩擴充元件系統 |
| 既有規則 | AGENTS／使用者 | 來源與再散布門檻未關閉前不發 Setup／worker／模型（含產品 artifact）、不建 Release 或 tag；ONNX 繁中、RAM 軟性預算、實機／GPU 限制維持 |
| 2026-11-14–16 | Claude 專用分工 | CLAUDE.md 與 .claude/ 保存其角色與模型；不把工具專用設定視為所有 AI 的規則 |
| 2026-11-16 | 使用者本輪指示 | A5 已由 Claude reviewer 查驗通過；開始 A5b，第一個提交恢復使用者決定、修正 main 已合併 PR 1–9／next、補 A5 最終四個 CI run；D 節精簡不合併或刪除使用者親自做的決定。指定 A5 README 補註前保存原版及原始 manifest，其他舊證據不變 |
| 2026-11-16 | 使用者補充 A5c | A5 的 runtime probe 接受條件、缺失 OpenSSL 原文反例與 extension 版本說明列入 C 節待辦；獨立 PR、全部 Windows CI 通過才合併，A5b 不處理 |
| 2026-11-17 | 使用者決定 | 之後在 D 節新增紀錄時，不要再加原文已涵蓋的摘要列。 |
| 2026-11-17 | 使用者指示 | 之後不要再保存重複的舊嘗試完整 JSON，只留 hash 與 run 編號。 |
| 2026-11-17 | 使用者指示 | A7 完成後先停，大階段 A 的整體複查與剩餘義務的重新規劃，交由 Claude planner 處理。 |
| 2026-11-17 | 使用者決定 | 採用 Claude planner 的大階段 A 重新規劃：A 續編 A8–A17，使用者確認門檻由原 B4 前移為 A13（B1 之前）；A12 不做打包減量；A12 整理 `docs/progress.json`，把舊紀錄鍵搬到歷史目錄（搬移不刪除）；CPU 的 A14–A17 排在基本包 B1 之後；A8 交給 Codex（GPT） |
| 2026-11-17 | 使用者本輪指示 | A8 限制為單一 JSON 加一支檢核腳本，不動 spec、打包內容與既有計數口徑；三旗標現況仍為 false。A8 完成後先停，回報使用者。 |
| 2026-11-17 | 使用者決定 | 在 A9 之前插入 A8b（A8 檢核補強）；GPT 用量已滿，A8b 改由 Claude coder 接手 |
| 2026-11-17 | 使用者決定 | Claude 角色模型改為：規劃者 `planner` 用 `claude-opus-5-5`、編程者 `coder` 用 `claude-haiku-5-5`、查驗者 `reviewer` 用 `claude-sonnet-5-5`；協調者（主對話）預設 `claude-opus-5-5`；推理強度維持中。原因：Fable 5.2 在使用者方案中無法使用。取代 2026-11-16 planner 用 `claude-fable-5-2` 的設定 |
| 2026-11-17 | 使用者決定 | cryptography Windows wheel 靜態併入的 OpenSSL 要補授權原文隨包（列為 A9b，會改變安裝包內容）；A10 換手交給 Codex（GPT） |
| 2026-11-17 | 使用者本輪 A10 指示 | 從最新 main 開自己的新分支做 Microsoft 基本包逐檔證據；細節由 evidence 路徑加 hash 引用目錄，obligations.json 只改 Microsoft 條目並標 A13 使用者決定；base／cpu 三旗標維持 false。不動 spec、打包內容、鎖檔與既有計數，條款是否允許由使用者在 A13 決定。A10 完成後先停。 |
| 2026-11-18 | 使用者本輪指示 | 依序做 A9b 與 A11，各自一個 PR；先完成 A9b 並合併，再從最新 main 開新分支做 A11。A9b 已同意原文隨包內容變更；A11 hosted Windows 可替換驗收，base-qt 需 A13 使用者決定；不動 spec、鎖檔與既有計數口徑，不做 A12；A11 完成後先停。 |
| 2026-11-18 | 使用者補充授權 | 允許必要的 hash 同步：只更新共用目錄（或 A11 的共用來源）的 sha256 引用，其他條目的 status、選擇器、required_evidence、requires_user_decision 一律不變；並在 PR 說明與 CHANGELOG 列出哪些條目只做了 hash 同步。改完重跑 base、cpu 兩個 profile 的 gates，三旗標仍須為 false。 |
| 2026-11-18 | 使用者決定 | 同意插入 A12b（證據接線），並同意把 `base-cpython` 條目改為 `requires_user_decision: true`（libffi 僅建置宣告等留待 A13-3） |
| 2026-11-18 | 使用者決定 | A13-0：同意採用「接受並揭露」的關閉規則（A12c）；`runtime_sbom_complete` 維持嚴格，`redistribution_approved` 改依 `runtime_sbom_disclosed` |
| 2026-11-18 | 使用者說明 | 使用者判斷自己適用 Visual Studio Community（免費）授權；A12b 取回 Community 授權原文供 A13-1 參考 |
| 2026-11-18 | 使用者決定 | A12b 與 A12c 交給 Codex（GPT）接手，依序各一個 PR |
| 2026-11-18 | 使用者本輪指示 | A12c 完成後先停，回報使用者。 |
| 2026-11-18 | 使用者 A13 決定 | A13-1（base-microsoft）：選 b。根目錄 vcruntime140.dll、vcruntime140_1.dll 換成 Visual Studio 官方 Redist 版本；numpy／pandas 改名複本與 PySide6／shiboken6 的 9 份照現狀接受並揭露。同意此打包變更。使用者判斷適用 Visual Studio Community 授權 |
| 2026-11-18 | 使用者 A13 決定 | A13-2（base-qt）：接受現行 LGPL 做法（動態連結、隨包原文與固定上游原始碼連結、hosted Windows 可替換驗收），未知項目接受並揭露 |
| 2026-11-18 | 使用者 A13 決定 | A13-3（base-cpython、base-wheels-cffi）：libffi 僅有建置宣告，接受並在揭露檔註明版本為官方建置宣告 |
| 2026-11-18 | 使用者 A13 決定 | A13-4（base-wheels-numpy、pandas、pillow、lxml、cryptography、onnxruntime、pypdfium2、cffi）：選 b。先做 A12d 以 Windows 執行期觀測縮短未知清單，剩下的未知元件接受並揭露 |
| 2026-11-18 | 使用者 A13 決定 | A13-5（base-tesseract-models）：接受 CI 以固定來源靜態建置的 tesseract.exe 5.5.3 與固定提交的四語 tessdata_fast 模型 |
| 2026-11-18 | 使用者 A13 決定 | A13-6（base-clean-machine-manual）：同意測試版限制說明草稿：測試版非正式版；ONNX 繁中準確度已知缺口（內建 Tesseract 不受影響）；RAM 為軟性預算；未在乾淨 Windows 10／11 實機完整驗收；GPU 未在實卡驗證；部分內含元件版本未知並列於 known-gaps.json；安裝程式與 tesseract.exe 無程式碼簽章；問題回報到 GitHub Issues。該條目仍需大階段 C 證據才能關閉 |
| 2026-11-18 | 使用者 A13 決定 | A13-7（base-redistribution-decision）：同意 B1 以 CI artifact 公開產出基本包測試版 |
| 2026-11-18 | 使用者決定 | A12d 與 A13b 交給 Codex（GPT），依序各一個 PR |
| 2026-11-18 | 使用者決定 | GPT 用量耗盡、A12d 只完成一半：由 Claude reviewer 確認現況後交 Claude coder 收尾；A13b 也改交給 Claude coder |
| 2026-11-19 | 使用者決定 | 重新排程：CPU 的 A14–A17 移入大階段 B，改編號為 B3a（原 A14）、B3b（原 A15）、B3c（原 A16）、B3d（原 A17），作為 B3 的前置；A13c 完成後大階段 A 收尾並交 Claude planner 複查。D 節舊列中的「A14–A17」依此對照 |
| 2026-11-19 | 使用者決定 | B1 拆成 B1a（準備與試跑，不公開）與 B1b（公開產出）；A13c 與 B1a 可平行，B1b 待 planner 複查大階段 A 無必須修正後才做。測試版以 CI artifact 公開產出、保留 30 天，不建 Release 或 tag。A13c 與 B1a 交給 Codex（GPT） |
| 2026-11-19 | 使用者決定 | B3b 加入評估：以繁體中文識別模型（PP-OCRv5／v6 繁中、chinese_cht_PP-OCRv3_rec 等）解決 ONNX 繁中已知缺口；實際更換模型仍需使用者同意 |
| 2026-11-19 | 使用者決定 | B1b 採 planner 建議：以同一固定來源重建的安裝包公開，依據為與 A13b 固定候選完整逐檔清單的對照，並在公開說明聲明安裝程式容器與審閱時不同；若逐檔清單過期來不及，接受改用 repo 內較弱依據並在說明寫清楚 |
| 2026-11-19 | 使用者決定 | 公開上傳限定只從 main 觸發；B1b 公開完成後把 `PUBLIC_UPLOAD_ENABLED` 關回，之後需要重新公開時另開 PR 打開 |
| 2026-11-19 | 使用者決定 | 大階段 C 乾淨機驗收使用 B3 CPU 重新定版後的新版本，不使用 B1b 的公開包 |
| 2026-11-19 | 使用者決定 | B1b 交給 Codex（GPT），B2 同時進行 |

接手先列 PR，再讀最新分支的 AGENTS.md 與 STATUS.md。大階段 A 已收尾；下一步 Codex 做 B1b（2026-11-25 前完成逐檔對照）與 B2，各一個 PR。既有 OCR 輸入 artifact 只有一天期限，失效先重跑一般驗證。不建 Release／tag。

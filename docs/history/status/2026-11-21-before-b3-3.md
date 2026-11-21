# 現況

更新：2026-11-21（台北）｜程式 0.19.1／架構 0.4

開工只需要讀 [AGENTS.md](AGENTS.md) 和這份檔案。測試數、里程碑等數字只記在 [docs/progress.json](docs/progress.json)（[進度頁](docs/progress.html)），這裡不重抄。要追溯過去的做法或失敗，查 [歷史索引](docs/history-index.md)。

專案目標：把 Microsoft MarkItDown 做成一般人可安裝使用的 Windows 桌面應用程式，採「基本安裝包＋選配元件管理」。背景與模組責任見 [PROJECT_HANDOFF.md](PROJECT_HANDOFF.md)（背景資料，非必讀）。

## A. 分支與 PR

| 項目 | 狀態 |
| --- | --- |
| `main` | PR 1–52 已合併（B3d，PR 52，`b3a0e9c`）。B1b 公開開關已關。目前沒有開啟中的 PR。 |
| 本輪分支 | `claude/b3-0-decisions`：記錄 B3 計畫與使用者決定（B3-0），只改文件 |
| 下一棒 | B3-1、B3-4 與真實掃描用的列印測試包（B3b6）由 Claude coder 做；B3-2、B3-3 待使用者指派 GPT；真實掃描由使用者列印並掃描。詳見 C 節 B3 計畫 |
| 固定來源 | A13b `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`（base run 44295039865、cpu run 44295044417、Microsoft 探測 run 44300296037） |

## B. 這個階段完成了什麼

- **B3d**：查證固定 CPU worker 的建置工具檔案、Python 封存與實際啟動。setuptools、pip 和 hook 套件保留授權／套件資料，未見其可匯入封裝；PyInstaller 啟動器負責啟動凍結程式。資產調整留到 B3 確認。[逐檔證據](docs/development-records/runs/b3d-cpu-build-tools-2026-11-21/README.md)

- **B3b4／B3b5**（PR 48、50）：使用者決定識別模型候選改以 PP-OCRv6 small 為主並開放 Hugging Face 主機。官方 v6 small、v5 mobile 的 ONNX 已取得並核對雜湊，模型卡宣告 Apache-2.0（LICENSE 連結失效，屬模型卡宣告、非獨立授權文件）。官方檔與先前評估的 RapidOCR 轉檔版辨識逐字相同（135／135），所以 B3b3 的評估數字同樣適用。官方檔**沒有內嵌字表**，採用時要附外部字表。v6 簡中整體不輸 v4，但三個條件多 6 個編輯（多為全形半形標點）；v5 簡中在雜訊與 JPEG 條件明顯較差，排除。[B3b4](docs/development-records/runs/b3b4-v6-official-provenance-2026-11-20/README.md)、[B3b5](docs/development-records/runs/b3b5-official-onnx-rerun-2026-11-20/README.md)
- **B3c 已合併**（PR 47）：[查驗證據](docs/development-records/runs/b3c-cpu-native-review-2026-11-20/README.md)。LibYAML 0.2.5 原文及其餘待補原文列入 B3；使用者決定 GEOS 設計受支援替換路徑、CPU Microsoft 維持現狀並另存再散布依據。

- **B3c 查證內容**：逐一核對固定 CPU 候選的原生 wheels、GEOS 原文與外部載入、Microsoft DLL 來源及簽章。LibYAML 0.2.5 原文及其餘待補原文列入 B3；LGPL 與 CPU Microsoft 做法待使用者決定。[查驗證據](docs/development-records/runs/b3c-cpu-native-review-2026-11-20/README.md)

- **B3b2**：以固定的繁中、簡中及英文合成圖，對照 PP-OCRv4、v5 mobile、v6 small 及繁中 v3 封存版。涵蓋內文、表格、標題與小字，逐份保留字數、編輯距離和 OCR 原始輸出。使用者選定 v5 mobile 方向，正式採用前先完成 B3b3。[B3b2 評估](docs/development-records/runs/b3b2-expanded-ocr-evaluation-2026-11-20/README.md)
- **B3b3 證據**：PR 46 已合併來源分級與模擬掃描。真實公開掃描與官方權重／字表授權仍待查，現有證據尚不足支持直接換成 v5。[B3b3 證據](docs/development-records/runs/b3b3-v5-provenance-scan-2026-11-20/README.md)

- **B3b**：核對固定 CPU 候選的三個 ONNX 與 `config.yaml`，保存 PaddleOCR 授權原文、Paddle 與 ONNX 來源及尚缺的轉檔與授權適用證據。Linux CPU 對照 v5 mobile、v6 small、繁中 v3 與現有模型。兩 profile 的 gates 皆通過、旗標與阻擋清單維持原值。[B3b 證據](docs/development-records/runs/b3b-ppocr-model-review-2026-11-20/README.md)

- **B3a**：用鎖定 wheel 的版本與 METADATA，將已在固定 CPU 候選裡的兩份原文綁回各自的套件，包內 provenance 也會重驗。比對資產目錄後，只有既有 `installed-manifest.json` 改變。兩 profile 的 gates 通過，`cpu-flatbuffers` 已完成，`cpu-rapidocr-models` 保持 open，CPU 四旗標仍為 false。[證據](docs/development-records/runs/b3a-cpu-original-notices-2026-11-20/README.md)

- **B1b 完成完整逐檔對照試跑**（PR 38，run 44613509068）：已核原始 provenance SHA-256、完整路徑集合及純 Python 模組清單雜湊，逐項列生成檔差異與原因。產品與報告帶對照摘要並由 BUILD-INFO 綁定；實際報告 artifact 已回讀核對。[本輪證據](docs/development-records/runs/b1b-content-equivalence-2026-11-20/README.md)
- **B1b 已從 main 公開一次**（run 44659294752）：完整逐檔對照、安裝生命週期 SHA 與上傳條件通過。API 確認只有測試包及報告，資訊已寫進[證據 README](docs/development-records/runs/b1b-content-equivalence-2026-11-20/README.md)與 manifest。PR 41 已合併，`PUBLIC_UPLOAD_ENABLED` 已關閉。

- **大階段 A 收尾**：Claude planner 2026-11-19 整體複查 A1–A13c 全部通過、無必須修正。gates 以 A13b 審閱實跑：base `runtime_sbom_disclosed`、`redistribution_approved` true，`runtime_sbom_complete`（10 條已接受缺口）與 `release_ready`（只差大階段 C 的 `base-clean-machine-manual`）false；cpu 四旗標 false。基本包每個檔案以「已知或經使用者接受並隨包揭露」說得出來源、版本與授權義務。
- 相關 10 個測試模組 176 項在 planner 環境通過（`test_qt_notice` 1 項因無 PySide6 未執行）；完整 941 項回歸本輪未重跑，沿用 progress.json 來源提交。
- run 44307725980（PR 31 合併後的 main push）Windows 失敗位於升級測試重建前一版 990e600 的驗收；同一棵樹在 PR head 與後續兩次 main push 都通過，判定為間歇性問題，不影響 B1b。2026-11-20 查明：前一版建置成功，只有前一版自己固定的 GUI 視窗開啟檢查在 25 秒內未等到視窗。PR 40 只加診斷：保存前一版 gui.log，目前版本自身的等待放寬為 60 秒；前一版驗收仍為 25 秒，見 C 節（[證據](docs/development-records/runs/run-44307725980-gui-timeout-2026-11-20/README.md)）。
- 順帶修正過時敘述：progress.json m5、`docs/redistribution-gates.md` 的旗標現況、accepted_gaps 與 A16 編號。

- **B2 已補修**：加入受管 CPU OCR 安裝、辨識、移除與使用者資料保留，並補上乾淨機、離線、已知限制、測試樣本與修復／移除雜湊證據。[驗收表](docs/stage-c-acceptance.md)

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
| | **B1b 測試版公開產出**（交 Codex）：以 B1a 流程從 main 產出並公開上傳安裝包 artifact（保留 30 天）。驗收（planner 建議、使用者 2026-11-19 同意做法）：(1) **逐檔對照**：下載 run 44295039865 `windows-base-validation-reports` 的 `bundle-provenance.json`（sha256 `b7fa49e6df55…`，即 base-source-review.json 的 `provenance_report_sha256`；**2026-11-25T11:45Z 到期**），先核 sha，再與重建 bundle 的 inventory 比對：路徑集合相等、明列且附理由的生成檔例外外 bytes 全同、`pure_modules_sha256` 相同；多檔、少檔、改檔、清單外生成檔、provenance sha 不符皆拒絕並有反例測試。結果寫 `CONTENT-EQUIVALENCE.json` 放進產品與報告，BUILD-INFO 引用其 sha。來不及在到期前完成時，改用 repo 內較弱依據（264 列分類、153 原生檔、原文、模組雜湊、檔案數），並在公開說明寫明（使用者已接受此退路）。(2) 公開上傳只在 `github.ref == refs/heads/main`、`PUBLIC_UPLOAD_ENABLED=True`、gates 四旗標等於預期、逐檔對照通過、lifecycle 安裝包 sha 等於上傳安裝包時執行；腳本同步檢查 `GITHUB_REF`；非 main 要求公開被拒並有反例。(3) 產品含 Setup、BUILD-INFO（含 `byte_identical_installer_to_original` 與對照摘要 sha）、CONTENT-EQUIVALENCE.json、LICENSE-FILES.json、known-gaps.json／.md、test-build-limitations.md、SHA256SUMS.txt 與中文 README（測試版非正式版、需登入 GitHub 下載且 30 天到期、`certutil -hashfile … SHA256` 核對、未簽章與 SmartScreen、安裝與移除、授權與已知缺口位置、Issues 連結、安裝程式由同一固定來源重建且容器與審閱時不同）。(4) 報告 artifact 寫明 SHA256SUMS 對應產品目錄。(5) 合併後從 main dispatch 一次：記錄 artifact 名稱、digest、大小、到期日；API 核對只有預期兩份 artifact。dispatch 前先跑一般驗證取得當天有效的 OCR 輸入（只保留 1 天）。(6) **公開後立即另開小 PR 把 `PUBLIC_UPLOAD_ENABLED` 改回 False**，並更新 STATUS。(7) 完整回歸、EXPECTED_TESTS 與 progress.json 同步；PR CI 全過、reviewer 無必須修正。不動 spec、鎖檔、登記表狀態、gates 規則與固定候選，不碰 `windows-build.yml`，不建 Release 或 tag | PR 38 已合併，run 44659294752 已公開。PR 41 已合併，公開開關已關 |
| | **B2 驗收表**（交 Codex，與 B1b 平行，獨立 PR）：依 C1–C3 逐項列乾淨 Windows 10／11 安裝、離線首次啟動、四語 OCR、中文路徑、修復、移除與人工操作的勾選表；每項有預期結果與證據格式，填寫結果放 `docs/development-records/runs/stage-c-…/`（符合 `base-clean-machine-manual` 前綴）。依使用者決定，大階段 C 用 **B3 後的新版本**，表格以「待填安裝包 SHA」欄位綁定，不寫死 B1b 的 SHA。只改文件，不改程式 | [補修驗收表](docs/stage-c-acceptance.md)已完成，PR 37 經 Claude reviewer 複查，無必須修正項目；B3 後再實際驗收 |
| | B3a CPU：flatbuffers、rapidocr 原文綁定（接線 `prepare_worker_assets.py`；錯綁、缺檔及改檔反例）（原 A14） | 完成並合併（PR 42） |
| | B3b CPU：PP-OCR 模型來源、版本、雜湊與授權原文（不以套件的 Apache 宣告代替）；授權範圍需使用者確認（原 A15）。**另評估改用繁體中文識別模型以解決 ONNX 繁中已知缺口**（`tests/test_onnx_ocr.py` 的 `test_traditional_chinese_quality_known_gap` 預期失敗）：候選為 PP-OCRv5、PP-OCRv6 的繁中能力與專用 chinese_cht_PP-OCRv3_rec（需查證授權、ONNX 可用性與大小），以該固定繁中測試圖比較準確度；台灣聯發科 Breeze2 屬 3B／8B 多模態大型語言模型（Llama 社群授權），不適合 CPU 選配元件，若要採用改列大階段 E 或另立 GPU 選配元件。換模型屬更換模型與打包內容，需使用者同意；評估結果列表交使用者選擇。**驗收須含簡體中文準確度不退步**（目前 PP-OCRv4 中文模型以簡中為主；可選同時涵蓋簡繁的單一模型，或保留現模型另加繁中模型供選擇） | 來源與評估完成；授權範圍使用者選 A（2026-11-20），選定 v5 mobile 方向，須經 B3b3 查證 |
| | B3b2 CPU：擴大繁中、簡中與英文識別評估。各語言使用自製的內文、表格及含小字標題樣本，依 B3b 方法逐份列字數及字元正確率。對照現行 v4、v5 mobile、v6 small 與專用繁中 v3 封存版。評估腳本僅離線使用 | 評估完成並合併（PR 45），v5 mobile 方向確定，須經 B3b3 複驗 |
| | B3b3 CPU：逐檔查證 PP-OCRv5 mobile ONNX 的轉檔來源與授權。用公開文件印出後掃描，或直接取公開掃描樣本，複驗 v4 與 v5 的繁中、簡中及英文。樣本須來自公開來源，排除使用者文件。通過後於 B3 確認打包變更，再換模型 | 完成（PR 46）：v5 授權只到第三方宣告，簡中在雜訊與 JPEG 條件較 v4 差；真實公開掃描樣本未取得 |
| | B3b4 CPU：查證 PP-OCRv6 small 官方 ONNX、授權與字表（使用者 2026-11-20 決定候選改以 v6 small 為主，開放 `huggingface.co`、`paddle-model-ecology.bj.bcebos.com`、`us.aws.cdn.hf.co` 等主機） | 完成（PR 48）：官方模型卡宣告 Apache-2.0；官方 ONNX 與 RapidOCR 轉檔版不同檔 |
| | B3b5 CPU：以官方 ONNX 重跑評估（含不裁切畫布的旋轉條件） | 完成（PR 50）：官方與轉檔版逐字相同；v6 簡中整體不輸 v4、三條件多 6 個編輯；v5 排除；官方檔無內嵌字表，打包需外部字表 |
| | B3c CPU：Shapely／GEOS（LGPL）與 CPU wheel 內含元件（沿用 A9 格式），CPU Microsoft 6 檔（沿用 A10）；LGPL 做法需使用者確認（原 A16） | 完成並合併（PR 47）。使用者決定：GEOS 設計受支援替換路徑（受管雜湊目前阻擋直接替換）；CPU Microsoft 維持現狀並另存 CPython 與 wheel 各自的再散布依據 |
| | B3d CPU：查明 setuptools、pip、pyinstaller 等建置工具是否真的進了 worker；若要排除屬打包變更，需使用者同意（原 A17） | 完成並合併（PR 52）：只有授權與 metadata，沒有可匯入的建置工具模組；PyInstaller 啟動器必需；不排除（約 0.2%），B3-D5 決定不處理 |
| | **B3b6 真實掃描複驗**（使用者 2026-11-21 決定換 v6 前先做）：Claude coder 產生可列印測試 PDF（沿用 B3b2 的 9 段虛構文字，繁中、簡中、英文各內文、表格、含小字標題），使用者列印並以掃描機或手機掃描後交回；以現行 v4 與官方 v6 各辨識一次比較，結論如實寫（真實掃描、小樣本）。通過並確認簡中差異後才做 B3-6 | 下一步（coder 產生 PDF，使用者列印掃描） |
| | **B3 CPU 元件重新定版**（planner 2026-11-21 計畫，詳細驗收條件見該次回報；順序：決定 → 內容變更 → 一次重定 X → 逐列來源對照 → CPU 門檻確認 → 接線 → 產出 → 公開並關回）。**內容變更 PR 全部合併後才做 B3-9 重定，重定後不再改授權樹。** | 進行中 |
| | B3-0 決定收集與存檔：D 節新增 2026-11-21 決定並存固定檔 [`2026-11-21-b3-decisions.md`](docs/history/status/2026-11-21-b3-decisions.md)；修正 A 節 | 本 PR |
| | B3-1 原文補件 I：LibYAML 0.2.5 與 PaddleOCR 授權原文（比照 A9b：supplemental 原文、`sources.json` 固定上游來源、綁定 PyYAML；PaddleOCR 綁定方式由 coder 先提方案）；base 也會改到，使用者已同意（B3-D3）| 待開始（Claude coder） |
| | B3-2 原文補件 II：Pillow（libaom、dav1d；libyuv、Raqm、FriBidi 先查是否編入）、OpenCV（zlib、libpng）、pyclipper（Clipper 與 BSL-1.0）；onnxruntime、NumPy 只查證。依 B3c `notice-audit.json` 優先順序；可拆 B3-2a（Pillow，影響 base）、B3-2b（OpenCV、pyclipper、查證）；排在 B3-1 之後避免 `sources.json` 衝突 | 待開始（建議 GPT，待使用者指派） |
| | B3-3 GEOS 受支援替換路徑（B3-D4 選 (a)）：受管目錄之外放使用者替換目錄，worker 在匯入 shapely 前以完整路徑預先載入；不放寬受管完整性檢查；標示「使用者替換、未驗證」；hosted Windows 驗收（可辨識、覆蓋受管 DLL 被拒、放入不同 bytes 但相容的 GEOS 能運作、損壞時清楚失敗），標明非實體機；先做可行性實驗，失敗回報使用者 | 待開始（建議 GPT，待使用者指派） |
| | B3-4 CPU Microsoft 再散布依據（只做證據）：CPython 14.42 vcruntime 對 python.org 官方安裝檔、delvewheel 改名 msvcp140 的依據與 RECORD、兩份 MSVCP 與官方一致沿用；不換 DLL | 待開始（Claude coder） |
| | B3-5 CPU 揭露檔與揭露規則補強：`known_gaps.py` 支援 cpu、`known-gaps.md` 加 CPU 一節；補一道檢查讓模型授權揭露（決定 A）被 gates 或測試核對（目前 gates 對 `cpu-rapidocr-models` 推導缺口為空，不強制）。排在 B3-1、B3-2 之後 | 待開始（Claude coder） |
| | B3-6 識別模型更換為官方 PP-OCRv6 small ONNX＋外部字表（`rec_model_path`、`rec_keys_path`）；移除 ONNX 繁中預期失敗並改寫已知缺口與限制文字；Windows 驗收。**須 B3b6 通過並再確認簡中差異、模型卡授權（LICENSE 連結失效）、字表附檔方式、是否排除 v4 rec 後才開工** | 待 B3b6 結果與使用者確認 |
| | B3-7 CPU 交付通道（B3-D2 方案 1）：程式內固定「測試通道」Ed25519 公鑰與離線匯入信任政策，私鑰由使用者建立並存為 GitHub Actions secret，CI 簽署 CPU 元件目錄；不內建私鑰、不讓使用者輸入金鑰；錯簽、過期、版次倒退、他鑰簽名皆拒絕；hosted Windows 安裝、辨識、移除；改寫 `docs/component-management.md`「未發布正式目錄」敘述。**使用者需依逐步教學建立金鑰與 secret（教學隨 B3-7 設計提供）** | 待開始（建議 GPT，待使用者指派） |
| | B3-9 以內容變更合併後的提交 X 重新固定候選（base 與 cpu 一起）：重綁目錄與登記表 `source_commit`、重新審閱；**必須附 evidence 逐條綁定稽核表**，核對每個非 open 條目與每份目錄引用的證據屬於 X（A13c 陷阱，gates 偵測不到）；揭露檔 hash 與 `known_gaps.py --check` 用 X 的審閱重驗；base 四旗標須維持 | 待開始 |
| | B3-9b CPU 逐列來源對照（28 個 origin-known 列，比照 A12b／A13c）與 `cpu-archives` 改 evidence_complete | 待開始 |
| | B3-10 CPU 門檻確認（比照 A13，不寫程式）：cpu-microsoft、cpu-geos、cpu-cpython（libffi）、cpu-wheels（unknown 清單）、cpu-rapidocr-models（含 v6 模型卡授權）、cpu-redistribution-decision 逐條請使用者決定，寫入 D 節並存固定檔；B3-11 依此接線 `decision_source`、`accepted_gaps`、`requires_user_decision` 與狀態（只改登記表與證據，加反例） | 待開始（B3-9 之後） |
| | B3-12 測試版產出流程更新：來源改為 X，對照基準換成 X 的 provenance；新增 CPU 產品（zip、簽章目錄、BUILD-INFO、SHA256SUMS、中文 README，含離線匯入步驟與已知限制）與 `CPU_PUBLIC_UPLOAD_ENABLED=False`；只從 main、四旗標等於預期、逐檔對照通過才可公開；分支 dispatch 只產出報告；B3-13 才公開一次並關回開關 | 待開始 |
| | B3-13 從 main 公開一次（base 與 CPU 測試包）並另開 PR 關回開關；B3-D6 的公開意向與 A13 決定沿用在此前再問使用者 | 待開始 |
| | B4 使用者確認測試版結果（綁定所測安裝包的 SHA，並在其 artifact 30 天期限內完成，否則重新產出） | 需使用者實機測試 |
| C 乾淨機與人工驗收 | C1 乾淨 Windows 10／11 安裝與離線首次啟動；C2 四語、中文路徑、修復移除；C3 人工操作 | 需使用者或實體 Windows |
| D 功能擴充 | D1 圖片檔走本機 OCR；D2 影音獨立選配元件 | 等使用者決定 |
| | **D3 Tesseract 官方語言包（選配下載）**：簡體中文 chi_sim、法 fra、俄 rus、西 spa、德 deu，取自與四語相同的 tessdata_fast 固定提交（Apache-2.0），固定來源與雜湊、可個別下載與移除；不放進基本包（避免改打包內容與重新審閱）。需調整：`languages.py`／`bundled_ocr.py` 的四語寫死與最多 4 種的限制改為「內建、官方語言包、使用者加裝」三層；Tesseract 單一 tessdata 目錄的組合方式；各語合成測試圖與反例。CPU（PP-OCR）多語模型暫不擴充 | 已排入（使用者 2026-11-20 同意）；開工前交 planner 寫計畫 |
| | **D4 使用者自行加裝模型**：第一版只接受 Tesseract `.traineddata`（ONNX 需字典與架構相容、風險較高，暫不開放）；放在獨立的使用者目錄、不覆蓋內建或受管模型、標示「未經驗證、授權由使用者負責」、格式檢查與載入失敗提示、只移除使用者加入的檔案 | 已排入（使用者 2026-11-20 同意）；開工前交 planner 寫計畫 |
| E GPU | 實卡驗收 | 延後 |

**執行順序**：大階段 A 已收尾 → **B1b 已公開且開關已關，B2 已複查** → B3a–B3d（CPU，原 A14–A17，含 B3b3 的來源授權及掃描樣本複驗；B3 確認換模時同步更新 ONNX 繁中缺口揭露）→ B3 → B4 → 大階段 C。各編號一個 PR。

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

**升級測試的前一版 GUI 檢查**：升級測試以前一版 990e600 自己固定的 `check_windows_base.py` 驗收，GUI 開啟等待仍為 25 秒，hosted runner 冷啟動慢時可能再次間歇失敗（run 44307725980）。再發生時先看報告內 `previous-build/acceptance/gui.log` 判斷是逾時還是程序結束；previous-source 固定點往後移後才會改用 60 秒。不改前一版程式。

**既有限制**：ONNX 繁中缺口、RAM 軟性預算、Windows 實機／GPU 未驗收。B1b 只交付 GitHub Actions 測試版 artifact。

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
| 2026-11-20 | 使用者決定 | 簡體中文也常用，B3b 改模型時不可移除或降低簡中能力 |
| 2026-11-20 | 使用者決定 | 大階段 D 新增 D3（Tesseract 官方語言包選配下載：簡中、法、俄、西、德）與 D4（使用者自行下載模型加裝）；同意協調者的評估與架構調整方向 |
| 2026-11-20 | 使用者決定 | B1b（PR 38）合併，合併後的公開觸發與關回上傳開關交給 Codex（GPT）；B2（PR 37）的三項建議修正在合併前由 Codex 補上 |
| 2026-11-20 | 使用者決定 | B3a 交給 Codex（GPT） |
| 2026-11-20 | 使用者決定 | B3a 不走補原文同意流程：flatbuffers 與 rapidocr-onnxruntime 的原文已在 repo 與固定 CPU 候選 worker 內，B3a 沿用既有原文與路徑（不重抓、不改寫）、只接套件對應並加反例；`cpu-flatbuffers` 可關，`cpu-rapidocr-models` 只補 RapidOCR 套件原文部分、維持 open，PP-OCR 模型與 config.yaml 留給 B3b；若必須在 worker 內新增檔案路徑須先停下回報 |
| 2026-11-20 | 使用者決定 | B3b 交給 Codex（GPT） |
| 2026-11-20 | 使用者決定 | B3b 現有三個 PP-OCR 模型授權範圍選 A：接受 PaddleOCR 與 RapidOCR 的 Apache-2.0 涵蓋，隨 CPU 元件附兩份授權原文，並在揭露檔註明兩個 v4 權重與三個 ONNX 轉檔的授權未逐檔確認 |
| 2026-11-20 | 使用者決定 | 識別模型暫不更換；先以較大的繁中、簡中、英文樣本再評估 v4、v5 mobile、v6 small（必要時含繁中 v3），結果交使用者決定 |
| 2026-11-20 | 使用者決定 | 識別模型方向定為 PP-OCRv5 mobile（單一簡繁模型）；正式更換前先查明 v5 ONNX 轉檔來源與授權、以掃描類公開樣本複驗，通過後在 B3 更換；更換屬打包內容變更，B3 時再確認 |
| 2026-11-20 | 使用者決定 | B3c、B3d 交給 Codex（GPT） |
| 2026-11-20 | 使用者決定 | LibYAML 原文隨包列入 B3 重新定版；B3c 繼續完成查證，並系統性列出 CPU wheel 的待補原文清單 |
| 2026-11-20 | 使用者決定 | 協調者（主對話）預設模型改為 `claude-sonnet-5-5`，取代 2026-11-16 與 2026-11-17 決定中的 `claude-opus-5-5`；規劃者 `planner` 用 `claude-opus-5-5`、編程者 `coder` 用 `claude-haiku-5-5`、查驗者 `reviewer` 用 `claude-sonnet-5-5` 維持不變；推理強度維持中 |
| 2026-11-20 | 使用者決定 | 識別模型候選改以 PP-OCRv6 small 為主（v5 保留比較）；開放 `huggingface.co`、`paddle-model-ecology.bj.bcebos.com` 及 Hugging Face 下載主機（含 `us.aws.cdn.hf.co`）；後續查證交給 Claude coder |
| 2026-11-20 | 使用者決定 | B3c 的 GEOS（LGPL）選 A：設計受支援的替換路徑（例如放自備 DLL 的目錄並加驗收）；CPU Microsoft 六檔選 B：維持現狀，另外保存 CPython 與 wheel 各自的再散布依據；B3 待補原文照 reviewer 優先順序（LibYAML、Pillow、OpenCV、pyclipper，再查 onnxruntime、NumPy）。上述工作列入 B3 |
| 2026-11-20 | 使用者決定 | B3d 交給 Codex（GPT） |
| 2026-11-21 | 使用者決定 | B3-D2：CPU 交付通道選方案 1：程式內固定「測試通道」公鑰，私鑰由使用者建立並存為 GitHub Actions secret，CI 簽署 CPU 元件目錄；要求 Claude 提供逐步教學 |
| 2026-11-21 | 使用者決定 | B3-D1：識別模型換用 PP-OCRv6 small；換模型之前先做真實掃描複驗（由使用者列印並掃描 Claude 提供的測試 PDF）；簡中差異是否接受、模型卡授權、字表附檔方式、是否排除 v4 rec 於複驗後再確認 |
| 2026-11-21 | 使用者決定 | B3-D3：同意補原文（LibYAML、PaddleOCR、Pillow libaom／dav1d、OpenCV、pyclipper 等）改變安裝包內容；base 也一併補 |
| 2026-11-21 | 使用者決定 | B3-D4：GEOS 替換路徑採 (a)：受管目錄之外放使用者替換目錄並預先載入，不放寬完整性檢查 |
| 2026-11-21 | 使用者決定 | B3-D5：B3d 發現的重複授權檔與兩個 vendored `.py` 不處理；B3-D6（新 base 測試版是否重新公開、A13 決定是否沿用）等 B3 後半再問 |

接手先列 PR，再讀最新分支的 AGENTS.md 與 STATUS.md。B3 計畫與使用者決定已記錄（C 節 B3-0～B3-13、D 節 B3-D1～D6）；先做 B3-1、B3-4、B3b6（Claude coder），B3-2、B3-3、B3-7 待使用者指派。不建 Release／tag，不觸發 windows-build.yml。

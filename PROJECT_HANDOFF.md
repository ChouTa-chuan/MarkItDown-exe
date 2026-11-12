# MarkItDown-exe：專案說明與接手指南

更新日期：**2026-11-12（台北）**。這份文件寫給第一次接觸本專案的同事或新 AI session，不需要讀取過去聊天紀錄即可開始工作。先讀第 1–4 節了解產品，再讀第 5–8 節了解實作與證據；要開始開發，從第 9–12 節操作。

本次整理前的專案基準為 `da961af7ed2aea25be79a976f0d85479f009ae96`。最後完整功能／Windows 候選驗證來源為 `cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1`；之後另有網站與文件更新。**目前分支的 HEAD、程式版號與真正執行過測試的 source commit 必須分開記錄。**

**2026-11-12 接手後更新（工作分支 `claude/confident-ride-o38ls7`，尚未合併 main）：** 已保存 Windows CI 完整報告原檔並核對雜湊、完成 154／303 個未對照來源的證據分類、在新環境重跑 Linux 完整回歸、新增 Linux 回歸 CI 與 PR／手動驗證入口、修正自有 `THIRD_PARTY_NOTICES`，並提出授權提案待確認。Linux 最新回歸來源為 `582458e`；Windows 候選來源仍是 `cb8f24d`，沒有新的 Windows 執行。分支規則改為「工作分支＋PR，不直接推 main」，見第 11 節。

## 1. 接手摘要

我們正在把 **Microsoft MarkItDown 包裝、擴充成 Windows 文件轉 Markdown 桌面應用程式**。使用者安裝後以圖形介面操作，執行環境、基本 OCR 與四語模型由基本包提供；額外引擎與模型透過元件管理安裝。產品一般轉換在本機完成。

目前已有可運作的轉換核心、桌面介面、PDF 自動分析、四語 Tesseract、受管 CPU OCR 元件，以及真正 Windows hosted runner 上的建置與安裝驗證。**目前沒有提供使用者下載的測試 Setup，也沒有 Windows 正式版 Release。** 下一步主要是處理候選來源／授權缺口、準備可交付測試產物，再補乾淨 Windows 與人工驗收。

| 項目 | 截至本文件的狀態 |
| --- | --- |
| 專案 | [ChouTa-chuan/MarkItDown-exe](https://github.com/ChouTa-chuan/MarkItDown-exe)，預設分支 `main`；開發在工作分支進行，經 PR 由使用者指示後合併 |
| 自有程式 | `markitdown-desktop` **0.19.1**，權威版號在 [pyproject.toml](pyproject.toml) |
| 架構規劃 | **0.4**，「基本安裝包＋選配元件管理」 |
| 上游 | Microsoft MarkItDown **0.1.9**，固定提交，MIT；vendor 保持原樣 |
| 平台目標 | 第一目標 Windows 11 x64；Windows 10 相容性需另外驗收 |
| 開發／建置基線 | CPython **3.12 x64**；套件宣告最低 Python 3.11 不代表完整 profile 在其他版本已驗 |
| 新架構驗收 | **7/12**；C03 3/4、C04 2/4、C09 3/4、C11 2/5，GPU C12 未驗 |
| 早期基線 | **19/25**，與新架構 C01–C12 分開計算 |
| Linux 完整回歸 | **698 項：697 通過、1 既有 ONNX 繁中品質預期失敗、0 跳過**；混合程序與 45 獨立模組皆 exit 0（來源 `582458e`，Tesseract 5.3.4）。`cb8f24d` 當時為 684／683／43 模組，接手環境已獨立重跑出相同計數 |
| Windows 基本包 | 應用 10 項、安裝／同版修復／移除 6 項、真跨版 11 項、三停點續修接受 |
| Windows CPU 選配 | 功能 11、同版維護 8、跨版 8、程序終止／獨立恢復 6 案接受 |
| 候選檔案清單 | 基本包 **1,655 檔**；CPU bundle **741 檔**、真正 ZIP **742 檔**，含額外 NOTICE |
| 未關閉事項 | 未對照來源中 candidate／gap 基本 49、CPU 47 項、完整 runtime SBOM／再散布、應用公開授權（[提案待確認](docs/license-proposal.md)）、乾淨機／人工、GPU 與品質矩陣 |
| 固定進度網址 | **https://chouta-chuan.github.io/MarkItDown-exe/**，已上線並驗 HTTP 200／內容 hash |

7/12 是已關閉的驗收項目數，並非工期完成百分比。部分完成與一份候選包通過，都不能直接把整個 C03／C04／C11 改為完成。

| 開發用語 | 這個專案中的意思 |
| --- | --- |
| profile | 某個用途的依賴與打包組合，例如基本版、CPU 選配及其建置環境 |
| bundle／Setup | bundle 是打包後的執行檔與資源目錄；Setup 是把它安裝到 Windows 的安裝程式 |
| worker／IPC | worker 是隔離的背景引擎程序；IPC 是主程式與它交換請求／狀態的程序間通訊 |
| catalog | 元件 catalog 是受信任的元件描述目錄；安裝 catalog 則是基本包檔案收據，兩者用途不同 |
| SHA-256／簽章 | hash 核對檔案位元，簽章核對可信簽發者；兩者通過後仍須審核再散布授權 |
| SBOM | 軟體物料清單，說明實際產品包含的元件、版本與來源；外層檔案清單只是其中一部分 |
| hosted runner／乾淨機 | 前者是已備開發工具的 CI 機器；後者是要驗證使用者無 Python 等前置環境仍能操作的獨立環境 |

## 2. 專案為什麼存在，已做了哪些產品決定

上游固定在 `7482c092d9c0074a89803c9fdb63a969e7fe17fc`，來源與逐檔hash見 [vendor/markitdown/UPSTREAM.json](vendor/markitdown/UPSTREAM.json)。自有程式在`src/desktop_app`擴充服務、介面與建置；不要用最新PyPI版本悄悄替換vendor。

使用者最初希望將 Microsoft MarkItDown 改為容易使用的 Windows EXE，避免自行安裝 Python、pip、MCP 掛載與複雜環境設定。後來確認以下方向：

1. **基本安裝包＋選配元件管理。** 首次精靈與元件管理放在應用程式內，基本轉換離線可用；額外 CPU／GPU／模型功能按需要安裝。沒有另做帳號系統或常駐大型下載啟動器的需求。
2. **精準模式自動完成文件分析。** 使用者選精準後，程式逐頁判斷原生文字、掃描、混合、表格等情況，安排需要的解析／OCR；不用使用者逐頁判斷要啟動哪個模型。
3. **基本 OCR 支援繁體中文、英文、日文、韓文。** 基本預設為 Tesseract；保留舊雙語使用者偏好，不能更新後擅改語言組合。混合解碼不等於可靠的自動語言分類。
4. **提供 RAM 規劃。** 自動／手動預算、系統保留量、CPU 執行緒、低優先權、程序隔離與回壓，目標是降低其他工作的負擔。
5. **GPU 是選配與獨立驗收項。** 同一模型改用 GPU 主要影響效能，不保證提高準確率；較高品質模型仍需另外驗證。
6. **維持模組化與歷史可追溯。** 首頁保留中文架構、更新紀錄另存、程式重要契約與複雜流程加中文註解，架構圖要保留舊快照。

Markdown 的產品目標是內容完整、閱讀順序、表格結構及來源可追溯。字型、頁面幾何、任意圖表與複雜公式的完整還原不屬於目前完成承諾。圖片資產、進階版面模型、音訊與外部 AI 服務屬後續擴充。

## 3. 產品怎麼運作

### 一般文件轉換

1. 桌面或 CLI 建立不可變的 `Request`，包含輸入／輸出、品質、語言與資源偏好。
2. `planning.py` 估算任務，`Runner` 先檢查 RAM 准入，再以 `spawn` 啟動隔離程序。
3. 文字、Office、HTML 與原生 PDF 透過 MarkItDown／原生解析器處理；精準 PDF 逐頁分析，必要頁面才 OCR。
4. 使用受管 CPU OCR 時，能力解析核對可用元件，整份文件固定版本與共享租約；完成前再重驗。
5. 品質／表格處理保留來源、差異及不確定內容，最後安全提交輸出。取消、故障及能力不足須明確回報。

主要入口為桌面 `markitdown-gui`／`python -m desktop_app.desktop`，以及 CLI `markitdown-desktop`／`python -m desktop_app.cli`。

### 基本包與選配的界線

| 層級 | 內容 | 目前注意事項 |
| --- | --- | --- |
| 基本包 | Qt 桌面、CPython、MarkItDown、原生格式解析、Tesseract 與四語模型 | 使用 `packaging/base.spec`；已有 Windows hosted 實測，尚未完成使用者交付／乾淨機驗收 |
| CPU 選配 | RapidOCR／ONNX Runtime／模型及獨立 frozen worker | 使用 `packaging/ocr-worker.spec`；屬實驗性 OCR，繁中品質有固定已知缺口 |
| GPU 選配 | 目標為獨立 GPU worker、相容 runtime、模型與資源政策 | 裝置診斷／策略已有部分程式，完整 GPU bundle、實卡推論與品質矩陣未完成 |
| 進階模型 | 版面、表格等較高成本能力 | 尚未完成選型、來源／品質／負載驗收 |

**Magika 格式辨識本身仍依賴 CPU ONNX Runtime。** 基本包含此 runtime 是必要閉包的一部分；不能據此宣稱 RapidOCR 選配已安裝，也不能為縮小基本包而刪掉上游必要依賴。

### 資源與品質政策

- RAM 是**軟性預算**，會量測程序樹、准入、暫停與遲滯恢復。原生單頁／Office／OCR 呼叫不能任意中途釋放已配置記憶體，不能保證瞬時硬上限或其他程式完全不卡頓。
- 自動裝置模式的 GPU→CPU 回退需先通過 RAM 准入；明確指定 GPU 的失敗不能悄悄當作 GPU 成功。實卡驗收尚未完成。
- 缺少受管元件時，不在轉換途中默默下載大型模型或替換版本；使用者可另行選擇安裝，再重新處理。
- ONNX 繁中預期失敗是品質缺口。不能換成較容易的圖片、刪掉斷言或把 expected failure 算成準確率通過。
- 跨頁續表目前有提示與檢查，不代表任意長表已能自動可靠合併；雙引擎差異保留原文，不自動繁簡轉換或修字。

## 4. 程式架構與責任地圖

責任方向為介面、應用服務、核心契約／能力解析、引擎轉接。視窗透過服務操作元件；文件分析決定需要的能力，元件服務判斷可用版本，資源層決定執行時機。

| 位置 | 接手時要知道的責任 |
| --- | --- |
| [src/desktop_app/desktop.py](src/desktop_app/desktop.py)、[cli.py](src/desktop_app/cli.py) | 圖形／命令列入口，共用設定、請求與 Runner |
| [core.py](src/desktop_app/core.py)、[application.py](src/desktop_app/application.py)、[workers.py](src/desktop_app/workers.py) | 任務／狀態／結果契約、批次隔離、spawn、取消、回壓與程序清理 |
| [planning.py](src/desktop_app/planning.py)、[pdf_pipeline.py](src/desktop_app/pdf_pipeline.py)、[conversion.py](src/desktop_app/conversion.py) | 估算、自動逐頁路由、格式轉換與上游轉接 |
| [tables.py](src/desktop_app/tables.py)、[table_continuation.py](src/desktop_app/table_continuation.py)、[borderless.py](src/desktop_app/borderless.py)、[quality.py](src/desktop_app/quality.py) | 表格、合併格、續表候選、品質／來源與輸出處理 |
| [resources.py](src/desktop_app/resources.py) | RAM 預算、系統保留量、程序樹量測與准入 |
| [onboarding/](src/desktop_app/onboarding) | 首次檢查、RAM 建議、明確套用、完成標記與既有偏好保留 |
| [settings.py](src/desktop_app/settings.py) | 設定 schema 7、v1–v6 遷移、原文備份與並行寫入保護 |
| [languages.py](src/desktop_app/languages.py)、[models.py](src/desktop_app/models.py)、[model_dialog.py](src/desktop_app/model_dialog.py) | 四語契約、固定模型、舊模型下載／驗證／受管移除與介面 |
| [bundled_ocr.py](src/desktop_app/bundled_ocr.py)、[native_assets.py](src/desktop_app/native_assets.py)、[build_profile.py](src/desktop_app/build_profile.py) | 基本包內含 OCR、原生來源／PE、平台與資產完整性；損毀時不借用外部工具冒充正常 |
| [onnx_ocr.py](src/desktop_app/onnx_ocr.py)、[devices.py](src/desktop_app/devices.py)、[device_dialog.py](src/desktop_app/device_dialog.py) | 相容 OCR adapter、裝置偵測、候選 provider 與回退政策；程式存在不代表 GPU 已驗 |
| [components/contracts.py](src/desktop_app/components/contracts.py)、[capabilities.py](src/desktop_app/capabilities.py) | 元件描述、版本範圍、需求及真正可用能力解析 |
| [components/registry.py](src/desktop_app/components/registry.py)、[legacy_models.py](src/desktop_app/components/legacy_models.py) | 登錄 schema 2、版本／模型引用、受管與外部只讀資料的界線 |
| [components/catalog.py](src/desktop_app/components/catalog.py)、[downloads.py](src/desktop_app/components/downloads.py)、[cache.py](src/desktop_app/components/cache.py)、[network.py](src/desktop_app/components/network.py) | Ed25519 可信目錄、來源政策、Range／ETag 下載、hash、離線匯入與快取 |
| [components/lifecycle.py](src/desktop_app/components/lifecycle.py)、[lifecycle_store.py](src/desktop_app/components/lifecycle_store.py)、[locks.py](src/desktop_app/components/locks.py)、[archives.py](src/desktop_app/components/archives.py) | 交易安裝、staging、原子啟用、共享／排他鎖、修復、移除、恢復與受限解壓 |
| [components/management.py](src/desktop_app/components/management.py)、[component_dialog.py](src/desktop_app/component_dialog.py) | 桌面背景維護服務、元件版本／健康／授權／容量／使用中狀態 |
| [component_workers/](src/desktop_app/component_workers) | frozen worker server/client、版本化 IPC、binding、guard、整份文件租約及提交前重驗 |
| [diagnostics.py](src/desktop_app/diagnostics.py)、[help_ui.py](src/desktop_app/help_ui.py) | 依實際 profile 做離線自檢、說明與來源查看 |
| [vendor/markitdown/](vendor/markitdown) | 固定上游原始碼，非自有程式的任意改寫區 |
| [packaging/](packaging)、[scripts/](scripts) | profile、PyInstaller、安裝器、候選清單、實際平台驗收與進度產生工具 |
| [tests/](tests)、[docs/development-records/](docs/development-records) | 合成／公開樣本、測試，以及具來源／hash 的歷史證據 |

`updates/` 等名稱在架構指引中代表規劃責任，並非全部已有同名目錄。以實際程式樹及上表判斷，不要為湊齊規劃名稱重建既有框架。完整規劃與原圖見[架構指引第四節](docs/architecture-guide.md)及[架構快照索引](docs/architecture/README.md)，目前保留 28 份圖。

### 元件更新必須遵守的契約

元件描述固定 ID、版本、來源、授權、檔案大小／hash、平台／架構、依賴、app／worker 相容範圍與資源需求。`ready` 需要完整性、相容性及可信健康檢查；目錄存在或下載完成不等於 ready。

worker 使用有界 JSON-lines 控制訊息，文件內容／結果放檔案。**CPU 元件目前為 1.0.1，協定為 1.0.0，明確支援已驗的元件 1.0.0／1.0.1**；hello 與結果都要符合租約固定的精確版本，未知同 major 版本不自動接受。

共享租約保護正在使用的版本；安裝、修復、移除取得排他鎖。提交前失敗恢復舊 active，提交後完成收尾；未知檔案及未接管外部資料保留。Windows CPU 六案是指定停點的真程序終止／另一程序 recover，尚未涵蓋物理斷電或 OS 重啟。

桌面資料根由 Qt `QStandardPaths.AppLocalDataLocation` 決定，組織與應用名稱均為 `MarkItDownDesktop`。設定為該根目錄的 `settings.json`；管理服務使用 `component-catalog.json` 與 `component-state`，registry 再管理 `component-registry.sqlite3`、版本 payload 等。維護這些位置應讀取實際服務，不硬編碼使用者帳號或把 cache／staging 與正式元件混用。

## 5. 已經走過的開發階段

下表概括過程；完整逐次變動在 [CHANGELOG](CHANGELOG.md) 與[開發紀錄](docs/development-records/README.md)。

| 階段 | 已交付的主要變化 |
| --- | --- |
| 早期核心／原型 | 固定上游、格式轉換、精準 PDF／表格、Qt 批次、模型管理、RAM 與獨立程序；保留 19/25 早期基線 |
| 架構改版 0.4 | 使用者確認基本安裝包＋選配元件管理，建立 C01–C12；這是架構版號，與程式版號分開 |
| 程式 0.2–0.8 系列 | 元件契約／登錄、簽章下載、交易與鎖、獨立 worker、管理 UI、首次流程與自動分析接線 |
| 程式 0.9–0.13 | 基本依賴拆分、四語、原生來源檢查、最小 Windows 原生候選、基本包內含 OCR／離線解析 |
| 程式 0.14–0.16 | hosted Windows 四語／中文路徑／CLI／Qt、每位使用者安裝修復移除、真跨版本升級與明確回復 |
| 程式 0.17 系列 | 基本包三停點續修、Qt 正常退出修正、CI 自有中斷暫存產物清理；保留之前退出失敗紀錄 |
| 程式 0.18–0.19.1 | 獨立 Windows CPU profile、同版維護、精確跨版、程序終止與獨立恢復；完整回歸擴充 |
| 0.19.1 的後續建置檢核 | PyInstaller 原文、原生來源指紋、全部普通檔案快照／重驗、真正 CPU ZIP 核對；基本快照移至安裝 catalog 產生後 |
| 2026-11-12 網站 | 使用者啟用 Pages 後，固定視覺進度網址部署成功，HTTP 200／內容 hash 與既有瀏覽器驗證頁相符 |

上述最後兩類主要更動建置／文件，程式仍是 0.19.1；新增提交不代表已產生同版新安裝包或 Release。

## 6. 十二項里程碑的當前狀態

這是[架構指引第十二節](docs/architecture-guide.md)的最新讀法；詳細狀態以 [docs/progress.json](docs/progress.json) 的 `component_rollout` 為準。

| 項目 | 狀態 | 已有成果／未關閉條件 |
| --- | --- | --- |
| C01 元件／能力／版本契約與登錄 | 完成 | 相容範圍、狀態、依賴、能力解析與持久化 |
| C02 舊模型 adapter 與設定遷移 | 完成 | 舊資料辨識、外部只讀、遷移與備份；後續四語擴充 schema 7 |
| C03 Windows Tesseract 與四語 OCR | 3/4 | 固定模型、來源／原文、內含基本包已驗；仍缺乾淨 Windows 四語掃描／中文路徑／安裝的完整驗收 |
| C04 profile 鎖定、打包與自檢 | 2/4 | 基本閉包及 Linux 打包自檢完成；Windows 候選清單已有新證據，但逐項來源／再散布、所有 profile 及乾淨隔離環境尚未關閉 |
| C05 可信目錄與可恢復下載 | 完成 | 簽章、來源政策、hash、取消／重試、Range／ETag、離線及損毀拒絕 |
| C06 交易安裝、鎖、修復與移除 | 完成 | 受管生命週期 API、原子切換／恢復、使用中保護與資料保留 |
| C07 獨立選配 worker 協定 | 完成 | 真 frozen CPU、版本化 IPC、取消／逾時、資源與 guard；GPU 另屬 C12 |
| C08 元件管理介面 | 完成 | 背景維護、版本／容量／授權／健康／使用中狀態；正式目錄來源尚未發布 |
| C09 首次啟動與引擎自動設定 | 3/4 | RAM 建議與偏好保留、完成標記、既有引擎健康已驗；全新基本包離線首次完整流程仍待 C03／C04 門檻 |
| C10 自動分析與能力協作 | 完成 | 按頁需求、固定租約／版本、提交前重驗、原品質與批次隔離 |
| C11 Windows 完整安裝生命週期 | 2/5 | hosted 安裝／同版修復／移除、基本真跨版已完成；各 profile 完整相容／中斷恢復、無 Python 乾淨機、人工 UI 尚待 |
| C12 GPU 實卡與品質矩陣 | 待驗 | GPU 實際 provider／推論、VRAM／OOM／回退、負載與品質／效能對照 |

GPU 加值與 CPU 基本版交付分開排程；C12 未完成不需要阻止已達門檻的 CPU 基本版，但不能把 GPU 功能標為已驗可用。

## 7. 最新驗證證據及其範圍

### 功能與 Windows

| 證據 | 真正驗過的內容 | 來源 |
| --- | --- | --- |
| Linux 全 684／43 模組 | 683 pass、唯一既有繁中 expected failure、0 skip；混合與逐模組程序均正常退出 | [完整記錄](docs/development-records/runs/candidate-inventory-ci-2026-11-11/README.md)、[混合退出](docs/development-records/runs/candidate-inventory-ci-2026-11-11/full-mixed-exit.json)、[隔離摘要](docs/development-records/runs/candidate-inventory-ci-2026-11-11/isolated/summary.json) |
| Windows 基本包 run 42982427175 | app10、安裝6、0.16.0→0.19.1 真跨版11、三停點續修及資料保留 | [CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427175)、[公開摘要](docs/development-records/runs/candidate-inventory-ci-2026-11-11/windows-base-public-summaries.json) |
| Windows CPU run 42982427186 | 功能11、同版8、元件1.0.0↔1.0.1跨版8、真程序終止／獨立恢復6 | [CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42982427186)、[公開摘要](docs/development-records/runs/candidate-inventory-ci-2026-11-11/windows-cpu-public-summary.json) |
| Pages run 43133764140 | 公開固定網址 HTTP 200，回傳 SHA-256 與產生器／已驗瀏覽器 HTML 精確一致 | [CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/43133764140)、[發布證據](docs/development-records/runs/progress-pages-live-2026-11-12/README.md) |
| 接手環境 Linux 684（來源 `2e06631`，程式與 `cb8f24d` 相同） | 新容器、雜湊鎖、固定四語模型：混合與 43 模組皆 684／683／1 預期失敗／0 跳過、exit 0；Tesseract 5.3.4、CPython 3.12.3，與基線版本不同 | [紀錄](docs/development-records/runs/handover-regression-2026-11-12/README.md) |
| 新增測試後 Linux 698／45 模組（來源 `582458e`） | 697 通過、同一項預期失敗、0 跳過；混合與逐模組 exit 0。新增 14 項為來源分類與回歸 driver 的測試 | [紀錄](docs/development-records/runs/handover-ci-and-classification-2026-11-12/README.md) |
| Windows CI 完整報告原檔 | 三份 artifact ZIP 原位元組保存；`bundle-provenance.json` 雜湊與公開摘要 `report_sha256` 相符 | [保存紀錄](docs/development-records/runs/ci-full-reports-2026-11-12/README.md) |

功能／候選來源是 `cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1`，Pages 發布來源是 `bc5d601cbb9480d179edb26372891771b5fa955a`。Linux 完整回歸沿用 CPython 3.12.14、Tesseract 5.5.0、固定四語／三個 ONNX 模型及字型；環境指紋見[先前完整回歸](docs/development-records/runs/full-regression-0.19.1-2026-11-11/preflight.json)，最新測試結果仍以 684 那一輪為準。

Windows hosted runner 預裝開發工具與 Python，不能當作無 Python 乾淨機。自動 Qt 開關不是人工操作驗收；固定樣本通過不是任意四語文件的品質保證。CPU 修復六案初始 payload 有效，損毀修復另有同版八案證據；程序 kill 不等於實體斷電。

### 候選檔案與再散布

| 當次候選 | 基本包 | CPU 選配 |
| --- | ---: | ---: |
| 普通檔案數 | 1,655，含安裝 catalog | bundle 741／ZIP 742，額外 NOTICE |
| 套件來源表 | 40 個 runtime／本地專案 | 26 個 build 環境套件，不是全 runtime SBOM |
| Analysis 原生來源筆數 | 201 | 106 |
| 未對照來源的檔案 | **154** | **303**，以 bundle 計 |
| 需審閱檔案（包含來源缺口） | 191 | 337 |

完整普通檔案快照、hash 與 ZIP 核對已通過。`file_inventory_complete: true` 只代表這個候選目錄的普通檔案列舉完整；`runtime_sbom_complete`、`redistribution_approved`、`release_ready` 仍為 **false**。未展開的 Python archive 成員、未知／生成檔來源、應用公開授權、Qt 對應來源／替換、Microsoft／其他原生 runtime 義務仍待處理。

來源與收集後 binary hash 分列，PyInstaller 轉換差異會保留；不能只依檔名或位於 Python 目錄就套用某個授權。基本快照在安裝／升級／續修完成後才產生，以涵蓋 `base-install-catalog.json`；CPU 在真正 ZIP 產生後驗含 NOTICE 的全部內容／CRC／descriptor。

未對照的 154／303 項已依雜湊證據分類：基本包 confirmed 73、origin-known 32、candidate 48、gap 1；CPU confirmed 227、origin-known 29、candidate 46、gap 1。candidate 主要是自 runner 系統路徑收集、僅檔名像 Microsoft runtime 的 DLL，以及基本包來源不明的 `libcrypto-3-x64`／`libssl-3-x64.dll`；gap 是未展開成員的 `base_library.zip`。分類不改變上述三個 false 旗標，見[來源分類](docs/source-classification.md)。

細節見[候選清單](docs/candidate-inventory.md)、[原文追溯](docs/bundle-provenance.md)。當次 CPU ZIP hash 為 `5dee53420a4b7214fc44dbf132907a6356f63257f19bf858bb73274906083b21`，只識別那次測試候選，不代表有正式下載來源。

**保存限制：** Repo 保存公開原頁、完整有界摘要、報告 hash、Linux 原始回歸及其他工程紀錄。2026-11-12 起，run 42982427175／42982427186 的三份報告 artifact 原檔（含完整逐檔 `bundle-provenance.json`）已保存在 [ci-full-reports-2026-11-12](docs/development-records/runs/ci-full-reports-2026-11-12/README.md)；**更早各次 run 的完整報告沒有保存**，傳遞用 native 輸入（EXE／模型本體）保留一天、未保存。新接手者不能宣稱所有 Windows 詳細報告永久備份；其他 run 的明細過期後應從固定來源重新建置，另存新證據。

## 8. 建置與依賴要分清楚

| 環境 | 第三方鎖定套件數 | 權威位置 |
| --- | ---: | --- |
| 完整 Linux／Windows 開發 | 55／58 | `packaging/requirements-linux.txt`、`requirements-windows.txt` |
| 基本 Linux／Windows runtime | 38／38 | `packaging/profiles/base-*-runtime.txt` |
| 基本 Linux／Windows build | 47／49 | `packaging/profiles/base-*-build.txt` |
| Windows CPU build／精簡 controller | 24／5 | `packaging/profiles/cpu-windows-build.txt`、`cpu-windows-controller.txt` |

以上數字不包含另外安裝的本地專案與 venv 自帶 pip；CPU build 另有自有 app 與 pip，所以實際來源表是 26。基本 build／runtime 另安裝 vendor MarkItDown 及自有 app。九份相關 hash 鎖保持固定；用 `--require-hashes` 安裝第三方依賴，再用 `--no-deps --no-build-isolation` 安裝本地專案。

| 入口 | 用途 |
| --- | --- |
| [packaging/base.spec](packaging/base.spec)、[run_windows_base_ci.py](scripts/run_windows_base_ci.py) | 目前基本包方向：同平台資產、四語 OCR、真 Windows 建置與完整自動驗收 |
| [packaging/ocr-worker.spec](packaging/ocr-worker.spec)、[run_windows_cpu_ci.py](scripts/run_windows_cpu_ci.py) | 獨立 CPU 選配與精簡 controller，控制端不安裝 OCR／Qt 原生套件 |
| [windows-base-validation.yml](.github/workflows/windows-base-validation.yml) | main 特定來源變動時自動跑：Linux 準備固定 Windows 原生輸入，再由 Windows 2022 原生建置與執行 |
| [windows-cpu-validation.yml](.github/workflows/windows-cpu-validation.yml) | main 特定來源變動自動跑：新舊來源分開建置，驗功能／同版／跨版／恢復 |
| [windows-build.yml](.github/workflows/windows-build.yml)、`packaging/desktop.spec`／`build-windows.ps1` | 早期完整開發包的手動工作流程；不能當作新版模組化基本包的正式發行管線 |
| [progress-pages.yml](.github/workflows/progress-pages.yml) | 只發布進度網站；資料／模板／產生器更新後自動部署，與應用程式 Release 分開 |
| [linux-regression.yml](.github/workflows/linux-regression.yml) | PR、main 與手動：Ubuntu 24.04 以雜湊鎖與固定四語模型跑混合＋逐模組完整回歸，測試總數由 `EXPECTED_TESTS` 固定；只上傳日誌與摘要 |

兩條 Windows 驗證流程自 2026-11-12 起另接受 `pull_request`（目標 main）與 `workflow_dispatch`。PR 執行的是 GitHub 產生的暫時 merge commit，報告中的 commit 是該暫時提交；要以分支上的固定提交留存候選證據，使用 `workflow_dispatch` 指定分支，或以合併後 main 的執行為準。這些新入口與 Linux 流程已在 [PR 1 首次執行](docs/development-records/runs/pr1-ci-first-run-2026-11-12/README.md)且皆 Success（Linux 698／697／1 預期失敗／0 跳過）；`workflow_dispatch` 尚未實際使用過。

原生 Windows EXE／Setup 必須在 Windows 實際建置及驗證。Linux 可做可攜核心測試、來源／PE 分析與固定輸入交叉建置；Linux 的 frozen 程式無法充作 Windows 成果。

## 9. 新接手者的第一輪操作

### 9.1 確認專案與既有狀態

```bash
git clone https://github.com/ChouTa-chuan/MarkItDown-exe.git
cd MarkItDown-exe
git status --short
git log -5 --oneline
```

已有工作目錄就先檢查，不重新 clone 覆蓋、不清除未知變更。閱讀 [AGENTS.md](AGENTS.md)、本文件、`docs/progress.json` 與最新開發紀錄，確認本次任務；這份指南之後的提交也可能更新現況。

新 AI session 先確認實際工具與執行環境：Linux 雲端、Windows PowerShell、只讀聊天等能力不同；桌面客戶端本身不代表已取得本機 shell。專案交接以 repo 檔案為基礎，不依賴兩個客戶端同步聊天。

在此雲端曾使用 `/workspace/MarkItDown-exe`。`/workspace/markitdown-full-0191-venv` 與 `/workspace/markitdown-test-models-0191` 只是當時可重用的工作區資源；新 session 應檢查是否存在及是否仍符鎖定，不把這些絕對路徑當成專案必要條件。

### 9.2 建立完整 Linux 開發環境

以下在 repo 根目錄，以 Bash 執行。只改文件時不需要重裝套件或跑全回歸。

```bash
python3.12 -m venv .venv-handoff
.venv-handoff/bin/python -m pip install --require-hashes -r packaging/requirements-linux.txt
.venv-handoff/bin/python -m pip install --no-deps --no-build-isolation ./vendor/markitdown .
.venv-handoff/bin/python -m pip check
.venv-handoff/bin/python scripts/verify_upstream.py
.venv-handoff/bin/python scripts/license_inventory.py --verify
.venv-handoff/bin/python scripts/packaging_profiles.py
.venv-handoff/bin/python scripts/cpu_worker_profiles.py
```

完整 OCR 測試另需可執行的 Tesseract，以及 Latin／CJK 字型。已驗基線使用 Tesseract 5.5.0、DejaVu Sans、NotoSansCJK-Bold；先核對 `tesseract --version` 與字型來源。其他 OS 原生版本須另記錄，不能直接宣稱完全重現同一基線。測試可用 `TEST_LATIN_FONT`／`TEST_CJK_FONT` 指定字型。

四語模型必須使用專案固定清單（commit `87416418657359cb625c412a48b6e1d6d41c29bd`）與 LICENSE：

```bash
export TESSDATA_PREFIX=/tmp/markitdown-handoff-tessdata
.venv-handoff/bin/python - <<'PY'
import os
from pathlib import Path
from desktop_app.languages import model_manifest
from desktop_app.models import install, inspect
directory = Path(os.environ['TESSDATA_PREFIX'])
install(directory, progress=print, spec=model_manifest())
assert set(inspect(directory, spec=model_manifest()).values()) == {'valid'}
PY
```

此下載使用固定來源與 hash，既有錯誤檔不會直接覆寫。`scripts/fetch_ocr_models.py` 是舊雙語入口，不要誤當四語模型準備完成。模型與 venv 留在開發資料位置，不加入 Git。三個 ONNX 模型由固定依賴提供，完整測試會驗對應資產；版本／模型資料見[環境指紋](docs/development-records/runs/full-regression-0.19.1-2026-11-11/preflight.json)。

### 9.3 啟動與最小轉換

```bash
.venv-handoff/bin/python -m desktop_app.cli --help
.venv-handoff/bin/python - <<'PY'
from pathlib import Path
directory = Path('/tmp/markitdown-handoff-demo-1')
directory.mkdir()  # 使用新位置，已存在時改用新的名稱，不清除舊結果。
(directory / 'input.txt').write_text('交接測試：繁體中文、日本語、한국어、English。\n', encoding='utf-8')
PY
.venv-handoff/bin/python -m desktop_app.cli /tmp/markitdown-handoff-demo-1/input.txt /tmp/markitdown-handoff-demo-1/output.md --ram-budget-mib 1024 --reserve-mib 2048
# 以下在有圖形顯示的環境啟動；視窗開啟後可手動關閉。
.venv-handoff/bin/python -m desktop_app.desktop
```

範例 RAM 為 1 GiB 預算、2 GiB 系統保留，需依機器調整。其他輸入請用自己建立的公開／合成檔案，輸出選新的位置。CLI 品質為 `--quality precise`／`fast`；語言例為 `--ocr-languages chi_tra+eng+jpn+kor`，後端可用 `tesseract`、`onnx`、`onnx_verify`、`managed_cpu`。受管後端還需要可信元件與管理 context，不能只改一個參數就視為引擎已安裝。

無圖形桌面的 Linux 使用 `QT_QPA_PLATFORM=offscreen` 跑測試；這不能當成人工 UI 驗收。安全輸出使用同磁碟硬連結等保護，檔案系統不支援時會明確失敗。

### 9.4 完整回歸與真正退出檢查

先準備 native OCR／字型／模型。以下 `-1` 結果目錄必須是新的；已存在就換新名稱，保留舊紀錄。

```bash
set -e
export PYTHONPATH=src:tests
export TESSDATA_PREFIX=/tmp/markitdown-handoff-tessdata
export QT_QPA_PLATFORM=offscreen
export PYTHONFAULTHANDLER=1
export OMP_THREAD_LIMIT=1
export OMP_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export MKL_NUM_THREADS=1
mkdir /tmp/markitdown-handoff-run-1
mkdir /tmp/markitdown-handoff-run-1/qt-runtime
chmod 700 /tmp/markitdown-handoff-run-1/qt-runtime
export XDG_RUNTIME_DIR=/tmp/markitdown-handoff-run-1/qt-runtime
.venv-handoff/bin/python scripts/run_mixed_regression.py --expected-count 698 --output /tmp/markitdown-handoff-run-1/mixed-result.json > /tmp/markitdown-handoff-run-1/mixed.log 2>&1
.venv-handoff/bin/python scripts/check_isolated_tests.py --expected-count 698 --output /tmp/markitdown-handoff-run-1/isolated > /tmp/markitdown-handoff-run-1/isolated.log 2>&1
```

Ubuntu 24.04 缺少的系統前置可用 `apt-get install --no-install-recommends tesseract-ocr libegl1 fonts-noto-cjk fonts-dejavu-core` 補齊；apt 提供的 Tesseract 是 5.3.4，不是歷史基線的 5.5.0，需如實記錄。缺 `libEGL.so.1` 時 Qt 測試類別會在 `setUpClass` 失敗、其下方法不會執行；缺 Tesseract 時相關測試會跳過，兩者都不算完成回歸。

當前接受條件是 698 項、唯一既有 `test_onnx_ocr.OnnxIntegrationTests.test_traditional_chinese_quality_known_gap`、0 skip、混合程序 exit 0、45 個隔離模組全部 exit 0；同一條件由 [linux-regression.yml](.github/workflows/linux-regression.yml) 的 `EXPECTED_TESTS` 在 CI 執行。新增測試後依真正 discovery 結果維護計數；品質修正須以原樣本／原目標證據更新預期失敗條件。不要為了變綠放寬白名單或刪斷言。

`spawn` 測試 driver 一定要有 `if __name__ == '__main__'`。判定時讀取**外層真正 process exit code**，不能只看日誌裡的 `OK`；也不能讓 `tail` 的成功蓋掉前一個測試失敗。舊 Qt teardown 失敗與錯誤暫存 driver 都已有原始紀錄，接手後不要抹除。

### 9.5 Windows 與候選清單

需要修改 Windows 管線時，優先沿用第 8 節兩個自動驗收 workflow。舊版 source checkout、各自 venv、空 PATH、中文位置與資料哨兵都是既有接受條件，不為了方便拿新版改個描述冒充舊版。

已建置的候選可用下列命令重新核對；請用相同來源建置環境，報告必須在 bundle 外且是新檔案：

```powershell
python scripts/check_bundle_provenance.py --profile base --bundle out/windows/dist/MarkItDownBase --report out/review/base-first.json
python scripts/check_bundle_provenance.py --profile cpu --bundle out/windows-cpu/dist/MarkItDownOCRWorker --package-directory out/windows-cpu/package --report out/review/cpu-first.json
python scripts/check_bundle_provenance.py --profile cpu --bundle out/windows-cpu/dist/MarkItDownOCRWorker --package-directory out/windows-cpu/package --verify-inventory out/review/cpu-first.json --report out/review/cpu-second.json
```

重驗基準報告本身也要有可信來源／hash。這些命令不簽署正式目錄，也不發布產品。

## 10. 下一步工作，按優先順序做

### P0：取得完整待查明細並保存

**2026-11-12 進度：** 第 1 步已完成（原檔與雜湊見 [ci-full-reports-2026-11-12](docs/development-records/runs/ci-full-reports-2026-11-12/README.md)），第 3、4 步已完成第一輪（[來源分類](docs/source-classification.md)與[逐檔結果](docs/development-records/runs/source-classification-2026-11-12/README.md)）。P0 尚未關閉的部分，需要在 Windows 建置時補資料：

- 為自系統路徑收集的 DLL 記錄來源路徑、數位簽章與版本資源（基本 48／CPU 46 項 candidate）。
- 查明並處理基本包的 `libcrypto-3-x64`／`libssl-3-x64.dll`（推測由 Qt TLS 外掛引入，未證實；排除會更動打包內容，需使用者同意）。
- 產生 `base_library.zip` 與 PYZ 的成員層級清單。
- 逐檔列出 CPython 隨附第三方元件的版本與原文。

以下為原始 P0 說明，保留作為程序與完成條件的依據。

當前最先接的工作是基本包 154／CPU 303 個未對照來源，以及 191／337 個需審閱檔案的分類與證據補齊。

1. 先嘗試從上述 CI 的 `windows-base-validation-reports`／`windows-cpu-validation-reports` artifact 取得 `bundle-provenance.json`。需要 GitHub 權限及網路可達；下載後保存來源 run／source commit／hash。
2. 若七天已過期或未能取得，從固定 source 重新建置；新 run 與舊 run 分開記錄，保存真正完整 JSON 與原始 log。不能用公開總數假造逐檔表，也不能改摘要旗標。
3. 按實際證據分類：RECORD 位元相符、Analysis 原生來源、CPython、PyInstaller 生成物、原文複本、模型、Python archive 成員與其他未知來源。名稱猜測不能直接變成已確認 owner。
4. 將檔案、來源包／版本、原文、hash、生成／轉換原因及仍待處理事項保存為可重驗對照。保留原始授權文字；補充中文說明另寫。

在已具 repo 權限且 GitHub API 可達的環境，可用以下入口；若 API 不可達，使用可用的 GitHub 工具或由擁有者介面取得，不反覆重試已被政策拒絕的端點：

```bash
gh run download 42982427175 --repo ChouTa-chuan/MarkItDown-exe --name windows-base-validation-reports --dir /tmp/markitdown-review-base-1
gh run download 42982427186 --repo ChouTa-chuan/MarkItDown-exe --name windows-cpu-validation-reports --dir /tmp/markitdown-review-cpu-1
```

下載後以 repo 內兩份 [base 摘要](docs/development-records/runs/candidate-inventory-ci-2026-11-11/windows-base-inventory-summary.json)／[CPU 摘要](docs/development-records/runs/candidate-inventory-ci-2026-11-11/windows-cpu-inventory-summary.json)的 `report_sha256` 核對各自報告，再讀 `candidate_inventory.files`、`review_reasons` 與 CPU 的 `package_inventory`。同一次候選來源不可換成另一輪檔案後仍沿用舊 hash。

**這項工作的完成條件：** 可取得或重建完整明細；每個待查項目有證據或明列缺口；驗證失敗／缺失不被清零掩蓋。完整 runtime SBOM 與再散布須另達門檻，不能只靠外層檔案快照關閉 C04。

### P1：關閉交付前來源與再散布事項

整理應用公開授權的待決策、Qt 對應來源／替換等要求、Microsoft／其他原生 runtime 再散布、Tesseract／模型原文、PyInstaller 啟動器原文與隨包通知。先做出具體可審閱的材料，再處理確實需要擁有者決定的項目。

**2026-11-12 進度：** 可審閱材料已整理為[應用程式授權提案](docs/license-proposal.md)：自有程式擬採 MIT（不等於整個產品採 MIT），並逐項列出 Qt、Microsoft runtime、OpenSSL、CPython、Tesseract、模型、FFmpeg、GEOS 的義務與缺口。提案待使用者確認，根目錄尚未加入 `LICENSE`。自有 `THIRD_PARTY_NOTICES` 已改為分 profile 敘述。

正式元件目錄 URL、維護金鑰與信任根還沒發布。測試使用臨時金鑰與 `example.invalid`，不能拿去當正式下載來源；主程式與元件更新的信任政策也不能由匯入包自行擴充。

### P2：準備測試產物，再做乾淨機／人工

先準備固定 source commit、版號、SHA-256、profile、隨包原文、測試限制與操作表的基本測試 Setup；CPU 實驗選配另列。工具與報告已存在，但尚未向使用者交付安裝包。

使用者指示（2026-11-12）：測試版優先規劃以 CI artifact 交付並附上述資料；必要授權與再散布門檻未關閉前，不自動對外上傳 Setup、worker 或模型，CI artifact 也屬交付、不得用來繞過門檻；暫不建立 Release／預發布或 tag。

| 驗收 | 開發端可先完成 | 需要實際 Windows／使用者配合的部分 |
| --- | --- | --- |
| 包裝完整性、版本、hash、功能回歸 | 現有 CI 與靜態／隔離驗證 | 通過也不能替代乾淨環境 |
| 全新環境 | 準備乾淨 VM、標準帳戶、無 Python、離線條件與步驟 | 在真正乾淨 Windows 完整執行安裝／首次啟動／四語／中文路徑 |
| 操作體驗與資料保留 | 自動 UI／哨兵／取消與故障測試 | 人工拖放、批次、預覽、RAM 設定、修復／移除與真實工作流程 |
| GPU | 整理相容 runtime、模型、政策與量測程序 | 相符的實體顯卡／驅動、VRAM 壓力、回退、品質與效能實測 |

使用者目前不需要先自行安裝未知測試包；等產物及具體驗收表備妥，再安排實際安裝。可由開發者使用合適乾淨 VM 完成一部分驗收，但人工使用與特定硬體仍需相應環境。

### P3：完整 profile 與 GPU 後續

補齊各 profile 的跨版相容、故障恢復及首次離線流程，再依實際證據關閉 C03／C04／C09／C11。GPU 另做獨立 worker／相依與相容矩陣，實卡確認 provider、推論、VRAM／OOM、CPU 回退准入及資源負載；以同輸入／模型／版本比較品質與速度。不要承諾尚未量測的工期、包體積或準確率。

## 11. 文件、同步與保存規則

| 資訊 | 優先閱讀位置 |
| --- | --- |
| 新人／新 AI 起點 | 本文件與 [AGENTS.md](AGENTS.md) |
| 產品規劃、模組責任與十二里程碑 | [architecture-guide.md](docs/architecture-guide.md)，注意各段補記的版本日期 |
| 目前勾選／測試／最新 source | [progress.json](docs/progress.json)、[validation-results.json](docs/validation-results.json) 與對應 run 證據 |
| 線上／離線視覺頁 | [固定網站](https://chouta-chuan.github.io/MarkItDown-exe/)／[progress.html](docs/progress.html)；JSON 是視覺頁資料來源 |
| 逐次改動與版本差異 | [CHANGELOG.md](CHANGELOG.md) |
| 過程、失敗、樣本、截圖、原始 log | [開發紀錄](docs/development-records/README.md)及各 run 的 manifest |
| 交付缺口與驗收次序 | [windows-test-build-readiness.md](docs/windows-test-build-readiness.md) |
| 未對照來源分類與剩餘缺口 | [source-classification.md](docs/source-classification.md) |
| 授權提案與第三方義務 | [license-proposal.md](docs/license-proposal.md)（待確認） |
| 原始架構圖與快照 hash | [architecture/README.md](docs/architecture/README.md) |

`docs/development-status.md`、`docs/packaging.md`、`docs/packaging-profiles.md` 等文件保留早期階段敘述。它們有些「Windows 待跑」「本版完整回歸未跑」是當時狀態，閱讀時要比對日期、版號及 source；不能推翻本文件列出的較新實證，也不能把新實證倒填進舊 run。

接手後維持以下習慣：

- 新程式契約與複雜流程加中文註解；vendor 固定上游、第三方原文／模型／公開樣本維持來源與 hash。
- 以實際證據維護本文件狀態段、`progress.json`、`validation-results.json`、CHANGELOG 與開發紀錄。只做文件更新就寫清楚未重跑產品測試，不抄舊數字冒充新執行。
- 新證據放新的 run 目錄，保存原始失敗、樣本與 hash；不要覆寫舊附件、把真實使用者文件／環境秘密／venv／cache 加入 Git。
- 架構圖若改動，新增快照及索引／hash；目前 28 份舊圖保持不變。本文件的責任表引用既有架構，沒有新增或更改圖。
- 分支規則（2026-11-12 起）：在工作分支作業並同步 GitHub，獨立工作開新分支；可自行提交、推送工作分支與建立 PR。**不直接推送 `main`，合併由使用者另行指示**；不 force push、不刪除分支或標籤、不改寫歷史。進度網站只在 `main` 更新後由 Pages workflow 部署，因此工作分支上的進度資料要等合併後才會出現在固定網址。先前「正常推送 `main`」的做法自此停用。
- 刪除檔案、更動授權、升級大版本相依套件、更改打包方式，先取得使用者同意。
- 應用程式 Release／Setup 發布、雲端環境設定發布與進度網站發布是不同動作。已有進度網站發布授權；未另有產品發行指示時，不自行建立 Release／tag、上傳 Setup 或觸發舊手動發行 workflow。後續使用者新指示優先。

更新視覺頁使用 `python scripts/build_progress.py`。如改 UI／頁面行為，可用 `scripts/check_progress_browser.py` 驗分頁、篩選、鍵盤與手機版；需要 Playwright／Chromium。只改本交接說明不需重跑原生建置、OCR 或全 684。

雲端環境可能替換或暫停；既有本機 venv、`/tmp`、未推送檔案與 CI artifact 保留期都不等於永久保存。GitHub 保存程式與已提交紀錄，ChatGPT／Codex 對話是否跨客戶端出現需另查，不能靠 Git 推送恢復聊天紀錄。

這份交接保存已確認決策與可取得的工程證據；不宣稱完整備份所有聊天逐字內容，或補回未下載而已過期的 artifact。

若雲端 Git 請求顯示連不到代理，先依環境 runtime 指引確認狀態與網路政策，再用相同代理／憑證的合適執行方式重試；不要停用 TLS 或任意改網路設定。此前 GitHub API／github.io 直接讀取受限，Git 推送與 GitHub 公開 Actions 頁仍可使用；Pages 的實際 HTTP／hash 已由 GitHub runner 驗證。這是當時環境差異，不代表所有新 session 都相同。

## 12. 可直接貼給新 AI session 的接手指令

> 請接手專案 https://github.com/ChouTa-chuan/MarkItDown-exe 。先讀根目錄 AGENTS.md、PROJECT_HANDOFF.md；若尚無 checkout，交接文件可先讀 https://raw.githubusercontent.com/ChouTa-chuan/MarkItDown-exe/main/PROJECT_HANDOFF.md 。再核對遠端 main、pyproject.toml、docs/progress.json 與最新開發紀錄。這是以 Microsoft MarkItDown 為核心的 Windows 桌面應用程式，採基本安裝包＋選配元件管理；精準模式自動分析，基本 Tesseract 四語，RAM 是軟性預算，GPU 尚未實卡驗收。
>
> 2026-11-12交接基線：程式0.19.1／架構0.4，C01–C12為7/12（C03 3/4、C04 2/4、C09 3/4、C11 2/5），完整698項為697 pass＋1既有ONNX繁中品質expected failure、0 skip，混合及45獨立模組exit0（cb8f24d當時為684／43模組）。真正功能／Windows候選來源cb8f24d；基本10／安裝6／跨版11／三停點續修，CPU11／同版8／跨版8／程序恢復6已接受。固定進度網站https://chouta-chuan.github.io/MarkItDown-exe/已上線。
>
> 完整候選報告原檔已保存於docs/development-records/runs/ci-full-reports-2026-11-12，基本154／CPU303個來源未對照項目已依雜湊證據分類（docs/source-classification.md）；下一項優先工作是在Windows建置補記系統DLL的來源路徑／簽章／版本、處理來源不明的OpenSSL、產生Python封存成員清單，並等使用者確認docs/license-proposal.md。更早各次run的完整報告未保存，不能憑總數補造明細。普通檔案清單已驗不等於runtime SBOM或授權核准。接著準備固定版本／hash／原文與操作表的測試產物，再做無Python乾淨Windows／離線／人工／GPU驗收；目前沒有使用者可下載的正式Setup。
>
> 在工作分支作業、推送分支並以PR提交，不直接推送main、不force push，合併由使用者指示。依當下任務先完成一個具體可驗證子項，維持中文註解、CHANGELOG、開發紀錄、交接摘要與視覺進度並同步GitHub；保留舊證據／架構圖／vendor／原文／模型。不重做已完成核心，不放寬品質目標，不把模擬、跳過或expected failure當品質通過；未另有發行指示時不建立Release／tag或發布Setup。若後續提交已更新狀態，以實際來源及新證據調整這份歷史基線。


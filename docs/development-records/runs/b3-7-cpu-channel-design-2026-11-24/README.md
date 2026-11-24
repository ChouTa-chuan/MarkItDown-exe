# B3-7 CPU 測試通道設計

2026-11-24（台北）。設計以 `main` `77f2d80` 為基準，依 2026-11-21 的 B3-D2。供 Claude reviewer 查驗及 Claude 撰寫逐步教學。實作的前提是設計查驗完成，以及使用者回報已建立金鑰及 Actions secret。正式安裝、上線和再散布另依 B3-9 至 B3-13 辦理。[B3-D2 固定紀錄](../../../history/status/2026-11-21-b3-decisions.md)

## 信任根與金鑰

| 項目 | 設計 |
| --- | --- |
| 通道 | 介面名稱「CPU 元件測試通道」。`catalog_id = markitdown-cpu-test`、`policy_version = 1`、`minimum_revision = 1`。初始 `key_id = cpu-test-2026-01`。版本下限由基本包提供。 |
| 演算法 | Ed25519，沿用目前的 Python `cryptography`。驗證端將 OpenSSH 公鑰解碼為 32 bytes，簽章為 64 bytes，再以帶補位的標準 Base64 寫入封套。 |
| 公鑰 | 後續實作放在 `src/desktop_app/components/test_channel.py`，保存 `ssh-ed25519 <Base64 公鑰>` 兩段文字，省略註解。以 `load_ssh_public_key` 讀取，確認型別後將原始 32 bytes 交給 `TrustPolicy.keys`。公鑰及指紋可公開，由 repo 的程式審閱固定到基本包。 |
| 私鑰 | 一次性產生的 OpenSSH Ed25519 私鑰，檔案以 `-----BEGIN OPENSSH PRIVATE KEY-----` 開頭。CI 會以 `load_ssh_private_key(..., password=None)` 讀取，先從私鑰算出公鑰，核對已審閱的 repo 公鑰及 key ID。 |
| Actions secret | GitHub Environment `cpu-test-signing` 的 **`CPU_TEST_ED25519_PRIVATE_KEY_B64`**。值是整份 OpenSSH **私鑰檔的原始 bytes** 經標準 Base64 編碼後的一行，保留末端補位，不加引號、不附換行。Base64 本身沒有加密。使用者自行設定這個 secret，設計與驗收不假定它已存在。 |

### Windows 一次性操作草案

Windows 10／11 提供 Windows PowerShell、`Set-Clipboard` 與 OpenSSH Client 選用功能。先開啟「開始」搜尋 **Windows PowerShell**，貼上 `Get-Command ssh-keygen.exe` 再按 Enter。若找不到，從 Windows「設定 → 選用功能 → 檢視功能／新增功能」安裝 **OpenSSH Client（OpenSSH 用戶端）**，重新開啟 PowerShell 再查一次。這個選用功能可能需要管理員或組織 IT 核准。金鑰操作使用一般使用者權限，無需先裝 Python、Git、GitHub CLI 或 OpenSSL。

1. 將下列整段貼到 PowerShell。它會在目前使用者的本機資料夾建立測試通道金鑰，既有金鑰不會被覆寫。`ssh-keygen` 詢問 passphrase 及確認時，各按一次 Enter，讓 Actions 能以這一個 secret 非互動簽署。私鑰留在受保護的本機使用者目錄。請避開共用、雲端同步或會自動備份到外部的資料夾。

   ```powershell
   $folder = Join-Path $env:LOCALAPPDATA 'MarkItDown-KeySetup'
   $key = Join-Path $folder 'cpu-test-ed25519'
   if ((Test-Path -LiteralPath $key) -or (Test-Path -LiteralPath "$key.pub")) {
       throw '已存在金鑰，請沿用既有檔案。'
   }
   New-Item -ItemType Directory -Path $folder -Force | Out-Null
   ssh-keygen.exe -t ed25519 -f "$key" -C "MarkItDown CPU test channel"
   if ($LASTEXITCODE -ne 0) { throw '金鑰建立失敗。' }
   Get-Content -LiteralPath "$key.pub"
   ssh-keygen.exe -E sha256 -lf "$key.pub"
   ```

2. 只提供畫面上 `ssh-ed25519` 開頭的**公開金鑰**與下一行的 `SHA256:` 指紋給實作者，供審查寫入 repo。若關閉了視窗，可重開 PowerShell，執行上段最後兩行前先貼上前兩行路徑設定。
3. 在 repo 的 **Settings → Environments** 建立 `cpu-test-signing`，將可使用的 deployment branch 限為 **`main`**。啟用環境覆核，讓指定覆核者確認要簽署的 run 與提交。從同一頁的 **Environment secrets → Add secret** 輸入上表名稱。先在 Windows 關閉剪貼簿歷程與跨裝置同步，再把下段貼進本機 PowerShell，然後把剪貼簿內容貼到 GitHub 的 secret **Value** 欄，儲存後以第二段指令覆寫剪貼簿。

   ```powershell
   $key = Join-Path $env:LOCALAPPDATA 'MarkItDown-KeySetup\cpu-test-ed25519'
   Set-Clipboard -Value ([Convert]::ToBase64String([IO.File]::ReadAllBytes($key)))
   ```

   ```powershell
   Set-Clipboard -Value '已清除測試金鑰剪貼簿。'
   ```

4. 回報「secret 已設定」及第 2 步的公開資料即可。私鑰檔、Base64、剪貼簿內容及含 secret 的畫面都不得貼進對話、Issue、PR、repo 或 CI 記錄。若需保留本機備份，使用只有管理者可讀的加密儲存。

來源與按鈕名稱供教學者核對。[Microsoft OpenSSH 安裝說明](https://learn.microsoft.com/windows-server/administration/openssh/openssh_install_firstuse) · [GitHub Environment 與保護規則](https://github.com/github/docs/blob/main/content/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments.md)

## 目錄、簽章與 ZIP

沿用現有 [目錄驗證器](../../../../src/desktop_app/components/catalog.py) 的 schema 1 封套。交付單一 **`cpu-test-catalog.json`**，頂層只有 `payload` 和 `signature`。簽章隨 JSON 封在 `signature`，離線匯入只需選一次目錄檔。`component.json` 是提供給簽署步驟的建置輸入，保留在 CI 工作區。簽署後的目錄及簽章與 CPU ZIP 分開交付，三者均不內嵌在基本包。

| 欄位 | 固定契約 |
| --- | --- |
| `payload.schema_version`、`payload.catalog_id`、`payload.trust_policy_version` | 各為 `1`、`markitdown-cpu-test`、`1`。三者必須符合基本包內的政策。 |
| `payload.revision` | 正整數。初始只允許一個正式持有測試私鑰的 workflow 為此通道編號，採該流程的 `github.run_number`。實際簽署只限該 run 第一次執行，失敗要重新開新 run 取得新號碼。更換流程前須證明新編號高於已簽過的最高版次。 |
| `payload.issued_at`、`payload.expires_at` | UTC `YYYY-MM-DDTHH:MM:SSZ`，由 CI 時鐘產生，測試通道最長有效 30 天。驗證沿用目前 5 分鐘的時鐘誤差容許與到期即拒絕，另限制簽署與驗證兩端的最長有效期。 |
| `payload.components` | 一筆完整的 `ComponentSpec`，限 Windows x64 `onnx-cpu-ocr`。簽章綁定版本、相容範圍、`package_sha256`（整個 CPU ZIP）、`download_bytes`、解壓容量、逐檔大小與雜湊、能力與健康探針等完整資訊。 |
| `signature.algorithm`、`signature.key_id`、`signature.value` | 分別為 `ed25519`、`cpu-test-2026-01` 與 Base64 簽章。使用現有 `canonical_json(payload)` 的 UTF-8 bytes 簽署，鍵排序且無額外空白，不簽任意原始 JSON 排版。 |

`minimum_revision` 在基本包內的 `TrustPolicy`。匯入的目錄只能宣告自己的 `revision`。保留現有 `ComponentSpec.source_url` 格式，測試描述沿用 `https://example.invalid` 作為不提供下載的保留網域，作為此政策唯一允許的 descriptor origin。實際傳輸另受 `offline_only` 拒絕。簽署工具從本次建置產生的 `component.json` 取出完整描述，重新串流核對 ZIP 的 SHA-256 與長度，格式、平台、範圍或摘要錯誤即停。使用現有驗證器回讀自身產物再交下游，並記錄公鑰指紋、提交、版次、到期、目錄與 ZIP SHA-256。[元件描述](../../../../src/desktop_app/components/contracts.py) · [現有封裝工具](../../../../scripts/package_cpu_worker.py)

## 離線安裝

1. 取得**內建測試通道公鑰的基本包**，並取得同一批提供的 **`cpu-test-catalog.json`** 與 **CPU 元件 ZIP**。準備好檔案後可斷網。公告的 SHA-256 可另行對照，程式仍逐一檢查目錄簽章與 ZIP 雜湊。
2. 安裝並開啟基本包。到「選配元件管理」，確認顯示「CPU 元件測試通道」，按「匯入簽章目錄」，選剛取得的 JSON。成功時顯示目錄版次與到期日。
3. 選清單中的 Windows CPU OCR 元件，按「匯入包檔並安裝」，選 ZIP，等待雜湊核對、交易安裝與健康檢查。ZIP 由程式解壓到受管資料夾。本階段停用「更新線上目錄」、「下載並安裝」與現行會走網路的「修復此版本」。
4. 回主畫面，明確選「受管 CPU OCR（選配、繁體品質未達標）」後再轉換。移除時回到「選配元件管理」，選「移除此版本」。元件安裝、停用或到期不改寫既有 OCR 後端設定。舊基本包未內建本通道的公鑰，需換用對應測試基本包。

## 既有程式接線

| 預計改動 | 責任 |
| --- | --- |
| 新的 `src/desktop_app/components/test_channel.py`、`components/catalog.py` | 封裝固定 Windows 測試通道公鑰、ID、版本門檻、最大目錄效期及 `offline_only`。沿用 `TrustPolicy` 的簽章、來源 origin、容量與驗證。若加新欄位，保持現有預設，並讓 pickle／spawn 保留相同政策。 |
| `components/management.py`、`components/network.py`、`components/downloads.py` | `TrustedSource(policy, catalog_url=None)`。在服務層擋掉線上更新及下載路徑（含會走網路的修復），並在發出網路請求的共用入口檢查 `offline_only`，包括測試注入 opener 的分支。離線沿用 `DownloadService.import_offline`、包檔 SHA-256、C06 staging 與健康探針。原樣保留受管檔案完整性、鎖及租約。 |
| `desktop.py`、`component_dialog.py`、`cli.py`、`diagnostics.py` | 在 Windows 的正常應用入口建立同一個固定信任政策，從既有 `ManagedContext` 傳給轉換子程序。保留固定測試 fixture 的注入接口。介面與診斷顯示「測試通道」，診斷只列可公開欄位，例如通道 ID、版次及到期。 |
| `docs/component-management.md`、新增簽署腳本及專用 Actions workflow | 實作後更新「未發布正式目錄」段落與離線操作，沿用現有授權和包檔來源。簽署腳本可預計放 `scripts/sign_cpu_test_catalog.py`，專用 workflow 可預計放 `.github/workflows/windows-cpu-test-catalog.yml`，B3-12 接上同一簽署路徑。 |

基本包只有公鑰與政策程式碼。靜態 Python import 供 PyInstaller 收入，不需另增型錄資料路徑或變更 spec。hosted Windows 應以凍結封存清單和安裝後逐檔清單確認該事實。共用 `ComponentManagement` 保留現有開發 fixture 行為，目錄、環境變數或使用者設定都不能為測試通道新增金鑰或 URL。定版前把基本包的 Python 模組與包內雜湊變化交 B3-9 重新核對。

## CI 簽署、重放與撤銷

- 真實測試私鑰只在受保護的 **`main` 手動啟動**簽署 job 使用。該 job 使用上述 GitHub Environment，GitHub 環境保護與 workflow 的 `github.ref == 'refs/heads/main'` 同時檢查。僅簽同次由已審閱原始碼建置、符合預期描述且核對過的 ZIP。B3-12／13 產出另綁定 B3-9 固定候選與公開 gates。避免接收 PR／外部 ZIP、路徑或指令作為簽署輸入，PR 驗收以當次短效臨時金鑰執行。私鑰只透過簽署步驟環境變數傳入並在記憶體解碼，不作命令列值、檔案、workflow output、快取、報告或 artifact。secret 缺少、格式錯誤或公私鑰不匹配即失敗，不能改用替代簽章。
- 目前 `CatalogVerifier` 的已見版次在記憶體。設計沿用原子儲存方式，由測試通道專用的本機簽章目錄（例如 `component-catalog-markitdown-cpu-test-v1.json`）提供跨重啟的已見紀錄。在既有管理鎖內核對**已存目錄的簽章、通道、政策版本與內容**，以其版次和 canonical payload SHA 設定拒絕門檻。已存目錄即使過期也只可提供版次紀錄，不能授權安裝或執行。新目錄先完整重驗，再以原子替換一併提交內容和已見版次。跨程序拒絕低版次或同版次不同 signed payload，允許重匯仍有效的同版同內容。已存目錄損毀時停止使用測試通道並提示管理者，不默認清空版次。此紀錄無法防止刻意刪除或回滾使用者資料、重裝或惡意改時鐘。乾淨安裝只知道內建下限，沒有遠端刷新。
- 到期、錯簽、他鑰、政策版本不符、撤銷或版次倒退的目錄無法授予安裝、修復與新的 worker 租約。保留受管版本的授權查看與安全移除，基本包轉換可用。輸入同版內容的判定只比較已簽的 payload，不比較 JSON 空白。
- 私鑰外洩可讓持有者替仍信任此金鑰的舊基本包簽偽造目錄，裝上的 worker 以使用者身分執行。先停用簽署 job、刪除舊 secret 並撤下可控的下載入口。再出新版基本包，撤銷舊 key ID，固定新公鑰、提高政策版本，並把內建版次下限定在已知合法簽署的最高版次之上。新版使用對應政策版本的新目錄路徑，排除已撤銷的舊快取。更新後重新匯入新目錄才允許新的工作。刪除 secret 無法遠端更新離線舊安裝，也無法使曾經散布的檔案消失。最長效期只約束一份目錄，持有外洩私鑰的人仍能持續為舊版基本包簽新的目錄。
- 商用或正式發行另建立 ID、公鑰與私鑰、分開的簽署環境及版次序列。正式包只信任正式通道，不能把測試 key 當成正式 root。使用者只能匯入簽署目錄和 ZIP，沒有金鑰輸入欄或信任例外開關。

## 驗收與交付拆分

| 驗收層 | 要求 |
| --- | --- |
| Linux／Qt 單元與整合 | 正確簽章、只改 ZIP 一個位元、簽章損毀、signed payload 被改、到期（含剛好到期）、超過效期、版本倒退、同版換內容、他鑰帶正確 key ID、已撤銷 key、通道不符全部有對例。重新啟動、已存目錄過期再匯舊版、取消／失敗保留已存目錄、離線政策底層不觸網、缺 secret 與公私鑰不匹配均有測試。 |
| Hosted Windows 2022 | 用凍結基本包及凍結 CPU worker，以內建公鑰走真正的 GUI 匯入、運行 OCR 固定樣本、移除，並檢查基本轉換仍可用。PR 使用臨時金鑰與獨立測試凍結包走相同驗證路徑。合併後再在受保護的 main 驗收實際內建公鑰、實際保護環境的簽章與凍結包配對。該次包件只在 runner 上留存，證據只輸出檢查結果與雜湊。實體 Windows 另在大階段 C 驗收。 |
| 包件及流程 | 確認基本包含固定公鑰，沒有目錄、簽章封套、原始 `component.json` 或任何私鑰。一般測試及診斷不可輸出 secret。確認回歸與既有 gates，測試計數依跑出的結果同步。公開仍由 B3-12／13 的獨立規則決定。 |

建議 **B3-7 用兩個 PR**，以 B3-7a 設計、B3-7b 實作各一次。設計 PR 只交本說明與交接紀錄。實作 PR 在使用者回報金鑰與 secret 完成後，按提交拆成「讀取端（固定公鑰、政策、介面與診斷）」及「CI 簽署、文件與驗收」，由 Claude reviewer 整體複查。只有實作 PR 的讀取端會改變基本包程式與信任模型。CI 簽署腳本、workflow 和證據留在建置端。B3-9 仍負責重定候選，B3-12／13 各照既定計畫處理產出與公開。

本輪在 Linux 以一次性 OpenSSH fixture 驗證 Base64 傳輸格式、公私鑰一致、Ed25519 簽名與修改 payload 後被拒。fixture 已刪除。Windows 的 PowerShell 及按鈕步驟尚未實機試跑。簽署與應用程式實作、實際 secret 設定及凍結包驗收留待後續。

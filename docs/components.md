# C01：元件契約、登錄與能力解析

C01 交付程式版本 **0.2.0**，架構版本 **0.4**，2026-11-06（台北）。本項完成 Linux 的底層驗收；[逐項結果與原始日誌](development-records/runs/c01-2026-11-06/README.md)保存於專案。

目前程式 **0.4.0** 已完成 [C02](component-migration.md)、[C05](component-downloads.md)及 [C06 維護與使用租約](component-lifecycle.md)，主登錄仍為 schema 2，維護日誌另外保存；下文保留 C01 的責任邊界及交付範圍。

## 模組與呼叫邊界

| 模組 | 已實作責任 | 後續接入 |
| --- | --- | --- |
| `components/contracts.py` | 不可變元件描述、嚴格 JSON 解析、穩定版本與半開版本範圍、平台、依賴、檔案與容量、授權及簽章欄位 | C02 轉接舊模型；C05 驗證可信目錄與簽章 |
| `components/registry.py` | SQLite schema 1、不可變 ID／版本描述、狀態保存、串流 SHA-256、安裝清單與並行世代檢查 | C06 下載後的交易安裝、修復、鎖與回復 |
| `capabilities.py` | 主程式核准目錄、平台／架構／app／協定相容、依賴與健康檢查、明確引擎限制 | C07 實際隔離 worker；C10 接入自動文件分析 |

C01 交付當時沒有新增第三方依賴。當時 GUI、轉換器、`models.py` 與設定 schema v5 保持原流程；C01 尚未讓桌面使用者操作元件下載或安裝。

## 描述與資料

`ComponentSpec.from_dict()` 只解析 schema 1，拒絕未知／缺漏欄位、可變或過大陣列、重複檔名、不安全路徑及不合法容量。版號限三段穩定版，例如 `1.10.0`；以數字比較，範圍為 `[minimum, maximum_exclusive)`。目前不支援預發版、萬用字元或套件管理器的版本運算式。

每份描述包含來源 HTTPS URL、授權 ID／檔案、包檔 SHA-256／大小、展開上限、每個檔案的大小／SHA-256、平台／架構、相容 app／worker 範圍、能力、依賴、RAM／VRAM／磁碟預估及健康檢查 ID。`required` 供必要元件優先選擇；簽章欄位可保存 Ed25519 資料，但**格式通過不代表簽章或來源已驗證**。C01 的 catalog 必須由可信程式碼提供，不能直接載入網路 JSON 作為核准目錄。

呼叫端指定登錄根目錄；檔案為 `component-registry.sqlite3`，元件位置為 `components/<id>/<version>`。Qt 使用者資料目錄的實際接線留待後續。外部原有模型不會被移動、接管或刪除。

SQLite 保存描述及其雜湊、最後狀態、包檔位置、安裝註記、原因、檢查時間與世代號。相同 ID／版號不得換描述。未知 schema、損壞資料或超限資料明確失敗，不自動清空使用者登錄。

## 何時可用

| 狀態 | 證據與含義 |
| --- | --- |
| `missing` | 僅登錄描述或尚無元件 |
| `downloaded` | 呼叫端提供的一般包檔存在且大小完整，尚未驗證雜湊 |
| `verified` | 包檔串流 SHA-256 與大小相符；仍不是可用元件 |
| `installed` | 呼叫端已準備的目錄與檔案清單、大小、雜湊相符；尚待能力檢查，或依賴尚未就緒 |
| `ready` | 本次完整性、平台／架構／app／協定、依賴及可信健康探針全部通過 |
| `incompatible` | 平台或版本不符，或依賴循環／深度超限 |
| `unhealthy` | 探針未註冊、回傳失敗／無效資料或執行異常 |
| `corrupt` | 包檔、安裝內容或登錄遭修改／缺漏／損壞 |

登錄狀態是**上次觀察**。每次 `assess()`／`resolve()` 重驗實檔、相容性、依賴及探針，不把舊 `ready` 當作永久可用；探針通過後再次驗證 payload，避免探針改動內容仍列為就緒。依賴可用版本按數字由新到舊尋找；能力解析先必要元件，再按固定 ID 順序與版本挑選。明確指定 `component_id` 時不改用其他引擎；完全找不到可用項目時回傳 `available=False` 與原因。

探針是主程式以 ID 註冊的函式，回傳 `HealthResult`，不執行描述中的任意指令。合成測試探針只代表檔案讀取驗收，不能冒充 OCR／GPU 真實推論；後續各引擎需註冊實際載入／推論測試。

## 後續程式如何使用

```python
from desktop_app.capabilities import CapabilityResolver, HostContext
from desktop_app.components.contracts import ComponentSpec, Version
from desktop_app.components.registry import ComponentRegistry

# approved_metadata 必須來自可信程式碼；network catalog 的驗證屬 C05。
spec = ComponentSpec.from_dict(approved_metadata)
registry = ComponentRegistry(user_component_directory)
registry.register(spec)
host = HostContext('windows', 'x86_64', Version.parse('0.2.0'), Version.parse('1.0.0'))
resolver = CapabilityResolver(registry, [spec], host, trusted_health_checks)
result = resolver.resolve('ocr.text.zh-hant', component_id=spec.component_id)
if not result.available:
    # 交給應用服務顯示原因；不能以目錄存在直接執行引擎。
    reasons = [item.reason for item in result.assessments]
```

`record_download()`／`verify_download()` 只登錄並檢查已存在的包檔；`record_installation()` 只驗證已準備的內容，**不負責解壓、安裝或來源信任**。詳見測試中的完整生命週期正反例。取消使用既有 `Cancelled`，不寫入驗證成功；寫回時比較世代號，舊探針不能覆蓋較新的狀態。

## 範圍與限制

- 登錄最多 256 版本、描述最多 256 KiB、檔案最多 4,096、目錄列舉最多 8,192、依賴深度最多 32；檔案使用 64 KiB 緩衝驗證並可取消。容量仍以可信描述限制，資源欄位是估計，不是硬性 RAM 上限。
- 拒絕路徑逃逸、Windows 裝置名稱、ADS、符號連結與 reparse point；Windows 實際檔案系統／junction 行為仍需 Windows 驗收。本次測試在 Linux 執行。
- 世代檢查保護登錄寫回；沒有宣稱 C06 的使用中鎖、原子啟用、回復或檔案生命週期交易已完成。解析之後仍可能有檔案變動，未取得使用租約前不能把結果當作任務全程保證。
- C05 可信來源／金鑰驗證、下載續傳，C06 安裝維護、C07 實際 worker、C08 管理頁及 C10 自動路由都另有檢核。Windows 安裝包與真實 GPU 尚未驗收。

重跑：在安裝專案的環境執行 `python scripts/check_component_acceptance.py --report /tmp/c01-acceptance.json`；任何跳過、錯誤或預期失敗均不列 C01 通過。完整回歸仍須具備 GUI／Office／PDF／OCR 測試依賴。

# VS2022 Community 授權條文白話摘要

來源是 Microsoft 官方頁連結的 [英文授權原文](official-vs2022-community.docx)，文件名稱為 **MICROSOFT VISUAL STUDIO COMMUNITY 2022**，EULAID 為 `VS_Comm_2022_ENU.1033`。取得日期、官方網址、HTTP 資料及 SHA-256 見 [來源紀錄](community-source.json)。原文的使用權以遵守條款為前提。以下以原文節名定位，不是完整翻譯。

本摘要只陳述條文，不判斷使用者、本專案、hosted CI，或任何 Microsoft DLL 複本是否適用。A13-1 的適用條款與再散布決定仍由使用者做；取得原文不等於核准。

| 原文位置 | 條文內容的白話整理 |
| --- | --- |
| 第 1 節 INSTALLATION AND USE RIGHTS／Individual License | 個人為自己的應用程式工作時，可以使用軟體開發及測試這些程式，目的可以是銷售或其他用途。這段是在描述個人使用權。 |
| 第 1 節／Organizational License | 組織可讓不限人數的使用者，在條文指定情境中開發與測試：以 OSI 認可授權發布的開源應用程式、Visual Studio 擴充、Windows 裝置驅動、使用所列工具的 SQL Server 開發，以及課堂教育或學術研究。各項仍有原文所列範圍。 |
| 第 1 節／Organizational License 的其他使用 | 若前述情境均不適用，且組織不是條文定義的 enterprise，最多五位個別使用者可同時開發及測試。enterprise 的員工與承包商則受原文列出的例外情境限制。 |
| 第 1 節／enterprise 定義 | 條文合併計算組織及其 affiliates，列出「超過 250 部 PC 或使用者」與「年收入 100 萬美元（或其他貨幣等值）」的條件；affiliates 以多數持股控制、被控制或共同控制的關係定義。此處保留原文的門檻表述，不套用到特定組織。 |
| 第 1 節／Workloads | 工作負載或其元件若有不同授權條款及支援政策，依該元件的條款處理。 |
| 第 3 節 TERMS FOR SPECIFIC COMPONENTS／Build Devices and Visual Studio Build Tools | 原文允許把相關檔案安裝至其定義的 Build Devices，限用於編譯、建置、驗證及建置過程中的品質／效能測試；條文也描述實體機、VM／容器及所列遠端設備條件。此摘要不判斷特定 CI runner 是否符合定義。 |
| 第 3 節／Licenses for Other Components | Microsoft 平台元件可能由其他協議及產品支援政策規範；第三方元件也可能有自己的 notices 或協議。NuGet 等套件管理器取得的套件依各自授權，而不是直接套用本文件。 |
| **第 4 節 DISTRIBUTABLE CODE／Right to Use and Distribute** | 對原文所定義的 Distributable Code，授予所述複製及散布權。Distributable List 子項指向 `https://aka.ms/vs/17/redistribution`，允許複製及散布該清單所列程式碼的 object code；sample、template、simple styles、sketch styles 另有原始碼／object code 的規定。也可允許應用程式的散布者隨該應用程式散布這些程式碼。原文也將讓第三方透過網際網路存取應用程式的部署納入 distribution 定義。 |
| **第 4 節／Distribution Requirements** | 應用程式須加入顯著的主要功能；須要求散布者及外部最終使用者同意至少與本協議同等保護 Distributable Code 的條款。這些是散布時需符合的要求。 |
| **第 4 節／Distribution Restrictions** | 不得散布標為 Preview、Pre-release 或 Beta 的元件／runtime；不得以應用程式名稱或其他方式使用 Microsoft 商標，使人認為程式來自 Microsoft 或獲其背書；不得修改或散布 Distributable Code 原始碼，使其任何部分受到原文定義的 Excluded License 約束。Excluded License 的定義包括要求揭露／散布原始碼或賦予他人修改權的條件。此處不判斷任何具體授權的適用結果。 |
| 第 7 節 SCOPE OF LICENSE | 軟體是授權使用而非出售，只授予明列權利；另列技術限制、逆向工程、保留 notices，以及分享、發布、出租、提供整套軟體或移轉協議等限制與例外。整套軟體的使用／移轉限制與第 4 節特定 Distributable Code 的權利須按各段原文閱讀。 |

第 4 節引用的清單入口與原文分開；本輪沒有把 Community 的使用資格或清單的存在當成包內逐檔授權結論。既有 [Microsoft 逐檔目錄](../../../../packaging/microsoft/base-windows.json) 仍保留每份複本的來源、版本、簽章及 hash 差異，`base-microsoft` 保持 open。

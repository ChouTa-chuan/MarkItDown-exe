# A13c 固定候選逐列來源對照

以 A13b 固定候選 b17d51b 的 base-source-review 重產來源對照與封存／MIT 證據；原 A12／A12b 證據原地保留。[逐列來源](origin-known-review.json)、[差異 fingerprint](changes-from-a12b.json) 與 [工程證據評估](evidence-assessment.json) 均引用同一候選。每個生成腳本引用包含固定 Git 提交與 SHA，Microsoft 目錄／探測引用包含本輪審閱基準；不以未來工作樹檔案替代歷史輸入。

根目錄 vcruntime140／_1 已是 Visual Studio 官方 VC143 Redist，PE 14.44.35211.0、來源／包內／官方同名 SHA 相同；不再沿用 A12b「CPython 來源、14.42」的理由。其他差異是 ZIP 及生成清單／說明檔。生成檔的來源腳本及當前 fingerprint 可以追溯；精簡報告沒有全部生成內容，不宣稱已逐位元重新建置或解釋每個 byte 的差異原因。

base-source-attribution、base-archives、base-own-mit-binding 只刷新 evidence，不改條目狀態、使用者決定、accepted_gaps、來源選擇器與原始計數。base 的 disclosed／redistribution_approved 維持 true，strict complete／release_ready 維持 false；CPU 全部 false。這份來源對照本身不新增核准。

封存列舉、pure modules fingerprint 與 MIT 套件綁定以 b17d51b 重新核對；完整 pure TOC 仍在原 A13b CI 報告，不宣稱 PYZ bytecode 反編譯。build_only_modules_absent 沿原規則只表示 setuptools 排除，不能擴寫成所有建置工具都不存在。

來源候選使用既有 A13b Windows base run 44295039865；本輪 PR 的 Windows CI 只是整合驗證，不重新固定候選或改安裝內容。階段完整回歸與最終 PR 查驗完成後補記；不交付產品、Release 或 tag。下一項 B1a 為獨立分支與 PR，試跑只上傳報告，B1b 留待 Claude planner 複查後另行開始。

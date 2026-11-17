# A9b cryptography 內含 OpenSSL 原文

2026-11-18（台北），程式 0.19.1／架構 0.4 不變。從 main 0b6fc51 新開 codex/a9b-openssl-notice-20261118，對應 [PR 21](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/21)。開工時沒有開啟中的 PR。

## 版本與原文

[Windows 觀測](windows-observation.json)來自真正 hosted Windows run 44142370284，初始 head 6187e0e。由 cryptography 連結的 OpenSSL 文字／數值 API 讀到同一版本，_rust.pyd SHA-256 與 A6 完全相同。使用既有 runtime-observed，不以靜態字串、CPython ssl 或 Linux 觀測冒充 Windows 版本；不是實體使用者機驗收，也不宣稱完整連結旗標、PE 匯入表與 Rust 相依已驗證。

原始 LICENSE 保存在 src/desktop_app/data/licenses/windows/supplemental/cryptography.txt。官方 openssl-4.0.3 tag 解參照到固定 commit af1775b60dfa141a4ad762585052cabeb9f37e9e，原始 URL、SHA-256、Git blob 與 tag chain 在 packaging/cryptography/openssl.json 及 openssl-4.0.3-ref.json；原始位元組不改寫。

原文由既有 supplemental_sources 管線複製到基本包 licenses/supplemental/cryptography.txt，綁到實際 cryptography 套件；API 觀測與來源資訊另隨包保存在 licenses/cryptography-openssl.json。資產準備先驗版本／原文，最終 bundle 再驗缺檔、內容、套件對應及 _rust 實際 bytes。重建資產 hash 也不能掩蓋錯綁或竄改。

元件詳情只放 packaging/embedded/base-windows.json，登記表引用目錄與 Windows 觀測 path／hash。Rust 相依仍 unknown，base-wheels-cryptography 仍 open。A6 本身沒有新增原文，本輪只把同一 _rust bytes 的觀測對回 A6，並驗新建置會隨包；不把 PR 候選當 A12 固定候選或核准再散布。

## 共用來源同步

使用者明確允許必要 hash 連動。以下其他條目只刷新共用目錄 SHA-256，status、選擇器、required_evidence、requires_user_decision 均不變：

`base-wheels-numpy`, `base-wheels-pandas`, `base-wheels-pillow`, `base-wheels-lxml`, `base-wheels-onnxruntime`, `base-wheels-pypdfium2`, `base-wheels-cffi`, `base-wheels-charset-normalizer`, `base-wheels-psutil`.

授權衍生清單 base-closure.json 與 cpu-windows-closure.json 因新原文增加對應；這是既有產生器的輸出同步，不改套件集合、鎖檔或 worker 收集策略。CPU 現有授權上位集合的複製沿用舊管線，不接 A14–A17。inventory、來源索引與 HTML 原文連結一起更新，不重寫其他授權原文。

## 驗證與限制

原 A6 base／cpu gates 重新執行，三旗標皆 false、輸入與計數口徑不變。原文缺失／竄改／錯綁、runtime text／numeric 版本不符、原生檔不同、Linux 觀測冒充 Windows、來源 tag／commit 不符皆有反例。完整混合／獨立模組結果見本目錄 JSON，數字只記 [progress.json](../../../progress.json)。完整本機回歸來源 7125978fde73a3b60df8a38b63f85578c4792098。

首輪 Linux／CPU CI 的授權衍生清單過期問題及修正見 [失敗摘要](first-failure.json)，沒有把失敗改成通過，也不重存舊完整 CI JSON。成功的第一份 Windows 觀測 run／artifact hash／期限在 manifest；最終 head 的所有 CI、公開 metadata、Merge 與 Pages 結果以 PR 21 為準，不能用首輪成功代替。

不改 spec、鎖檔、計數演算法；新原文與觀測資料是使用者已同意的隨包內容變更。ONNX 繁中既有 expected failure、RAM 軟性預算、實體 Windows／GPU／人工驗收限制保留；沒有 Setup／worker／模型交付、Release 或 tag。依使用者順序，A9b 合併後才從最新 main 另開 A11 分支，A11 完成後停，不做 A12。

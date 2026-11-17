# A11 Qt 第三方與替換驗收

A9b 先以 PR 21 合併（9360a54），本輪從該最新 main 的自有新分支作業，PR 22。Windows 首次成功 head 為 `0a1108a304123deac64c1a2f38581128060b0591`，實際 checkout 為 GitHub 暫時 merge `937ce8b43e087fb25c256af1bae1338de9a512a7`，兩者 Git tree 已核對相同。這是 PR 驗證，沒有執行 A12，也不是新固定候選。

- [第三方目錄](../../../../packaging/qt/6.12.0/thirdparty/catalog.json) 保留固定來源、版本依據、原文與 A6 Qt 逐檔對照；[替換測試輸入](../../../../packaging/qt/6.12.0/replacement-input.json) 另釘 wheel 及 DLL hash。
- [Windows 建置觀測](windows-qt-sources.json) 是真正 QLibraryInfo API、shared／debug、Qt／PySide／shiboken 版本及 Core extension SHA。不能用 Linux 觀測冒充。
- [Windows 替換結果](windows-replacement.json) 驗真正 frozen GUI：原版 → 不同 bytes 的 Core 替換 → 移除 Core loader 失敗 → 還原成功。每次成功均核對子程序實際載入路徑／hash，正式 bundle 未變。
- 透過完整公開 metadata 重組／replay，另核對實際基本包的 Qt 逐檔 source／bundled SHA 與 A6 目錄一致，摘要與 metadata hash 見 [CI 引用](ci-reference.json)。
- [原失敗](first-failure.json)：最初控制端在建立隔離環境前匯入未安裝的 app，已本機重現並修復；只保存 run／註記 hash，不重複保存舊嘗試完整 JSON。

## CI 與保存界線

Windows 基本包 run [44155124181](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44155124181) 已 success；其餘同 head 的 Linux、CPU、Microsoft 與歷史索引也全部成功。最終 head 的全 CI、逐項查驗及 Merge 提交統一記錄於 [PR 22](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/22)，避免為補寫完成通知持續重跑打包。

原始日誌、本程式視窗截圖與大型報告留在 CI。Windows reports artifact digest `sha256:bc5ee78095affcd45388932b4054209da61ebf8a03b86c640f467e0ba672771c`，到期 `2026-11-24T19:23:32Z`。本環境無法下載該 artifact 主機，已由公開 check-run annotation 保存必要的小型結果及訊息 SHA；沒有宣稱下載或保存完整 artifact。其他 artifact 引用在 ci-reference.json。

Qt 替換 wheel／DLL／暫存副本均在 reports 目錄之外，不上傳產品。隨包只增加宣告與授權原文；不是把 Qt 原始碼或測試用 wheel 打包。spec、鎖檔、原計數口徑與 A6 固定來源不變。

## 仍待處理

`source-declared` 只指固定發布來源的版本欄位，實際是否編入保持 unverified；來源上位集合包含其他平台宣告。無版本維持 unknown。QLibraryInfo.build 不能證明完整編譯選項／上游修補，Mesa 的精確版本與對應來源仍未知。

只變更 base-qt 的 evidence 與 requires_user_decision=true，status 仍 open，LGPL 做法留 A13 使用者決定。其他條目沒有變更，本輪僅 hash 同步的其他條目為「無」。base／cpu 的三旗標 false，原始 coverage 與計數摘要不改。測試數與完整回歸來源只記 [progress.json](../../../progress.json)。

本驗收是 hosted Windows CI，**不是實體機或乾淨機**；沒有產品交付、Release 或 tag。ONNX 繁中缺口、RAM 軟性預算、Windows／GPU 實機未驗收保持。本輪在 A11 完成後停止，不做 A12。

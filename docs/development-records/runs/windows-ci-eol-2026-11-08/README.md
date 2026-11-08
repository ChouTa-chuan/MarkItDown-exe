# Windows 固定來源換行保護紀錄

2026-11-08（台北），程式 0.14.0、架構 0.4。這次在 Linux 真正執行 Git checkout-index（core.autocrlf=true）重現四份固定 lock／來源契約／原始授權／舊 receipt 被轉為 CRLF，導致 bytes／SHA-256 改變；並非 Windows 應用程式執行證據，也尚未證實是 CI #1 的根因。

.gitattributes 將自有文字設為 LF，第三方 vendor、packaging、開發紀錄、架構快照與原文維持原位元組。沒有重新格式化舊檔。新增測試在獨立暫存 Git repository 加入真實七類檔案，再用 core.autocrlf=true checkout，比對完整 bytes，修正後七類全數保留。來源 ZIP 沒有 .git 也能執行此測試。workflow 另將 .gitattributes 列為建置觸發來源。

工具 21/21、相關 134/134 通過。GitHub 頁面仍反覆 503／504，第二次提交 fda3b7c 已推送，但尚未取到它的實際遠端結果；現有已確認證據仍是 CI #1 原生來源成功、Windows job 失敗。持續保留底層未知，不猜測 Windows 已修好。

C03 3/4、C04 2/4、C09 3/4、完整 7/12、既有 19/25 保留；乾淨機、安裝、人工 UI、GPU 及品質門檻不變。只保存工具與公開合成／工程證據，沒有 runtime binary、模型或憑證加入 Git。

最終完整回歸 **548 項：547 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。

稍後成功讀到公開列表：[CI #2](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42472740347)（fda3b7c）亦失敗，底層診斷頁仍暫時 503／504；此輪換行保護另待新 CI，不增加 Windows 進度。

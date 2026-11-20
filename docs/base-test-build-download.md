# MarkItDown 基本包測試版

這是供試用的測試版，正式版仍待大階段 C 驗收。請先登入 GitHub，從 Actions 執行頁面的 Artifacts 區下載 `MarkItDownBase-test-build`。下載期限為產出後 30 天。

1. 完整解壓 ZIP，在該資料夾開啟 PowerShell。
2. 執行 `certutil -hashfile ".\MarkItDownBase-Setup-0.19.1-windows-x64.exe" SHA256`。比對 `SHA256SUMS.txt` 的同名項目與 `BUILD-INFO.json` 的安裝包 SHA-256。若不一致，先停止安裝。
3. 開啟已核對的 Setup，依畫面提示安裝，完成後從開始功能表啟動。Setup 沒有數位簽章，Windows SmartScreen 會顯示警告。遇到組織的執行限制時請由管理員依規定處理。
4. 移除前先關閉應用程式。在 Windows 11 開啟「設定 → 應用程式 → 已安裝的應用程式」，在 Windows 10 開啟「設定 → 應用程式 → 應用程式與功能」，選擇 MarkItDown 並按「解除安裝」。

本次 Setup 由同一固定來源重建。安裝程式外殼與審閱時可能不同，請以本次 SHA-256 驗證。`BUILD-INFO.json` 記錄來源提交、版本、本次 SHA-256、與審閱時 Setup 是否逐位元一致，以及 `CONTENT-EQUIVALENCE.json` 的 SHA-256。內容對照方式、檢查範圍與生成檔差異見 `CONTENT-EQUIVALENCE.json`。

授權原文隨程式安裝，在安裝目錄的 `_internal/desktop_app/data/licenses/`，實際檔案清單見解壓目錄的 `LICENSE-FILES.json`。解壓目錄也包含 `known-gaps.json`、`known-gaps.md` 與 `test-build-limitations.md`。

回報時請提供版本、Setup SHA-256、Windows 版本、重現步驟與可公開的錯誤資訊。[GitHub Issues](https://github.com/ChouTa-chuan/MarkItDown-exe/issues)

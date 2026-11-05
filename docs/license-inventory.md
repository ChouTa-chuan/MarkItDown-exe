# 授權清單與使用說明：檢核證據

本項檢核交付的是可離線審查的依賴授權清單及開發預覽版操作手冊，不等同正式 Windows 二進位檔已完成法務／發佈審核。Windows 建置、原生檔清單及乾淨機驗收仍保留未完成。

## 清單範圍與來源

Windows CPython 3.12 鎖定檔的 58 個套件全部列入，包括開發／建置工具的上位集合，不表示每個套件都被打包。每個 wheel 先由 pip --require-hashes 下載，再由盤點工具比對版本與鎖定雜湊，保存原始 METADATA、wheel 授權／聲明與來源。

共保存 214 份 notice／metadata／補充來源檔案（其中 149 個原始 wheel 授權／聲明檔）。缺漏的文字從官方固定來源補充，保留 URL、SHA-256 及範圍說明，沒有自行改寫授權。

- Cobble：官方 README 宣告 BSD-2-Clause，作者與套件資料保留；標準 BSD 原文另附，不代填未知作者聲明。
- Magika：標準 Apache-2.0 原文來自固定官方提交，明確不把它宣稱為 wheel 的對應來源版本。
- Qt：wheel 內商業提示原樣保留，另附版本來源 LGPLv3/GPLv3 原文；發佈前仍須落實動態函式庫替換、通知、對應來源等義務。
- CPython：打包時收錄實際使用的直譯器 LICENSE.txt，避免把其他版本原文當成該執行檔授權。
- MarkItDown／測試 PDF：MIT 原文與來源提交保留；Tesseract 模型授權及其固定來源另附。

應用程式本身尚未選定公開發佈授權。Windows 原生 DLL、MS runtime、Qt 最終再散布條件及程式碼簽章仍需在建置後審核。

## 可查閱檔案

- 操作手冊：src/desktop_app/data/user-guide.md。
- 人類可讀清單：src/desktop_app/data/third-party.md。
- 可搜尋 HTML：src/desktop_app/data/licenses/index.html。
- 完整清單、來源與雜湊：src/desktop_app/data/licenses/windows/inventory.json。
- 原文：同目錄各套件資料夾及 supplemental；標準授權、模型及 MarkItDown 原文在 licenses 的其他子目錄。

資料作為套件資源安裝，開發版與 frozen 版都能離線開啟。桌面「說明」選單提供使用說明、第三方授權與開啟完整資料夾。

## 重現與防止遺漏

```bash
python scripts/license_inventory.py --verify
python scripts/license_inventory.py --render
```

新增或更新鎖定依賴後，舊清單會因 lock SHA 不符而驗證失敗。先依 Windows lock 下載且驗證 wheel，再使用 --wheels、--supplements 與新的 --output 目錄產生可審查清單；不覆寫既有目錄。成功才原子提交新目錄，失敗清理暫存。

檢查涵蓋套件集合、版本、wheel SHA、來源檔案完整性及缺漏授權證據；路徑穿越與符號連結聲明檔會拒絕。這是完整性與範圍檢查，不是授權相容性法律認證。

## 驗收條件

1. 58/58 鎖定套件版本與 wheel SHA 覆蓋，214 份文件校驗通過。
2. 手冊涵蓋匯入、輸出、不覆寫、模式、OCR／模型、RAM／CPU、GPU 限制、表格、取消、錯誤與已知品質缺口。
3. 一般套件安裝能開啟手冊、清單與說明選單。
4. frozen 程式能讀取兩份文件、驗證全部 214 個文件雜湊及實際 Python runtime 授權；既有轉換 smoke 不退步。
5. 清單與手冊隨備份保存，沒有以「完成清單」取代 Windows／GPU／安裝包未完成事項。

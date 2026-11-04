# MarkItDown Windows 桌面應用程式

目前為開發中的 Windows 桌面應用程式，已整合 Microsoft MarkItDown 官方原始碼。
原生 Word／Excel／PowerPoint／HTML／文字型 PDF 與 UTF-8 txt/md 已通過 Linux 樣本驗證。
Qt 桌面原型已可操作；Windows 實測、掃描 OCR、自動精準分析及 GPU 尚未完成。

- [產品與架構指引](docs/architecture-guide.md)
- [開發進度](docs/development-status.md)
- [互動進度頁：里程碑／模組架構](docs/progress.html)（可下載後離線開啟）

## 本機開發驗證

需求 Python 3.11+ 與 psutil。專案根目錄執行：

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
markitdown-desktop input.txt output.md --ram-budget-mib 1024 --reserve-mib 2048
```

若已提供 psutil 但無法存取套件來源，Linux 可直接驗證：

```bash
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m desktop_app.cli input.txt output.md
```

完整開發依賴與桌面啟動（專案根目錄）：

```bash
python -m pip install './vendor/markitdown[docx,pptx,xlsx,pdf]' '.[desktop,test-formats]'
python -m desktop_app.desktop
python -m unittest discover -s tests -v
```

Linux 無桌面時以 `QT_QPA_PLATFORM=offscreen` 執行測試。未安裝 GUI／格式依賴時相關測試會明確跳過，不代表整合通過。CLI 可加 `--settings preferences.json` 載入版本化 RAM 設定，命令列參數優先。

目前 CLI 是開發工具。轉換使用獨立 spawn 程序，低優先權與 RAM 回壓；文字可串流，Office/PDF 原生引擎尚不能逐頁協作暫停。等待逾時明確失敗。RAM 為軟性預算，不保證瞬時上限。輸出目的地須支援同磁碟硬連結（例如 NTFS），不支援時明確失敗。Windows 相容性仍須實測。

目前依賴是範圍宣告，尚未完成可重現的鎖定與正式安裝包。上游 MIT 已保留；全部依賴、Qt 打包與未來模型的授權清單尚需完成。

## 更新進度頁

以 `docs/progress.json` 為唯一視覺進度資料來源，更新實際完成項目與驗證證據後執行：

```bash
python scripts/build_progress.py
```

產生的 HTML 不使用外部資源。里程碑進度條採等權檢核，並非工期百分比；模組卡片可切換篩選。可選用 `scripts/check_progress_browser.py` 驗證瀏覽器互動，需要另外提供 Playwright 與 Chromium。

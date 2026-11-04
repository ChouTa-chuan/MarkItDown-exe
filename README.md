# MarkItDown Windows 桌面應用程式

目前為開發中的核心原型，尚未取得或整合 Microsoft MarkItDown 原始碼。
現階段僅支援 UTF-8 txt/md，不含 Office/PDF/OCR/GPU 或 Qt 桌面介面。

- [產品與架構指引](docs/architecture-guide.md)
- [開發進度](docs/development-status.md)

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

目前 CLI 是開發工具，並非最終使用者介面。轉換使用獨立 spawn 程序，串流讀寫、低優先權與 RAM 回壓；等待逾時明確失敗。RAM 為軟性預算，不保證瞬時上限。輸出目的地須支援同磁碟硬連結（例如 NTFS），不支援時明確失敗。Windows 相容性仍須實測。

目前依賴是範圍宣告，尚未完成可重現的鎖定與正式安裝包。上游與模型授權清單待實際取得後建立。

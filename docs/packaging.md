# 建置與可重現環境

Python 3.12 為基線。packaging/requirements-linux.txt 與 requirements-windows.txt 保存套件版本與雜湊，來源為兩個 pyproject 與 packaging/build.in，編譯指令在鎖定檔頭。Linux Qt 要求 glibc 2.34+，不代表所有 Linux 相容。

## 乾淨 Linux 驗證

```bash
python3 -m venv /path/to/clean-venv
/path/to/clean-venv/bin/python -m pip install --require-hashes -r packaging/requirements-linux.txt
/path/to/clean-venv/bin/python scripts/verify_upstream.py
/path/to/clean-venv/bin/python -m pip install --no-deps --no-build-isolation ./vendor/markitdown .
QT_QPA_PLATFORM=offscreen TESSDATA_PREFIX=/path/to/tessdata /path/to/clean-venv/bin/python -m unittest discover -s tests -v
```

不繼承系統 Python 套件。Tesseract、模型及測試字型是原生前置條件，不在 pip 鎖定檔。缺少元件的跳過須與通過分開計數。

## Windows

PowerShell 執行 packaging/build-windows.ps1，檢查 Windows／Python 3.12、建立隔離環境、按雜湊安裝、驗證上游、安裝本機來源、執行測試及 PyInstaller，再以打包執行檔完成文字／PDF 轉換。預期輸出 dist/MarkItDownDesktop。

GitHub Actions windows-build.yml 僅手動觸發，不建立 Release、不推送或發布環境。尚未執行 Windows 流程；保存腳本不等於 Windows 建置成功，需同步儲存庫及 Windows 執行器。

這是開發用資料夾執行檔，尚非安裝精靈，未簽章、未乾淨 Windows 驗收，也未包含 OCR 原生元件及模型。發佈前須完整依賴授權、Qt LGPL、OCR 及模型再散布檢查；目前 notice 不是完整合規清單。

## 當前平台打包

```bash
python -m PyInstaller --noconfirm packaging/desktop.spec
python scripts/smoke_frozen.py dist/MarkItDownDesktop/MarkItDownDesktop
```

spec 蒐集 Magika 模型、MarkItDown 子模組及 metadata；Linux 產物不能當成 Windows EXE，也不能證明顯卡相容性。

OCR 模型來源及雜湊清單隨套件保存在 desktop_app/data/ocr-models.json，不再依賴原始碼目錄的 docs。打包驗證會呼叫執行檔的開發檢查模式，確認該資源可讀取；模型本體仍由使用者在模型管理視窗明確啟動下載。

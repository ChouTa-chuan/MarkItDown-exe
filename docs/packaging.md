# 建置與可重現環境

以下為現有開發 profile。新版 [架構指引 v0.4](architecture-guide.md) 已採「基本安裝包＋選配元件管理」；C05 已完成簽章／下載服務，但基本 Tesseract native、分離選配 worker、profile 拆分與相依授權仍待實作，不能把現有 ONNX 開發包當成已完成的新基本版。

程式 0.3.0 將既有鎖定版本的 cryptography 50.0.2 明確列為 Ed25519 驗證依賴；兩平台套件版本與雜湊不變，授權 inventory 的鎖定檔摘要已更新。這不等於 C04 profile 拆包完成。

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

PowerShell 執行 packaging/build-windows.ps1，檢查 Windows／Python 3.12 x64、重新建立受管理的 .venv-build 隔離環境、按雜湊安裝、驗證上游及授權、安裝本機來源、執行測試及 PyInstaller，再以打包執行檔完成轉換與內建自我檢查。預期輸出 dist/MarkItDownDesktop；勿將個人資料放在受管理的 .venv-build、build、dist 目錄。

GitHub Actions windows-build.yml 僅手動觸發，不建立 Release、不推送或發布環境。預設還會編譯 Inno Setup 預覽安裝包，安裝、驗收並解除安裝，保存報告；尚未實際執行 Windows 流程。詳見 [Windows 驗收流程與待辦](windows-acceptance.md)。

目前只有已驗證的 Linux 資料夾執行檔，以及未經 Windows 執行的安裝精靈來源。未簽章、未乾淨 Windows 驗收。ONNX 模型隨選配套件打包；Tesseract 原生元件未整合，Tesseract 模型由模型管理下載。58 套件授權清單已驗證，但最終 Windows 原生二進位／Qt 發佈義務仍須在建置後審核。

本機 Windows 需 Inno Setup 6.3+，加 `-BuildInstaller` 產生預覽 Setup.exe；預設每位使用者安裝，不需系統管理員。每次建置的獨立報告位於 dist/reports/build-*；檔案雜湊清單不能取代數位簽章。

## 當前平台打包

```bash
python -m PyInstaller --noconfirm packaging/desktop.spec
python scripts/smoke_frozen.py dist/MarkItDownDesktop/MarkItDownDesktop
```

spec 蒐集 Magika 模型、MarkItDown 子模組及 metadata；Linux 產物不能當成 Windows EXE，也不能證明顯卡相容性。

OCR 模型來源及雜湊清單隨套件保存在 desktop_app/data/ocr-models.json，不再依賴原始碼目錄的 docs。打包驗證會呼叫執行檔的開發檢查模式，確認該資源可讀取；模型本體仍由使用者在模型管理視窗明確啟動下載。

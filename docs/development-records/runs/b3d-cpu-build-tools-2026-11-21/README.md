# B3d：CPU worker 建置工具查證

## 固定候選逐檔結果

以 A13b 固定 Windows CPU 候選 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c` 為準。GitHub Actions 讀取原始 run 的完整 `bundle-provenance.json`，比對原檔 SHA-256，再核對完整實體檔案清冊、PYZ 來源模組清冊與 `base_library.zip` 清冊。只保存查證範圍逐檔結果。資料包含實體路徑、位元組大小、SHA-256 和候選記錄的 owners，並另以 repo 內 Windows wheel 清冊與實體 bytes 對照授權目錄複本，補上來源套件、版本及 wheel SHA-256。[固定候選審閱](../a13b-fixed-review-2026-11-18/cpu-source-review.json) · [原始清冊節錄](original-cpu-build-tools.json) · [授權複本逐檔來源](repo-notice-sources.json)

| 套件 | 固定候選的實際內容 | 執行用途 |
| --- | --- | --- |
| setuptools 84.2.1 | 實體包有 METADATA、原文和其複本。另有 vendored `packaging/licenses/__init__.py` 與 `_spdx.py` 兩個實體檔，位於授權資產目錄。 | 固定候選的 PYZ 與 `base_library.zip` 沒有 setuptools、`pkg_resources`、`_distutils_hack` 或 `distutils` 模組。兩種 `.py` 仍存在於檔案系統的授權資產路徑。 |
| pip 25.0.1 | `installed/pip` 下有 METADATA 和原文。 | pip 在建置機安裝相依。固定候選的實體檔案沒有 pip 命令或模組，兩個 Python 成員清冊也沒有 pip／ensurepip。 |
| PyInstaller 6.22.3 | `MarkItDownOCRWorker.exe` 的來源列同時綁 PyInstaller 與自有 worker；另有 METADATA、原文及 bootloader 原文。 | bootloader 與封存啟動程式負責啟動凍結 worker。固定候選的 PYZ 與 `base_library.zip` 沒有 PyInstaller 的建置／打包套件。 |
| PyInstaller Hooks Contrib 2026.9 | 有原文、複本和 METADATA。 | 固定候選的 PYZ 與 `base_library.zip` 沒有 `_pyinstaller_hooks_contrib` 模組。個別啟動程式另見 Windows 重建的 CArchive。 |

固定完整報告的 SHA-256 為 `da7857f5a315347c4c65e3a35a49f882c19e3c34ebbba055c7fa8434b93eecce`。報告同時記錄 build 環境套件清單，該清單不能單獨用來判斷套件程式碼是否入包。實際判讀按實體檔案、PYZ 純模組來源、base_library 成員，以及下一節獨立比對的 CArchive 啟動層進行。

## Windows 啟動、資產讀取與限制

用 A13b 固定提交、原 spec 與雜湊鎖檔在 hosted Windows 2022 重建可丟棄的 worker。檢查其 EXE CArchive 啟動程式的來源、大小和 SHA-256，讀取實際 PYZ 名稱，不執行反組譯的 code object。另在空 PATH 下由實際 frozen worker 完成專案公開的 health 圖片和一般 OCR，兩者均使用 CPUExecutionProvider。重建後的純模組來源清冊 SHA-256 與原候選一致。逐名比對實際 PYZ 時，清冊裡只有 CPython 的 `struct` 位於外層 CArchive，符合 PyInstaller 的 bootstrap 規則。外層另有 PyInstaller loader 與 runtime hooks，以及自有 worker 入口。沒有 setuptools、pip 或 Hooks Contrib 的啟動腳本。重建 EXE 的 SHA-256 與原候選不同，兩者指紋和逐項清冊見報告。[Windows 重建結果](frozen-runtime.json)

worker 的啟動與 OCR 路徑使用 PyInstaller loader，以及 CPython、ONNX Runtime 和 OCR 相關套件。即使工具程式碼不存在，`verify_assets()` 仍會按隨包的 `installed-manifest.json` 讀取並驗證清單中的原文／METADATA。Windows 重建報告列出這些與原候選同 SHA-256 的資產。這就是移除原文或 METADATA 時需要同步重建清冊並重新驗收的原因。原候選未發布 EXE，只有逐檔原始報告可重驗。重建證據僅適用於註明的範圍，沒有聲稱對原 EXE 作逐位元重驗，也沒有實體機驗收。[worker 資產準備](../../../../scripts/prepare_worker_assets.py) · [worker 執行路徑](../../../../src/desktop_app/component_workers/server.py)

## B3 可能的精簡

A4 曾對基本包的 Analysis 排除實際被收進來的 setuptools 模組。這次固定 CPU 候選的兩個 Python 模組清冊沒有相關程式碼，現階段沒有依據複製 A4 的 spec 排除。若使用者於 B3 同意精簡，先盤點建置用套件的重複資產及被授權選取規則帶入的 `.py`，再調整授權資產管線和對應 manifest。PyInstaller 啟動器與其原文需按實際分發內容留存。變更後應核對原文歸屬、重建候選清冊與雜湊、重跑 Windows health／OCR／生命週期及 gates。是否刪減與相應授權做法交使用者確認。[A4 排除證據](../a4-setuptools-audit-2026-11-16/README.md)

## 重驗與 CI 來源

- 原始 CPU CI [44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417)，報告 artifact `windows-cpu-validation-reports`（ID `14424905894`），digest `sha256:8f38a60b9473ea915879d62adedd4dfc3b0a91ac9b1c5db3e7473ea51b89692e`，台北時間 2026-11-25 19:43 到期。工作環境直接下載在 GitHub 報告儲存站被拒。GitHub Actions 原生下載器於 [44782434625](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44782434625) 取得並核對。精簡結果的 canonical JSON SHA-256 見 manifest。
- [Windows 重建與封存對照 run 44783968301](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44783968301) 使用 `7ca45c3` 的觀測程式，從 `b17d51bc` 建置。只以 GitHub checks 註記保存證據，沒有上傳 EXE 或另外建立 artifact。
- 前序擷取 run `44781803704`、`44782043306`、`44782223588` 未產出可用結果，修正 canonical 編碼與註記輸出後由成功 run 取代。Windows 試跑 `44782915760` 的長註記被截斷，`44783498128` 已用分段保存，但尚未逐名解釋 `struct` 的位置差異。
- 原始完整報告可用時，執行 `python scripts/cpu_build_tools_audit.py --provenance <bundle-provenance.json> --output <新檔>`。後續可用 `--repo-copies <original-cpu-build-tools.json>`，以保存的 wheel inventory 核對同位元組 repo 複本。Windows 重建可用 `scripts/cpu_build_tools_runtime.py` 重讀 CArchive 並重跑樣本。受檢的歷史 Windows 暫存 EXE、模型、wheel 與原始日誌均未加入 repo。
- B3d 的 base 與 cpu gates 都 exit 0。CPU `cpu-archives` 連結上上述證據，仍為 open，因整體封存來源與原文盤點尚未結案。CPU 四旗標仍為 false。Linux 混合與獨立模組完整回歸見[進度資料](../../../progress.json)。

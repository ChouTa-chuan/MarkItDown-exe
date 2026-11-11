# 隨包原文與原生來源追溯

基本安裝包與CPU選配共用建置來源保存方式。這一層協助開發者確認「檔案來自哪個建置套件、隨包原文是否仍完整」，後續更新元件時也能比對差異。

| 資料 | 基本包位置 | CPU worker位置 |
| --- | --- | --- |
| 實際套件METADATA與原文 | `_internal/desktop_app/data/licenses/installed/` | `_internal/worker-assets/installed/` |
| PyInstaller啟動器原文與hash | `_internal/desktop_app/data/licenses/bootloader/` | `_internal/worker-assets/bootloader/` |
| CPython原文 | `_internal/desktop_app/data/licenses/python-runtime/` | `_internal/worker-assets/python-runtime/` |
| Analysis原生來源指紋 | `_internal/desktop_app/data/licenses/native/manifest.json` | `_internal/worker-assets/native/manifest.json` |

`prepare_base_assets.py`與`prepare_worker_assets.py`從實際安裝環境複製原文；`build_provenance.py`保留啟動器原文及distribution來源對照。原生manifest的schema2增加來源SHA-256、大小與可確認的套件名稱／版本，路徑統一以`/`保存。未知來源保持未知，不以DLL名稱猜授權。

PyInstaller完成後，兩條Windows CI執行`check_bundle_provenance.py`，報告寫入各自reports目錄的`bundle-provenance.json`。腳本失敗會停止該次建置驗收。報告要寫在bundle外的新位置，避免把檢核結果混入產物或覆寫舊證據。

```powershell
python scripts/check_bundle_provenance.py --profile base --bundle out/windows/dist/MarkItDownBase --report out/manual-reports/base-provenance.json
python scripts/check_bundle_provenance.py --profile cpu --bundle out/windows-cpu/dist/MarkItDownOCRWorker --report out/manual-reports/cpu-provenance.json
```

執行時使用相同來源的建置環境與目前pyproject版號。這些是開發檢核命令，使用者安裝程式時不需要Python或手動操作。

報告的`accepted`只表示這次追溯一致性檢查通過：原文指紋、METADATA版號、啟動器原文及Analysis所列收集檔案符合檢查條件。`source_sha256`與`bundled_sha256`分列；PyInstaller可能處理原生檔案，`bytes_changed`會顯示差異，仍需依建置工具與來源進一步審閱。根EXE另外保存hash。

`packages_without_wheel_notice`保留wheel內缺原文的套件，不能解讀為無授權義務。CPU套件表記錄build環境，並非所有套件都進入runtime。`redistribution_approved`與`release_ready`維持false；完整runtime SBOM／逐項內容審閱、各套件與原文對照、Qt替換與對應來源、Microsoft原生runtime再散布及應用公開授權仍須獨立完成。此腳本不執行EXE，也不代表Windows乾淨機或人工驗收。

目前完整原生報告由CI保存七天，專案紀錄保存可取得的公開摘要與來源；未下載的登入artifact不宣稱永久備份。實際驗證與初輪問題見[開發紀錄](development-records/runs/bundle-provenance-ci-2026-11-11/README.md)。

候選報告schema2已新增全部普通檔案快照與CPU實際ZIP檢核，欄位與可信舊報告重驗命令見[候選包完整檔案清單](candidate-inventory.md)。

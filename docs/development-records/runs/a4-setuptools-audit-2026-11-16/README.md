# A4：setuptools 匯入來源與基本包排除驗證

2026-11-16（台北），程式／架構版號不變。程式與測試來源為 `8c2645156babedbb8152f1113017366997cf3fb0`；後續 `653ed8e` 只合入已合併 PR 6／7 的文件與 Claude 設定，`src`、`scripts`、`tests`、`packaging`、驗證流程與受測提交相同。回歸總數與里程碑以 [progress.json](../../../progress.json) 為單一現況來源。

## 原因與處理

- 在同一個鎖定版本的完整開發 Linux venv，以 `packaging/desktop_entry.py`、基本包的 hidden imports／excludes 重建前後兩份 PyInstaller Analysis；這組匯入圖實驗不等於隔離基本 profile 的建置。`urllib3.response` 與 `urllib3.util.request` 的選用 `backports.zstd` 匯入，經 `hook-backports.py` 指向 `setuptools._vendor.backports`；PyInstaller 進一步收集父套件 setuptools，及其 vendored jaraco、distutils 編譯器。具體入邊、型別、版本與前後清單 hash 見 [import-audit.json](import-audit.json)。這是實際 Linux 匯入圖，未假稱 Windows 匯入圖也已逐邊驗過。
- 原有 unknown 是沒有 `__init__.py` 來源檔的 namespace，不是遺失的普通檔案。保留原有分類規則，不按名稱改列已知套件。基本包不安裝或編譯 Python 套件，故在 Analysis 排除 setuptools；建置環境的 setuptools 及其原始授權／鎖定不刪除，CPU 元件不改。
- `base.spec` 與建置後 `check_bundle_provenance.py` 都拒絕基本包的 setuptools 根／子模組。公開 CI 小結新增 `python_archives.build_only_modules_absent`；只在基本包通過隨包清單檢查後設 true。它代表模組清單符合排除規則，不是完整 SBOM 或再散布核准。
- 本機 Linux 基本包真正建置成功；直接讀取 EXE 內嵌 PYZ，沒有 setuptools 模組，也沒有 `pyi_rth_setuptools`。凍結程式在空 PATH、沒有 checkout PYTHONPATH 下，通過既有核心、說明資產、格式轉換與「缺少原生／選配 OCR 時應失敗」驗收。這次故意使用無原生 OCR 的 core profile，完整自檢退出失敗是既有預期，不能當四語原生 OCR 已驗。
- 新增反例涵蓋 namespace／一般套件、相似名稱不誤擋，以及重算資產 hash 仍無法把 setuptools 放回基本包；CPU fixture 保持可接受。完整混合回歸與獨立模組的原始小型結果見 [mixed-result.json](mixed-result.json)、[isolated-summary.json](isolated-summary.json)；凍結驗收見 [frozen-acceptance.json](frozen-acceptance.json)。

## 執行方式

先按 `packaging/profiles/base-linux-build.txt` 的固定版本與 SHA-256 建立隔離 venv，再以 `--no-deps --no-build-isolation` 安裝本地 vendor 與專案。不要將完整開發 venv 當成基本包建置環境。

```bash
# out 應是本輪全新的目錄；既有驗證輸出不覆寫。
python scripts/prepare_base_assets.py --output out/base-assets
MARKITDOWN_BASE_ASSETS="$PWD/out/base-assets" python -m PyInstaller --noconfirm \
  --workpath out/build --distpath out/dist packaging/base.spec
# 合成文件由完整測試 venv 準備（內含 python-docx、reportlab），再真正執行基本包。
python scripts/check_base_profile.py --prepare-fixtures --fixtures out/fixtures
python scripts/check_base_frozen.py --executable out/dist/MarkItDownBaseCore/MarkItDownBaseCore \
  --fixtures out/fixtures --output out/frozen-checks
# 完整測試環境另設 PYTHONPATH=src:tests、QT_QPA_PLATFORM=offscreen、固定四語 TESSDATA_PREFIX，
# 並把 OMP／OpenBLAS／MKL 執行緒設為 1；N 取 linux-regression.yml 的 EXPECTED_TESTS。
python scripts/run_mixed_regression.py --expected-count N --output out/mixed-result.json
python scripts/check_isolated_tests.py --expected-count N --output out/isolated
```

實際本輪的暫存工作目錄為 `/tmp/markitdown-a4-audit`；完整本機建置／回歸日誌及產物留在該目錄，隔離基本 venv 在 `/workspace/markitdown-a4-base-venv`，不承諾環境更換後仍存在。repo 只保存必要的小型結果及 hash，不提交 EXE、模型或大型日誌。本輪未有 A4 GitHub CI run 或 artifact，沒有可列的 CI artifact hash／到期日。

## 原始失敗與限制

- 第一次匯入圖匯出在 Analysis 完成後遇到 `getReferers()` 含 `None` 而發生 `AttributeError`，程序 exit 1；過濾空 referer 後重跑 exit 0。這是一次性分析腳本錯誤，沒有修改第三方工具。
- 第一次準備資產時使用 `PYTHONPATH=src`，讀到 pip 建置留下的本機 egg-info，因缺 METADATA 而 exit 1；移除該命令的 PYTHONPATH，使用實際安裝 wheel 的隔離環境後 exit 0。沒有繞過獨立建置環境檢查。
- 初次套件下載在正常沙箱無法連到環境代理；保留相同代理與 TLS，經允許的命令升權重試安裝成功。全部仍使用雜湊鎖定。
- GitHub CLI 的 GraphQL 請求回覆 `Forbidden`；目前沒有可用 GitHub 連接器，環境有效主機清單沒有 `api.github.com`。本次只能推送自己的 Git 分支，尚未建立 PR、未執行 A4 Windows CI，也沒有合併。[PR 說明稿](PR_BODY.md)已保存，工具恢復後可直接使用；它不是已建立的 PR。
- A4 的 Windows 排除效果仍須 PR CI 確認（公開 `unknown_names` 與 `build_only_modules_absent`、原生建置及既有自動驗收）。Linux core 成功不取代原 Windows 候選、四語 OCR、乾淨機、人工或 GPU 驗收；runtime SBOM／再散布／發行旗標維持未完成。

[返回歷史索引](../../../history-index.md)

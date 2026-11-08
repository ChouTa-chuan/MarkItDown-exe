# Windows 原生來源與 DLL 檢查

程式 **0.11.0**、架構 **0.4**。本輪完成 C03 原生來源的**靜態檢查機制**，包括實際候選檔核對與封裝阻擋；C03 的「Windows 固定原生引擎／DLL、來源與授權」仍未驗收，C03 維持 **1/4**，完整導入 **7/12**。

## 模組責任

| 層 | 責任 |
| --- | --- |
| `packaging/native/tesseract-windows.json` | 固定官方安裝程式、原始碼提交、56 個候選 runtime 與三份說明／授權原文的 SHA-256 和大小；只提供待審候選來源 |
| `src/desktop_app/native_assets.py` | 有界讀取、拒絕連結／大小寫衝突、解析 AMD64 PE32+ import／delay-import、入口閉包與逐檔授權證據缺口；不載入 DLL 或執行 EXE |
| `scripts/check_windows_native.py` | 離線檢查報告、可選發布頁 digest 及 objdump 獨立比對；要求再散布時回傳失敗 |
| 既有 profile／自檢 | 基本包仍標記缺少 native OCR，full 自檢保持失敗；沒有接入候選 binary |

固定來源為 [Tesseract 官方 5.5.3 release](https://github.com/tesseract-ocr/tesseract/releases/tag/5.5.3)，資產 `tesseract-ocr-w64-setup-5.5.3.20260724.exe`，26,573,224 bytes，SHA-256 `bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4`。發布 digest 與下載檔一致；原始碼 tag 解參照到 `db0ec62f81b0737fbbe184d8fea40af5738f8eef`，不代表所有第三方 DLL 已對應到確切建置來源。

在 Linux 僅使用官方 7-Zip 26.06 解開 NSIS，未執行安裝程式。安裝器 bootstrap 本身是 x86；真正候選 payload 為 **56 個 AMD64 PE32+（1 EXE＋55 DLL）**，合計 97,632,889 bytes。入口可達閉包 **34 個檔案**，其餘 **22 個**未在靜態 import 閉包中使用，不能據此宣稱動態載入永遠不需要它們。入口與主 DLL 的 import 另與系統 objdump 核對一致。

## 授權與封裝門檻

已保存來源內的 `doc/LICENSE`、`doc/AUTHORS`、`doc/README.md` 原文與 hash。Tesseract Apache 原文只映射已確認的主程式與 `libtesseract-5.dll`；可達閉包的其他 **32 個 DLL** 尚缺專案可追溯的逐檔來源、版本及原授權證據。這表示我們的證據尚未補齊，不是指控上游檔案沒有授權，也不能只根據檔名猜測授權或版本。

目前 `require_bundle_permission()` 一律拒絕此待審契約；修改 JSON 報告的 `bundle_allowed` 或 `redistribution_approved` 不能繞過。未來需新增明確的已審來源契約與對應整合，不能把此旗標當核准流程。檢查報告的 `accepted` 只表示靜態檢查機制成功，`bundle_allowed`、`native_ocr_bundled`、`full_c03_complete`、`windows_executed` 都維持 false。

PE 系統 DLL 清單與 API-set 判斷只是靜態分類，未驗證 Windows 機器上這些 DLL 的存在、載入或 ABI；沒有驗 Authenticode、執行 OCR 或量測 Windows／GPU 負載。讀取上限為單檔 128 MiB、runtime 合計 512 MiB；這與使用者 RAM 軟性預算不同。

## 使用方式

先由開發者從固定官方來源取得安裝程式、以可信解包工具解到獨立目錄；以下只檢查，不會下載或執行 Windows 程式。每次報告須使用新檔名。

```bash
python scripts/check_windows_native.py \
  --installer /path/tesseract-ocr-w64-setup-5.5.3.20260724.exe \
  --directory /path/extracted \
  --report /path/inspection.json
```

正確候選檔靜態檢查退出碼為 0，但仍不可封裝。另加 `--release-metadata /path/expanded-assets.txt --objdump /usr/bin/objdump` 可重做發布 digest／獨立 import 比對；不加這兩項時不宣稱驗證它們。加 `--require-redistribution` 則必須以退出碼 **1** 阻擋，報告仍保存檢查與缺口。

本輪新增 **20 項**來源／PE 反例，含相關 profile、診斷及授權回歸 **64/64**；真實來源另 **7/7** 靜態檢查，全專案 **478 項：477 通過、1 既有 ONNX 繁體品質預期失敗**。[原始頁面、來源原文與全部檢查紀錄](development-records/runs/c03-native-static-2026-11-08/README.md)可追溯；大型 installer／EXE／DLL 不加入 Git。

## 接續工作

補齊可達 DLL 的確切版本、來源與原授權／義務對應，或評估只保留 PNG／zlib 等必要能力的最小原生建置，降低依賴負擔；兩者都需要新的證據，不能直接推定可再散布。來源審查完成後，才整合四語基本包、離線自檢，再於 Windows 實際建置、測試中文路徑、掃描、乾淨機安裝／移除。C04 維持 2/4、C09 維持 3/4，Windows／GPU、ONNX 繁體品質與 RAM 軟預算限制保留。

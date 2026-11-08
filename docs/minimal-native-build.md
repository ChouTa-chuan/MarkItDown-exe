# 最小 Windows OCR 候選與來源準備

> 本頁保存 0.12.0 來源準備；0.13.0 已接續[內含四語基本包](bundled-base.md)，C03 為 3/4。Windows 候選仍未執行，原先來源證據與限制保持。

程式 **0.12.0**、架構 **0.4**。完成 C03「固定原生引擎／必要相依、來源與授權原文準備」子檢核，範圍為 **Linux 離線交叉建置與靜態／來源驗證**。C03 **1/4 → 2/4**，完整導入仍 **7/12**、既有 **19/25**；沒有 Windows OCR、完整基本包或發行驗收。

## 為何另建最小候選

0.11.0 官方 installer 候選的 32 個可達 DLL，仍缺本專案可追溯的確切套件／原文對應。固定上游 `nsis/build.sh` 使用即時 `pacman -S`、沒有鎖定全部套件版本；補上各專案最新 LICENSE 不能證明符合那批 DLL。因此保留[舊候選的檢查與阻擋](windows-native-intake.md)，另從固定原始碼建立最小候選，不把舊缺口改成通過。

目前 PDF OCR 在 Python 端逐頁渲染及正規化後，以暫存 `page.png` 送入 Tesseract。因此本候選保留 PNG／zlib，關閉額外影像編碼器、網路／封存、ScrollView、訓練與 legacy engine；Leptonica 仍有內建 BMP／PNM 等程式碼，並非宣稱每個內建格式都已驗收。Office／PDF 格式判斷與渲染仍由原核心負責。

## 固定來源與模組責任

| 來源／模組 | 版本與責任 |
| --- | --- |
| Tesseract | 5.5.3，固定 `db0ec62f81b0737fbbe184d8fea40af5738f8eef`；LSTM CLI 與核心 |
| Leptonica | 1.87.0，固定 `13275a278eb55b5746e33f95fbf5a2c8f604b3ab`；PNG 影像處理 |
| libpng | 1.6.59，固定 `cd952f49f95bb27154ae77dbb103032d95f6e580`；PNG 解碼 |
| zlib | 1.4，固定 `99623ef7097352da7993ba614161fd6a311e046e`；PNG 壓縮資料 |
| LLVM-MinGW | 官方 20261104 UCRT Linux x64 工具；發布 SHA-256 與下載一致，LLVM 23.1.5／固定 MinGW runtime 來源與原文另記 |
| `packaging/native/minimal-windows.json` | 四份 commit 原始碼封存檔、工具鏈的 URL／SHA-256／bytes、21 份原文／來源文字及限制 |
| `packaging/native/minimal-notices/` | 四項直接來源原授權、作者、LLVM／MinGW runtime 原文與工具鏈固定建置腳本；不覆蓋原 221 份授權資產 |
| `scripts/build_minimal_native.py` | 不連網的開發建置工具：驗來源、私有目錄有界解包、依序靜態建置、來源／實際設定／linker 檢查及候選 receipt |

四份原始碼由官方固定 commit URL 取得，保存 SHA-256／大小；工具鏈保留官方發布 digest。CMake **3.31.6** 與 Ninja **1.11.1.4 wheel** 是開發主機工具，獨立 venv 安裝、不加入產品依賴；Ninja 實際版本字串 `1.11.1.git.kitware.jobserver-1` 另核對。下載來源、工具 wheel hash 與建置紀錄見[本輪紀錄](development-records/runs/c03-minimal-source-2026-11-08/README.md)。

## 建置契約

只接受新工作目錄，失敗產物／日誌不覆寫。先驗全部輸入，再複製到新目錄重驗，避免驗完外部路徑後讀到替換檔；單一來源上限 128 MiB，封存最多 12,000 筆／768 MiB 解包大小，採 Python data filter 阻擋逃逸連結及特殊檔案。相依按 zlib → libpng → Leptonica → Tesseract 建置，Windows include／library 僅從隔離 prefix／工具鏈取得。並行數 1–4、預設 2；這是開發工具限制，與程式的 RAM 軟性預算分開。

本輪處理的相容事項均寫入 recipe：zlib 1.4 靜態庫為 `libzs.a`；以真實 Windows 連結探針判斷函式，避免只編 archive 造成 `open_memstream` 誤判。Tesseract 的 TIFF `try_run` 以 **1（不可用）**預置，因 Leptonica 明確停用 TIFF，沒有執行或偽造 Windows 測試；並驗生成標頭。libc++ 以 `-include string -include cstdlib` 補標準標頭，沒有修改上游程式。Linux 的 `Ws2_32` 大小寫問題，透過從固定工具鏈複製相同 bytes 的 import archive 別名處理；不是下載或加入 DLL。

Leptonica 在 MinGW 下會將靜態 archive 命名成 `libleptonica-1.87.0.dll`；已核對為 ar archive，最後靜態連入 EXE，不以副檔名誤判為需要散布的 DLL。libpng 的安裝別名也保留實際 linker 名稱／hash 對應。

CMake／Ninja 路徑為開發者明確指定的可信主機工具；此腳本不是執行任意不可信編譯器的隔離沙箱。

```bash
python scripts/build_minimal_native.py \
  --inputs /path/fixed-archives \
  --work /path/new-build-directory \
  --cmake /path/build-venv/bin/cmake \
  --ninja /path/build-venv/bin/ninja \
  --jobs 2 --report /path/new-report.json
```

`--inputs` 放入契約內五份原始碼／工具鏈封存檔，檔名、大小與 hash 均須一致；本命令不會下載。成功候選在工作目錄 `candidate/`，包含 EXE、原文與來源 receipt；大型 binary 不加入 Git。沒有切換既有主程式 profile／spec 或使用者引擎設定。

## 驗收與限制

新增 **22 項**來源、原文、解包、linker／PE／設定反例，含既有 native／profile／診斷／授權回歸 **86/86**；真實空目錄離線交叉建置及獨立靜態／來源驗證 **8/8**。全專案 **500 項：499 通過、1 既有 ONNX 繁體品質預期失敗、0 跳過**。

最小入口是單一 AMD64 PE32+ EXE，靜態 import／delay-import 沒有第三方 DLL；14 個 Windows 系統／UCRT import 名稱另與 objdump 核對。26 個 linker 輸入檔及實際 member 記錄均對應到四個固定來源或工具鏈；不是只看傳給 CMake 的 OFF 字串。原始標頭與候選原文另以 hash 核對。完整 binary hash／bytes 見實際報告，不以來源鎖定宣稱跨主機逐位元組重建一致。

來源與原文準備完成，不代表已核准產品再散布。`redistribution_approved`、`release_ready`、`native_ocr_bundled`、`windows_executed` 均為 false，修改資料旗標無法變成封裝核准。未驗 Authenticode、Windows API／UCRT 實際載入、動態載入、掃描 OCR／一般準確率、中文路徑、Windows 建置／安裝與 GPU；新候選也沒有替代既有 Linux 四語品質證據。

下一步是把此來源候選接進四語基本包 profile、離線引擎／模型設定與完整自檢，再用 Windows 實際建置及乾淨機驗收，接續 C03 剩餘兩項、完整 C04／C09／C11。Windows 安裝包仍須在 Windows 建置驗證；ONNX 繁體缺口與 RAM 軟預算限制保留。

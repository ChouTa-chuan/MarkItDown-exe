# 候選包完整檔案清單

基本包與CPU選配沿用隨包追溯檢查，在`bundle-provenance.json`增加`candidate_inventory`。清單列出候選目錄內全部普通檔案的相對路徑、大小、SHA-256、角色、可確認的套件版號及原文路徑。隱藏檔、空檔案也列入；連結、junction、特殊檔、大小寫別名、讀不到的目錄及超過上限的輸入會使檢核失敗。

| 報告欄位 | 內容與限制 |
| --- | --- |
| `candidate_inventory.files` | 完整普通檔案快照，逐檔大小與hash；檢核後立即再列舉重驗 |
| `owners` | 已安裝RECORD的目的路徑與檔案hash都相符，或既有Analysis／METADATA／原文來源證據；證據類型逐項標記 |
| `packages` | 保存原METADATA hash、版號、原樣授權宣告及原文位置／hash；CPU此表仍為build環境範圍 |
| `notice_paths` | 已保存在包內的原文路徑，不代表該文字涵蓋所有再散布義務 |
| `review_reasons` | 未知來源、缺原文、原生轉換差異、Microsoft runtime及尚未展開的archive成員等待查事項 |
| `file_inventory_complete` | 這次普通檔案快照完整；不等於來源與授權審查全部完成 |
| `runtime_sbom_complete`／`redistribution_approved`／`release_ready` | 保持false；來源缺口、完整runtime SBOM與再散布另行處理 |

`source_sha256`與`bundled_sha256`保留差異。Windows runtime可能來自Python或wheel所在目錄，VCRUNTIME／MSVCP等檔案另列再散布待查，不能因位置而套用Python授權。壓縮檔本身會列入逐檔hash，內部Python模組成員尚未展開，不宣稱runtime SBOM已完整。

CPU管線先產生元件ZIP，再以`--package-directory`驗證實際ZIP，報告新增`package_inventory`：包含額外的`NOTICE.txt`，核對component描述的全檔清單、大小與hash、ZIP每項內容與CRC，拒絕缺項、多項、重複、連結或變更。壓縮包SHA-256與descriptor SHA-256也保存；沒有把「目錄清單通過」當作ZIP已驗證。

```powershell
python scripts/check_bundle_provenance.py --profile base --bundle out/windows/dist/MarkItDownBase --report out/review/base-first.json
python scripts/check_bundle_provenance.py --profile cpu --bundle out/windows-cpu/dist/MarkItDownOCRWorker --package-directory out/windows-cpu/package --report out/review/cpu-first.json

# 交付或保存前，使用可信的既有報告重驗同一個候選，拒絕增刪、改名或任何byte變更。
python scripts/check_bundle_provenance.py --profile cpu --bundle out/windows-cpu/dist/MarkItDownOCRWorker --package-directory out/windows-cpu/package --verify-inventory out/review/cpu-first.json --report out/review/cpu-second.json
```

報告必須寫在bundle外的新位置，不能覆寫舊證據。重驗報告是核對基準，須先確認其來源／SHA-256；重驗不是數位簽章或正式更新信任根。一般使用者不需執行這些開發命令。

完整逐檔JSON由CI artifact暫存七天；兩條管線會另外輸出有界的公開摘要，保存檔案數、待查數、報告hash及CPU ZIP hash，方便同步開發紀錄。未下載的完整登入報告仍不宣稱永久保存。

程式0.19.1／架構0.4，這次只更新建置檢核。完整候選內容審閱、應用公開授權、Qt對應來源／替換、Microsoft原生再散布及乾淨機／人工仍待完成。歷次原文及模型不修改；技術清單不直接提高C04／C11或產品發行進度。

基本包在安裝、升級及續修測試完成後才產生最後快照，包含安裝封裝新增的`base-install-catalog.json`；清單檢核通過也是整條流程接受的必要條件。清單範圍為基本包候選目錄，Setup本身另由既有安裝報告保存hash與驗收證據。

[Windows最終實證](development-records/runs/candidate-inventory-ci-2026-11-11/README.md)：cb8f24d基本包1655檔、CPU bundle741／ZIP742檔接受，ZIP含額外NOTICE，兩份快照重驗通過。來源未對照檔案基本154、CPU303項，完整runtime SBOM與再散布保留待查；683通過／1既有品質預期失敗，完整684項與43模組exit0。

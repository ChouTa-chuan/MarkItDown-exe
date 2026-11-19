# B1b 固定候選逐檔對照

Hosted Windows 用固定來源 `b17d51b` 重建並驗收安裝包。從 GitHub Actions run 44295039865 的 `windows-base-validation-reports` 取出原始 provenance，核對原件 SHA-256 `b7fa49e6df55b2a72026fa2c82ce56624cd823e1f7aebce1a62da59b2272657b` 後，再比較完整路徑、允許的生成檔差異與純 Python 模組雜湊。對照於原始 artifact 期限前完成，使用完整 inventory。[對照摘要](CONTENT-EQUIVALENCE.json)

對照摘要逐項記錄生成檔的理由與原始、重建 SHA-256，並由 BUILD-INFO 引用。實際安裝／修復／移除驗收的 Setup SHA 等於組裝副本；重建的 Setup 指紋見 [BUILD-INFO](BUILD-INFO.json)。這是 hosted Windows 證據，實機及人工驗收在 B3 後的大階段 C 進行。

[報告式試跑 run 44613509068](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44613509068) 只上傳兩份報告相關 artifact，runner 已回讀正式報告 ZIP 解出的成員並逐檔核對 bytes。產品 uploader 跳過。報告內的 SHA256SUMS 對應的是產品目錄。

| Artifact | Digest | 大小（bytes） | 到期（UTC） |
| --- | --- | --- | --- |
| `base-test-build-reports` | `sha256:fcbfe46e2de3f8b3bc316c84c7ce07ed8b2e4504652939f001d413dec4e9c006` | 29523 | 2026-12-19T21:00:03Z |
| `b1b-fixed-baseline-report` | `sha256:e842bc8fd6337e5437a2b53afdc6f1290694e0242456c21cdd7b1add0c163cd5` | 196948 | 2026-12-19T21:00:02Z |

原始 provenance 因有時效，且後續公開仍須重驗同一份原件，試跑額外保存驗過 SHA-256 的報告原件。來源 artifact 過期時可指定上述試跑 run，程式會重新核對原件 SHA。先前的試跑只留 run、雜湊與失敗訊息供追蹤。[嘗試紀錄](previous-attempts.json)

Linux 混合與獨立模組回歸和 CI 另記於 [進度資料](../../../progress.json)。PR #38 交 Claude reviewer 查驗。公開上傳、公開產物收據與關回開關，安排在查驗與合併後。

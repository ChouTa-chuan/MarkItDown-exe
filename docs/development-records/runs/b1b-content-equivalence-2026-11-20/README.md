# B1b 固定候選逐檔對照

Hosted Windows 用固定來源 `b17d51b` 重建並驗收安裝包。從 GitHub Actions run 44295039865 的 `windows-base-validation-reports` 取出原始 provenance，核對原件 SHA-256 `b7fa49e6df55b2a72026fa2c82ce56624cd823e1f7aebce1a62da59b2272657b` 後，再比較完整路徑、允許的生成檔差異與純 Python 模組雜湊。對照於原始 artifact 期限前完成，使用完整 inventory。[對照摘要](CONTENT-EQUIVALENCE.json)

對照摘要逐項記錄生成檔的理由與原始、重建 SHA-256，並由 BUILD-INFO 引用。實際安裝／修復／移除驗收的 Setup SHA 等於組裝副本；重建的 Setup 指紋見 [BUILD-INFO](BUILD-INFO.json)。這是 hosted Windows 證據，實機及人工驗收在 B3 後的大階段 C 進行。

[報告式試跑 run 44613509068](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44613509068) 只上傳兩份報告相關 artifact，runner 已回讀正式報告 ZIP 解出的成員並逐檔核對 bytes。產品 uploader 跳過。報告內的 SHA256SUMS 對應的是產品目錄。

試跑 run 44613509068 使用提交 `8974372`。之後程式只把檢查收緊，要求標準庫 ZIP 成員大小和 CRC 也一致，並限定已確認的 RECORD 路徑格式。 本目錄的 `BUILD-INFO.json` 屬於該次試跑。各次重建的安裝程式不具逐 byte 一致性，公開版指紋以 [public-release.json](public-release.json) 為準。

| Artifact | Digest | 大小（bytes） | 到期（UTC） |
| --- | --- | --- | --- |
| `base-test-build-reports` | `sha256:fcbfe46e2de3f8b3bc316c84c7ce07ed8b2e4504652939f001d413dec4e9c006` | 29523 | 2026-12-19T21:00:03Z |
| `b1b-fixed-baseline-report` | `sha256:e842bc8fd6337e5437a2b53afdc6f1290694e0242456c21cdd7b1add0c163cd5` | 196948 | 2026-12-19T21:00:02Z |

原始 provenance 因有時效，且後續公開仍須重驗同一份原件，試跑額外保存驗過 SHA-256 的報告原件。來源 artifact 過期時可指定上述試跑 run，程式會重新核對原件 SHA。先前的試跑只留 run、雜湊與失敗訊息供追蹤。[嘗試紀錄](previous-attempts.json)

Linux 混合與獨立模組回歸和 CI 另記於 [進度資料](../../../progress.json)。PR #38 已合併。公開結果及本次安裝包指紋見下節。

## B1b 公開測試版

從 main `545ef2b4ca98e0ce7a9df8b3273d6fe3f67fdea3` 手動觸發一次，使用一般驗證 run 44657156187 當日產生的 OCR 輸入。這次完整比對使用 A13b 的原始 provenance。GitHub API 確認只有下表兩份 artifact，均保留 30 天。[公開 run 44659294752](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44659294752)

安裝包 `MarkItDownBase-Setup-0.19.1-windows-x64.exe` 的 SHA-256 為 `b230fee72457faed2f009d7389f92ab4f420827d93491f4bd02672b9949c0992`。GitHub API 的 lifecycle 摘要、本次公開報告中的 BUILD-INFO、實際報告回讀與上傳前勘驗的 Setup 指紋一致。上傳閘門與產品 uploader 成功。此 SHA 與 A13b 審閱時的 Setup 指紋比較結果記於收據。[公開收據](public-release.json)

| Artifact | Digest（ZIP） | 大小（bytes） | 到期（UTC） |
| --- | --- | --- | --- |
| [base-test-build-reports](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44659294752/artifacts/14594742875) | `sha256:db31e161ab40c41021d5eb524fff945e38bcb58cbf2c2db41dbb3bd30509a30d` | 29499 | 2026-12-20T02:20:02Z |
| [MarkItDownBase-test-build](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44659294752/artifacts/14595001990) | `sha256:7a9c7eb442f636c3cb9331e014a41e6f79e38851e0a5a1691cda4a3bd021e4fa` | 101940113 | 2026-12-20T02:20:06Z |

下載須登入 GitHub。本次基本包是測試版，C1–C3 驗收使用 B3 重新定版後的安裝包。

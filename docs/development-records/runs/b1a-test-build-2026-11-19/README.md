# B1a 固定基本包測試版流程

以已整合 A13c 的控制端 `3731dac8deabda462d607154a1c36f98b0cc834c`，建置固定 A13b 應用程式來源 `b17d51bc99f8402f16b99f98bbe3b3370530bc6c`。[流程與界線](../../../base-test-build.md)；[實際試跑查驗](trial-summary.json)、[提交／版本／Setup SHA](BUILD-INFO.json)、[組裝副本核對](package-audit.json)。來源固定不代表安裝包逐位元相同，報告明列原安裝包 SHA 與本次比較結果。

Hosted Windows 2022 實際執行四語 OCR／GUI／中文路徑與 Qt 替換驗收，並完成安裝／修復／移除。沒有在此試跑重跑跨版升級與中斷恢復；一般 PR CI 仍執行。此證據不是乾淨 Windows 10／11、實體機、人工或 GPU 驗收，release_ready 仍 false。

[workflow_dispatch run 44447627530](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44447627530) 成功，產物 uploader 跳過，兩個一般工作依試跑模式跳過，沒有把它們算通過。API 核對只有 `base-test-build-reports` 一份 artifact，digest `sha256:9a88aaf20210711d0cea13ab79c05356c3943dbc3e988e39be2b2fafa1072096`，到期 `2026-12-19T02:59:10Z`（API UTC）；保留 30 天。報告 uploader 的明確文字清單、公開分片及實際副本 SHA 已核對；hosted runner 已下載實際報告 artifact，九個成員的 SHA／大小與原始檔完全相同；只有報告被公開，Setup 留在可拋棄 runner。公開 metadata fingerprint、每份報告 SHA、隨包原文清單 fingerprint 與輸入 artifact receipt 均見查驗 JSON；原始大型資料留該 CI，不重複保存。

首次試跑 Windows 建置驗收通過但組裝拒絕，補診斷後定位為將本次生成的 `native/source.json` 與舊 run hash 錯比。現在只對此固定生成檔以實際 receipt SHA／固定契約／UTF-8 manifest 的完整結構核對；執行檔、模型、DLL 及原文 SHA 的標準不變。反例與原始失敗的 run／hash 見 [嘗試紀錄](attempts.json)。另保留原始 CRLF 於公開文字 metadata，重組後仍能對實際檔案核 SHA。

完整混合與獨立模組回歸通過，數字與來源只記 [progress.json](../../../progress.json)，摘要見本目錄；[gates](gates-summary.json) 與 A13b／A13c 相同。最終 head CI、artifact digest／期限、技術查驗、一般 Merge 與 Pages 核對見 [PR 34](https://github.com/ChouTa-chuan/MarkItDown-exe/pull/34)，避免為補通知反覆觸發 Windows 建置。

A13c 已一般 Merge（PR 33／e8d8074）。本 PR 完成後停止，交 Claude planner 複查大階段 A；通過後才另行 B1b。`PUBLIC_UPLOAD_ENABLED=False`，不能從 dispatch 勾選繞過。不建 Release／tag、不公開安裝包、不改 spec／鎖檔／候選計數或義務狀態。

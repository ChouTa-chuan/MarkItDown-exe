# 義務登記與三旗標判定（A8）

核心只有 [obligations.json](../packaging/redistribution/obligations.json) 與 [redistribution_gates.py](../scripts/redistribution_gates.py)，沒有規則外掛、額外資料模型或發佈動作。以既有 A6 base／cpu source-review 為輸入，原始報告與計數不改寫。A12 出口報告須使用此腳本的推導結果；來源報告中的舊 false 保留作當時建置證據，不拿來代替本判定。

| 旗標 | 條件 |
| --- | --- |
| runtime_sbom_complete | 此 profile 所有影響來源盤點的義務皆完成證據審閱，並有可重驗的證據引用；不以套件宣告或外層 wheel 擁有權代替內含第三方盤點 |
| redistribution_approved | runtime_sbom_complete 為 true，所有再散布義務完成；需要使用者決定的條目必須 user_approved 且有決定原文引用。每個 profile 的 redistribution-decision 為必要門檻，協調者不能代為決定 |
| release_ready | redistribution_approved 為 true，加上 clean-machine-manual 必要條目完成並經使用者確認。hosted Windows CI 不代替大階段 C 的乾淨機與人工驗收 |

base 與 cpu 分開判定；CPU 尚未關閉不妨礙基本包依自己的證據完成。共用登記 JSON 本身仍須結構有效，任何標成使用者已核准而沒有有效決定出處的條目都拒絕。

## 精確覆蓋與計數

- `native_files` 是 A6 `classification_input.report.native_files` 的精確路徑列表，以 Windows 路徑不分大小寫的規則比對，不支援通配或兜底；每個原生檔須恰好對到一個條目。
- `review_reasons` 是另一個獨立對應軸。每個 reason 字串須恰好對到一個條目，所有帶該 reason 的檔案引用同一義務；摘要須與輸入列一致。未知 reason、未知原生檔或重複對應皆拒絕，沒有優先順序掩蓋重疊。
- `file_groups` 只描述人工審閱範圍，例如模型、PYZ／base_library，不是執行時通配規則。清單不宣稱已展開 wheel 內的隱藏元件，細部目錄由 A9 等後續階段處理。
- **unresolved_files 沿用原盤點「無 wheel 擁有者」的計數，不是要歸零的指標。** 合理的非 wheel 來源包括 CPython、自行產生檔案及模型。腳本保留輸入 summary，依義務／證據判定旗標，不降低或重新定義任何既有數字。

## A8b 檢核補強（schema 2）

- **封閉結構**：`schema_version` 為 2（只接受 2）。頂層、profile、每個條目、每個 evidence／decision_source 參照物件的鍵集合都是固定允許集合（條目的 `decision_source` 可省略或為 null），未知鍵拒絕。
- **決定出處格式**：`decision_source.path` 必須是 `docs/history/status/YYYY-MM-DD-<slug>.md` 固定存檔，不接受 STATUS.md 本身（它持續改動，hash 會失效）。`quote` 必須等於該存檔中**完整的一行**，該行位於 `## D` 標題之後、下一個 `## ` 標題之前，且符合 `| 日期 | 使用者… | 內容 |` 形式（來源欄以「使用者」開頭）。任意子字串、非 D 節的行、來源欄不是使用者的行都拒絕。這只限制出處的位置與格式，不證明該行真的出自使用者，仍須人工查驗。
- **反向檢查**：除了輸入每一項恰好對到一個條目，登記表該 profile 的每個 `native_files`、`review_reasons` 選擇器也必須真的出現在輸入中；否則以 stale selector 拒絕。
- **release_ready 綁定大階段 C**：`*-clean-machine-manual` 要關閉（非 open）時，`evidence` 須至少有一筆 path 以 `docs/development-records/runs/stage-c-` 開頭。這個前綴目前不存在，所以在大階段 C 的乾淨機與人工驗收完成之前，release_ready 不可能為 true。
- **仍須人工審查的部分**：腳本不檢查決定列與條目的語意是否對應，同一列使用者決定可以被多個條目引用；`stage-c-` 前綴也只是格式門檻，不證明驗收真的做過。D 節標題須為 `## D` 後接標點、空白或行尾，程式碼區塊（``` 圍欄）內的內容不算；日期須為有效日期；`schema_version` 須為整數 2。把條目改為 `evidence_complete` 或 `user_approved` 的提交，一律要逐條比對其引用的決定列與證據內容。
- **各 profile 分別評估**：反向檢查只涵蓋被評估的 profile，base 與 cpu 必須各跑一次。

## 狀態與證據

每項含 id、檔案／reason 對應、所需證據、狀態、旗標範圍與使用者決定出處。`open` 為未關閉；`evidence_complete` 表示所列證據已經人工審閱完成；`user_approved` 再加上使用者已作決定。工程證據完成可以關閉盤點義務，但不會自動滿足需要使用者決定的再散布或實機驗收義務。

非 open 狀態須有證據引用；引用使用 repo 相對路徑與 SHA-256，決定還須符合上節的出處格式（固定存檔 D 節中完整的一行使用者決定）。已核准卻無出處、引用不存在、hash 不符或 quote 不存在皆拒絕。required_evidence 是審閱清單，語意是否已滿足須由維護者依證據查驗；腳本驗證引用完整性與已記錄的狀態，不判定法律充分性、作者身分或自動產生使用者核准。

登記表綁定該 profile 的來源提交，避免把不同候選的確認直接帶過去。當前基準是 A6 的 8285450，不包含 A7。自有 MIT 授權選擇已有原始使用者決定；但本候選的 MIT 綁定仍是 open，A7 後的新候選須待後續驗收／登記更新。其他現有義務未關閉，**base／cpu 的三旗標現況均為 false**。

## 執行與驗收

```bash
python scripts/redistribution_gates.py --source-review docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json
python scripts/redistribution_gates.py --source-review docs/development-records/runs/a6-fixed-review-2026-11-17/cpu-source-review.json
```

有效輸入輸出旗標、各旗標阻擋條目、相依關係與精確對應。exit 0 只表示登記／涵蓋性有效，交付流程必須另檢查對應旗標；未關閉時仍會列出 blockers。錯誤輸入非零退出，指定 `--output` 時只准寫新檔，驗證錯誤不留下部分成功報告。

測試含未知檔／reason、重複對應、缺少決定出處、改證據／決定原文、三旗標的分層與相依、base／cpu 獨立、保留原始計數與 CLI 不覆寫。全關閉的正例使用合成證據，只證明旗標不是常數，不代表實際授權或實機驗收已通過。

A8 不動 spec、依賴或套件收集內容。除 C 節指定的說明文字勘誤外，不改安裝資產；不接續 A9–A17，不交付產品、Release 或 tag，完成後先停。

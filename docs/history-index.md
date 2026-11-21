# 歷史索引

由 `scripts/build_history_index.py` 自動產生，**請勿手動編輯**；新增紀錄後重新執行腳本。
這份索引用來查找，不是開工必讀。開工只需要讀 [AGENTS.md](../AGENTS.md) 與 [STATUS.md](../STATUS.md)。

出錯或需要追溯時：先用日期、主題或關鍵字在下表找到那一筆，再打開它的路徑。
「來源」是當次受測的提交；「結果」只列該筆清單檔實際記錄的欄位，空白表示沒有記錄，不代表通過。

共 160 筆。

| 日期 | 類型 | 主題 | 來源 | 結果 | 關鍵字 | 路徑 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-21 | 證據 | B3d：CPU worker 建置工具查證 | b17d51b | 接受、Windows已執行 | B3d、CPU worker、setuptools、pip、PyInstaller、原文、CArchive、PYZ | [development-records/runs/b3d-cpu-build-tools-2026-11-21/README.md](development-records/runs/b3d-cpu-build-tools-2026-11-21/README.md) |
| 2026-11-21 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-21-b3-decisions.md](history/status/2026-11-21-b3-decisions.md) |
| 2026-11-21 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-21-before-b3-plan.md](history/status/2026-11-21-before-b3-plan.md) |
| 2026-11-21 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-21-before-b3d.md](history/status/2026-11-21-before-b3d.md) |
| 2026-11-20 | 證據 | B1b 固定候選逐檔對照 |  | 接受 | B1b、逐檔對照、固定候選、Windows | [development-records/runs/b1b-content-equivalence-2026-11-20/README.md](development-records/runs/b1b-content-equivalence-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3a CPU worker 套件授權原文綁定 | a8704d0 | 接受 | B3a、flatbuffers、RapidOCR、CPU、授權原文綁定 | [development-records/runs/b3a-cpu-original-notices-2026-11-20/README.md](development-records/runs/b3a-cpu-original-notices-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3b PP-OCR 模型來源、授權與辨識評估 | 07084c2 | 接受 | B3b、PP-OCR、CPU、模型授權、簡繁辨識 | [development-records/runs/b3b-ppocr-model-review-2026-11-20/README.md](development-records/runs/b3b-ppocr-model-review-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3b2 擴大三語識別樣本 | d48af8f | 接受 | B3b2、PP-OCR、繁中、簡中、固定圖片、CPU 識別 | [development-records/runs/b3b2-expanded-ocr-evaluation-2026-11-20/README.md](development-records/runs/b3b2-expanded-ocr-evaluation-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3b3 PP-OCRv5 來源授權查證與模擬掃描複驗 | 3b522bc | 接受 | B3b3、PP-OCRv5、ONNX 來源、授權分級、模擬掃描、繁中、簡中、被擋主機 | [development-records/runs/b3b3-v5-provenance-scan-2026-11-20/README.md](development-records/runs/b3b3-v5-provenance-scan-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3b4 PP-OCRv6 small 官方來源、授權與旋轉條件補測 |  |  | PP-OCRv6、PP-OCRv6 small、PP-OCRv5、PP-OCRv4、Hugging Face、Apache-2.0、ONNX、RapidOCR、provenance、旋轉、expand、簡體中文、繁體中文、模擬掃描 | [development-records/runs/b3b4-v6-official-provenance-2026-11-20/README.md](development-records/runs/b3b4-v6-official-provenance-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3b5 以官方 PP-OCRv6 small／PP-OCRv5 mobile ONNX 重跑評估 | c42aa27 |  | PP-OCRv6、PP-OCRv6 small、PP-OCRv5、PP-OCRv4、官方 ONNX、外部字表、rec_keys_path、模擬掃描、簡體中文、繁體中文、ONNX、RapidOCR、B3b5 | [development-records/runs/b3b5-official-onnx-rerun-2026-11-20/README.md](development-records/runs/b3b5-official-onnx-rerun-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3c CPU 固定候選原生元件與授權原文 | b17d51b | 接受 | B3c、CPU、wheel、GEOS、LGPL、Microsoft、LibYAML、原文、OpenCV | [development-records/runs/b3c-cpu-native-review-2026-11-20/README.md](development-records/runs/b3c-cpu-native-review-2026-11-20/README.md) |
| 2026-11-20 | 證據 | B3c 暫停於 LibYAML 原文查證 | b17d51b | 未接受 | B3c、PyYAML、LibYAML、授權原文、CPU 固定候選 | [development-records/runs/b3c-libyaml-notice-gap-2026-11-20/README.md](development-records/runs/b3c-libyaml-notice-gap-2026-11-20/README.md) |
| 2026-11-20 | 證據 | run 44307725980 Windows 失敗原因（2026-11-20 查明） | 35233ae | 未接受 | 44307725980、GUI、Qt Windows window did not open、升級測試、previous-build、gui.log、間歇性 | [development-records/runs/run-44307725980-gui-timeout-2026-11-20/README.md](development-records/runs/run-44307725980-gui-timeout-2026-11-20/README.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b1b-public-closeout.md](history/status/2026-11-20-before-b1b-public-closeout.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b1b.md](history/status/2026-11-20-before-b1b.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b2.md](history/status/2026-11-20-before-b2.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b3a.md](history/status/2026-11-20-before-b3a.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b3b.md](history/status/2026-11-20-before-b3b.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b3b2.md](history/status/2026-11-20-before-b3b2.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b3c-merged.md](history/status/2026-11-20-before-b3c-merged.md) |
| 2026-11-20 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-20-before-b3c.md](history/status/2026-11-20-before-b3c.md) |
| 2026-11-19 | 證據 | A13c 固定候選逐列來源對照 | 9712e88 | 接受 | A13c、origin-known、Redist、來源對照 | [development-records/runs/a13c-source-attribution-2026-11-19/README.md](development-records/runs/a13c-source-attribution-2026-11-19/README.md) |
| 2026-11-19 | 證據 | B1a 固定基本包測試版流程 |  | 接受 | B1a、test-build、報告試跑、固定候選、artifact 30 天 | [development-records/runs/b1a-test-build-2026-11-19/README.md](development-records/runs/b1a-test-build-2026-11-19/README.md) |
| 2026-11-19 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-19-a13b-before-replan.md](history/status/2026-11-19-a13b-before-replan.md) |
| 2026-11-19 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-19-before-a13c-complete.md](history/status/2026-11-19-before-a13c-complete.md) |
| 2026-11-19 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-19-before-b1a-complete.md](history/status/2026-11-19-before-b1a-complete.md) |
| 2026-11-19 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-19-before-stage-a-closeout.md](history/status/2026-11-19-before-stage-a-closeout.md) |
| 2026-11-18 | 證據 | A11 Qt 第三方與替換驗收 |  |  | A11、Qt、替換、qt_attribution | [development-records/runs/a11-qt-2026-11-18/README.md](development-records/runs/a11-qt-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A12 固定候選來源審閱與基本包出口（2026-11-18） | 2555687 | 接受、Windows已執行 | A12、固定候選、2555687、來源審閱、登記表、出口報告、A13、Microsoft探測、目錄綁定 | [development-records/runs/a12-fixed-review-2026-11-18/README.md](development-records/runs/a12-fixed-review-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A12b 既有證據接線 |  |  | A12b、證據接線、origin-known、Community | [development-records/runs/a12b-evidence-wiring-2026-11-18/README.md](development-records/runs/a12b-evidence-wiring-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A12c 揭露式關閉規則 | 1fee37a |  | A12c、accepted_gaps、runtime_sbom_disclosed、揭露式關閉 | [development-records/runs/a12c-disclosure-gates-2026-11-18/README.md](development-records/runs/a12c-disclosure-gates-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A12d wheel 內含元件執行期版本觀測 | fb4f510 | 接受、Windows已執行 | A12d、runtime-observed、Windows API、lxml、libxml2、libxslt、libexslt、pillow、libaom、dav1d、numpy、LAPACK、receipt | [development-records/runs/a12d-runtime-versions-2026-11-18/README.md](development-records/runs/a12d-runtime-versions-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A13b 固定候選：來源審閱、Microsoft 探測與使用者決定寫入（b17d51b，2a＋2b） | b17d51b | 接受、Windows已執行 | A13b、2b、固定候選、b17d51b、Microsoft探測、check_catalog放寬收回、使用者決定、accepted_gaps、known-gaps、release_ready | [development-records/runs/a13b-fixed-review-2026-11-18/README.md](development-records/runs/a13b-fixed-review-2026-11-18/README.md) |
| 2026-11-18 | 證據 | A9b cryptography 內含 OpenSSL 原文 | 7125978 | 接受、Windows已執行 | A9b、cryptography、OpenSSL、LICENSE、runtime-observed、Windows API、原文隨包、共用hash | [development-records/runs/a9b-openssl-2026-11-18/README.md](development-records/runs/a9b-openssl-2026-11-18/README.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-a11-before-a12.md](history/status/2026-11-18-a11-before-a12.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-a12-before-a13-plan.md](history/status/2026-11-18-a12-before-a13-plan.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-a12d-before-a13b.md](history/status/2026-11-18-a12d-before-a13b.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-a13-before-a12d.md](history/status/2026-11-18-a13-before-a12d.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-a13-decisions.md](history/status/2026-11-18-a13-decisions.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-before-a11-complete.md](history/status/2026-11-18-before-a11-complete.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-before-a12b-complete.md](history/status/2026-11-18-before-a12b-complete.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-before-a12c-complete.md](history/status/2026-11-18-before-a12c-complete.md) |
| 2026-11-18 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-18-before-a9b.md](history/status/2026-11-18-before-a9b.md) |
| 2026-11-17 | 證據 | A10 Microsoft 執行期逐檔對照 | 077d280 | 接受、Windows已執行 | A10、Microsoft、VC runtime、PE版本、簽章、Redist、改名複本、A13、條款原文、來源缺口 | [development-records/runs/a10-microsoft-runtime-2026-11-17/README.md](development-records/runs/a10-microsoft-runtime-2026-11-17/README.md) |
| 2026-11-17 | 證據 | A6 固定來源候選與審閱紀錄 | 8285450 | 接受、Windows已執行 | A6、固定候選、來源重分類、metadata、CPU排程、完整回歸、整體審閱 | [development-records/runs/a6-fixed-review-2026-11-17/README.md](development-records/runs/a6-fixed-review-2026-11-17/README.md) |
| 2026-11-17 | 證據 | A7 自有 MIT 對照與工作流驗證 | 07afa79 | 接受、Windows已執行 | A7、自有MIT、套件原文對照、EXPECTED_SOURCE、缺片、越界、Claude planner | [development-records/runs/a7-mit-binding-2026-11-17/README.md](development-records/runs/a7-mit-binding-2026-11-17/README.md) |
| 2026-11-17 | 證據 | A8 義務登記與旗標判定驗證 | 5e7fd53 | 接受 | A8、義務登記、旗標推導、唯一對應、使用者決定出處、無wheel擁有者 | [development-records/runs/a8-gates-2026-11-17/README.md](development-records/runs/a8-gates-2026-11-17/README.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a10-before-official-completion.md](history/status/2026-11-17-a10-before-official-completion.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a5c-before-a6.md](history/status/2026-11-17-a5c-before-a6.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a6-before-a7.md](history/status/2026-11-17-a6-before-a7.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a6-before-cpu-evidence.md](history/status/2026-11-17-a6-before-cpu-evidence.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a6-before-fixed-review.md](history/status/2026-11-17-a6-before-fixed-review.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a7-before-stage-a-replan.md](history/status/2026-11-17-a7-before-stage-a-replan.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a7-before-validation.md](history/status/2026-11-17-a7-before-validation.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a8-before-a8b.md](history/status/2026-11-17-a8-before-a8b.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a8-before-validation.md](history/status/2026-11-17-a8-before-validation.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a8b-before-a9.md](history/status/2026-11-17-a8b-before-a9.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-a9-before-a10.md](history/status/2026-11-17-a9-before-a10.md) |
| 2026-11-17 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-17-planner-before-a8.md](history/status/2026-11-17-planner-before-a8.md) |
| 2026-11-16 | 證據 | A4：PR 8 首輪 Windows 與 Linux CI 實證 | dd72bf4 | 接受、Windows已執行 | A4、PR8、Windows CI、setuptools排除、API恢復、CPython版本對照 | [development-records/runs/a4-pr8-ci-2026-11-16/README.md](development-records/runs/a4-pr8-ci-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A4：setuptools 匯入來源與基本包排除驗證 | 8c26451 | 接受 | A4、setuptools、namespace、PyInstaller、基本包排除、Linux frozen、PR API限制 | [development-records/runs/a4-setuptools-audit-2026-11-16/README.md](development-records/runs/a4-setuptools-audit-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5：CPython 隨附元件逐檔版本與原文 | 2104418 | 接受 | A5、CPython、OpenSSL、libffi、SQLite、原文、109基準、A4現況修正 | [development-records/runs/a5-cpython-components-2026-11-16/README.md](development-records/runs/a5-cpython-components-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5：PR 9 Windows 逐檔元件驗證 | 3ef16b6 | 接受、Windows已執行 | A5、CPython、OpenSSL、libffi、SQLite、逐檔、Windows、PR9、原文、來源指紋 | [development-records/runs/a5-pr9-ci-2026-11-16/README.md](development-records/runs/a5-pr9-ci-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5b 第一個提交：交接與使用者決定復原 | c51089a | 接受 | A5b、交接、使用者決定、A5c、最終CI、PR9 | [development-records/runs/a5b-handoff-corrections-2026-11-16/README.md](development-records/runs/a5b-handoff-corrections-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5b：PR 10 原生 Windows Qt 來源驗證 | 30c9eaf | 接受、Windows已執行 | A5b、PR10、Qt、Windows、原生、來源對應、wheel指紋、annotation、A5c待辦 | [development-records/runs/a5b-pr10-ci-2026-11-16/README.md](development-records/runs/a5b-pr10-ci-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5b：Windows 控制端的 Qt 摘要接線 | 5376c99 | 接受 | A5b、Qt、CI、stdout、annotation、控制端、完整回歸 | [development-records/runs/a5b-qt-ci-forwarding-2026-11-16/README.md](development-records/runs/a5b-qt-ci-forwarding-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5b：Qt 發布來源與版本對應 | bc2f77c | 接受 | A5b、Qt、PySide、shiboken、發布來源、gitlink、Windowswheel、版本宣告、A5c待辦 | [development-records/runs/a5b-qt-source-2026-11-16/README.md](development-records/runs/a5b-qt-source-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5c：PR 11 原生 Windows 新探測門檻驗證 | 24094d6 | 接受、Windows已執行 | A5c、PR11、Windows、CPython、OpenSSL、SQLite、runtimeprobe、接受條件、原生CI | [development-records/runs/a5c-pr11-ci-2026-11-16/README.md](development-records/runs/a5c-pr11-ci-2026-11-16/README.md) |
| 2026-11-16 | 證據 | A5c：CPython runtime probe 驗收補強 | afb2062 | 接受 | A5c、CPython、OpenSSL、SQLite、probe_error、接受條件、CLI、缺失原文、反例 | [development-records/runs/a5c-runtime-probe-2026-11-16/README.md](development-records/runs/a5c-runtime-probe-2026-11-16/README.md) |
| 2026-11-16 | 證據 | Python 模組來源清單的首次 Windows CI 輸出 | c49c729 | 接受、Windows已執行 | Python模組清單、base_library成員、setuptools不明模組 | [development-records/runs/python-archive-inventory-ci-2026-11-16/README.md](development-records/runs/python-archive-inventory-ci-2026-11-16/README.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a3-before-a4.md](history/status/2026-11-16-a3-before-a4.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a4-before-a5.md](history/status/2026-11-16-a4-before-a5.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a4-before-api-recovery.md](history/status/2026-11-16-a4-before-api-recovery.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a4-before-windows-ci-result.md](history/status/2026-11-16-a4-before-windows-ci-result.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5-before-a5b.md](history/status/2026-11-16-a5-before-a5b.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5-before-windows-ci.md](history/status/2026-11-16-a5-before-windows-ci.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5b-before-a5c.md](history/status/2026-11-16-a5b-before-a5c.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5b-before-source-verification.md](history/status/2026-11-16-a5b-before-source-verification.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5b-before-windows-ci.md](history/status/2026-11-16-a5b-before-windows-ci.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-a5c-before-windows-ci.md](history/status/2026-11-16-a5c-before-windows-ci.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-ci-self-check-and-ms-runtime.md](history/status/2026-11-16-ci-self-check-and-ms-runtime.md) |
| 2026-11-16 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-16-python-archive-inventory.md](history/status/2026-11-16-python-archive-inventory.md) |
| 2026-11-13 | 證據 | CPU 文字辨識元件排除 FFmpeg 後的 Windows CI | 0b53235 | 接受、Windows已執行 | FFmpeg排除、OpenCV、CPU元件體積、元件版號未重定 | [development-records/runs/ffmpeg-exclusion-ci-2026-11-13/README.md](development-records/runs/ffmpeg-exclusion-ci-2026-11-13/README.md) |
| 2026-11-13 | 證據 | 微軟執行期改用官方來源後的 Windows CI | c3cd3eb | 接受、Windows已執行 | Universal CRT不隨包、VC runtime官方來源、系統DLL來自Java JDK目錄、PATH收集、簽章查詢失敗、PSModulePath | [development-records/runs/ms-runtime-official-source-ci-2026-11-13/README.md](development-records/runs/ms-runtime-official-source-ci-2026-11-13/README.md) |
| 2026-11-13 | 證據 | 取得非 wheel 原生檔數位簽章的 Windows CI | 8e4dc2d | 接受、Windows已執行 | 數位簽章取得、PSModulePath修正、VC runtime由Microsoft簽署、CPython由PSF簽署、CPU元件未對照259 | [development-records/runs/native-signatures-ci-2026-11-13/README.md](development-records/runs/native-signatures-ci-2026-11-13/README.md) |
| 2026-11-13 | 證據 | 基本包排除來源不明 OpenSSL 後的 Windows CI | 746c4f4 | 接受、Windows已執行 | OpenSSL排除、Qt TLS外掛、artifact下載被網路政策拒絕、儲存主機不固定 | [development-records/runs/openssl-exclusion-ci-2026-11-13/README.md](development-records/runs/openssl-exclusion-ci-2026-11-13/README.md) |
| 2026-11-13 | 證據 | 現況檔與歷史索引上線後的完整回歸 | 15a425b | 接受、回歸703／通過702 | 現況檔、歷史索引、規則改寫 | [development-records/runs/status-and-index-2026-11-13/README.md](development-records/runs/status-and-index-2026-11-13/README.md) |
| 2026-11-13 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-13-license-and-exclusions.md](history/status/2026-11-13-license-and-exclusions.md) |
| 2026-11-13 | 現況存檔 | 現況 |  |  |  | [history/status/2026-11-13-status-and-index.md](history/status/2026-11-13-status-and-index.md) |
| 2026-11-12 | 證據 | Windows CI 完整報告原檔保存 | cb8f24d | 接受 | artifact下載被網路政策拒絕、CONNECT 403、artifact到期 | [development-records/runs/ci-full-reports-2026-11-12/README.md](development-records/runs/ci-full-reports-2026-11-12/README.md) |
| 2026-11-12 | 證據 | 新增分類工具與 CI 後的 Linux 完整回歸 | 582458e | 接受、回歸698／通過697 |  | [development-records/runs/handover-ci-and-classification-2026-11-12/README.md](development-records/runs/handover-ci-and-classification-2026-11-12/README.md) |
| 2026-11-12 | 證據 | 接手環境的 Linux 完整回歸 | 2e06631 | 接受、回歸684／通過683 | 缺libEGL、setUpClass載入錯誤、缺Tesseract跳過、Tesseract版本差異 | [development-records/runs/handover-regression-2026-11-12/README.md](development-records/runs/handover-regression-2026-11-12/README.md) |
| 2026-11-12 | 證據 | PR 1 上新 CI 入口的首次 GitHub 執行 | cd14fe7 | 接受、Windows已執行、回歸698／通過697 |  | [development-records/runs/pr1-ci-first-run-2026-11-12/README.md](development-records/runs/pr1-ci-first-run-2026-11-12/README.md) |
| 2026-11-12 | 證據 | 視覺進度網站上線 |  |  |  | [development-records/runs/progress-pages-live-2026-11-12/README.md](development-records/runs/progress-pages-live-2026-11-12/README.md) |
| 2026-11-12 | 證據 | 專案交接說明整理 |  |  |  | [development-records/runs/project-handoff-2026-11-12/README.md](development-records/runs/project-handoff-2026-11-12/README.md) |
| 2026-11-12 | 證據 | 未對照來源分類紀錄 | cb8f24d | 接受 |  | [development-records/runs/source-classification-2026-11-12/README.md](development-records/runs/source-classification-2026-11-12/README.md) |
| 2026-11-11 | 證據 | 建置來源追溯檢核 |  |  |  | [development-records/runs/bundle-provenance-2026-11-11/README.md](development-records/runs/bundle-provenance-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 隨包原文與原生來源追溯 | 70f03f0 | 接受、Windows已執行、回歸661／通過660 | Windows反斜線路徑、Analysis路徑正規化 | [development-records/runs/bundle-provenance-ci-2026-11-11/README.md](development-records/runs/bundle-provenance-ci-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 候選完整清單與ZIP檢核 | cb8f24d | 接受、Windows已執行、回歸684／通過683 | 安裝後新增catalog、快照時點、CI被後續提交取消 | [development-records/runs/candidate-inventory-ci-2026-11-11/README.md](development-records/runs/candidate-inventory-ci-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 基本包封裝後清單 |  |  |  | [development-records/runs/candidate-inventory-finalization-2026-11-11/README.md](development-records/runs/candidate-inventory-finalization-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 候選完整清單準備 |  |  |  | [development-records/runs/candidate-inventory-prep-2026-11-11/README.md](development-records/runs/candidate-inventory-prep-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 0.19.1完整回歸 | ca5a296 | 接受 |  | [development-records/runs/full-regression-0.19.1-2026-11-11/README.md](development-records/runs/full-regression-0.19.1-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 視覺進度Pages發布 |  |  | Pages未啟用、部署Not Found、需管理員設定來源 | [development-records/runs/progress-pages-2026-11-11/README.md](development-records/runs/progress-pages-2026-11-11/README.md) |
| 2026-11-11 | 證據 | Windows CPU維護程序中斷恢復實測 | ad7d227 | Windows已執行 |  | [development-records/runs/windows-cpu-recovery-ci-2026-11-11/README.md](development-records/runs/windows-cpu-recovery-ci-2026-11-11/README.md) |
| 2026-11-11 | 證據 | CPU維護程序中斷與恢復準備 |  |  |  | [development-records/runs/windows-cpu-recovery-prep-2026-11-11/README.md](development-records/runs/windows-cpu-recovery-prep-2026-11-11/README.md) |
| 2026-11-11 | 證據 | 首輪Windows恢復接受與公開摘要長度調整 |  | Windows已執行 |  | [development-records/runs/windows-cpu-recovery-summary-2026-11-11/README.md](development-records/runs/windows-cpu-recovery-summary-2026-11-11/README.md) |
| 2026-11-11 | 證據 | Windows測試安裝包準備盤點 | ad7d227 | Windows已執行 |  | [development-records/runs/windows-test-readiness-2026-11-11/README.md](development-records/runs/windows-test-readiness-2026-11-11/README.md) |
| 2026-11-10 | 證據 | Windows CI 自有中斷產物清理實測 |  |  |  | [development-records/runs/temporary-cleanup-ci-2026-11-10/README.md](development-records/runs/temporary-cleanup-ci-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU第一輪原生驗證 |  | 未接受、Windows已執行 | CPU worker健康檢查未通過、診斷不足 | [development-records/runs/windows-cpu-attempt1-2026-11-10/README.md](development-records/runs/windows-cpu-attempt1-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU第二輪：健康工作逾時 |  | 未接受、Windows已執行 | CPU worker逾時、stderr為空 | [development-records/runs/windows-cpu-attempt2-2026-11-10/README.md](development-records/runs/windows-cpu-attempt2-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU第三輪：原生匯入阻塞定位 |  | 未接受、Windows已執行 |  | [development-records/runs/windows-cpu-attempt3-2026-11-10/README.md](development-records/runs/windows-cpu-attempt3-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU第四輪：調整原生初始化順序 |  | 未接受、Windows已執行 | ONNX Runtime原生匯入逾時、管道讀取互鎖、ReadFile候選無效 | [development-records/runs/windows-cpu-attempt4-2026-11-10/README.md](development-records/runs/windows-cpu-attempt4-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU選配原生驗證 | f0708d0 | 接受、Windows已執行 | CPU worker互鎖解法、先初始化原生庫再啟動背景讀取 | [development-records/runs/windows-cpu-ci-2026-11-10/README.md](development-records/runs/windows-cpu-ci-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU選配元件維護實測 | fd69854 | 接受、Windows已執行 |  | [development-records/runs/windows-cpu-lifecycle-ci-2026-11-10/README.md](development-records/runs/windows-cpu-lifecycle-ci-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU元件維護準備 |  |  |  | [development-records/runs/windows-cpu-lifecycle-prep-2026-11-10/README.md](development-records/runs/windows-cpu-lifecycle-prep-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU 選配建置準備 |  |  |  | [development-records/runs/windows-cpu-prep-2026-11-10/README.md](development-records/runs/windows-cpu-prep-2026-11-10/README.md) |
| 2026-11-10 | 證據 | Windows CPU元件跨版本實測 | db601e2 | 接受、Windows已執行 |  | [development-records/runs/windows-cpu-upgrade-ci-2026-11-10/README.md](development-records/runs/windows-cpu-upgrade-ci-2026-11-10/README.md) |
| 2026-11-10 | 證據 | CPU跨版驗收腳本版號接續 |  |  |  | [development-records/runs/windows-cpu-upgrade-followup-2026-11-10/README.md](development-records/runs/windows-cpu-upgrade-followup-2026-11-10/README.md) |
| 2026-11-10 | 證據 | CPU元件跨版本準備 |  |  |  | [development-records/runs/windows-cpu-upgrade-prep-2026-11-10/README.md](development-records/runs/windows-cpu-upgrade-prep-2026-11-10/README.md) |
| 2026-11-09 | 證據 | C11 Hosted 基本包安裝／修復／移除驗證完成 |  |  |  | [development-records/runs/c11-installer-2026-11-09/README.md](development-records/runs/c11-installer-2026-11-09/README.md) |
| 2026-11-09 | 證據 | C11 基本包安裝生命週期準備 |  |  |  | [development-records/runs/c11-installer-prep-2026-11-09/README.md](development-records/runs/c11-installer-prep-2026-11-09/README.md) |
| 2026-11-09 | 證據 | Windows 安裝程序中斷後續修實測 |  |  |  | [development-records/runs/c11-recovery-2026-11-09/README.md](development-records/runs/c11-recovery-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 程序中斷續修第一次Windows實測：Pascal註解編譯失敗 |  | 未接受 | Inno編譯失敗、Pascal註解語法、BEGIN expected | [development-records/runs/c11-recovery-attempt1-2026-11-09/README.md](development-records/runs/c11-recovery-attempt1-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 程序中斷續修第二次Windows實測：Inno暫存產物所有權 |  |  | 中斷續修、Inno暫存檔is-*.tmp、完整性檢查拒絕 | [development-records/runs/c11-recovery-attempt2-2026-11-09/README.md](development-records/runs/c11-recovery-attempt2-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 基本包安裝程序中斷後續修準備 |  |  |  | [development-records/runs/c11-recovery-prep-2026-11-09/README.md](development-records/runs/c11-recovery-prep-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 基本包真跨版本升級與明確回復實測 |  |  |  | [development-records/runs/c11-upgrade-2026-11-09/README.md](development-records/runs/c11-upgrade-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 跨版 CI 第一次實測：Inno Script 編譯錯誤 |  | 未接受 | Inno編譯失敗、不存在的函式ExcludeTrailingBackslash | [development-records/runs/c11-upgrade-attempt1-2026-11-09/README.md](development-records/runs/c11-upgrade-attempt1-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 跨版 CI 第二次實測：升級後自檢失敗與診斷修正 |  |  | 升級後自檢失敗、公開尾段選錯日誌 | [development-records/runs/c11-upgrade-attempt2-2026-11-09/README.md](development-records/runs/c11-upgrade-attempt2-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 基本包跨版本升級／明確回復準備 |  |  |  | [development-records/runs/c11-upgrade-prep-2026-11-09/README.md](development-records/runs/c11-upgrade-prep-2026-11-09/README.md) |
| 2026-11-09 | 證據 | Qt 視窗生命週期與正常退出 |  |  | Qt退出SIGSEGV、exit -11、QApplication cleanup、偶發 | [development-records/runs/qt-lifecycle-2026-11-09/README.md](development-records/runs/qt-lifecycle-2026-11-09/README.md) |
| 2026-11-09 | 證據 | 中斷測試暫存清理準備 |  |  |  | [development-records/runs/temporary-cleanup-prep-2026-11-09/README.md](development-records/runs/temporary-cleanup-prep-2026-11-09/README.md) |
| 2026-11-09 | 證據 | Windows 基本包自動驗證完成 |  |  |  | [development-records/runs/windows-base-ci-2026-11-09/README.md](development-records/runs/windows-base-ci-2026-11-09/README.md) |
| 2026-11-09 | 證據 | Windows 下載階段診斷與隔離回歸保存 |  |  | 固定來源下載失敗、Windows job被略過 | [development-records/runs/windows-ci-retry-2026-11-09/README.md](development-records/runs/windows-ci-retry-2026-11-09/README.md) |
| 2026-11-08 | 證據 | C03 內含四語基本包開發紀錄 |  |  |  | [development-records/runs/c03-bundle-2026-11-08/README.md](development-records/runs/c03-bundle-2026-11-08/README.md) |
| 2026-11-08 | 證據 | C03 四語模型與語言選擇開發紀錄 |  |  |  | [development-records/runs/c03-languages-2026-11-08/README.md](development-records/runs/c03-languages-2026-11-08/README.md) |
| 2026-11-08 | 證據 | C03 最小原生來源準備開發紀錄 |  |  |  | [development-records/runs/c03-minimal-source-2026-11-08/README.md](development-records/runs/c03-minimal-source-2026-11-08/README.md) |
| 2026-11-08 | 證據 | C03 原生來源與 DLL 靜態檢查開發紀錄 |  |  |  | [development-records/runs/c03-native-static-2026-11-08/README.md](development-records/runs/c03-native-static-2026-11-08/README.md) |
| 2026-11-08 | 證據 | C04 基本核心打包與自檢開發紀錄 |  |  |  | [development-records/runs/c04-build-2026-11-08/README.md](development-records/runs/c04-build-2026-11-08/README.md) |
| 2026-11-08 | 證據 | C04 基本版依賴拆分開發紀錄 |  |  |  | [development-records/runs/c04-locks-2026-11-08/README.md](development-records/runs/c04-locks-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows 基本包 CI 開發紀錄 |  |  |  | [development-records/runs/windows-ci-2026-11-08/README.md](development-records/runs/windows-ci-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows CI 第一次執行紀錄 |  |  | Windows CI首次失敗、exit 1原因未知、公開頁503 | [development-records/runs/windows-ci-attempt1-2026-11-08/README.md](development-records/runs/windows-ci-attempt1-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows 九項通過與 Qt 正常關閉工具修正 |  |  | Qt視窗關閉逾時、closeEvent | [development-records/runs/windows-ci-close-2026-11-08/README.md](development-records/runs/windows-ci-close-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows 中文路徑診斷解碼修正 |  |  | CP1252解碼、UnicodeDecodeError、UTF-8模式 | [development-records/runs/windows-ci-decode-2026-11-08/README.md](development-records/runs/windows-ci-decode-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows 固定來源換行保護紀錄 |  |  | 換行CRLF、autocrlf、雜湊改變、.gitattributes | [development-records/runs/windows-ci-eol-2026-11-08/README.md](development-records/runs/windows-ci-eol-2026-11-08/README.md) |
| 2026-11-08 | 證據 | Windows 原生建置、四語自檢與中文搬移修正 |  |  | profile鎖檢查失敗、中文空格路徑、list-langs失敗、摘要被截斷 | [development-records/runs/windows-ci-native-2026-11-08/README.md](development-records/runs/windows-ci-native-2026-11-08/README.md) |
| 2026-11-07 | 證據 | C07 開發紀錄 |  |  |  | [development-records/runs/c07-2026-11-07/README.md](development-records/runs/c07-2026-11-07/README.md) |
| 2026-11-07 | 證據 | C08 開發紀錄 |  |  |  | [development-records/runs/c08-2026-11-07/README.md](development-records/runs/c08-2026-11-07/README.md) |
| 2026-11-07 | 證據 | C09 首次流程開發紀錄 |  |  |  | [development-records/runs/c09-flow-2026-11-07/README.md](development-records/runs/c09-flow-2026-11-07/README.md) |
| 2026-11-07 | 證據 | C10 自動分析與元件協作開發紀錄 |  |  |  | [development-records/runs/c10-2026-11-07/README.md](development-records/runs/c10-2026-11-07/README.md) |
| 2026-11-06 | 證據 | C01 開發與驗收紀錄 |  |  |  | [development-records/runs/c01-2026-11-06/README.md](development-records/runs/c01-2026-11-06/README.md) |
| 2026-11-06 | 證據 | C02 開發與驗收紀錄 |  |  |  | [development-records/runs/c02-2026-11-06/README.md](development-records/runs/c02-2026-11-06/README.md) |
| 2026-11-06 | 證據 | C05 開發與驗收紀錄 |  |  |  | [development-records/runs/c05-2026-11-06/README.md](development-records/runs/c05-2026-11-06/README.md) |
| 2026-11-06 | 證據 | C06 開發與驗收紀錄 |  |  |  | [development-records/runs/c06-2026-11-06/README.md](development-records/runs/c06-2026-11-06/README.md) |
|  | 決策 | 0001：保留上游原始碼，透過本機轉接器接入 |  |  |  | [decisions/0001-upstream-source.md](decisions/0001-upstream-source.md) |
|  | 決策 | 0002：採用基本安裝包與選配元件管理 |  |  |  | [decisions/0002-base-and-optional-components.md](decisions/0002-base-and-optional-components.md) |
|  | 決策 | 0003：基本 OCR 語言擴充為繁中、英文、日文、韓文 |  |  |  | [decisions/0003-four-language-ocr.md](decisions/0003-four-language-ocr.md) |
|  | 決策 | 決策 0004：原生候選檔與可封裝來源分開驗證 |  |  |  | [decisions/0004-native-intake-license-gate.md](decisions/0004-native-intake-license-gate.md) |
|  | 決策 | 決策 0005：以固定最小原生來源取代未齊 DLL 證據的基本包候選 |  |  |  | [decisions/0005-minimal-native-source.md](decisions/0005-minimal-native-source.md) |
|  | 決策 | 決策 0006：內含 OCR 使用明確資產契約與唯讀自動路徑 |  |  |  | [decisions/0006-bundled-native-profile.md](decisions/0006-bundled-native-profile.md) |

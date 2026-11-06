# 開發與驗證原始日誌

2026-11-06 收集仍可取得的既有日誌，保留原始位元組。包含成功、預期失敗與調試失敗；**不把歷史失敗改列為通過，也不代表本次重新執行**。

原檔沒有來源提交時保持未知；不以檔名猜測 Windows 執行器。下表摘要僅從原始文字擷取，正式目前狀態另見 [驗證摘要](../../validation-results.json)。

| 原始日誌 | 可辨識的 unittest 摘要 |
| --- | --- |
| [layout-targeted-v2.log](layout-targeted-v2.log) | `FAILED (errors=1)` |
| [layout-targeted-v3.log](layout-targeted-v3.log) | `OK` |
| [layout-targeted.log](layout-targeted.log) | `FAILED (failures=1)` |
| [markitdown-011-install.log](markitdown-011-install.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-011-tests.log](markitdown-011-tests.log) | `OK (expected failures=1)` |
| [markitdown-borderless-complete.log](markitdown-borderless-complete.log) | `OK (expected failures=2)` |
| [markitdown-borderless-final.log](markitdown-borderless-final.log) | `OK (expected failures=1)` |
| [markitdown-borderless-frozen.log](markitdown-borderless-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-borderless-targeted.log](markitdown-borderless-targeted.log) | `OK (expected failures=1)` |
| [markitdown-borderless-verified.log](markitdown-borderless-verified.log) | `FAILED (errors=1, expected failures=2)` |
| [markitdown-borderless.log](markitdown-borderless.log) | `OK (expected failures=1)` |
| [markitdown-build.log](markitdown-build.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-continuation-final.log](markitdown-continuation-final.log) | `OK (expected failures=1)` |
| [markitdown-continuation-frozen.log](markitdown-continuation-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-continuation-tests.log](markitdown-continuation-tests.log) | `FAILED (failures=1, expected failures=1)` |
| [markitdown-crosscheck-frozen.log](markitdown-crosscheck-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-crosscheck.log](markitdown-crosscheck.log) | `OK (expected failures=1)` |
| [markitdown-devices-final.log](markitdown-devices-final.log) | `OK` |
| [markitdown-final-targeted.log](markitdown-final-targeted.log) | `OK (expected failures=1)` |
| [markitdown-frozen-review.log](markitdown-frozen-review.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-frozen-self-test.log](markitdown-frozen-self-test.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-full-layout.log](markitdown-full-layout.log) | `OK (expected failures=1)` |
| [markitdown-layout-acceptance-final.log](markitdown-layout-acceptance-final.log) | `OK` |
| [markitdown-layout-acceptance.log](markitdown-layout-acceptance.log) | `OK` |
| [markitdown-layout-build.log](markitdown-layout-build.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-layout-frozen-final.log](markitdown-layout-frozen-final.log) | `OK` |
| [markitdown-layout-frozen.log](markitdown-layout-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-licenses-final.log](markitdown-licenses-final.log) | `OK (expected failures=2)` |
| [markitdown-licenses-frozen.log](markitdown-licenses-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-licenses-tests.log](markitdown-licenses-tests.log) | `FAILED (failures=1, expected failures=2)` |
| [markitdown-onnx-final.log](markitdown-onnx-final.log) | `OK (expected failures=1)` |
| [markitdown-onnx-tests.log](markitdown-onnx-tests.log) | `FAILED (failures=1)` |
| [markitdown-release-prep-smoke.log](markitdown-release-prep-smoke.log) | `OK` |
| [markitdown-review-final.log](markitdown-review-final.log) | `OK (expected failures=1)` |
| [markitdown-review-verified.log](markitdown-review-verified.log) | `OK (expected failures=1)` |
| [markitdown-selftest-build.log](markitdown-selftest-build.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-selftest-final-build.log](markitdown-selftest-final-build.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-selftest-final-install.log](markitdown-selftest-final-install.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-selftest-install.log](markitdown-selftest-install.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-source-self-test.log](markitdown-source-self-test.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-sparse-targeted.log](markitdown-sparse-targeted.log) | `FAILED (unexpected successes=1)` |
| [markitdown-tables-final.log](markitdown-tables-final.log) | `OK (expected failures=1)` |
| [markitdown-tables-frozen.log](markitdown-tables-frozen.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [markitdown-tables-tests.log](markitdown-tables-tests.log) | `OK (expected failures=1)` |
| [markitdown-tests.log](markitdown-tests.log) | `FAILED (errors=1)` |
| [markitdown-windows-prep-final-tests.log](markitdown-windows-prep-final-tests.log) | `OK (expected failures=1)` |
| [markitdown-windows-prep-tests.log](markitdown-windows-prep-tests.log) | `OK (expected failures=1)` |
| [onnx-quality-probe.log](onnx-quality-probe.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [windows-tooling-011.log](windows-tooling-011.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [windows-tooling-final-validated.log](windows-tooling-final-validated.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [windows-tooling-final.log](windows-tooling-final.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [windows-tooling-verified.log](windows-tooling-verified.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |
| [windows-tooling.log](windows-tooling.log) | 無標準 unittest 摘要，查看原始建置／工具／調試內容 |

[返回開發紀錄](../README.md)

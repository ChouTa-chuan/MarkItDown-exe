# Windows CPU第二輪：健康工作逾時

2026-11-10，程式0.18.0。[Windows CI](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42784669436)（bbb82a2）編譯完成，原生staging健康仍未通過、checks0。新增的固定fixture診斷確認binding回傳「選配工作逾時，已停止該程序」，stderr為空；不能以此判定DLL或模型已壞，也沒有提高期限或把失敗列通過。

接著對固定公開health驗收補協定stdout與notify事件，同一位元組照常傳給原reader；只由該驗收顯式啟用45秒faulthandler堆疊，不含locals或文件文字，產品控制端仍不保存stderr。程序仍須在原120秒期限成功並通過原10項，診斷不替代真正推論。新2項／相關140項在鎖定環境通過，完整623尚未執行；0.17.2的611原基線不倒填。

原始頁與短診斷保存；完整需登入artifact未下載。C04 2/4、C11 2/5、完整7/12／歷史19/25保留，Windows問題仍待下一輪定位，沒有產品發行。

本地初次140項有1個新增測試錯誤（測試漏匯入os），原 `related-tests-progress.log` 保留未接受；補上匯入後完整重跑相關140項、0跳過且正常退出，見 `related-tests-progress-final.log`，此才是最終本地結果。

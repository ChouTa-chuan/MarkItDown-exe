# 基本包安裝程序中斷後續修準備

2026-11-09（台北），程式0.16.0 → **0.17.0**，架構0.4。新增12項、本地相關177/177；34模組591斷言（590通過、1既有ONNX繁體品質預期失敗），其中Qt元件管理23項斷言全過後exit -11，整輪accepted=false。Linux合成與真實檔案／入口／診斷契約不代表Windows中斷驗收，C11仍2/5／整體7/12。

新增固定hash的未完成標記、完整暫存metadata rename、原位置／匹配payload與明確續修、逐檔最終hash及過期空目錄清理後才清除標記。打包入口在未完成時退出3、不進入診斷／轉換。未知metadata、不同payload、變更過的舊過期檔或舊目錄內未知文件先拒絕；只重建固定source清單中的程式路徑，不讀取使用者文件。

Windows待實跑：CI-only停點安裝器與一般安裝器配同一payload，在intent、第一檔複製後、payload寫完／舊目錄未清三階段握手後真正taskkill自己PID子樹，改用一般Setup明確續修，各跑installed app10項、移除及未知文件／外部合成settings／model／SQLite／output／cache保留。不是只改幾個檔案假裝中斷，也不是斷電或自動失敗回滾。

前版改為真正0.16固定990e600來源、原controller／原spec／原generator獨立建置，支援本輪已知兩個build；舊CI已產生的不同hash安裝品不宣稱可直接相容。原版Setup與本版相容Setup分開，不以新版Pascal規則冒充舊版原安裝器。原0.16沒有新pending保護，未完成時須使用匹配的新安裝器續修；invalid／部分metadata寫入損壞、重啟／斷電、中斷解除安裝、各profile／人工／乾淨機仍待。完整C11及C03／C04／C09不提高，Linux退出錯誤已延伸至單一Qt管理模組，整輪不接受；ONNX品質與GPU／RAM軟預算限制保留。Setup只在CI工作目錄，不發布下載／tag／Release。

失敗模組單獨補驗23/23並正常exit0，原591整輪仍accepted=false；不以一次補驗抹去原失敗，也不宣稱退出問題已修復。原始崩潰／faulthandler與補驗日誌均保存。

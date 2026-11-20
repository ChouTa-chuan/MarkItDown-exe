# B3c CPU 固定候選原生元件與授權原文

比對基準為 A13b 的 CPU 候選 `b17d51bc`（run 44295044417）。依候選的原生檔和包內授權清冊，逐一核對鎖定 Windows wheels 的檔名、版本、封存 SHA-256、候選原生檔 SHA-256 與原文。保留 PE 一般匯入及延遲匯入，另列 wheel 有而候選沒有的原生檔。Microsoft 改名複本的 PE 身分放在 Microsoft 目錄，其位元組仍按原 wheel 對照。B3c 的檢查只讀取既有內容。[固定候選](../a13b-fixed-review-2026-11-18/cpu-source-review.json) · [逐檔證據與 B3 待補原文](notice-audit.json) · [內含元件目錄](../../../../packaging/embedded/cpu-windows.json)

| Windows wheel | 原文核對與 B3 待辦 |
| --- | --- |
| NumPy／OpenBLAS | NumPy、OpenBLAS、LAPACK、GCC runtime 與例外條款都有段落，OpenBLAS 版本沿用同位元組的 A12d Windows 觀測。B3 核對未知的 GCC runtime 版本及建置來源，發現歸屬缺口再補原文。 |
| Pillow | 既有 LICENSE 含主要影像元件。A12d 在同位元組 AVIF 承載檔觀測到 libaom 3.14.1 和 dav1d 1.5.3-0-gb546257。前者缺對應原文，後者只找到 libavif 內 `src/obu.c` 的 dav1d 歸屬。B3 補精確原文。libyuv 已有段落，先核對版本。Raqm 併入與否仍未知，FriBidi 為選配動態載入且 DLL 無隨 wheel 入包，先確認實際編譯範圍再決定是否補原文。 |
| opencv-python | Windows API 回報 OpenCV 5.0.0。建置宣告 JPEG、WebP、TIFF、OpenJPEG、Protobuf，各有既有原文段落。zlib 1.3.2、libpng 1.6.57 有 Windows build 宣告，對應段落卻標示其他平台，B3 以精確來源補 Windows 歸屬及原文。IPP ICV 在原文有 x86/x64 靜態連結說明。獨立 FFmpeg DLL 已排除，PE 與 Windows build 宣告無法確定所有靜態成員。 |
| ONNX Runtime | 有套件 MIT 與跨配置的 ThirdPartyNotices。B3 核對 Windows CPU 的實際成員、版本及歸屬後，再決定哪些需要補原文。 |
| pyclipper | wheel 自身 MIT 原文存在，wheel METADATA 與固定上游標頭均指出 Clipper 6.4.2，候選沒有 Clipper 專屬原文。BSL 1.0 有純機器可執行物件例外。B3 確認適用範圍及署名，建議保存固定標頭與原文。 |
| PyYAML | 已有 wrapper 的 MIT。獨立 LibYAML 0.2.5 原文缺口已核對，使用者同意 B3 以 supplemental 固定並綁 PyYAML。`.pyd` 的 0.2.5 字串只是較弱的佐證，主要依據是上游建置設定，並已用同位元組的 Windows 版本 API 複驗。 |
| Shapely／GEOS | 候選已附 Shapely 原文與 GEOS 的 LGPL 2.1 原文。兩個外部 GEOS DLL 有獨立檔名與雜湊；替換方式與 LGPL 做法待使用者決定。 |
| psutil | 已附套件 BSD 原文，PE 匯入為 Windows／CPython API；本次未找到另一個實際內含的第三方元件證據。 |

PE 匯入、授權文字及建置宣告都有範圍限制。未知版本維持 unknown，Windows build 宣告仍屬於建置線索。只要原文能對到確切元件，就指向候選既有文字，已確認缺漏與待釐清範圍分開列在逐檔證據。[LibYAML 停點及上游原文](../b3c-libyaml-notice-gap-2026-11-20/README.md) · [Clipper 固定原始碼](https://github.com/fonttools/pyclipper/blob/f998920369565dca56d346bb30c5741e273f0b9b/src/clipper.cpp) · [BSL 1.0 原文](https://www.boost.org/LICENSE_1_0.txt)

## GEOS 的來源、受管替換限制與選擇

Shapely 2.2.0 的上游發行流程設 `GEOS_VERSION=3.14.1`，Windows 腳本設定 `BUILD_SHARED_LIBS=ON`，再以 Delvewheel 修補 wheel。候選 PE 顯示 Shapely extension 匯入 `geos_c-…dll`，該 DLL 匯入 `geos-…dll`。Hosted Windows 2022 在 wheel 測試環境執行幾何面積後，確認程序載入兩份同候選 SHA-256 的外部 DLL，並從已載入的 C API 取得 `3.14.1-CAPI-1.20.5`。詳細檔名、匯入及雜湊見 `notice-audit.json`。[發行建置](https://github.com/shapely/shapely/blob/229c71f7128713b37201f3c77336d32b52467454/.github/workflows/release.yml) · [Windows 腳本](https://github.com/shapely/shapely/blob/229c71f7128713b37201f3c77336d32b52467454/ci/install_geos.cmd) · [GEOS 固定原始碼](https://github.com/libgeos/geos/tree/c389f532d25fe6228861d9b19339f9cb57ca4bdb) · [隨包原文](../../../../src/desktop_app/data/licenses/windows/shapely/wheel/shapely-2.2.0.dist-info/licenses/LICENSE_GEOS)

受管元件啟動前，`lease()` 經 `_ready()` 以簽章目錄中的檔案清單、大小與 SHA-256 呼叫 `verify_tree()`。因此直接覆蓋受管目錄的任一 GEOS DLL，就算架構及 ABI 相同也會被完整性檢查拒絕。測試環境裡的外部載入證據只確認 Windows 連結方式。A11 基本包能直接換 Qt DLL 的結果不能套到這條 CPU 路徑。[啟動租約與 _ready](../../../../src/desktop_app/components/lifecycle.py) · [逐檔驗證](../../../../src/desktop_app/components/archives.py)

- **設計可驗證的自建／自帶元件路徑**。隨包保留原文、固定原始碼與建置指引。替代 DLL 需維持 CPU 架構、ABI、Delvewheel 改名及匯入名稱相容；另外需要受支援、具自身驗證資料的元件路徑，才能在保留受管版完整性檢查的情況下驗收。B3 可比較乾淨受管版、直接覆蓋會被拒的情形，以及受支援路徑中的替代 GEOS 與移除反例。
- **增加對應來源與重建材料**。可隨元件提供固定 GEOS 原始碼或確切取得方式，以及建置／修補命令和必要變更，讓使用者能重建並測試替換。仍需決定如何交付來源資料與驗收。

目前已驗證外部載入與同位元組的版本回報，並從受管啟動路徑查證直接換檔的限制。尚無受支援的替換驗收，也未做實體機驗收。`cpu-geos` 維持 open，做法與充分性由使用者決定。

## Microsoft 六檔與處理選擇

按 A10 格式，逐檔保存來源路徑、候選 bytes、PE 版本、簽章身分與官方 Redist 同名檔的 SHA-256。四個根目錄檔的 PE 身分來自固定候選審閱，兩個改名檔新增 Windows 簽章觀測並核對到相同 wheel bytes。六檔簽章均為 `Valid`。[逐檔目錄](../../../../packaging/microsoft/cpu-windows.json) · [A13b 官方 Redist 探測](../a13b-fixed-review-2026-11-18/microsoft-probe-7cf098e.json) · [A13-1 使用者原決定](../../../history/status/2026-11-18-a13-decisions.md)

| 候選檔 | PE 版本 | 逐位元符合 A13b 官方 Redist |
| --- | --- | --- |
| 根目錄 `MSVCP140_1.dll`、`msvcp140.dll` | 14.44.35211.0 | 是 |
| 根目錄 `vcruntime140.dll`、`vcruntime140_1.dll` | 14.42.34438.0 | 否，來源為 CPython 安裝 |
| NumPy `msvcp140-a4c2…dll` | 14.40.33810.0 | 否 |
| Shapely `msvcp140-0fa7…dll` | 14.44.35229.0 | 否 |

使用者可以在 B3 讓 CPU 比照基本包 A13-1，將兩個根目錄 `vcruntime` 換成 Visual Studio 官方 Redist 並重跑 CPU 驗收，對兩個改名複本保留原 wheel 路徑並逐檔揭露。若保留現狀，仍要釐清 CPython 及 wheel 來源各自的適用範圍，並保存相應的再散布決定。有效簽章只能用來確認這些 bytes 的身分。`cpu-microsoft` 維持 open，條款範圍與做法由使用者決定。[微軟條款與 REDIST 清單證據](../a10-microsoft-runtime-2026-11-17/README.md)

## 驗證與證據取得

- Hosted Windows 2022 run [44755140396](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44755140396) 使用 `392d094` 的觀測程式及固定 CPU 來源 `b17d51bc`。CPU 報告 artifact `cpu-native-observation-reports`，ID `14637211999`，digest `sha256:d4a988f30e7947dd150f4bc9e5a55f2e38684ba9bcac94698398b3162020736b`，到期台北時間 2026-11-27 22:37。由 job `136352780732` 的 check annotation 序號重組、解壓並對上公告的 SHA-256，保存小型 JSON 供 gates 重驗。
- 基本包與 CPU gates 均 exit 0。基本包的旗標、條目與阻擋清單相同，完整 SBOM 與可發布為 false，已揭露與可再散布為 true。CPU 四旗標仍為 false，各旗標的阻擋條目清單相同。`cpu-wheels` 新列實際未知版本，`cpu-geos` 和 `cpu-microsoft` 記為需使用者決定。三條維持 open。
- 授權原文、安裝包、worker、模型、spec、鎖檔及候選均沿用 B3c 之前的內容。Linux 回歸見[進度資料](../../../progress.json)。

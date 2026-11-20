# B3c 暫停於 LibYAML 原文查證

固定 CPU 候選 `b17d51b` 的 `yaml/_yaml.cp312-win_amd64.pyd` 已與 PyYAML 6.0.3 wheel 內的同名檔案核對大小與 SHA-256。PyYAML 上游 Windows 建置固定 LibYAML 0.2.5 並設定 `YAML_DECLARE_STATIC=1`。一致的候選位元組含 `0.2.5` 字串，PE 匯入清單沒有外部 LibYAML DLL。版本判定的主要依據是上游建置設定，`.pyd` 內的 `0.2.5` 字串只是較弱的佐證。這是靜態及上游建置證據，Windows 執行期 API 留待後續觀測。[PyYAML 固定建置](https://github.com/yaml/pyyaml/blob/49790e73684bebad1df05ef8d828fa12f685bffb/.github/workflows/ci.yaml)

固定候選的 PyYAML 原文清單只有 PyYAML LICENSE。已驗證的 Windows wheel 亦只附這一份。LibYAML 0.2.5 上游 License 與它的 MIT 條文相同，Ingy döt Net 的著作權年份分別為 2017–2020 與 2017–2021，SHA-256 不同。專案隨包授權清冊與保存的候選套件授權清單都找不到 LibYAML 原文的指紋。要以逐件原文完成這筆對照，會需要額外的原文及套件綁定。此處保留可查證的來源與差異，法律適用範圍交使用者確認。[LibYAML 固定 License](https://github.com/yaml/libyaml/blob/2c891fc7a770e8ba2fec34fc6b545c672beb37e6/License) · [逐檔指紋與證據](libyaml-gap.json)

固定 CPU 報告 run [44295044417](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/44295044417) 的 artifact 在 API 可查，保存了報告指紋。原 artifact 儲存端下載回覆 403，所以此次比對用已保存的 source-review 和實際鎖定 wheel。

GEOS 初步查證確認 Shapely 2.2.0 的 `LICENSE_GEOS` 已隨固定候選保存，內容含 LGPL 2.1 原文。兩個 GEOS DLL 與鎖定 wheel 的雜湊相符，PE 確認 Shapely 擴充模組透過外部 C API DLL 動態連結。GEOS 原始碼、版本及實際替換驗收，其餘 wheel 目錄、Microsoft 六檔對照與反例測試仍待續作。

依使用者指示在發現需要補原文時暫停。兩個 profile 的 gates 以既有登記表執行均 exit 0，CPU 四旗標仍為 false。此次紀錄只保存查證停點。

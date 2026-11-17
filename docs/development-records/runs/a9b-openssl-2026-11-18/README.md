# A9b cryptography 內含 OpenSSL 原文

此目錄保存真正 hosted Windows 的 OpenSSL API 觀測，非 Linux 推論或實體使用者機驗收。來源為 PR 21 初始 head 6187e0e，run 44142370284。文字 API、數值 API 與 A6 的 _rust.pyd SHA-256 一致；版本沿用 runtime-observed，不以 PE 字串當 wheel-declared。

原文位於 src/desktop_app/data/licenses/windows/supplemental/cryptography.txt，上游 tag、固定 commit、Git blob 與 SHA-256 在 packaging/cryptography/openssl.json，元件細節在 packaging/embedded/base-windows.json。Rust 相依仍未知，cryptography 義務維持 open。初次 Linux／CPU CI 因授權衍生清單未重建而失敗，修正與最終驗證收尾補記；沒有改鎖檔、spec 或計數口徑。

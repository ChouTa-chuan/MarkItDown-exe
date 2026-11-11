# 首次Pages部署

2026-11-11（台北），來源73f4ebb，[run42986578102](https://github.com/ChouTa-chuan/MarkItDown-exe/actions/runs/42986578102)。建置job成功，部署job在configure-pages讀取站台時回覆Not Found，網站未發布。正式發布驗證尚未執行。公開原頁與錯誤保存，不當作部署成功。

需專案管理員在Settings → Pages將Source設為GitHub Actions；現有GITHUB_TOKEN不能首次建立Pages站台，官方action.yml已明列。沒有索取或外洩PAT，也沒有修改雲端網路設定；使用者設定完成後，既有流程可部署並驗HTTP 200／hash。

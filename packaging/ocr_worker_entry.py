"""選配 CPU worker 專用入口，打包時不載入主程式 Qt／格式轉換器。"""
import multiprocessing
import os

if __name__=='__main__':
    multiprocessing.freeze_support()
    # 僅固定公開health驗收顯式啟用；輸出Python堆疊、不含locals或文件文字。
    # 產品控制端仍排空stderr，不會自動保存這些內容，也不延長工作逾時或放寬健康門檻。
    diagnostic=os.environ.get('MARKITDOWN_FIXED_HEALTH_TRACE')=='1'
    if diagnostic:
        import faulthandler
        faulthandler.enable();faulthandler.dump_traceback_later(45)
    try:
        from desktop_app.component_workers.server import main
        raise SystemExit(main())
    finally:
        if diagnostic:faulthandler.cancel_dump_traceback_later()

"""選配 CPU worker 專用入口，打包時不載入主程式 Qt／格式轉換器。"""
import multiprocessing

if __name__=='__main__':
    multiprocessing.freeze_support()
    from desktop_app.component_workers.server import main
    raise SystemExit(main())

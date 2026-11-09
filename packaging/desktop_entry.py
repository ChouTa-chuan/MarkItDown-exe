"""打包程式入口：先處理子程序啟動，再載入自我檢查、CLI 或 Qt。"""
import multiprocessing
import sys


def installation_incomplete(executable, frozen):
    """來源模式不受安裝標記影響；打包模式在任何核心匯入前阻擋半套程式。"""
    if not frozen:return False
    from pathlib import Path
    return any((Path(executable).parent/name).exists() or (Path(executable).parent/name).is_symlink()
               for name in ('.markitdown-install.pending','.markitdown-install.pending.new'))


if __name__ == "__main__":
    multiprocessing.freeze_support()
    # 尚未修復的安裝不能進入診斷／轉換；只檢查本程式目錄，不讀取使用者文件。
    if installation_incomplete(sys.executable,getattr(sys,'frozen',False)):
        print('安裝尚未完成，請重新執行原安裝程式完成修復。',file=sys.stderr)
        raise SystemExit(3)
    if '--self-test' in sys.argv:
        sys.argv.remove('--self-test')
        from desktop_app.diagnostics import main
        raise SystemExit(main(sys.argv[1:]))
    if '--verify-help-assets' in sys.argv:
        from desktop_app.build_profile import load_profile
        if load_profile() is not None:
            from desktop_app.diagnostics import verify_help
            verify_help()
            raise SystemExit(0)
        from importlib.resources import files
        from pathlib import Path
        import json,hashlib
        for name in ['user-guide.md','third-party.md']:
            assert len(files('desktop_app').joinpath('data/'+name).read_text(encoding='utf-8'))>100
        root=Path(files('desktop_app').joinpath('data/licenses'))
        inventory=json.loads((root/'windows/inventory.json').read_text())
        assert inventory['package_count']==len(inventory['packages'])>0
        for name,digest in inventory['files'].items():
            assert hashlib.sha256((root/'windows'/name).read_bytes()).hexdigest()==digest
        assert (root/'python-runtime/LICENSE.txt').is_file()
        assert (root/'models/tessdata-fast-Apache-2.0.txt').is_file()
        raise SystemExit(0)
    if "--verify-model-manifest" in sys.argv:
        from desktop_app.models import manifest
        spec = manifest()
        assert set(spec["files"]) == {"chi_tra.traineddata", "eng.traineddata", "LICENSE"}
        raise SystemExit(0)
    if "--verify-onnx-models" in sys.argv:
        from desktop_app.onnx_ocr import verify_models
        verify_models()
        raise SystemExit(0)
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from desktop_app.cli import main
    else:
        from desktop_app.desktop import main
    raise SystemExit(main())

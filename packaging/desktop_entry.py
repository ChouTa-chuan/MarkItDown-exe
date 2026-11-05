"""Frozen multiprocessing entry: handle child bootstrap before importing Qt."""
import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if '--verify-help-assets' in sys.argv:
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

"""Frozen multiprocessing entry: handle child bootstrap before importing Qt."""
import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if "--verify-model-manifest" in sys.argv:
        from desktop_app.models import manifest
        spec = manifest()
        assert set(spec["files"]) == {"chi_tra.traineddata", "eng.traineddata", "LICENSE"}
        raise SystemExit(0)
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from desktop_app.cli import main
    else:
        from desktop_app.desktop import main
    raise SystemExit(main())

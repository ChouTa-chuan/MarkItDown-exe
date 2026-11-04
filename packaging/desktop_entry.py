"""Frozen multiprocessing entry: handle child bootstrap before importing Qt."""
import multiprocessing
import sys

if __name__ == "__main__":
    multiprocessing.freeze_support()
    if "--cli" in sys.argv:
        sys.argv.remove("--cli")
        from desktop_app.cli import main
    else:
        from desktop_app.desktop import main
    raise SystemExit(main())

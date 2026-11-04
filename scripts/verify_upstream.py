"""Check the original upstream runtime source has not drifted silently."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1] / "vendor/markitdown"
manifest = json.loads((root / "UPSTREAM.json").read_text())
for name, expected in manifest["files"].items():
    if hashlib.sha256((root / name).read_bytes()).hexdigest() != expected:
        raise SystemExit(f"Upstream source mismatch: {name}")
print(f"Verified {len(manifest['files'])} upstream source files")

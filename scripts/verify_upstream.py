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
fixtures = Path(__file__).resolve().parents[1] / 'tests/fixtures'
fixture_manifest = fixtures / 'UPSTREAM.json'
if fixture_manifest.exists():
    metadata=json.loads(fixture_manifest.read_text())
    if metadata['commit']!=manifest['commit'] or hashlib.sha256((fixtures/'upstream-sparse.pdf').read_bytes()).hexdigest()!=metadata['sha256']:
        raise SystemExit('Upstream PDF fixture provenance/hash mismatch')
    print('Verified upstream PDF fixture and matching commit')

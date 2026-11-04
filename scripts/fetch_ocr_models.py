"""Explicit developer download; pinned official source, TLS and SHA-256 checks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def fetch(directory):
    manifest = json.loads((ROOT / "docs/ocr-models.json").read_text())
    directory.mkdir(parents=True, exist_ok=True)
    for name, expected in manifest["files"].items():
        target = directory / name
        if target.exists():
            if hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise ValueError(f"既有檔案驗證失敗，未覆寫：{target}")
            print(f"Verified existing: {name}")
            continue
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{manifest['commit']}/{name}"
        temporary = None
        try:
            with urllib.request.urlopen(url, timeout=60) as response:
                with tempfile.NamedTemporaryFile(dir=directory, delete=False) as output:
                    temporary = Path(output.name)
                    digest = hashlib.sha256()
                    total = 0
                    while block := response.read(65536):
                        total += len(block)
                        if total > 16*1024**2:
                            raise ValueError("模型超過允許大小。")
                        digest.update(block)
                        output.write(block)
            if digest.hexdigest() != expected:
                raise ValueError(f"下載完整性驗證失敗：{name}")
            os.link(temporary, target)
            print(f"Downloaded and verified: {name}")
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="下載繁體中文／英文 OCR 模型，約 6.4 MB")
    parser.add_argument("directory", type=Path)
    fetch(parser.parse_args().directory)

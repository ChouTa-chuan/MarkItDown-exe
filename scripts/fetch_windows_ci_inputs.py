"""只為 Windows 驗證 CI 取得固定公開輸入；串流驗 hash，不執行下載的程式。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import urllib.error
import urllib.request

from desktop_app.components.registry import _chain
from desktop_app.languages import model_manifest

ROOT = Path(__file__).resolve().parents[1]


def fetch(url, target, expected_hash, expected_bytes=None, *, limit=128 * 1024**2, opener=urllib.request.urlopen):
    _chain(target)
    if target.exists():
        raise FileExistsError(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with opener(url, timeout=60) as response, tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as output:
            temporary = Path(output.name)
            digest, size = hashlib.sha256(), 0
            while block := response.read(65536):
                size += len(block)
                if size > limit or (expected_bytes is not None and size > expected_bytes):
                    raise ValueError('CI 固定來源超過容量。')
                digest.update(block)
                output.write(block)
            output.flush()
            os.fsync(output.fileno())
        if digest.hexdigest() != expected_hash or (expected_bytes is not None and size != expected_bytes):
            raise ValueError('CI 固定來源完整性不符。')
        os.link(temporary, target)
        return dict(url=url, file=target.name, sha256=digest.hexdigest(), bytes=size)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def fetch_with_retry(*args, operation=fetch, wait=time.sleep, **kwargs):
    """只重試暫時網路錯誤；hash／長度不符不得以重試掩蓋。"""
    for attempt in range(3):
        try:
            return operation(*args, **kwargs)
        except urllib.error.HTTPError as exc:
            if exc.code not in (429, 500, 502, 503, 504) or attempt == 2:
                raise
            retry = exc.headers.get('Retry-After') if exc.headers else None
            if retry is not None:
                from datetime import datetime, timezone
                from email.utils import parsedate_to_datetime
                delay = int(retry) if retry.isdigit() else max(0, (parsedate_to_datetime(retry)-datetime.now(timezone.utc)).total_seconds())
            else:
                delay = 2**attempt
            wait(delay)
        except (urllib.error.URLError, TimeoutError):
            if attempt == 2: raise
            wait(2**attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    _chain(args.output)
    if args.output.exists():
        parser.error('請使用新的 CI 輸入目錄。')
    args.output.mkdir(parents=True)
    contract = json.loads((ROOT/'packaging/native/minimal-windows.json').read_text())
    records = []
    for record in [*contract['source_archives'], contract['toolchain_archive']]:
        records.append(fetch_with_retry(record['url'], args.output/record['file'], record['sha256'], record['bytes']))
    models = model_manifest()
    for name, digest in models['files'].items():
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{models['commit']}/{name}"
        records.append(fetch_with_retry(url, args.output/'models'/name, digest, limit=16*1024**2))
    (args.output/'downloads.json').write_text(json.dumps(dict(records=records), indent=2)+'\n')
    print('Fixed CI downloads verified:', len(records))


if __name__ == '__main__':
    main()

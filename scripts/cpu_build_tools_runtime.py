"""唯讀檢查受控 Windows 重建的 CArchive，並執行實際 worker 的公開 OCR 驗收。"""
import argparse
import dis
from importlib import metadata
import json
import marshal
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import CodeType
from unittest.mock import patch

from candidate_review import canonical
from cpu_build_tools_audit import module_in_scope, sha

ROOT = Path(__file__).resolve().parents[1]


def tool_imports(code):
    """列出啟動腳本內明示的匯入，包含巢狀程式碼；不執行封存中的 bytecode。"""
    imports = {instruction.argval for instruction in dis.get_instructions(code)
               if instruction.opname == 'IMPORT_NAME' and module_in_scope(instruction.argval)}
    for value in code.co_consts:
        if isinstance(value, CodeType):
            imports.update(tool_imports(value))
    return imports


def inspect(bundle, original):
    from PyInstaller.archive.readers import CArchiveReader

    entry = bundle/'MarkItDownOCRWorker.exe'
    assets = bundle/'_internal/worker-assets'
    manifest = json.loads((assets/'native/python-modules.json').read_bytes())
    archive = CArchiveReader(entry)
    pyz_names = set(archive.open_embedded_archive('PYZ.pyz').toc)
    source_names = {row['name'] for row in manifest['modules']}
    scripts = []
    for name, info in archive.toc.items():
        if info[-1] not in ('s', 'm', 'M'):
            continue
        raw = archive.extract(name)
        imports = tool_imports(marshal.loads(raw))
        scripts.append(dict(name=name, type=info[-1], bytes=len(raw), sha256=sha(raw),
                            explicit_tool_imports=sorted(imports)))
    installed = json.loads((assets/'installed-manifest.json').read_bytes())['files']
    prefix = '_internal/worker-assets/'
    asset_rows = [row for row in original['physical_files'] if row['path'].startswith(prefix)]
    # 逐檔驗證讀到的是本次重建的實體資產，並對回原候選相同 bytes。
    asset_matches, asset_differences = [], []
    for row in asset_rows:
        name = row['path'].removeprefix(prefix)
        data = (assets/name).read_bytes()
        if (len(data), sha(data)) != (row['bytes'], row['sha256']):
            asset_differences.append(name)
        elif installed.get(name) == row['sha256']:
            asset_matches.append(name)
    pure_sha = sha(canonical(manifest['modules']))
    return dict(entry_sha256=sha(entry.read_bytes()), entry_bytes=entry.stat().st_size,
                version=metadata.version('pyinstaller'), startup_entries=scripts,
                pyz_sources_sha256=pure_sha,
                original_pyz_sources_match=pure_sha == original['pure_modules_sha256'],
                pyz_names_match_manifest=pyz_names == source_names,
                pyz_tool_modules=sorted(name for name in pyz_names if module_in_scope(name)),
                integrity_checked_matching_assets=asset_matches, different_assets=asset_differences)


def smoke(bundle, source):
    from desktop_app.component_workers.client import WorkerRunner
    from desktop_app.core import State
    from desktop_app.resources import MIB, Policy

    fixture = source/'src/desktop_app/data/worker-health.png'
    with tempfile.TemporaryDirectory(prefix='b3d-cpu-runtime-') as temporary:
        folder = Path(temporary)
        runner = WorkerRunner((str(bundle/'MarkItDownOCRWorker.exe'),), folder/'guard.lock',
                              Policy(budget=2048*MIB, reserve=0), require_frozen=True,
                              timeout=120, handshake_timeout=60)
        with patch.dict(os.environ, {'PATH': '', 'PYTHONPATH': '', 'PYTHONHOME': ''}):
            health = runner.run(operation='health')
            ocr = runner.run(fixture, folder/'fixture.md')
        if any(x.state != State.COMPLETED for x in (health, ocr)):
            raise ValueError(f'Frozen CPU fixture failed: {health.message}, {ocr.message}')
        if health.report['health_passed'] is not True or any(
            x.report['runtime']['frozen'] is not True
            or x.report['providers'] != ['CPUExecutionProvider']*3
            or 'WORKER HEALTH CHECK 12345' not in ' '.join(x.report['text'].split())
            for x in (health, ocr)
        ):
            raise ValueError('Frozen CPU fixture results differ')
    return dict(fixture_sha256=sha(fixture.read_bytes()), health_passed=True, ocr_passed=True,
                providers=ocr.report['providers'], frozen=True, path_empty=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--original', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    original = json.loads(args.original.read_bytes())
    source = args.source.resolve()
    head = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if sys.platform != 'win32' or head != original['candidate_source']:
        raise ValueError('Expected the fixed source rebuilt on Windows')
    bundle = args.bundle.resolve()
    data = dict(check='cpu-build-tools-runtime', schema_version=1, source_commit=head,
                python=sys.version.split()[0], run_id=os.environ.get('GITHUB_RUN_ID'),
                archive=inspect(bundle, original), smoke=smoke(bundle, source))
    with args.output.open('xb') as output:
        output.write(canonical(data)+b'\n')
    # 只輸出指定的封存摘要及合成測試狀態，不傳出任何產品 bytes。
    print('::notice title=B3d frozen archive::'+canonical(data).decode('utf-8')
          .replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A'))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError) as error:
        message = str(error).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::error title=B3d frozen archive::{type(error).__name__}: {message}')
        raise SystemExit(1) from error

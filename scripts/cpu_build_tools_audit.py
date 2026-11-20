"""從固定 Windows CPU 候選的原始 provenance 擷取建置工具證據。"""
import argparse
import base64
import gzip
import hashlib
import json
from pathlib import Path
import re

from candidate_inventory import canonical

ROOT = Path(__file__).resolve().parents[1]
BASIS = ROOT/'docs/development-records/runs/a13b-fixed-review-2026-11-18/cpu-source-review.json'
ROOTS = frozenset(('setuptools', 'pip', 'pyinstaller', '_pyinstaller_hooks_contrib',
                   'pkg_resources', '_distutils_hack', 'distutils', 'ensurepip'))
TOOL_OWNERS = frozenset(('setuptools', 'pip', 'pyinstaller', 'pyinstaller-hooks-contrib'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def module_in_scope(name):
    """只接受完整模組根，另保留 PyInstaller 的啟動腳本命名。"""
    root = name.split('.', 1)[0].lower()
    return root in ROOTS or root.startswith(('pyi_rth_', 'pyimod')) or root == 'pyiboot01_bootstrap'


def file_in_scope(row):
    if any(owner['name'] in TOOL_OWNERS for owner in row['owners']):
        return True
    # 路徑只提供待核對的線索，套件歸屬沿用候選清單中的 owners。
    return any(
        part.lower() in ROOTS
        or re.fullmatch(r'(?:setuptools|pip|pyinstaller(?:_hooks_contrib)?)-[^/]+\.dist-info', part, re.I)
        or part.lower().startswith(('pyi_rth_', 'pyimod', 'pyiboot01_'))
        for part in row['path'].split('/')
    )


def extract(raw, review):
    """先用固定審閱綁原檔與兩份完整清單，再節錄相關列。"""
    if sha(raw) != review['provenance_report_sha256']:
        raise ValueError('Fixed CPU provenance fingerprint mismatch')
    report = json.loads(raw)
    if (report['profile'] != review['profile'] or report['profile'] != 'cpu'
            or report['source_commit'] != review['selection']['source_commit']
            or report['accepted'] is not True or report['inventory_reverified'] is not True
            or report['host_platform'] != 'win32'):
        raise ValueError('Provenance does not identify the accepted Windows CPU candidate')
    inventory = report['candidate_inventory']
    archives = report['python_archives']
    modules = archives['pure_modules']
    library = archives['base_library']
    if sha(canonical(inventory)) != review['inventory_sha256']:
        raise ValueError('Fixed CPU physical inventory fingerprint mismatch')
    if sha(canonical(modules)) != review['pure_modules_sha256']:
        raise ValueError('Fixed CPU pure module fingerprint mismatch')
    if library != review['classification_input']['report']['python_archives']['base_library']:
        raise ValueError('Fixed CPU base_library inventory differs')
    return dict(
        schema_version=1,
        check='cpu-build-tools-audit',
        candidate_source=report['source_commit'],
        candidate_run=review['selection']['run_id'],
        candidate_sha256=review['candidate']['sha256'],
        provenance_sha256=review['provenance_report_sha256'],
        inventory_sha256=review['inventory_sha256'],
        pure_modules_sha256=review['pure_modules_sha256'],
        counts=dict(files=len(inventory['files']), pure_modules=len(modules), library_members=len(library['members'])),
        build_environment_packages=[dict(name=p['name'], version=p['version'])
                                    for p in report['packages'] if p['name'] in TOOL_OWNERS],
        physical_files=[r for r in inventory['files'] if file_in_scope(r)],
        pyz_sources=[r for r in modules if module_in_scope(r['name']) or r.get('distribution') in TOOL_OWNERS],
        base_library_members=[r for r in library['members']
                              if module_in_scope(r['name'].removesuffix('.pyc').replace('/', '.'))],
    )


def publish(report, page):
    raw = canonical(report)
    encoded = base64.b64encode(gzip.compress(raw, mtime=0)).decode('ascii')
    chunks = [encoded[i:i+2200] for i in range(0, len(encoded), 2200)]
    if not 0 < len(chunks) <= 24:
        raise ValueError('CPU build tool evidence exceeds annotation budget')
    for index, data in enumerate(chunks[page*8:(page+1)*8], page*8+1):
        print('::notice title=CPU build tool evidence::'+json.dumps(
            dict(check=report['check'], sha256=sha(raw), part=index, parts=len(chunks), data=data),
            separators=(',', ':')
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provenance', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--page', type=int, choices=range(3), required=True)
    args = parser.parse_args()
    report = extract(args.provenance.read_bytes(), json.loads(BASIS.read_text(encoding='utf-8')))
    if args.page == 0:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write('\n')
    publish(report, args.page)


if __name__ == '__main__':
    main()

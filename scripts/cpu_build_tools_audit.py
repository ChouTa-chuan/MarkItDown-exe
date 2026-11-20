"""從固定 Windows CPU 候選的原始 provenance 擷取建置工具證據。"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from candidate_review import canonical

ROOT = Path(__file__).resolve().parents[1]
BASIS = ROOT/'docs/development-records/runs/a13b-fixed-review-2026-11-18/cpu-source-review.json'
LICENSE_INVENTORY = ROOT/'src/desktop_app/data/licenses/windows/inventory.json'
REPO_COPIES = ('_internal/worker-assets/licenses/windows/',
               '_internal/worker-assets/installed/markitdown-desktop/original/desktop_app/data/licenses/windows/')
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
        physical_files=[{k: r[k] for k in ('path', 'bytes', 'sha256', 'role', 'owners')}
                        for r in inventory['files'] if file_in_scope(r)],
        pyz_sources=[r for r in modules if module_in_scope(r['name']) or r.get('distribution') in TOOL_OWNERS],
        base_library_members=[r for r in library['members']
                              if module_in_scope(r['name'].removesuffix('.pyc').replace('/', '.'))],
    )


def repo_notice_sources(report, inventory, license_root):
    """repo 授權目錄的複本需同時符合封存記錄及實體 bytes，才可補上來源 wheel。"""
    packages = {row['name']: row for row in inventory['packages'] if row['name'] in TOOL_OWNERS}
    bindings = []
    for row in report['physical_files']:
        prefix = next((p for p in REPO_COPIES if row['path'].startswith(p)), None)
        if prefix is None:
            continue
        key = row['path'].removeprefix(prefix)
        name = key.partition('/')[0]
        package = packages.get(name)
        if package is None or inventory['files'].get(key) != row['sha256']:
            raise ValueError('Fixed CPU notice has no matching wheel inventory entry: ' + key)
        data = (license_root/key).read_bytes()
        if (len(data), sha(data)) != (row['bytes'], row['sha256']):
            raise ValueError('Fixed CPU notice bytes differ from repository copy: ' + key)
        bindings.append(dict(path=row['path'], bytes=row['bytes'], sha256=row['sha256'],
                             source_path=key, distribution=name, version=package['version'],
                             wheel=package['wheel'], wheel_sha256=package['wheel_sha256']))
    return bindings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    inputs = parser.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--provenance', type=Path)
    inputs.add_argument('--repo-copies', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if args.provenance is not None:
        report = extract(args.provenance.read_bytes(), json.loads(BASIS.read_bytes()))
    else:
        original = json.loads(args.repo_copies.read_bytes())
        inventory = LICENSE_INVENTORY.read_bytes()
        report = dict(candidate_source=original['candidate_source'],
                      original_audit_sha256=sha(canonical(original)), inventory_sha256=sha(inventory),
                      files=repo_notice_sources(original, json.loads(inventory), LICENSE_INVENTORY.parent))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    try:
        main()
    except (KeyError, OSError, ValueError) as error:
        # 使用 CI 註記保留錯誤類型，報告下載站及實際內容不進入訊息。
        message = str(error).replace('%', '%25').replace('\r', '%0D').replace('\n', '%0A')
        print(f'::error title=CPU build tool audit::{type(error).__name__}: {message}')
        raise SystemExit(1) from error

"""建置後檢查隨包原文、metadata 與原生來源指紋，不執行或核准產物。"""
import argparse
from email.parser import Parser
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tomllib

from build_provenance import sha256
from candidate_inventory import component_inventory, inventory, verify_inventory
from bundle_filters import is_excluded_name
from native_identity import identity_errors, summarize

# 建置時為非 wheel 來源原生檔記錄的身分欄位；原樣帶進報告，缺少的欄位不補造。
IDENTITY_FIELDS = ('source_directory', 'company', 'product', 'file_version', 'signature_status', 'signer',
                   'identity_error')


def contained_file(root, value):
    """清單僅能引用包內普通檔案，連結及 Windows 大小寫別名另由遍歷拒絕。"""
    relative = PurePosixPath(value)
    if not value or '\\' in value or ':' in value or relative.is_absolute() or any(p in ('..', '.') for p in value.split('/')):
        raise ValueError('Unsafe manifest path: ' + value)
    path = root.joinpath(*relative.parts)
    if any(p.is_symlink() for p in (path, *path.parents)) or not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Missing or linked bundle file: ' + value)
    return path


def verify_hashes(root, files):
    if not isinstance(files, dict) or not files:
        raise ValueError('Empty fingerprint manifest')
    for name, digest in files.items():
        if not isinstance(digest, str) or not re.fullmatch('[0-9a-f]{64}', digest) or sha256(contained_file(root, name)) != digest:
            raise ValueError('Fingerprint mismatch: ' + name)


def audit(bundle, profile, expected_version):
    """source 與 bundled 指紋分開記錄，容許 PyInstaller 處理 binary，但明列差異。"""
    bundle = Path(bundle).absolute()
    aliases = set()
    for path in bundle.rglob('*'):
        key = path.relative_to(bundle).as_posix().casefold()
        if path.is_symlink() or key in aliases:
            raise ValueError('Bundle link or case alias: ' + key)
        aliases.add(key)
    if profile == 'base':
        assets = bundle/'_internal/desktop_app/data'
        build = json.loads(contained_file(assets, 'build-profile.json').read_text(encoding='utf-8'))
        if build['source_version'] != expected_version:
            raise ValueError('Application version mismatch')
        verify_hashes(assets, build['assets'])
        installed = json.loads(contained_file(assets, 'licenses/installed/manifest.json').read_text(encoding='utf-8'))
        metadata_prefix, bootloader = 'licenses/installed/', assets/'licenses/bootloader'
        python_license = 'licenses/python-runtime/LICENSE.txt'
        expected = {**build['runtime_packages'], **build['local_packages']}
        if {p['name']:p['version'] for p in installed['packages']} != expected:
            raise ValueError('Runtime package list mismatch')
    elif profile == 'cpu':
        assets = bundle/'_internal/worker-assets'
        installed = json.loads(contained_file(assets, 'installed-manifest.json').read_text(encoding='utf-8'))
        verify_hashes(assets, installed['files'])
        metadata_prefix, bootloader = 'installed/', assets/'bootloader'
        python_license = 'python-runtime/LICENSE.txt'
    else:
        raise ValueError('Unknown profile')
    if not contained_file(assets, python_license).stat().st_size:
        raise ValueError('Empty Python original notice')
    loader = json.loads(contained_file(bootloader, 'manifest.json').read_text(encoding='utf-8'))
    verify_hashes(bootloader, loader['files'])
    if loader['name'] != 'pyinstaller' or not loader['version']:
        raise ValueError('Bootloader provenance mismatch')
    packages, pending = [], []
    for row in installed['packages']:
        name = row['name']
        raw = contained_file(assets, metadata_prefix+name+'/METADATA').read_text(encoding='utf-8')
        value = Parser().parsestr(raw)
        normalized = re.sub('[-_.]+', '-', value.get('Name', '')).lower()
        if normalized != name or value.get('Version') != row['version']:
            raise ValueError('Installed METADATA mismatch: ' + name)
        notices = row['notice_files']
        for notice in notices:
            if not contained_file(assets, notice).stat().st_size:
                raise ValueError('Empty installed notice: ' + notice)
        if not notices:
            pending.append(name)
        # 版本與授權宣告保留原metadata字串，不能把License欄位當作已核准SPDX。
        prefix=assets.relative_to(bundle).as_posix()
        references=[]
        for notice in dict.fromkeys([*notices,*[p['path'] for p in row.get('supplemental_sources',[])]]):
            file=contained_file(assets,notice)
            references.append(dict(path=prefix+'/'+notice,bytes=file.stat().st_size,sha256=sha256(file)))
        meta_path=metadata_prefix+name+'/METADATA'
        packages.append(dict(name=name, version=row['version'], original_notice_files=len(notices),
            metadata_path=prefix+'/'+meta_path,metadata_sha256=sha256(contained_file(assets,meta_path)),
            declared_license_expression=value.get('License-Expression'),declared_license=value.get('License'),
            declared_license_files=value.get_all('License-File',[]),notices=references))
    if len({p['name'] for p in packages}) != len(packages):
        raise ValueError('Duplicate package provenance')
    if next((p['version'] for p in packages if p['name']=='markitdown-desktop'), None) != expected_version:
        raise ValueError('Application version mismatch')
    native_root = assets/('licenses/native' if profile=='base' else 'native')
    native = json.loads(contained_file(native_root, 'manifest.json').read_text(encoding='utf-8'))
    if native.get('schema_version') != 2 or not native['files']:
        raise ValueError('Native source fingerprints missing')
    binaries, destinations = [], set()
    for row in native['files']:
        destination = row['file']
        if destination.casefold() in destinations:
            raise ValueError('Duplicate native destination')
        destinations.add(destination.casefold())
        if not re.fullmatch('[0-9a-f]{64}', row.get('source_sha256', '')) or type(row.get('source_bytes')) is not int or row['source_bytes'] <= 0:
            raise ValueError('Invalid native source fingerprint')
        path = contained_file(bundle, '_internal/'+destination)
        digest = sha256(path)
        binaries.append(dict(file=destination, source_sha256=row['source_sha256'], bundled_sha256=digest,
                             source_bytes=row['source_bytes'], bundled_bytes=path.stat().st_size,
                             bytes_changed=digest!=row['source_sha256'], origin=row['origin'],
                             distributions=row['distributions'],
                             **{key: row[key] for key in IDENTITY_FIELDS if key in row}))
    entry = contained_file(bundle, 'MarkItDownBase.exe' if profile=='base' else 'MarkItDownOCRWorker.exe')
    prefix=assets.relative_to(bundle).as_posix()
    contents=inventory(bundle,packages,binaries,{**loader,'prefix':bootloader.relative_to(assets).as_posix()},
                       prefix,python_license,entry.relative_to(bundle).as_posix())
    verify_inventory(bundle,contents)
    # 已決定排除的檔案若又出現在候選包，代表排除失效；直接拒絕，不靠人工比對清單。
    forbidden = sorted(row['path'] for row in contents['files']
                       if is_excluded_name(row['path'].rsplit('/', 1)[-1]))
    if forbidden:
        raise ValueError('Excluded binaries present in bundle: ' + ', '.join(forbidden[:10]))
    return dict(check='bundle-provenance', schema_version=2, profile=profile, source_version=expected_version,
                source_commit=os.environ.get('GITHUB_SHA'), accepted=True, native_execution_performed=False,
                host_platform=sys.platform, packages=packages, packages_without_wheel_notice=pending,
                bootloader=loader, entry_sha256=sha256(entry), native_files=binaries,
                transformed_binaries=sum(p['bytes_changed'] for p in binaries),
                candidate_inventory=contents,inventory_reverified=True,excluded_binaries_absent=True,
                scope='Bundled provenance consistency; CPU package list describes build environment, not runtime closure',
                pending_review=['Application license', 'Qt obligations', 'Microsoft/native runtimes',
                                'Final redistribution review', 'Unresolved file ownership and archive member SBOM',
                                'Clean-machine acceptance'],
                redistribution_approved=False, release_ready=False)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--profile', choices=['base','cpu'], required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--verify-inventory', type=Path, help='以可信的既有報告重驗同一候選包，拒絕任何增刪改名或內容變更')
    parser.add_argument('--package-directory', type=Path, help='CPU候選ZIP／component.json／NOTICE.txt所在目錄')
    args=parser.parse_args()
    if args.report.exists() or args.report.resolve().is_relative_to(args.bundle.resolve()):
        raise ValueError('Report must be fresh and outside bundle')
    version=tomllib.loads((Path(__file__).resolve().parents[1]/'pyproject.toml').read_text())['project']['version']
    try:
        if args.package_directory and args.profile!='cpu':raise ValueError('Package directory requires CPU profile')
        if args.verify_inventory:
            if args.verify_inventory.resolve().is_relative_to(args.bundle.resolve()):
                raise ValueError('Previous report must be outside bundle')
            previous=json.loads(args.verify_inventory.read_text(encoding='utf-8'))
            if previous['profile']!=args.profile or previous['source_version']!=version:
                raise ValueError('Previous inventory profile/version mismatch')
            verify_inventory(args.bundle,previous['candidate_inventory'])
            if 'package_inventory' in previous:
                if not args.package_directory:raise ValueError('Previous inventory requires CPU package directory')
                if sha256(args.package_directory/'onnx-cpu-ocr-development.zip')!=previous['package_inventory']['archive_sha256']:
                    raise ValueError('Previous CPU archive fingerprint mismatch')
        report=audit(args.bundle, args.profile, version)
        if args.package_directory:
            report['package_inventory']=component_inventory(args.package_directory,report['candidate_inventory'])
        if args.verify_inventory:report['previous_inventory_report_sha256']=sha256(args.verify_inventory)
    except Exception as exc:
        report=dict(check='bundle-provenance', profile=args.profile, source_version=version,
                    accepted=False, error=type(exc).__name__+': '+str(exc), release_ready=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    brief={k:report[k] for k in ('check','profile','source_version','accepted','release_ready')}
    brief.update(report_sha256=sha256(args.report), native_files=len(report.get('native_files',[])),
                 packages=len(report.get('packages',[])), source_commit=os.environ.get('GITHUB_SHA'))
    if 'candidate_inventory' in report:
        brief['inventory']=report['candidate_inventory']['summary']
        brief['inventory_reverified']=report['inventory_reverified']
        brief['excluded_binaries_absent']=report['excluded_binaries_absent']
        brief['non_wheel_native']=summarize(report['native_files'])
        brief['identity_errors']=identity_errors(report['native_files'])
    if 'package_inventory' in report:
        brief['package_inventory']=report['package_inventory']['summary']
        brief['package_sha256']=report['package_inventory']['archive_sha256']
    if 'error' in report:brief['error']=report['error'][:500]
    message=json.dumps(brief, ensure_ascii=False, separators=(',',':'))
    if os.environ.get('GITHUB_ACTIONS')=='true':
        print('::'+('notice' if report['accepted'] else 'error')+'::'+message.replace('%','%25').replace('\n','%0A').replace('\r','%0D'))
    else:print(message)
    return 0 if report['accepted'] else 1


if __name__=='__main__':
    raise SystemExit(main())

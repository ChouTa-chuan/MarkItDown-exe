"""完整候選檔案快照與可證明的套件／原文對照；不自動判定授權。"""
import base64
import hashlib
from importlib import metadata
import os
from pathlib import Path, PurePosixPath
import re
import stat
import zipfile

from build_provenance import sha256

MAX_FILES = 20000
MAX_BYTES = 16 * 1024**3


def canonical(name):
    return re.sub('[-_.]+', '-', name).lower()


def snapshot(bundle):
    """只讀普通檔案，拒絕連結／junction／特殊檔及大小寫別名；hash時偵測變動。"""
    bundle = Path(bundle).absolute()
    if not bundle.is_dir() or any(p.is_symlink() or p.is_junction() for p in (bundle, *bundle.parents)):
        raise ValueError('Unsafe inventory root')
    files, aliases, total = [], set(), 0
    def unreadable(error):
        # os.walk預設略過scandir錯誤；完整清單不可把讀不到的目錄誤當空目錄。
        raise error
    for directory, dirs, names in os.walk(bundle, followlinks=False,onerror=unreadable):
        for name in sorted(dirs + names):
            path = Path(directory)/name
            relative = path.relative_to(bundle).as_posix()
            key = relative.casefold()
            info = path.lstat()
            reparse = getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT
            if path.is_symlink() or path.is_junction() or reparse:
                raise ValueError('Inventory link or reparse point: ' + relative)
            if key in aliases:
                raise ValueError('Inventory case alias: ' + relative)
            aliases.add(key)
            if stat.S_ISDIR(info.st_mode):
                continue
            if not stat.S_ISREG(info.st_mode):
                raise ValueError('Inventory special file: ' + relative)
            if len(files) >= MAX_FILES or total + info.st_size > MAX_BYTES:
                raise ValueError('Inventory exceeds bounded file/byte limit')
            digest = sha256(path)
            after = path.stat()
            if (info.st_size, info.st_mtime_ns, info.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
                raise ValueError('Inventory file changed while reading: ' + relative)
            total += info.st_size
            files.append(dict(path=relative, bytes=info.st_size, sha256=digest))
        dirs.sort()
    if not files:
        raise ValueError('Empty candidate inventory')
    return sorted(files, key=lambda row:row['path'])


def record_owners(paths):
    """僅在相對目的路徑與已安裝RECORD的SHA-256都相符時建立對照，不猜名稱。"""
    owners = {}
    for distribution in metadata.distributions():
        for entry in distribution.files or ():
            relative = PurePosixPath(str(entry).replace('\\', '/'))
            if relative.is_absolute() or '..' in relative.parts:
                continue
            key = ('_internal/'+relative.as_posix()).casefold()
            if key not in paths or not entry.hash or entry.hash.mode != 'sha256':
                continue
            try:
                digest = base64.b64decode(entry.hash.value+'='*((-len(entry.hash.value))%4), altchars=b'-_', validate=True).hex()
            except (ValueError, TypeError):
                continue
            if digest == paths[key]['sha256']:
                owner = dict(name=canonical(distribution.metadata['Name']), version=distribution.version,
                             evidence='installed-record-byte-match')
                if owner not in owners.setdefault(key, []):owners[key].append(owner)
    return owners


def inventory(bundle, packages, native_files, bootloader, asset_prefix, python_license, entry):
    """檔案列舉完整與來源／授權審查分開；每個未知項目均可在報告追查。"""
    rows = snapshot(bundle)
    paths = {row['path'].casefold():row for row in rows}
    owners = record_owners(paths)
    package_by_name = {row['name']:row for row in packages}
    if len(package_by_name) != len(packages):
        raise ValueError('Duplicate inventory package')
    explicit, notice_paths = {}, set()
    for package in packages:
        expected=[dict(path=package['metadata_path'],sha256=package['metadata_sha256']),*package['notices']]
        for reference in expected:
            actual=paths.get(reference['path'].casefold())
            if actual is None or actual['sha256']!=reference['sha256']:
                raise ValueError('Inventory package reference mismatch: '+reference['path'])
        references = [package['metadata_path'], *[p['path'] for p in package['notices']]]
        for path in references:
            explicit.setdefault(path.casefold(), []).append(dict(name=package['name'],version=package['version'],evidence='bundled-package-metadata-or-notice'))
        notice_paths.update(p['path'] for p in package['notices'])
    loader_notices = [asset_prefix+'/'+bootloader['prefix']+'/'+path for path in bootloader['files']]
    notice_paths.update(loader_notices)
    python_notice = asset_prefix+'/'+python_license
    notice_paths.add(python_notice)
    for path in loader_notices:
        explicit.setdefault(path.casefold(), []).append(dict(name='pyinstaller',version=bootloader['version'],evidence='preserved-bootloader-notice'))
    native = {('_internal/'+p['file']).casefold():p for p in native_files}
    for row in rows:
        key, name = row['path'].casefold(), Path(row['path']).name.lower()
        found = list(explicit.get(key, owners.get(key, [])))
        source = native.get(key)
        if source:
            found = [dict(name=canonical(d['name']),version=d['version'],evidence='analysis-source') for d in source['distributions']] or found
        if row['path'] == entry:
            found = [dict(name='pyinstaller',version=bootloader['version'],evidence='generated-bootloader-entry'),
                     dict(name='markitdown-desktop',version=package_by_name['markitdown-desktop']['version'],evidence='generated-application-entry')]
        notices, reasons = set(), []
        for owner in found:
            package = package_by_name.get(owner['name'])
            if package and package['version'] == owner['version']:
                notices.update(p['path'] for p in package['notices'])
                if not package['notices']:reasons.append('package-original-notice-pending:'+owner['name'])
            elif owner['name'] != 'pyinstaller':
                reasons.append('owner-outside-package-notice-table:'+owner['name'])
            if owner['name']=='pyinstaller':notices.update(loader_notices)
        if source and source['origin']=='python-runtime':notices.add(python_notice)
        # Windows runtime可能隨CPython或wheel取得；來源位置不能當作其授權。
        microsoft = name.endswith('.dll') and name.startswith(('vcruntime','msvcp','concrt','ucrtbase','api-ms-win-crt'))
        if microsoft:
            reasons.append('microsoft-native-redistribution-review')
            notices.discard(python_notice)
        if not found:
            reasons.append('source-owner-unresolved')
        if source and source['bytes_changed']:
            reasons.append('native-bytes-transformed')
        if key.endswith(('.pyz','.zip')):
            role='archive';reasons.append('archive-members-not-enumerated')
        elif row['path'] in notice_paths:role='original-notice'
        elif key.endswith('/metadata'):role='package-metadata'
        elif key.endswith(('.exe','.dll','.pyd','.so')) or source:role='native-binary'
        else:role='data-or-generated'
        row.update(role=role,owners=found,notice_paths=sorted(notices),review_reasons=sorted(set(reasons)))
        for notice in notices:
            if notice.casefold() not in paths:
                raise ValueError('Inventory notice reference missing: '+notice)
    summary = dict(files=len(rows),bytes=sum(row['bytes'] for row in rows),
                   unresolved_files=sum(not row['owners'] for row in rows),
                   review_files=sum(bool(row['review_reasons']) for row in rows),
                   original_notice_files=sum(row['role']=='original-notice' for row in rows),
                   packages=len(packages),file_inventory_complete=True,runtime_sbom_complete=False,
                   redistribution_approved=False,release_ready=False)
    return dict(schema_version=1,files=rows,summary=summary)


def verify_inventory(bundle, report):
    """對可信的既有快照重驗，缺檔、多檔、改名及任何byte變更都拒絕。"""
    expected = report['files']
    if not expected or len({row['path'].casefold() for row in expected}) != len(expected):
        raise ValueError('Invalid or duplicate inventory entries')
    actual = snapshot(bundle)
    expected_files = {row['path']:(row['bytes'],row['sha256']) for row in expected}
    actual_files = {row['path']:(row['bytes'],row['sha256']) for row in actual}
    if actual_files != expected_files:
        raise ValueError('Candidate inventory differs: added, missing, renamed or changed file')
    return True


def component_inventory(directory, contents):
    """CPU的ZIP比bundle多NOTICE；驗真正壓縮檔的每一項、CRC與descriptor，不只看目錄。"""
    import json
    from desktop_app.components.contracts import ComponentSpec
    from desktop_app.component_workers import protocol
    directory=Path(directory)
    descriptor=directory/'component.json'
    spec=ComponentSpec.from_dict(json.loads(descriptor.read_text(encoding='utf-8')))
    if spec.component_id!=protocol.COMPONENT_ID or str(spec.version)!=protocol.COMPONENT_VERSION:
        raise ValueError('CPU package component/version mismatch')
    archive=directory/'onnx-cpu-ocr-development.zip'
    if archive.is_symlink() or descriptor.is_symlink():raise ValueError('Linked CPU package')
    if archive.stat().st_size!=spec.download_bytes or sha256(archive)!=spec.package_sha256:
        raise ValueError('CPU package archive fingerprint mismatch')
    expected={p['path']:(p['bytes'],p['sha256']) for p in contents['files']}
    if 'NOTICE.txt' in expected:raise ValueError('CPU bundle shadows generated NOTICE.txt')
    notice=directory/'NOTICE.txt'
    if notice.is_symlink():raise ValueError('Linked CPU notice')
    expected['NOTICE.txt']=(notice.stat().st_size,sha256(notice))
    declared={p.path:(p.size,p.sha256) for p in spec.files}
    if declared!=expected:raise ValueError('CPU descriptor differs from complete bundle inventory')
    observed={};total=0
    with zipfile.ZipFile(archive) as source:
        seen=set()
        for entry in source.infolist():
            name=entry.filename
            mode=entry.external_attr>>16
            if (entry.is_dir() or name.casefold() in seen or name not in expected
                    or stat.S_IFMT(mode) not in (0,stat.S_IFREG)):
                raise ValueError('Unexpected, linked or duplicate ZIP entry')
            seen.add(name.casefold())
            size,digest=expected[name]
            if entry.file_size!=size or total+size>MAX_BYTES or len(observed)>=MAX_FILES:
                raise ValueError('ZIP entry size/limit mismatch')
            actual=hashlib.sha256();count=0
            with source.open(entry) as payload:
                while block:=payload.read(1024*1024):
                    count+=len(block)
                    if count>size:raise ValueError('ZIP expands beyond declared entry size')
                    actual.update(block)
            if count!=size or actual.hexdigest()!=digest:raise ValueError('ZIP entry fingerprint mismatch')
            observed[name]=(size,digest);total+=size
    if observed!=expected or total!=spec.unpacked_bytes:raise ValueError('ZIP missing inventory entry')
    return dict(archive_sha256=spec.package_sha256,descriptor_sha256=sha256(descriptor),
        component_id=spec.component_id,component_version=str(spec.version),
        files=[dict(path=name,bytes=size,sha256=digest) for name,(size,digest) in sorted(observed.items())],
        summary=dict(files=len(observed),bytes=total,archive_bytes=spec.download_bytes,
                     archive_verified=True,file_inventory_complete=True,runtime_sbom_complete=False,
                     redistribution_approved=False,release_ready=False))

"""保存啟動器原文與原生來源指紋；技術追溯不代表再散布核准。"""
import hashlib
from importlib import metadata
import json
from pathlib import Path, PurePosixPath
import shutil


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def is_notice_entry(value):
    """以完整相對路徑判斷，保留 licenses/Apache-2.0.txt，排除程式與快取。"""
    path = PurePosixPath(str(value))
    return (not path.is_absolute() and '..' not in path.parts
            and '__pycache__' not in path.parts and path.suffix.lower() not in ('.py', '.pyc', '.pyo')
            and any(term in path.as_posix().lower()
                    for term in ('license', 'licence', 'copying', 'notice', 'copyright')))


def bootloader_notices(output, distribution=None):
    """PyInstaller 雖為建置相依，其啟動器會進入產物，須另存實際安裝原文。"""
    distribution = distribution or metadata.distribution('pyinstaller')
    if output.exists():
        raise FileExistsError(output)
    files = {}
    for entry in distribution.files or ():
        if not is_notice_entry(entry):
            continue
        source = Path(distribution.locate_file(entry))
        if not source.is_file() or source.stat().st_size > 5 * 1024**2:
            raise ValueError('Missing or oversized bootloader notice: ' + str(entry))
        target = output / 'original' / str(entry)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        files[target.relative_to(output).as_posix()] = sha256(target)
    if not files:
        raise ValueError('PyInstaller original notice missing')
    report = dict(schema_version=1, name='pyinstaller', version=distribution.version, files=files,
                  redistribution_approved=False, release_ready=False)
    (output/'manifest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def distribution_sources():
    """依安裝 RECORD 的實際檔案對照來源；未知來源保持未知，不猜套件名稱。"""
    owners = {}
    for distribution in metadata.distributions():
        for entry in distribution.files or ():
            path = Path(distribution.locate_file(entry)).resolve()
            owners.setdefault(path, []).append(dict(name=distribution.metadata['Name'], version=distribution.version))
    return owners

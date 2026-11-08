"""離線組裝四語 OCR payload；Windows 用固定最小候選，Linux 只供開發驗證。"""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from desktop_app.bundled_ocr import LANGUAGES, validate_payload
from desktop_app.components.registry import _chain
from desktop_app.languages import model_manifest
from desktop_app.native_assets import file_hash, inspect_pe, is_system_dll

ROOT = Path(__file__).resolve().parents[1]
WINDOWS_EVIDENCE = ROOT / 'docs/development-records/runs/c03-minimal-source-2026-11-08/build-report.json'


def read_build_evidence(path, *, require_utf8=False):
    """接受同一可信建置管線產生的 receipt；它是稽核資料，不是簽章或發行許可。"""
    file_hash(path, 1024 * 1024)
    evidence = json.loads(Path(path).read_text(encoding='utf-8'))
    contract = json.loads((ROOT / 'packaging/native/minimal-windows.json').read_text())
    if (evidence.get('check') != 'C03-minimal-source' or evidence.get('cross_build_complete') is not True
            or evidence.get('source_evidence_prepared') is not True
            or evidence.get('source_contract_sha256') != file_hash(ROOT / 'packaging/native/minimal-windows.json')[0]):
        raise ValueError('建置 receipt 與固定最小原生來源不符。')
    for name in ('source_archives', 'toolchain_archive', 'notices'):
        if evidence.get(name) != contract[name]:
            raise ValueError('建置 receipt 的固定輸入不符：' + name)
    for flag in ('windows_executed', 'gpu_executed', 'native_ocr_bundled', 'full_c03_complete',
                 'redistribution_approved', 'release_ready'):
        if evidence.get(flag) is not False:
            raise ValueError('交叉建置 receipt 不能宣稱 Windows 執行或發行核准。')
    candidate = evidence.get('candidate', {})
    if candidate.get('file') != 'tesseract.exe' or candidate.get('machine') != 'AMD64' or candidate.get('is_dll') is not False:
        raise ValueError('建置 receipt 的固定入口不符。')
    if require_utf8:
        manifest = ROOT / 'packaging/native/windows-utf8.manifest'
        digest, size = file_hash(manifest)
        expected = dict(file='packaging/native/windows-utf8.manifest', sha256=digest,
                        bytes=size, resource_type=24, resource_id=1)
        if evidence.get('windows_utf8_manifest') != expected:
            raise ValueError('新 Windows CI receipt 缺少相符的 UTF-8 manifest。')
    return evidence


def prepare(output, tessdata, *, windows_candidate=None, linux_development=False, build_evidence=None):
    output, tessdata = Path(output).absolute(), Path(tessdata)
    _chain(output)
    if output.exists():
        raise FileExistsError('請使用新的 payload 輸出目錄。')
    if (windows_candidate is None) == (not linux_development):
        raise ValueError('須明確選擇固定 Windows 候選或 Linux 開發引擎其中一種。')
    if build_evidence is not None and windows_candidate is None:
        raise ValueError('建置 receipt 只適用於 Windows 最小候選。')
    fixed = model_manifest()
    sources = {}
    for name, expected in fixed['files'].items():
        if file_hash(tessdata / name, 16 * 1024**2)[0] != expected:
            raise ValueError('四語模型／授權完整性不符：' + name)
        sources['tessdata/' + name] = tessdata / name
    if windows_candidate is not None:
        evidence_path = Path(build_evidence) if build_evidence is not None else WINDOWS_EVIDENCE
        evidence = read_build_evidence(evidence_path, require_utf8=build_evidence is not None)
        candidate = Path(windows_candidate)
        entry = candidate / 'tesseract.exe'
        record = evidence['candidate']
        if file_hash(entry) != (record['sha256'], record['bytes']):
            raise ValueError('Windows 候選與固定來源證據不符。')
        pe = inspect_pe(entry.read_bytes())
        if pe['is_dll'] or any(not is_system_dll(name) for name in pe['imports'] + pe['delay_imports']):
            raise ValueError('Windows 候選出現未預期的第三方 DLL。')
        contract = json.loads((ROOT / 'packaging/native/minimal-windows.json').read_text())
        if file_hash(ROOT / 'packaging/native/minimal-windows.json')[0] != evidence['source_contract_sha256']:
            raise ValueError('最小原生來源契約已變更，須另做候選驗收。')
        for notice in contract['notices']:
            path = ROOT / 'packaging/native/minimal-notices' / notice['file']
            if file_hash(path) != (notice['sha256'], notice['bytes']):
                raise ValueError('原始原生授權／來源文字不符。')
            sources['notices/' + notice['file']] = path
        source = dict(kind='ci-rebuilt-windows-minimal' if build_evidence is not None else 'fixed-windows-minimal',
                      evidence_sha256=file_hash(evidence_path)[0],
                      source_contract_sha256=evidence['source_contract_sha256'],
                      upstream_version='5.5.3', windows_executed=False)
        if build_evidence is not None:
            source['windows_utf8_manifest'] = evidence['windows_utf8_manifest']
        target, executable = 'windows', 'bin/tesseract.exe'
    else:
        if sys.platform != 'linux':
            raise ValueError('Linux 開發引擎只能在 Linux 準備。')
        entry = Path('/usr/bin/tesseract')
        _chain(entry)
        header = entry.read_bytes()[:20]
        if header[:6] != b'\x7fELF\x02\x01' or header[18:20] != b'\x3e\x00':
            raise ValueError('Linux 開發引擎須為本機 AMD64 ELF。')
        version = subprocess.run([str(entry), '--version'], capture_output=True, text=True, check=True, timeout=10)
        copyright_file = Path('/usr/share/doc/tesseract-ocr/copyright')
        file_hash(copyright_file)
        sources['notices/tesseract-system-copyright.txt'] = copyright_file
        source = dict(kind='linux-development-system', version=version.stdout.splitlines()[0],
                      engine_sha256=file_hash(entry)[0],
                      scope='Existing Linux engine copied into development bundle; dependent library origins collected by PyInstaller Analysis. Not the Windows candidate.')
        target, executable = 'linux', 'bin/tesseract'
    sources[executable] = entry
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.native-assets-', dir=output.parent) as temporary:
        staged = Path(temporary) / 'native'
        staged.mkdir()
        for name, path in sources.items():
            _chain(path)
            destination = staged / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            before = file_hash(path)
            shutil.copyfile(path, destination)
            if file_hash(destination) != before:
                raise ValueError('複製期間來源已變更：' + name)
        (staged / executable).chmod(0o755)
        (staged / 'source.json').write_text(json.dumps(source, ensure_ascii=False, indent=2) + '\n')
        files = {path.relative_to(staged).as_posix(): dict(sha256=file_hash(path)[0], bytes=path.stat().st_size)
                 for path in sorted(staged.rglob('*')) if path.is_file()}
        spec = dict(schema_version=1, id='bundled-tesseract', platform=target, entrypoint=executable,
                    languages=list(LANGUAGES), model_commit=fixed['commit'],
                    development_only=True, redistribution_approved=False, files=files)
        (staged / 'manifest.json').write_text(json.dumps(spec, ensure_ascii=False, indent=2) + '\n')
        validate_payload(staged, expected_platform=target)
        shutil.move(str(staged), output)
    return spec


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--tessdata', type=Path, required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--windows-candidate', type=Path)
    group.add_argument('--linux-development', action='store_true')
    parser.add_argument('--build-evidence', type=Path, help='同一可信建置管線的固定來源 receipt；不視為來源簽章')
    args = parser.parse_args()
    result = prepare(args.output, args.tessdata, windows_candidate=args.windows_candidate,
                     linux_development=args.linux_development, build_evidence=args.build_evidence)
    print('Prepared offline OCR payload:', result['platform'], len(result['files']), 'files; four languages; development only')

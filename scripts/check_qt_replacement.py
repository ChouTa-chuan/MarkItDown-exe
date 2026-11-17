"""hosted Windows 上用不同 Qt6Core bytes 驗 frozen GUI，暫存副本不作為產品。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import traceback
import urllib.request
import zipfile

from build_provenance import sha256
from check_windows_base import gui_check, native_environment

ROOT = Path(__file__).resolve().parents[1]
INPUT = 'packaging/qt/6.12.0/replacement-input.json'


def extract_replacement(wheel, destination, record):
    """只抽出已釘 hash 的 Core DLL，不安裝 PyQt、不改依賴鎖檔或正式 bundle。"""
    if wheel.stat().st_size != record['bytes'] or sha256(wheel) != record['sha256']:
        raise ValueError('Replacement wheel fingerprint differs')
    with zipfile.ZipFile(wheel) as archive:
        data = archive.read(record['member'])
    if len(data) != record['member_bytes'] or hashlib.sha256(data).hexdigest() != record['member_sha256']:
        raise ValueError('Replacement DLL fingerprint differs')
    destination.write_bytes(data)


def validate_success(value, expected_path, expected_hash):
    """視窗與正常退出之外，必須載入本次副本內的正確 DLL，不能偷偷借宿主 Qt。"""
    if (value.get('opened') is not True or value.get('normal_exit') is not True or value.get('returncode') != 0
            or value.get('qt_core', {}).get('sha256') != expected_hash
            or Path(value.get('qt_core', {}).get('path', '')).resolve() != expected_path.resolve()):
        raise ValueError('Frozen GUI did not load the expected Qt6Core')


def validate_missing(returncode, log):
    """其他不相干錯誤不能冒充缺 Core 的反例通過。"""
    if (returncode == 0 or not re.search(r'Qt(?:6)?Core', log, re.I)
            or not re.search(r'DLL load failed|ImportError|module could not be found', log, re.I)):
        raise ValueError('Missing Qt6Core did not produce the expected loader failure')


def check(bundle, work, reports, *, root=ROOT):
    if work.exists() or reports.exists():
        raise FileExistsError('Qt replacement outputs must be new')
    work.mkdir(parents=True)
    reports.mkdir(parents=True)
    report = dict(schema_version=1, check='qt-replacement', accepted=False, platform=sys.platform,
        hosted_ci=os.environ.get('GITHUB_ACTIONS') == 'true', clean_machine_accepted=False,
        physical_machine_accepted=False, gpu_executed=False, redistribution_approved=False,
        release_ready=False, input_sha256=sha256(Path(root)/INPUT), phases={})
    original = bundle/'_internal/PySide6/Qt6Core.dll'
    before = None
    try:
        if sys.platform != 'win32' or os.environ.get('GITHUB_ACTIONS') != 'true':
            raise ValueError('Qt replacement acceptance requires hosted Windows CI')
        before = sha256(original)
        report['original_sha256'] = before
        record = json.loads((Path(root)/INPUT).read_text(encoding='utf-8'))
        if record['member_sha256'] == before:
            raise ValueError('Replacement DLL must have different bytes')
        wheel = work/record['wheel']
        # 固定 HTTPS 測試輸入；實際下載完整位元組與內部 DLL 各自驗 hash。
        if not record['url'].startswith('https://files.pythonhosted.org/packages/'):
            raise ValueError('Unexpected replacement input host')
        with urllib.request.urlopen(record['url'], timeout=90) as response, wheel.open('wb') as stream:
            shutil.copyfileobj(response, stream)
        replacement = work/'replacement.dll'
        extract_replacement(wheel, replacement, record)
        target = work/'bundle'
        shutil.copytree(bundle, target)
        core = target/'_internal/PySide6/Qt6Core.dll'
        app = target/'MarkItDownBase.exe'
        environment = native_environment()
        report['replacement_sha256'] = record['member_sha256']
        for label, digest in [('baseline', before), ('replaced', record['member_sha256']), ('restored', before)]:
            if label == 'replaced':
                shutil.copyfile(replacement, core)
            if label == 'restored':
                core.unlink()
                import ctypes
                kernel = ctypes.windll.kernel32
                old_mode = kernel.SetErrorMode(0x0001 | 0x8000)
                try:
                    failed = subprocess.run([str(app.resolve())], cwd=work, env={**environment,
                        'LOCALAPPDATA':str(work/'missing-settings')}, capture_output=True,
                        text=True, encoding='utf-8', errors='replace', timeout=45)
                finally:
                    kernel.SetErrorMode(old_mode)
                text = failed.stdout+failed.stderr
                (reports/'missing.log').write_text(text, encoding='utf-8')
                report['phases']['missing'] = dict(returncode=failed.returncode, log_sha256=sha256(reports/'missing.log'))
                validate_missing(failed.returncode, text)
                report['phases']['missing']['expected_loader_failure'] = True
                shutil.copyfile(original, core)
            phase = reports/label
            phase.mkdir()
            result = gui_check(app.resolve(), work.resolve(), phase, environment)
            validate_success(result, core, digest)
            report['phases'][label] = result
        report['original_bundle_unchanged'] = sha256(original) == before
        if not report['original_bundle_unchanged']:
            raise ValueError('Production bundle changed during replacement test')
        report['accepted'] = True
    except Exception as exc:
        report['error'] = type(exc).__name__+': '+str(exc)
        (reports/'error.log').write_text(traceback.format_exc(), encoding='utf-8')
    finally:
        if before is not None:
            report['original_bundle_unchanged'] = sha256(original) == before
        (reports/'qt-replacement.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def publish(report):
    """只公開小型驗收 metadata；wheel、DLL 與暫存執行檔均在 reports 外。"""
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        message = json.dumps(report, ensure_ascii=False, separators=(',', ':'))
        if len(message.encode('utf-8')) > 3900:
            raise ValueError('Qt replacement summary exceeds annotation budget')
        print('::notice title=Qt replacement::'+message.replace('%', '%25').replace('\n', '%0A').replace('\r', '%0D'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--reports', type=Path, required=True)
    args = parser.parse_args()
    result = check(args.bundle, args.work, args.reports)
    publish(result)
    raise SystemExit(0 if result['accepted'] else 1)

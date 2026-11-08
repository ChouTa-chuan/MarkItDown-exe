"""在真正 Windows 執行基本包驗收；不建立安裝包，也不宣稱乾淨機或人工驗收。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

from desktop_app.bundled_ocr import validate_payload


def native_environment():
    # 只移除待測 child 的工具／模型搜尋來源，保留 Windows 系統必要環境。
    return {**os.environ, 'PATH': '', 'TESSDATA_PREFIX': '', 'PYTHONPATH': '',
            'PYTHONUTF8': '1', 'QT_QPA_PLATFORM': 'offscreen'}


def check(executable, output, *, gui=True):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    report = dict(check='windows-base-ci', recorded_at=datetime.now(timezone.utc).isoformat(),
                  accepted=False, windows_executed=False, clean_machine_accepted=False,
                  hosted_runner_has_python=True, gpu_executed=False, release_ready=False,
                  full_c03_complete=False, full_c04_complete=False, full_c09_complete=False,
                  platform=sys.platform, checks=[], invocations=[])
    try:
        if sys.platform != 'win32':
            raise RuntimeError('本驗收必須在真正 Windows 執行，不接受 Linux 模擬平台。')
        report['platform'] = platform.platform()
        executable = executable.resolve()
        original_data = executable.parent/'_internal/desktop_app/data'
        profile = json.loads((original_data/'build-profile.json').read_text(encoding='utf-8'))
        assert profile['platform'] == 'windows' and profile['native_ocr_integrated']
        validate_payload(original_data/'native', expected_platform='windows', assets=profile['assets'])
        report['source_version'] = profile['source_version']
        report['checks'].append('Windows profile and all fixed native/model/notice hashes verified')
        env = native_environment()
        with tempfile.TemporaryDirectory(prefix='markitdown-win-base-') as temporary:
            root = Path(temporary)

            def run(label, app, args, expected=0, environment=None):
                result = subprocess.run([str(app), *map(str, args)], cwd=root, env=environment or env,
                    capture_output=True, encoding='utf-8', errors='replace', timeout=180)
                (output/(label+'.log')).write_text(result.stdout+result.stderr, encoding='utf-8')
                report['windows_executed'] = True
                report['invocations'].append(dict(label=label, returncode=result.returncode, expected=expected))
                assert result.returncode == expected, (label, result.returncode, result.stdout, result.stderr)
                return result

            core, full = output/'core-self-test.json', output/'full-self-test.json'
            run('core-self-test', executable, ['--self-test', '--scope', 'core', '--report', core])
            value = json.loads(core.read_text(encoding='utf-8'))
            assert value['frozen'] and value['complete'] and not value['external_python_required']
            assert value['python_utf8_mode'], 'Frozen Python must use UTF-8 independently of the host locale'
            report['python_utf8_mode'] = value['python_utf8_mode']
            assert not value['native_ocr_verified']
            report['checks'].append('Native Windows frozen core runs without external Python command')
            run('full-self-test', executable, ['--self-test', '--report', full])
            value = json.loads(full.read_text(encoding='utf-8'))
            assert value['complete'] and value['native_ocr_verified'] and not value['release_ready']
            assert value['checks'][-1]['detail']['scanned_pdfs'] == 4
            report['checks'].append('Actual Windows native four-language health and scanned PDF self-test passes')
            relocated = root/'中文 空格測試'/'應用程式'
            shutil.copytree(executable.parent, relocated)
            app = relocated/executable.name
            data = relocated/'_internal/desktop_app/data'
            languages = run('relocated-native-language-list', data/'native/bin/tesseract.exe',
                            ['--list-langs', '--tessdata-dir', data/'native/tessdata'])
            assert {'chi_tra','eng','jpn','kor'} <= set(languages.stdout.splitlines())
            relocated_report = output/'relocated-self-test.json'
            run('relocated-four-languages', app, ['--self-test', '--report', relocated_report])
            value = json.loads(relocated_report.read_text(encoding='utf-8'))
            assert value['complete'] and value['native_ocr_verified']
            report['checks'].append('Four-language native OCR works after relocating into a Chinese/spaced path')
            source = output/'繁體來源.txt'
            source.write_bytes('# 中文 UTF-8 路徑\r\n\r\nWindows 基本包驗證\r\n'.encode())
            run('unicode-text', app, ['--cli', source, output/'繁體輸出.md', '--reserve-mib', '0'])
            assert (output/'繁體輸出.md').read_bytes() == source.read_bytes()
            report['checks'].append('Chinese input/output filenames preserve exact UTF-8 bytes')
            settings = output/'settings.json'
            raw = '{"schema_version":7,"reserve_mib":0,"ocr_executable":null,"ocr_data_dir":null}\n'
            settings.write_text(raw, encoding='utf-8')
            from PIL import Image
            samples = []
            for language, stem in [('chi_tra','setup-chinese'),('eng','worker-health'),
                                   ('jpn','setup-japanese'),('kor','setup-korean')]:
                source, target = output/(language+' 掃描.pdf'), output/(language+' 輸出.md')
                with Image.open(data/(stem+'.png')) as image:
                    rgb = image.convert('RGB')
                    try: rgb.save(source, 'PDF', resolution=144)
                    finally: rgb.close()
                run(language+'-cli', app, ['--cli', source, target, '--settings', settings, '--ocr-languages', language])
                reference = json.loads((data/(stem+'.json')).read_text(encoding='utf-8'))
                expected = reference.get('expected', reference.get('reference'))
                assert ''.join(expected.split()) in ''.join(target.read_text(encoding='utf-8').split())
                samples.append(source)
            assert settings.read_text(encoding='utf-8') == raw
            report['checks'].append('Four real Windows CLI scans preserve selected language targets and settings bytes')
            # 準備真正可用的外部 engine/model，確保後續故障案例不能靠偷偷回退通過。
            external = root/'external-engine'
            external.mkdir()
            shutil.copyfile(data/'native/bin/tesseract.exe', external/'tesseract.exe')
            shutil.copytree(data/'native/tessdata', external/'models')
            fallback_env = {**env, 'PATH': str(external), 'TESSDATA_PREFIX': str(external/'models')}
            run('external-control', external/'tesseract.exe', ['--list-langs'], environment=fallback_env)
            model = data/'native/tessdata/jpn.traineddata'
            saved = model.read_bytes()
            model.unlink()
            failed = output/'missing-model.md'
            run('missing-model', app, ['--cli', samples[1], failed, '--reserve-mib', '0'], 1, fallback_env)
            assert not failed.exists()
            run('text-despite-missing-model', app, ['--cli', output/'繁體來源.txt', output/'文字仍可用.md', '--reserve-mib', '0'])
            assert (output/'文字仍可用.md').read_bytes() == (output/'繁體來源.txt').read_bytes()
            model.write_bytes(saved+b'corrupt')
            failed = output/'changed-model.md'
            run('changed-model', app, ['--cli', samples[1], failed, '--reserve-mib', '0'], 1, fallback_env)
            assert not failed.exists()
            model.write_bytes(saved)
            report['checks'].append('Missing/changed model rejects OCR despite usable external fallback; text remains usable')
            entry = data/'native/bin/tesseract.exe'
            saved_entry = entry.read_bytes()
            entry.write_bytes(b'MZ damaged fixture, never executed')
            failed = output/'changed-engine.md'
            run('changed-engine', app, ['--cli', samples[1], failed, '--reserve-mib', '0'], 1, fallback_env)
            assert not failed.exists()
            entry.write_bytes(saved_entry)
            report['checks'].append('Changed native EXE hash is rejected without silently borrowing a host engine')
            failed = output/'optional.md'
            run('optional-missing', app, ['--cli', samples[1], failed, '--ocr-backend', 'onnx', '--reserve-mib', '0'], 1)
            assert not failed.exists()
            report['checks'].append('Unavailable optional OCR does not replace the chosen backend')
            if gui:
                report['gui'] = gui_check(app, root, output, env)
                report['checks'].append('Actual Qt Windows platform opens a window and closes normally; no human acceptance claim')
            files = []
            for path in sorted(relocated.rglob('*')):
                if path.is_file():
                    raw_file = path.read_bytes()
                    files.append(dict(file=path.relative_to(relocated).as_posix(), bytes=len(raw_file),
                                      sha256=hashlib.sha256(raw_file).hexdigest()))
            (output/'bundle-files.json').write_text(json.dumps(dict(files=files), indent=2)+'\n', encoding='utf-8')
            (output/'build-profile.json').write_bytes((data/'build-profile.json').read_bytes())
            (output/'native-payload.json').write_bytes((data/'native/manifest.json').read_bytes())
            report['bundle_files'] = len(files)
            report['bundle_bytes'] = sum(entry['bytes'] for entry in files)
        report['accepted'] = True
    except Exception as exc:
        report['error'] = f'{type(exc).__name__}: {exc}'
        (output/'driver-error.log').write_text(traceback.format_exc(), encoding='utf-8')
    report['checks_passed'] = len(report['checks'])
    (output/'windows-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    return report


def close_windows_child(child, get_handles, request_close, *, timeout=25):
    """首次檢查忙碌時先取消再關閉；在總期限內重送正常要求，不以 terminate 當成功。"""
    deadline = time.monotonic()+timeout
    requests = 0
    while True:
        result = child.poll()
        if result is not None:
            if result != 0: raise RuntimeError('Qt process did not close normally')
            return requests
        remaining = deadline-time.monotonic()
        if remaining <= 0: raise TimeoutError('Qt normal close exceeded its total deadline')
        # get_handles 由 caller 限定剛啟動的 child PID，每輪重新列舉已存在的視窗。
        for handle in get_handles():
            request_close(handle)
            requests += 1
        try: child.wait(timeout=min(0.2,remaining))
        except subprocess.TimeoutExpired: pass


def gui_check(app, root, output, environment):
    """只控制剛啟動的自身 child 視窗；截圖限該視窗，不擷取桌面或其他程式。"""
    import ctypes
    from ctypes import wintypes
    env = {**environment, 'LOCALAPPDATA': str(root/'isolated-local-app-data')}
    env.pop('QT_QPA_PLATFORM', None)
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    with (output/'gui.log').open('wb') as log:
        child = subprocess.Popen([str(app)], cwd=root, env=env, stdout=log, stderr=subprocess.STDOUT)
        try:
            handles = []
            def visit(hwnd, _):
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if pid.value == child.pid and user32.IsWindowVisible(hwnd): handles.append(hwnd)
                return True
            callback = callback_type(visit)
            deadline = time.monotonic()+25
            while time.monotonic() < deadline and child.poll() is None:
                handles.clear()
                user32.EnumWindows(callback, 0)
                if handles: break
                time.sleep(0.2)
            assert handles and child.poll() is None, 'Qt Windows window did not open'
            from PIL import ImageGrab
            rect = wintypes.RECT()
            user32.GetWindowRect(handles[0], ctypes.byref(rect))
            ImageGrab.grab(bbox=(rect.left,rect.top,rect.right,rect.bottom)).save(output/'windows-gui.png')
            def current_handles():
                handles.clear()
                user32.EnumWindows(callback,0)
                return list(handles)
            requests = close_windows_child(child,current_handles,
                lambda handle:user32.PostMessageW(handle,0x0010,0,0))
            return dict(opened=True,normal_exit=True,returncode=child.returncode,close_requests=requests)
        finally:
            if child.poll() is None:
                child.terminate()
                child.wait(timeout=10)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--no-gui', action='store_true', help='只供定位故障；CI 預設仍檢查 GUI')
    args = parser.parse_args()
    result = check(args.executable, args.output, gui=not args.no_gui)
    print('Windows CI accepted:', result['accepted'], 'checks:', result['checks_passed'])
    raise SystemExit(0 if result['accepted'] else 1)

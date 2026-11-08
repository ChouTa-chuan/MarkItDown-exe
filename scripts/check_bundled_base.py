"""實際驗收 Linux 內含四語 frozen 開發包；Windows payload 只做靜態檢查。"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from desktop_app.bundled_ocr import validate_payload


def check(executable, fixtures, windows_payload, output):
    if output.exists():
        raise FileExistsError(output)
    output.mkdir(parents=True)
    executable, fixtures = executable.resolve(), fixtures.resolve()
    environment = dict(os.environ, PATH='', TESSDATA_PREFIX='', PYTHONPATH='', QT_QPA_PLATFORM='offscreen')
    environment.pop('PYTHONHOME', None)
    checks, invocations = [], []
    with tempfile.TemporaryDirectory(prefix='markitdown-bundled-relocate-') as temporary:
        work = Path(temporary)
        relocated = work / '搬移後的程式'
        shutil.copytree(executable.parent, relocated, symlinks=True)
        app = relocated / executable.name
        data = relocated / '_internal/desktop_app/data'
        native = data / 'native'

        def run(label, args, expected=0):
            result = subprocess.run([str(app), *map(str, args)], capture_output=True, text=True,
                                    cwd=work, env=environment, timeout=180)
            (output / (label + '.log')).write_text(result.stdout + result.stderr, encoding='utf-8')
            invocations.append(dict(label=label, returncode=result.returncode, expected=expected))
            assert result.returncode == expected, (label, result.stdout, result.stderr)

        profile = json.loads((data / 'build-profile.json').read_text())
        assert profile['schema_version'] == 2 and profile['native_ocr_integrated'] and not profile['release_ready']
        validate_payload(native, expected_platform='linux', assets=profile['assets'])
        checks.append('Native schema-v2 profile and complete four-language payload verified after relocation')
        core, full = output / 'core-self-test.json', output / 'full-self-test.json'
        run('core-self-test', ['--self-test', '--scope', 'core', '--report', core])
        core_report = json.loads(core.read_text())
        assert core_report['complete'] and not core_report['native_ocr_verified']
        assert core_report['frozen'] and not core_report['external_python_required']
        checks.append('Frozen core passes without external Python and does not claim OCR execution')
        run('full-self-test', ['--self-test', '--report', full])
        full_report = json.loads(full.read_text())
        assert full_report['complete'] and full_report['native_ocr_verified'] and not full_report['release_ready']
        detail = full_report['checks'][-1]['detail']
        assert detail['health_samples'] == 4 and detail['scanned_pdfs'] == 4
        checks.append('Full frozen self-test executes all four native health samples and scanned PDFs')
        results = []
        for record in json.loads((fixtures / 'fixtures.json').read_text()):
            source = fixtures / record['file']
            assert hashlib.sha256(source.read_bytes()).hexdigest() == record['sha256']
            destination = output / (source.name + '.md')
            run(source.name, ['--cli', source, destination, '--device', 'cpu', '--reserve-mib', '0'])
            text = destination.read_text(encoding='utf-8')
            assert all(value in text for value in record['expected']), source.name
            if source.suffix == '.txt':
                assert destination.read_bytes() == source.read_bytes()
            results.append(dict(file=source.name, converted=True))
        checks.append('All original core fixtures plus scanned PDF convert with empty PATH and model environment')
        # 另保存日韓實際 CLI 原始樣本／輸出，設定維持自動路徑，不靠精靈回填絕對位置。
        from PIL import Image
        settings = output / 'auto-settings.json'
        raw_settings = '{"schema_version":7,"reserve_mib":0,"ocr_executable":null,"ocr_data_dir":null}\n'
        settings.write_text(raw_settings)
        for language, stem in [('jpn', 'setup-japanese'), ('kor', 'setup-korean')]:
            source, destination = output / (language + '.pdf'), output / (language + '.md')
            with Image.open(data / (stem + '.png')) as image:
                converted = image.convert('RGB')
                try:
                    converted.save(source, 'PDF', resolution=144)
                finally:
                    converted.close()
            run(language + '-cli', ['--cli', source, destination, '--settings', settings, '--ocr-languages', language])
            reference = json.loads((data / (stem + '.json')).read_text())
            expected = reference.get('expected', reference.get('reference'))
            assert ''.join(expected.split()) in ''.join(destination.read_text().split())
        assert settings.read_text() == raw_settings
        checks.append('Japanese/Korean CLI use automatically relocated native paths and preserve user settings bytes')
        checks.append('Entire application copied to a Chinese directory and used from an unrelated working directory')
        scan = fixtures / '掃描.pdf'
        ja = native / 'tessdata/jpn.traineddata'
        backup = work / 'japanese-backup'
        ja.rename(backup)
        destination = output / 'missing-model.md'
        run('missing-model', ['--cli', scan, destination, '--reserve-mib', '0'], 1)
        assert not destination.exists()
        text_source = output / '純文字.txt'
        text_source.write_text('缺少 OCR 模型仍可轉換文字。\n')
        run('text-with-missing-model', ['--cli', text_source, output/'純文字.md', '--reserve-mib', '0'])
        assert (output/'純文字.md').read_bytes() == text_source.read_bytes()
        backup.rename(ja)
        checks.append('Missing required model refuses OCR without output or fallback while plain text still converts')
        original = ja.read_bytes()
        ja.write_bytes(original + b'corrupt')
        destination = output / 'corrupt-model.md'
        run('corrupt-model', ['--cli', scan, destination, '--reserve-mib', '0'], 1)
        assert not destination.exists()
        ja.write_bytes(original)
        checks.append('Changed model hash is rejected before native OCR; no partial output')
        entry = native / 'bin/tesseract'
        entry.rename(work / 'engine-backup')
        entry.symlink_to('/usr/bin/tesseract')
        destination = output / 'linked-engine.md'
        run('linked-engine', ['--cli', scan, destination, '--reserve-mib', '0'], 1)
        assert not destination.exists()
        entry.unlink()
        (work / 'engine-backup').rename(entry)
        checks.append('A substituted host-engine symlink cannot bypass the embedded native contract')
        destination = output / 'optional.md'
        run('optional-missing', ['--cli', scan, destination, '--ocr-backend', 'onnx', '--reserve-mib', '0'], 1)
        assert not destination.exists()
        checks.append('Absent optional ONNX remains explicit failure without automatic backend replacement')
        # 驗真正 native loader 路徑，不僅看到 bundle 中有同名 library。
        loader = subprocess.run([str(entry), '--version'], cwd=work, capture_output=True, text=True,
            env={**environment, 'LD_LIBRARY_PATH': str(relocated/'_internal'), 'LD_DEBUG': 'libs'}, timeout=15)
        (output/'native-loader.log').write_text(loader.stdout+loader.stderr)
        assert loader.returncode == 0
        origins = json.loads((data/'licenses/native/manifest.json').read_text())
        libraries = []
        for prefixes in [('libtesseract.so.',), ('libleptonica.so.', 'liblept.so.')]:
            matches = [entry['file'] for entry in origins['files'] if entry['file'].startswith(prefixes)]
            assert len(matches) == 1, matches
            libraries += matches
        for library in libraries:
            assert re.search(r'calling init:\s+' + re.escape(str(relocated/'_internal'/library)), loader.stderr), library
        checks.append('Native loader resolves Tesseract and Leptonica libraries inside the relocated bundle')
        windows = validate_payload(windows_payload, expected_platform='windows')
        assert windows['entrypoint'] == 'bin/tesseract.exe'
        checks.append('Fixed Windows minimal EXE, all four models and original notices statically assembled; no PE execution')
        (output/'windows-payload.json').write_bytes((windows_payload/'manifest.json').read_bytes())
        files = []
        for path in sorted(relocated.rglob('*')):
            if path.is_symlink():
                assert path.resolve().is_relative_to(relocated)
                files.append(dict(file=path.relative_to(relocated).as_posix(), link=os.readlink(path)))
            elif path.is_file():
                value = path.read_bytes()
                files.append(dict(file=path.relative_to(relocated).as_posix(), bytes=len(value), sha256=hashlib.sha256(value).hexdigest()))
        (output/'bundle-files.json').write_text(json.dumps(dict(files=files), ensure_ascii=False, indent=2)+'\n')
        (output/'build-profile.json').write_bytes((data/'build-profile.json').read_bytes())
        (output/'linux-payload.json').write_bytes((native/'manifest.json').read_bytes())
        for name, label in [('installed','installed-notices-manifest.json'),('native','native-binaries-manifest.json')]:
            (output/label).write_bytes((data/'licenses'/name/'manifest.json').read_bytes())
    report = dict(recorded_at=datetime.now(timezone.utc).isoformat(), source_version=profile['source_version'],
        check='C03-bundle-actual', accepted=True, checks_passed=len(checks), checks=checks,
        invocations=invocations, results=results, frozen=True, path_empty=True, model_environment_empty=True,
        linux_native_ocr_verified=True, windows_payload_static=True, windows_executed=False, gpu_executed=False,
        full_c03_complete=False, full_c04_complete=False, full_c09_complete=False, release_ready=False,
        bundle_files=len(files), bundle_bytes=sum(entry.get('bytes',0) for entry in files),
        scope='Actual Linux frozen development engine/4 models; Windows candidate static only. No Windows installation, GPU or general accuracy acceptance')
    (output/'frozen-acceptance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('Bundled frozen checks passed:', len(checks), '; Windows/installer remain unverified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable', type=Path, required=True)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--windows-payload', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.executable, args.fixtures, args.windows_payload, args.output)

"""在只有基本版 Python 閉包的新 venv 實際轉換；原生 OCR／Windows 另待驗收。"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from packaging.utils import canonicalize_name
from packaging_profiles import ROOT, metadata_record, read_lock, verify_profiles


def prepare(directory):
    """測試文件由完整開發環境產生，基本環境不用安裝 python-docx／reportlab。"""
    if directory.exists():
        raise FileExistsError(directory)
    directory.mkdir(parents=True)
    from docx import Document
    from openpyxl import Workbook
    from pptx import Presentation
    from PIL import Image
    from desktop_app.diagnostics import sample_pdf
    fixtures = []
    def record(name, expected):
        path = directory/name
        fixtures.append(dict(file=name, expected=expected, sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    (directory/'中文.txt').write_text('# 繁體中文基本版\n\n原文保留 12345\n', encoding='utf-8')
    record('中文.txt', ['# 繁體中文基本版', '原文保留 12345'])
    (directory/'網頁.html').write_text('<html><meta charset="utf-8"><h1>基本版標題</h1><p>測試內文 12345</p></html>', encoding='utf-8')
    record('網頁.html', ['# 基本版標題', '測試內文 12345'])
    doc = Document(); doc.add_heading('基本版文件', level=1); doc.add_paragraph('繁體內容 12345')
    table = doc.add_table(rows=2, cols=2)
    for row, values in zip(table.rows, [('項目', '金額'), ('測試', '123')]):
        for cell, value in zip(row.cells, values): cell.text = value
    doc.save(directory/'文件.docx'); record('文件.docx', ['# 基本版文件', '繁體內容 12345', '項目', '金額', '123'])
    book = Workbook(); book.active.title = '工作表'; book.active.append(['名稱', '數量']); book.active.append(['產品', 42])
    book.save(directory/'資料.xlsx'); record('資料.xlsx', ['工作表', '名稱', '產品', '42'])
    deck = Presentation(); slide = deck.slides.add_slide(deck.slide_layouts[1])
    slide.shapes.title.text = '基本版簡報'; slide.placeholders[1].text = '簡報內容 12345'
    deck.save(directory/'簡報.pptx'); record('簡報.pptx', ['基本版簡報', '簡報內容 12345'])
    sample_pdf(directory/'原生.pdf'); record('原生.pdf', ['INSTALLATION PDF CHECK 12345', 'route: native'])
    with Image.open(ROOT/'src/desktop_app/data/worker-health.png') as image:
        image.convert('RGB').save(directory/'掃描.pdf', 'PDF')
    record('掃描.pdf', [])
    (directory/'fixtures.json').write_text(json.dumps(fixtures, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def accept(fixtures, output):
    from desktop_app.core import Request, State
    from desktop_app.application import Runner
    from desktop_app.resources import Policy, MIB
    from desktop_app.diagnostics import write_report
    if output.exists(): raise FileExistsError(output)
    output.mkdir(parents=True)
    profile = verify_profiles()['profiles']['linux-runtime']
    lock = read_lock(ROOT/profile['lock'])
    installed = {canonicalize_name(dist.metadata['Name']): dist.version for dist in metadata.distributions()}
    assert set(installed) == set(lock) | {'markitdown-desktop', 'markitdown', 'pip'}, installed.keys()
    assert all(installed[name] == pin['version'] for name, pin in lock.items())
    saved_metadata = json.loads((ROOT/'packaging/profiles/metadata-linux.json').read_text())['packages']
    for name in lock:
        raw = metadata.distribution(name).read_text('METADATA').encode()
        assert metadata_record(raw) == saved_metadata[name], name
    assert sys.prefix != sys.base_prefix and 'include-system-site-packages = false' in (Path(sys.prefix)/'pyvenv.cfg').read_text()
    for module in ['rapidocr_onnxruntime', 'cv2', 'pyclipper', 'shapely', 'docx', 'reportlab']:
        assert importlib.util.find_spec(module) is None, module
    checked = subprocess.run([sys.executable, '-m', 'pip', 'check'], text=True, capture_output=True, timeout=60)
    (output/'pip-check.log').write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0, checked.stdout+checked.stderr
    records = json.loads((fixtures/'fixtures.json').read_text())
    for record in records:
        assert hashlib.sha256((fixtures/record['file']).read_bytes()).hexdigest() == record['sha256']
    # 子程序也使用空 PATH，不能借用外部 Python、Tesseract 或選配 OCR。
    os.environ['PATH'] = ''; os.environ['TESSDATA_PREFIX'] = ''
    results = []; runner = Runner(Policy(budget=2048*MIB, reserve=0), max_resource_wait=15)
    for record in records:
        source = fixtures/record['file']; destination = output/(source.name+'.md')
        outcome = runner.run(Request(source, destination, device='cpu'))
        if source.name == '掃描.pdf':
            assert outcome.state == State.FAILED and not destination.exists(), outcome
        else:
            assert outcome.state == State.COMPLETED, outcome
            content = destination.read_text(encoding='utf-8')
            assert all(value in content for value in record['expected']), (source.name, content)
            if source.suffix == '.txt': assert destination.read_bytes() == source.read_bytes()
        results.append(dict(file=source.name, state=outcome.state.value, message=outcome.message))
    from PySide6.QtWidgets import QApplication
    from desktop_app.desktop import Window
    app = QApplication.instance() or QApplication([])
    window = Window(settings_path=output/'settings.json'); window.show()
    try:
        window.add_sources([fixtures/'文件.docx', fixtures/'原生.pdf', fixtures/'中文.txt'])
        gui = output/'gui'; window.output.setText(str(gui)); window.start()
        deadline = time.monotonic()+60
        while window.job and window.job.isRunning() and time.monotonic() < deadline:
            app.processEvents(); time.sleep(.01)
        app.processEvents()
        assert window.job is not None and not window.job.isRunning()
        assert len(window.job.outcomes) == 3 and all(item.state == State.COMPLETED for item in window.job.outcomes)
        for name in ['文件.docx', '原生.pdf', '中文.txt']:
            assert (gui/(name+'.md')).read_bytes() == (output/(name+'.md')).read_bytes()
        assert window.grab().save(str(output/'desktop-base-profile.png'))
    finally:
        if window.job and window.job.isRunning():
            window.job.cancel.set(); window.job.wait(15000)
        window.close(); app.processEvents()
    report = dict(recorded_at=datetime.now(timezone.utc).isoformat(),
        source_version=metadata.version('markitdown-desktop'), check='C04-locks', accepted=True,
        checks_passed=6, checks=['exact isolated 38-package runtime and matching installed metadata', 'pip dependency integrity',
        'six actual formats in spawned workers with empty PATH', 'missing native OCR fails explicitly',
        'actual Qt batch without optional OCR or test generators', 'saved profile and notice verification'],
        results=results, installed=installed, path_empty=True, frozen=False, windows_executed=False,
        gpu_executed=False, native_ocr_bundled=False, full_c04_complete=False, full_c09_complete=False)
    write_report(report, output/'base-runtime-acceptance.json')
    print('Base isolated runtime checks passed: 6; full C04/native/Windows gates remain pending')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fixtures', type=Path, required=True)
    parser.add_argument('--prepare-fixtures', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.prepare_fixtures: prepare(args.fixtures)
    elif args.output: accept(args.fixtures, args.output)
    else: parser.error('--output is required for acceptance')


if __name__ == '__main__':
    raise SystemExit(main())

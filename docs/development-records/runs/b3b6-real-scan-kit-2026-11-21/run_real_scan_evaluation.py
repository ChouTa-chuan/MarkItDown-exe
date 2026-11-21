"""B3b6：比較現行 v4 與官方 PP-OCRv6 small 在「實際掃描」9 頁上的表現。

輸入：一個資料夾，內含 01～09 共 9 個影像檔（jpg、jpeg 或 png），第 N 頁即 README 頁序表中的第 N 個樣本。
檔名可帶後綴，第二輪的掃描檔為 01-scanner.jpg、01-phone.jpg 之類，用 --suffix 指定要評估的那一組。

計分沿用 B3b evaluate.py 的 normalized() 與 edit_distance()，語言彙總沿用 B3b2 run_evaluation.py 的 language_totals()。
參考字串來自 B3b2 samples.json。模型設定沿用 B3b5：v4 為 rapidocr-onnxruntime 1.4.4 內附權重，
v6 為官方 ONNX，字表由 B3b5 official_check.py 從官方 inference.yml 建立並核對雜湊。
偵測器、方向分類器與信心門檻都沿用 1.4.4 內附設定，只替換識別權重，CPU 單執行緒。

影像前處理（--mode）：
- page：整張影像直接辨識（預設，見 README 的實驗結果與理由）。
- trim：先找出墨跡範圍再裁切，只用來做對照實驗。

本腳本只讀取輸入圖、不修改，結果 JSON 以 'x' 模式寫入新檔，不覆蓋既有結果。
"""
import argparse
import hashlib
import importlib.metadata
import importlib.util
import json
from importlib.resources import files
from pathlib import Path
import platform
import re

from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
B3B = RUNS/'b3b-ppocr-model-review-2026-11-20'
B3B2 = RUNS/'b3b2-expanded-ocr-evaluation-2026-11-20'
B3B5 = RUNS/'b3b5-official-onnx-rerun-2026-11-20'
IMAGE_SUFFIXES = ('.jpg', '.jpeg', '.png')
NAME_PATTERN = re.compile(r'^(\d{2})(-[A-Za-z]+)?\.(jpe?g|png)$', re.IGNORECASE)
V4, V6 = 'v4-current', 'v6-official'


def load(name, path):
    """以檔案路徑載入同層的歷史評估模組，不改動原檔。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_inputs(folder, suffix, samples):
    """依檔名找出 9 頁。數量、頁號與後綴有任何不符就停止，並說明原因。"""
    if not folder.is_dir():
        raise SystemExit(f'找不到輸入資料夾：{folder}')
    groups = {}
    for path in sorted(folder.iterdir()):
        if not path.is_file() or path.suffix.lower() not in IMAGE_SUFFIXES:
            continue
        match = NAME_PATTERN.match(path.name)
        if not match:
            raise SystemExit(f'檔名不符規則（應為 01.jpg、01-scanner.png 之類）：{path.name}')
        page = int(match.group(1))
        # 後綴去掉開頭的連字號並轉小寫，例如 01-Scanner.jpg 的後綴為 scanner。
        tag = (match.group(2) or '')[1:].lower()
        if not 1 <= page <= len(samples):
            raise SystemExit(f'頁號超出 01～{len(samples):02d}：{path.name}')
        groups.setdefault(tag, {}).setdefault(page, []).append(path)
    wanted = suffix.lower().lstrip('-')
    chosen = groups.get(wanted, {})
    for page, paths in chosen.items():
        if len(paths) != 1:
            raise SystemExit(f'第 {page:02d} 頁有 {len(paths)} 個同名後綴的檔案，請只保留一個：'
                             + '、'.join(p.name for p in paths))
    missing = [f'{i:02d}' for i in range(1, len(samples)+1) if i not in chosen]
    if missing:
        raise SystemExit(f'後綴 "{suffix or "（無）"}" 缺少頁：{"、".join(missing)}；共需 9 頁')
    ignored = sorted(tag for tag in groups if tag != wanted)
    return [dict(sample=samples[i-1]['id'], page=i, path=chosen[i][0]) for i in range(1, len(samples)+1)], ignored


def ink_bbox(gray, margin_ratio=0.02):
    """找墨跡範圍並保留少量邊界。只用於 trim 對照。"""
    mask = gray < 160
    rows = np.where(mask.any(axis=1))[0]
    cols = np.where(mask.any(axis=0))[0]
    if rows.size == 0 or cols.size == 0:
        return (0, 0, gray.shape[1], gray.shape[0])
    h, w = gray.shape
    mh, mw = int(h*margin_ratio), int(w*margin_ratio)
    top, bottom = max(0, rows[0]-mh), min(h, rows[-1]+mh)
    left, right = max(0, cols[0]-mw), min(w, cols[-1]+mw)
    return (left, top, right, bottom)


def load_bgr(path, mode):
    """讀入影像並轉成 OpenCV 慣用的 BGR 陣列（與 B3b、B3b5 相同的通道順序）。"""
    with Image.open(path) as image:
        gray = image.convert('L')
        if mode == 'trim':
            gray = gray.crop(ink_bbox(np.asarray(gray)))
        rgb = gray.convert('RGB')
        return np.asarray(rgb)[:, :, ::-1].copy(), gray.size


def recognize(engine, bgr):
    rows, _ = engine(bgr)
    rows = rows or []
    return '\n'.join(row[1] for row in rows), len(rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan-dir', type=Path, required=True, help='含 01～09 影像的資料夾（repo 外）')
    parser.add_argument('--suffix', default='', help='檔名後綴，例如 scanner 或 phone；預設無後綴')
    parser.add_argument('--mode', choices=('page', 'trim'), default='page')
    parser.add_argument('--official-v6', type=Path, required=True, help='repo 外的官方 v6 ONNX')
    parser.add_argument('--official-v6-yml', type=Path, required=True, help='repo 外的官方 v6 inference.yml')
    parser.add_argument('--chars-dir', type=Path, required=True, help='字表輸出目錄（新目錄，repo 外）')
    parser.add_argument('--output', type=Path, required=True, help='新的結果 JSON，不覆蓋')
    args = parser.parse_args()

    b3b = load('b3b_evaluate', B3B/'evaluate.py')
    b3b2 = load('b3b2_run_evaluation', B3B2/'run_evaluation.py')
    b3b5_check = load('b3b5_official_check', B3B5/'official_check.py')
    b3b5_run = load('b3b5_run_official', B3B5/'run_official_evaluation.py')

    # 1. 套件版本與 v4 權重必須與 B3b 基準相同；官方 v6 由 B3b5 的固定指紋核對。
    inputs = json.loads((B3B/'evaluation-inputs.json').read_text(encoding='utf-8'))
    expected_versions = inputs['required_versions']
    versions = {name: importlib.metadata.version(name) for name in expected_versions}
    if versions != expected_versions:
        raise SystemExit(f'套件版本與 B3b 基準不同：{versions}')
    installed = files('rapidocr_onnxruntime')
    for asset in json.loads((B3B/'current-models.json').read_text(encoding='utf-8'))['members']:
        b3b.read_verified(installed/asset['wheel_member'].partition('/')[2], asset['sha256'], asset['bytes'])
    pins = {row['id']: row for row in inputs['models']}
    v4_path = installed/pins[V4]['filename']
    b3b.read_verified(v4_path, pins[V4]['sha256'], pins[V4]['bytes'])
    args.chars_dir.mkdir(parents=True, exist_ok=True)
    v6_info = b3b5_check.check_one('v6', args.official_v6, args.official_v6_yml,
                                   args.chars_dir/'v6-official-keys.txt')
    keys_v6 = args.chars_dir/'v6-official-keys.txt'

    # 2. 樣本與輸入：參考字串來自 B3b2 samples.json，輸入頁依檔名對應，逐張計算雜湊記錄。
    plan = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))
    samples = plan['samples']
    references = {s['id']: s['reference'] for s in samples}
    pages, ignored = collect_inputs(args.scan_dir, args.suffix, samples)
    input_records = []
    for page in pages:
        data = page['path'].read_bytes()
        input_records.append(dict(page=page['page'], sample=page['sample'], file=page['path'].name,
                                  bytes=len(data), sha256=hashlib.sha256(data).hexdigest()))

    # 3. 建立兩個引擎。每個引擎只建立一次，並檢查 provider 與字表長度。
    engines = {
        V4: (b3b5_run.build_engine(v4_path, None)[0], pins[V4]['sha256'], pins[V4]['bytes']),
        V6: (b3b5_run.build_engine(args.official_v6, keys_v6)[0], v6_info['onnx_sha256'], v6_info['onnx_bytes']),
    }

    # 4. 逐頁辨識與計分。
    results = {}
    for name, (engine, digest, size) in engines.items():
        per_page = {}
        for page in pages:
            bgr, size_px = load_bgr(page['path'], args.mode)
            text, lines = recognize(engine, bgr)
            score = b3b5_run.score(b3b, references[page['sample']], text, lines)
            score['image_size_px'] = list(size_px)
            per_page[page['sample']] = score
        results[name] = dict(sha256=digest, bytes=size, pages=per_page,
                             by_language=b3b2.language_totals(per_page, samples))
        print(f'done {name}', flush=True)

    # 5. 三語與全部合計。language_totals 只分語言，這裡另算全部頁的字數加權。
    overall = {}
    for name, result in results.items():
        edits = sum(p['edits'] for p in result['pages'].values())
        chars = sum(p['reference_characters'] for p in result['pages'].values())
        overall[name] = dict(reference_characters=chars, edits=edits,
                             character_error_rate=round(edits/chars, 6),
                             character_accuracy=max(0, round(1-edits/chars, 6)))

    output = dict(
        method='B3b normalized() 與 edit_distance()；語言與合計 CER = 總編輯數／總參考字數；accuracy = max(0, 1-CER)',
        mode=args.mode,
        suffix=args.suffix,
        ignored_suffix_groups=ignored,
        inputs=input_records,
        environment=dict(python=platform.python_version(), system=platform.platform(), packages=versions,
                         provider='CPUExecutionProvider', intra_threads=1, inter_threads=1),
        official_v6=dict(repo=v6_info['repo'], commit=v6_info['commit'], onnx_sha256=v6_info['onnx_sha256'],
                         chars_file_sha256=v6_info['chars_file_sha256']),
        results=results,
        overall=overall,
    )
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(overall, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

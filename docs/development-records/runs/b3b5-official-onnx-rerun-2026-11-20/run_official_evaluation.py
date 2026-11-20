"""B3b5：以官方 PP-OCRv6 small 與 PP-OCRv5 mobile ONNX 重跑 B3b 的評估，輸入與 B3b3、B3b4 相同。

比較的模型：
- v4-current：現行 rapidocr-onnxruntime 1.4.4 內附權重。本輪重跑一次，作為環境一致性的檢查
  （必須與 B3b3、B3b4 已記錄的逐樣本編輯數相同）。
- v6-official、v5-official：本輪下載的官方 ONNX，字表以官方 inference.yml 建立（見 official_check.py）。
- v6-rapid-small、v5-rapid-mobile：RapidOCR 轉檔版，直接引用 B3b3 與 B3b4 已記錄的結果，不重跑。

計分沿用 B3b evaluate.py 的 normalized() 與 edit_distance()，語言彙總沿用 B3b2 run_evaluation.py 的 language_totals()。
偵測與方向分類器都沿用 1.4.4 內附設定，只替換識別權重；CPU 單執行緒。

重要的差別：官方 ONNX 沒有內嵌字表，因此本腳本以 rec_keys_path 指定外部字表（由 official_check.py 產生）。
RapidOCR 轉檔版的字表來自 ONNX metadata，不需要外部字表，兩者都會通過「CTC 輸出類別 = 字表長度」的檢查。

所有輸入圖都依登記的 SHA-256 核對；不符就停止。模擬劣化圖由 B3b3 與 B3b4 的腳本產生，本腳本不產生圖。
"""
import argparse
import hashlib
import importlib.metadata
from importlib.resources import files
import importlib.util
import json
from pathlib import Path
import platform
import statistics
import time

from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
B3B = RUNS/'b3b-ppocr-model-review-2026-11-20'
B3B2 = RUNS/'b3b2-expanded-ocr-evaluation-2026-11-20'
B3B3 = RUNS/'b3b3-v5-provenance-scan-2026-11-20'
B3B4 = RUNS/'b3b4-v6-official-provenance-2026-11-20'
SEED = 20261120  # 與 B3b3、B3b4 相同；本腳本沒有亂數，此值只為記錄來源。

# 條件分組。名稱與 B3b3、B3b4 結果檔內的條件 id 完全相同。
NON_ROTATION = ['blur-0.8', 'blur-1.5', 'noise-10', 'noise-20', 'contrast-0.5', 'contrast-0.3',
                'down-up-50', 'down-up-33', 'jpeg-q30', 'jpeg-q12']
OLD_ROTATION = ['rotate-0.8', 'rotate-2.0']           # B3b3：無 expand，旋轉時裁切四角
EXPAND_ROTATION = ['rotate-0.8-expand', 'rotate-2.0-expand']  # B3b4：expand=True，不裁切
LANGS = ('zh-hant', 'zh-hans', 'en')
RAPID_V6, RAPID_V5, V4 = 'v6-rapid-small', 'v5-rapid-mobile', 'v4-current'


def load(name, path):
    """以檔案路徑載入同層的歷史評估模組，不改動原檔。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def build_engine(model_path, keys_path):
    """建立 RapidOCR 引擎並檢查 provider 與字表長度。keys_path 為 None 時沿用 ONNX metadata 字表。"""
    kwargs = dict(rec_model_path=str(model_path), intra_op_num_threads=1, inter_op_num_threads=1)
    if keys_path is not None:
        kwargs['rec_keys_path'] = str(keys_path)
    engine = RapidOCR(**kwargs)
    rec = engine.text_rec
    sessions = (engine.text_det.infer.session, engine.text_cls.infer.session, rec.session.session)
    if any(session.get_providers() != ['CPUExecutionProvider'] for session in sessions):
        raise ValueError('本輪只使用 CPUExecutionProvider')
    session = rec.session.session
    labels = len(rec.postprocess_op.character)
    classes = session.get_outputs()[0].shape[-1]
    if classes != labels:
        raise ValueError(f'CTC 輸出類別 {classes} 與字表長度 {labels} 不符：{model_path.name}')
    info = dict(input_shape=[str(d) for d in session.get_inputs()[0].shape],
                ctc_output_classes=classes, character_len=labels)
    return engine, info


def recognize(engine, path):
    """與 B3b evaluate.measure() 相同的輸入處理：RGB 轉 BGR，逐行合併辨識文字。"""
    with Image.open(path) as image:
        bgr = np.asarray(image.convert('RGB'))[:, :, ::-1].copy()
    rows, _ = engine(bgr)
    return '\n'.join(row[1] for row in (rows or [])), len(rows or [])


def score(b3b, reference, recognized, lines):
    expected, actual = b3b.normalized(reference), b3b.normalized(recognized)
    edits = b3b.edit_distance(expected, actual)
    return dict(text=recognized, recognized_lines=lines, reference_characters=len(expected), edits=edits,
                character_error_rate=round(edits/len(expected), 6),
                character_accuracy=max(0, round(1-edits/len(expected), 6)))


def check_manifest(manifest_path, reference_path, b3b):
    """新產生的劣化 manifest 必須與 B3b3 或 B3b4 已登記的每張輸出圖雜湊完全相同。"""
    new = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    old = json.loads(Path(reference_path).read_text(encoding='utf-8'))
    a = {(o['condition'], o['sample']): o['sha256'] for o in new['outputs']}
    b = {(o['condition'], o['sample']): o['sha256'] for o in old['outputs']}
    if a != b:
        raise ValueError(f'劣化圖 manifest 與登記不符：{manifest_path}')
    return new


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official-v6', type=Path, required=True, help='repo 外的官方 v6 ONNX')
    parser.add_argument('--official-v5', type=Path, required=True, help='repo 外的官方 v5 ONNX')
    parser.add_argument('--keys-v6', type=Path, required=True, help='official_check.py 產生的 v6 字表')
    parser.add_argument('--keys-v5', type=Path, required=True, help='official_check.py 產生的 v5 字表')
    parser.add_argument('--check', type=Path, required=True, help='official_check.py 的結果 JSON（含字表雜湊）')
    parser.add_argument('--scan-dir', type=Path, required=True, help='B3b3 degrade_scan.py 的輸出目錄')
    parser.add_argument('--scan-manifest', type=Path, required=True)
    parser.add_argument('--expand-dir', type=Path, required=True, help='B3b4 degrade_expand.py 的輸出目錄')
    parser.add_argument('--expand-manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='新的結果 JSON，不覆蓋')
    args = parser.parse_args()

    b3b = load('b3b_evaluate', B3B/'evaluate.py')
    b3b2 = load('b3b2_run_evaluation', B3B2/'run_evaluation.py')

    # 1. 套件版本與 RapidOCR 內附權重必須與 B3b 基準相同。
    inputs = json.loads((B3B/'evaluation-inputs.json').read_text(encoding='utf-8'))
    expected_versions = inputs['required_versions']
    versions = {name: importlib.metadata.version(name) for name in expected_versions}
    if versions != expected_versions:
        raise ValueError(f'套件版本與 B3b 基準不同：{versions}')
    installed = files('rapidocr_onnxruntime')
    for asset in json.loads((B3B/'current-models.json').read_text(encoding='utf-8'))['members']:
        b3b.read_verified(installed/asset['wheel_member'].partition('/')[2], asset['sha256'], asset['bytes'])

    # 2. 模型檔：v4 來自 wheel；官方檔與字表以 official_check.py 的結果核對。
    pins = {row['id']: row for row in inputs['models']}
    check = json.loads(args.check.read_text(encoding='utf-8'))
    v4_path = installed/pins[V4]['filename']
    b3b.read_verified(v4_path, pins[V4]['sha256'], pins[V4]['bytes'])
    official = {
        'v6-official': (args.official_v6, args.keys_v6, check['models']['v6']),
        'v5-official': (args.official_v5, args.keys_v5, check['models']['v5']),
    }
    for name, (onnx, keys, info) in official.items():
        b3b.read_verified(onnx, info['onnx_sha256'], info['onnx_bytes'])
        b3b.read_verified(keys, info['chars_file_sha256'], info['chars_file_bytes'])

    # 3. 輸入圖：B3b2 原圖、B3b3 的 12 種劣化、B3b4 的 2 種 expand 旋轉。每張都核對雜湊。
    plan = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))
    languages = {s['id']: s['language'] for s in plan['samples']}
    references = {s['id']: s['reference'] for s in plan['samples']}
    sample_plan = [dict(id=s['id'], language=s['language']) for s in plan['samples']]
    conditions = [dict(id='clean', label='B3b2 原始合成圖（對照）',
                       files=[(s['id'], B3B2/'samples'/s['file'], s['sha256']) for s in plan['samples']])]
    for manifest_path, reference_path, directory in (
            (args.scan_manifest, B3B3/'scan-degradation-manifest.json', args.scan_dir),
            (args.expand_manifest, B3B4/'expand-manifest.json', args.expand_dir)):
        manifest = check_manifest(manifest_path, reference_path, b3b)
        grouped = {}
        for out in manifest['outputs']:
            grouped.setdefault(out['condition'], []).append(out)
        for cond in manifest['conditions']:
            conditions.append(dict(id=cond['id'], label=cond['label'],
                                   files=[(r['sample'], directory/r['file'], r['sha256'])
                                          for r in grouped[cond['id']]]))
    for cond in conditions:
        for sample_id, path, digest in cond['files']:
            b3b.read_verified(path, digest)

    # 4. 逐模型逐條件評估。每個模型只建立一次引擎。
    v4_engine, v4_meta = build_engine(v4_path, None)
    engines = {V4: (v4_engine, v4_meta, v4_path, pins[V4]['sha256'], pins[V4]['bytes'])}
    for name, (onnx, keys, info) in official.items():
        engine, meta = build_engine(onnx, keys)
        engines[name] = (engine, meta, onnx, info['onnx_sha256'], info['onnx_bytes'])

    results = {}
    for cond in conditions:
        cond_out = {}
        for name, (engine, meta, path, digest, size) in engines.items():
            samples = {}
            for sample_id, img_path, _ in cond['files']:
                recognized, lines = recognize(engine, img_path)
                samples[sample_id] = score(b3b, references[sample_id], recognized, lines)
            cond_out[name] = dict(sha256=digest, bytes=size, samples=samples,
                                  by_language=b3b2.language_totals(samples, sample_plan))
        results[cond['id']] = dict(label=cond['label'], models=cond_out)
        print(f'done {cond["id"]}', flush=True)

    # 5. 環境一致性：本輪重跑的 v4 必須與 B3b3（舊旋轉與非旋轉）、B3b4（expand）記錄的逐樣本編輯數相同。
    recorded_scan = json.loads((B3B3/'scan-evaluation-results.json').read_text(encoding='utf-8'))['results']
    recorded_expand = json.loads((B3B4/'expand-results.json').read_text(encoding='utf-8'))['results']

    def recorded(model, cond_id):
        src = recorded_expand if cond_id in EXPAND_ROTATION else recorded_scan
        return src[cond_id]['models'][model]

    mismatch = []
    for cond_id in results:
        if cond_id == 'clean':
            ref_clean = recorded_scan['clean']['models'][V4]['samples']
            for sid, meas in results[cond_id]['models'][V4]['samples'].items():
                if meas['edits'] != ref_clean[sid]['edits']:
                    mismatch.append(('clean', sid))
            continue
        ref = recorded(V4, cond_id)['samples']
        for sid, meas in results[cond_id]['models'][V4]['samples'].items():
            if meas['edits'] != ref[sid]['edits'] or meas['text'] != ref[sid]['text']:
                mismatch.append((cond_id, sid))
    sanity = dict(v4_rerun_vs_recorded_samples_compared=sum(len(c['models'][V4]['samples']) for c in results.values()),
                  v4_rerun_mismatches=mismatch)

    # 6. 彙總：三種口徑。參照組（RapidOCR 轉檔版、v4 記錄值）直接取 B3b3、B3b4 的結果檔，不重跑。
    def by_lang(model_key, cond_id):
        if model_key in ('v6-official', 'v5-official'):
            return results[cond_id]['models'][model_key]['by_language']
        if model_key == 'v4-rerun':
            return results[cond_id]['models'][V4]['by_language']
        return recorded(model_key.replace('v4-recorded', V4), cond_id)['by_language']

    def totals(model_key, conds):
        out = {}
        for lang in LANGS:
            edits = refs = 0
            for cond_id in conds:
                row = by_lang(model_key, cond_id)[lang]
                edits += row['edits']
                refs += row['reference_characters']
            out[lang] = dict(edits=edits, reference_characters=refs, accuracy=round(1-edits/refs, 4))
        return out

    views = {
        '含舊旋轉（12 條件）': NON_ROTATION + OLD_ROTATION,
        '排除舊旋轉（10 條件）': NON_ROTATION,
        '排除舊旋轉＋expand 旋轉（12 條件）': NON_ROTATION + EXPAND_ROTATION,
    }
    model_keys = ['v4-recorded', 'v4-rerun', RAPID_V6, 'v6-official', RAPID_V5, 'v5-official']
    summary = {view: {m: totals(m, conds) for m in model_keys} for view, conds in views.items()}

    # 簡中逐條件編輯數（含 expand 條件與原圖）。
    per_zh_hans = {}
    for cond_id in ['clean'] + NON_ROTATION + OLD_ROTATION + EXPAND_ROTATION:
        per_zh_hans[cond_id] = {m: by_lang(m, cond_id)['zh-hans']['edits'] for m in model_keys}

    # 官方與轉檔版逐樣本文字是否相同（v6 與 v5 各一組）。
    def text_diff(official_key, rapid_key):
        same, diff = 0, []
        for cond_id in results:
            if cond_id == 'clean':
                rapid_samples = recorded_scan['clean']['models'][rapid_key]['samples']
            elif cond_id in EXPAND_ROTATION:
                rapid_samples = recorded_expand[cond_id]['models'][rapid_key]['samples']
            else:
                rapid_samples = recorded_scan[cond_id]['models'][rapid_key]['samples']
            for sid, meas in results[cond_id]['models'][official_key]['samples'].items():
                if meas['text'] == rapid_samples[sid]['text']:
                    same += 1
                else:
                    diff.append(dict(condition=cond_id, sample=sid, language=languages[sid],
                                     official_edits=meas['edits'], rapid_edits=rapid_samples[sid]['edits']))
        return dict(identical_text_samples=same, different_text_samples=len(diff), differences=diff)

    # 7. 粗略推論時間（同環境、單執行緒，每張取 3 次中位數後加總，僅供參考）。
    images = [(s['id'], B3B2/'samples'/s['file']) for s in plan['samples']]
    timing = {}
    for name in (V4, 'v6-official', 'v5-official'):
        engine = engines[name][0]
        per_image = []
        for _, img_path in images:
            times = []
            for _ in range(3):
                t0 = time.perf_counter()
                recognize(engine, img_path)
                times.append(time.perf_counter() - t0)
            per_image.append(statistics.median(times))
        timing[name] = dict(total_median_seconds_9_images=round(sum(per_image), 3),
                            mean_per_image_seconds=round(sum(per_image)/len(per_image), 3))

    output = dict(
        method='B3b normalized() 與 edit_distance()；語言正確率 = 1 − 總編輯距離／總參考字數（按字數加權，B3b2 language_totals）',
        caveat='模擬掃描，不等於真實掃描機成像；官方檔只在這組固定條件上比較，結論不外推。',
        seed=SEED,
        environment=dict(python=platform.python_version(), system=platform.platform(),
                         packages=versions, provider='CPUExecutionProvider', intra_threads=1, inter_threads=1),
        official_models={name: dict(onnx_sha256=info['onnx_sha256'], onnx_bytes=info['onnx_bytes'],
                                    chars_file_sha256=info['chars_file_sha256'],
                                    ctc_output_classes=info['ctc_output_classes'],
                                    input_shape=info['onnx_input_shape'])
                         for name, (_, _, info) in official.items()},
        sanity=sanity,
        summary=summary,
        per_condition_zh_hans_edits=per_zh_hans,
        v6_official_vs_rapid_text=text_diff('v6-official', RAPID_V6),
        v5_official_vs_rapid_text=text_diff('v5-official', RAPID_V5),
        timing=timing,
        results=results,
    )
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

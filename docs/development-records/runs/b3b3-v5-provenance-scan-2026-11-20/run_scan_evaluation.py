"""比較 v4、v5 mobile 與 v6 small 在「模擬掃描」劣化圖上的識別表現。

沿用 B3b 的 evaluate.measure()（只換識別權重、偵測與方向分類固定）與
B3b2 的按語言字數加權計分。劣化圖由 degrade_scan.py 產生，這裡以其 manifest
核對每張輸入圖的 SHA-256，不接受未登記的輸入。
"""
import argparse
import importlib.metadata
import importlib.util
from importlib.resources import files
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
RUNS = HERE.parent
B3B = RUNS/'b3b-ppocr-model-review-2026-11-20'
B3B2 = RUNS/'b3b2-expanded-ocr-evaluation-2026-11-20'
MODEL_IDS = ('v4-current', 'v5-rapid-mobile', 'v6-rapid-small')


def load(name, path):
    """以檔案路徑載入同層的評估模組，不改動歷史腳本。"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True, help='repo 外的候選權重目錄')
    parser.add_argument('--degraded-dir', type=Path, required=True, help='degrade_scan.py 的輸出目錄')
    parser.add_argument('--manifest', type=Path, required=True, help='degrade_scan.py 產生的 manifest')
    parser.add_argument('--output', type=Path, required=True, help='新的結果 JSON，不覆蓋')
    args = parser.parse_args()

    b3b = load('b3b_evaluate', B3B/'evaluate.py')
    b3b2 = load('b3b2_run_evaluation', B3B2/'run_evaluation.py')

    sources = json.loads((B3B/'evaluation-inputs.json').read_text(encoding='utf-8'))
    expected_versions = sources['required_versions']
    versions = {name: importlib.metadata.version(name) for name in expected_versions}
    if versions != expected_versions:
        raise ValueError(f'套件版本與 B3b 基準不同：{versions}')

    installed = files('rapidocr_onnxruntime')
    baseline = json.loads((B3B/'current-models.json').read_text(encoding='utf-8'))
    for asset in baseline['members']:
        b3b.read_verified(installed/asset['wheel_member'].partition('/')[2], asset['sha256'], asset['bytes'])

    pins = {row['id']: row for row in sources['models']}
    model_paths = {}
    for ident in MODEL_IDS:
        pin = pins[ident]
        path = installed/pin['filename'] if ident == 'v4-current' else args.models/pin['filename']
        b3b.read_verified(path, pin['sha256'], pin['bytes'])
        model_paths[ident] = (path, pin)

    plan = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))
    manifest = json.loads(args.manifest.read_text(encoding='utf-8'))
    # 條件清單：先是原始合成圖（對照），再是各劣化條件。
    conditions = [dict(id='clean', label='B3b2 原始合成圖（對照）', source=B3B2/'samples', files=[
        (s['id'], s['language'], B3B2/'samples'/s['file'], s['sha256'], s['reference']) for s in plan['samples']])]
    grouped = {}
    for out in manifest['outputs']:
        grouped.setdefault(out['condition'], []).append(out)
    references = {s['id']: s for s in plan['samples']}
    for cond in manifest['conditions']:
        rows = grouped[cond['id']]
        conditions.append(dict(id=cond['id'], label=cond['label'], source=args.degraded_dir, files=[
            (r['sample'], references[r['sample']]['language'], args.degraded_dir/r['file'], r['sha256'],
             references[r['sample']]['reference']) for r in rows]))

    results = {}
    for cond in conditions:
        samples, sample_plan = {}, []
        for sample_id, language, path, digest, reference in cond['files']:
            # 輸入圖必須與登記的雜湊相符，否則停止。
            b3b.read_verified(path, digest)
            samples[sample_id] = dict(path=path.as_posix(), reference=reference)
            sample_plan.append(dict(id=sample_id, language=language))
        cond_result = {}
        for ident in MODEL_IDS:
            path, pin = model_paths[ident]
            measurements = b3b.measure(path, samples)
            cond_result[ident] = dict(
                sha256=pin['sha256'], bytes=pin['bytes'],
                samples=measurements['samples'],
                by_language=b3b2.language_totals(measurements['samples'], sample_plan),
            )
        results[cond['id']] = dict(label=cond['label'], models=cond_result)

    output = dict(
        method='B3b normalized() 與 edit_distance()；語言正確率 = 1 − 總編輯距離／總參考字數（按字數加權）',
        caveat='模擬掃描，不等於真實掃描機成像；結論只適用於這組固定參數。',
        seed=manifest['seed'],
        environment=dict(python=platform.python_version(), system=platform.platform(),
                         packages=versions, provider='CPUExecutionProvider',
                         intra_threads=1, inter_threads=1),
        results=results,
    )
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

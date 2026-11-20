"""用 B3b 的 CPU 評估入口和計分方式逐張比較 B3b2 固定圖。"""
import argparse
import importlib.metadata
from importlib.resources import files
import importlib.util
import json
from pathlib import Path
import platform

HERE = Path(__file__).resolve().parent
B3B = HERE.parent/'b3b-ppocr-model-review-2026-11-20'
MODEL_IDS = ('v4-current', 'v5-rapid-mobile', 'v6-rapid-small', 'v3-umi-cht')


def language_totals(results, samples):
    """以字數加權合併編輯距離，避免小樣本與長內文各占相同權重。"""
    totals = {}
    for sample in samples:
        measurement = results[sample['id']]
        total = totals.setdefault(sample['language'], dict(samples=0, reference_characters=0, edits=0))
        total['samples'] += 1
        total['reference_characters'] += measurement['reference_characters']
        total['edits'] += measurement['edits']
    for total in totals.values():
        rate = total['edits']/total['reference_characters']
        total['character_error_rate'] = round(rate, 6)
        total['character_accuracy'] = max(0, round(1-rate, 6))
    return totals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True, help='repo 外的本機候選權重目錄')
    parser.add_argument('--output', type=Path, required=True, help='新的評估結果 JSON')
    args = parser.parse_args()

    spec = importlib.util.spec_from_file_location('b3b_evaluate', B3B/'evaluate.py')
    b3b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3b)

    sources = json.loads((B3B/'evaluation-inputs.json').read_text(encoding='utf-8'))
    expected_versions = sources['required_versions']
    versions = {name: importlib.metadata.version(name) for name in expected_versions}
    if versions != expected_versions:
        raise ValueError(f'套件版本與 B3b 基準不同：{versions}')

    installed = files('rapidocr_onnxruntime')
    baseline = json.loads((B3B/'current-models.json').read_text(encoding='utf-8'))
    for asset in baseline['members']:
        path = asset['wheel_member'].partition('/')[2]
        b3b.read_verified(installed/path, asset['sha256'], asset['bytes'])

    plan = json.loads((HERE/'samples.json').read_text(encoding='utf-8'))
    samples = {}
    for sample in plan['samples']:
        file = HERE/'samples'/sample['file']
        b3b.read_verified(file, sample['sha256'], sample['bytes'])
        samples[sample['id']] = dict(path=file.relative_to(b3b.ROOT).as_posix(), reference=sample['reference'])
    model_pins = {row['id']: row for row in sources['models']}
    results = {}
    for ident in MODEL_IDS:
        pin = model_pins[ident]
        model_dir = installed if ident == 'v4-current' else args.models
        model = model_dir/pin['filename']
        b3b.read_verified(model, pin['sha256'], pin['bytes'])
        measurements = b3b.measure(model, samples)
        results[ident] = dict(sha256=pin['sha256'], bytes=pin['bytes'], **measurements,
                              by_language=language_totals(measurements['samples'], plan['samples']))

    output = {
        'method': 'B3b normalized() and edit_distance(); language CER = total edits / total reference characters',
        'environment': dict(python=platform.python_version(), system=platform.platform(), packages=versions,
                            provider='CPUExecutionProvider', intra_threads=1, inter_threads=1),
        'results': results,
    }
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(output, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

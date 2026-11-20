"""B3b 的離線試跑入口。只讀本機權重及固定圖，輸出測量 JSON。"""
import argparse
import hashlib
import importlib.metadata
from importlib.resources import files
import json
from pathlib import Path
import platform
import unicodedata

from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]


def read_verified(path, digest, size=None):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest or (size is not None and len(data) != size):
        raise ValueError(f'B3b 檔案與固定指紋不符：{path.name}')
    return data


def normalized(text):
    # 保留字形、大小寫及標點，忽略 OCR 框切分造成的空白差異。
    return ''.join(unicodedata.normalize('NFC', text).split())


def edit_distance(expected, actual):
    row = list(range(len(actual) + 1))
    for i, a in enumerate(expected, 1):
        next_row = [i]
        for j, b in enumerate(actual, 1):
            next_row.append(min(row[j] + 1, next_row[-1] + 1, row[j - 1] + (a != b)))
        row = next_row
    return row[-1]


def measure(model, samples):
    # 只換識別器路徑。偵測器、方向分類器、信心門檻都沿用同一份 wheel 設定。
    engine = RapidOCR(rec_model_path=str(model), intra_op_num_threads=1,
                      inter_op_num_threads=1)
    rec = engine.text_rec
    sessions = (engine.text_det.infer.session, engine.text_cls.infer.session, rec.session.session)
    if any(session.get_providers() != ['CPUExecutionProvider'] for session in sessions):
        raise ValueError('B3b 僅使用 CPUExecutionProvider')
    session = sessions[-1]
    input_shape = session.get_inputs()[0].shape
    output_shape = session.get_outputs()[0].shape
    labels = len(rec.postprocess_op.character)
    if output_shape[-1] != labels:
        raise ValueError(f'CTC 字元表長度與輸出類別數不同：{model.name}')
    measured = {}
    for language, sample in samples.items():
        with Image.open(ROOT/sample['path']) as image:
            bgr = np.asarray(image.convert('RGB'))[:, :, ::-1].copy()
        rows, _ = engine(bgr)
        recognized = '\n'.join(row[1] for row in (rows or []))
        expected, actual = normalized(sample['reference']), normalized(recognized)
        edits = edit_distance(expected, actual)
        measured[language] = dict(text=recognized, recognized_lines=len(rows or []),
            reference_characters=len(expected), edits=edits, character_error_rate=round(edits/len(expected), 6),
            character_accuracy=max(0, round(1-edits/len(expected), 6)))
    return dict(input_shape=input_shape, ctc_output_classes=labels, samples=measured)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--models', type=Path, required=True, help='本機候選模型目錄')
    parser.add_argument('--output', type=Path, required=True, help='新結果檔；不覆蓋歷史結果')
    parser.add_argument('--available-only', action='store_true', help='缺少候選檔時記為未執行')
    args = parser.parse_args()
    plan = json.loads((HERE/'evaluation-inputs.json').read_text(encoding='utf-8'))
    version = importlib.metadata.version
    environments = {name: version(name) for name in plan['required_versions']}
    if environments != plan['required_versions']:
        raise ValueError(f'套件版本與評估基準不同：{environments}')
    origin = json.loads((HERE/'current-models.json').read_text(encoding='utf-8'))
    install = files('rapidocr_onnxruntime')
    for member in origin['members']:
        package_path = member['wheel_member'].partition('/')[2]
        read_verified(install/package_path, member['sha256'], member['bytes'])
    for sample in plan['samples'].values():
        read_verified(ROOT/sample['path'], sample['sha256'])
    results = {}
    for row in plan['models']:
        name = row['id']
        path = install/row['filename'] if name=='v4-current' else args.models/row['filename']
        if not path.is_file() and name!='v4-current' and args.available_only:
            results[name] = dict(status='not-run', reason='missing candidate bytes')
            continue
        read_verified(path, row['sha256'], row['bytes'])
        results[name] = dict(status='measured', sha256=row['sha256'], **measure(path, plan['samples']))
    baseline = results['v4-current']['samples']
    for row in results.values():
        if row['status']=='measured':
            row['simplified_not_worse_on_sample'] = row['samples']['zh-hans']['edits'] <= baseline['zh-hans']['edits']
    result = dict(method='NFC and whitespace-stripped character edit distance; CER=edits/N; accuracy=max(0, 1-CER)',
                  environment=dict(python=platform.python_version(),system=platform.platform(),packages=environments,
                                   provider='CPUExecutionProvider',intra_threads=1,inter_threads=1),
                  results=results)
    with args.output.open('x', encoding='utf-8') as output:
        json.dump(result, output, ensure_ascii=False, indent=2)
        output.write('\n')


if __name__ == '__main__':
    main()

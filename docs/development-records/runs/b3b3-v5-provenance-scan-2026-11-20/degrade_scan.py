"""以固定參數與固定亂數種子，把 B3b2 的合成圖劣化成「模擬掃描」。

這只是模擬，不等於真實掃描機的成像。每種劣化各有一個固定的參數，
輸出圖的 SHA-256 與參數一併寫入 manifest，方便之後逐位元組核對。
本腳本只讀 B3b2 的固定 PNG，不讀任何使用者文件。
"""
import argparse
import hashlib
import io
import json
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter
import numpy as np

HERE = Path(__file__).resolve().parent
B3B2 = HERE.parent/'b3b2-expanded-ocr-evaluation-2026-11-20'
SEED = 20261120

# 每一項是一個劣化條件：id、說明、套用函式與參數。順序固定，影響亂數狀態。
CONDITIONS = [
    ('rotate-0.8', '輕微旋轉 0.8 度（白底）', {'rotate': 0.8}),
    ('rotate-2.0', '明顯旋轉 2.0 度（白底）', {'rotate': 2.0}),
    ('blur-0.8', '高斯模糊 半徑 0.8', {'blur': 0.8}),
    ('blur-1.5', '高斯模糊 半徑 1.5', {'blur': 1.5}),
    ('noise-10', '高斯雜訊 標準差 10', {'noise': 10}),
    ('noise-20', '高斯雜訊 標準差 20', {'noise': 20}),
    ('contrast-0.5', '對比降為 0.5', {'contrast': 0.5}),
    ('contrast-0.3', '對比降為 0.3', {'contrast': 0.3}),
    ('down-up-50', '降為 50% 再放回原尺寸', {'scale': 0.5}),
    ('down-up-33', '降為 33% 再放回原尺寸', {'scale': 0.33}),
    ('jpeg-q30', 'JPEG 品質 30', {'jpeg': 30}),
    ('jpeg-q12', 'JPEG 品質 12', {'jpeg': 12}),
]


def apply(image, params, rng):
    """依序套用單一條件。每一步都固定參數，不做隨機以外的分支。"""
    if 'rotate' in params:
        image = image.rotate(params['rotate'], resample=Image.Resampling.BICUBIC, fillcolor=255)
    if 'blur' in params:
        image = image.filter(ImageFilter.GaussianBlur(params['blur']))
    if 'noise' in params:
        arr = np.asarray(image, dtype=np.float64)
        arr = arr + rng.normal(0.0, params['noise'], arr.shape)
        image = Image.fromarray(np.clip(np.rint(arr), 0, 255).astype(np.uint8), mode='L')
    if 'contrast' in params:
        image = ImageEnhance.Contrast(image).enhance(params['contrast'])
    if 'scale' in params:
        w, h = image.size
        small = image.resize((round(w*params['scale']), round(h*params['scale'])), Image.Resampling.BILINEAR)
        image = small.resize((w, h), Image.Resampling.BILINEAR)
    if 'jpeg' in params:
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=params['jpeg'])
        buffer.seek(0)
        with Image.open(buffer) as decoded:
            image = decoded.convert('L')
            image.load()
    return image


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='repo 外的輸出目錄')
    parser.add_argument('--manifest', type=Path, required=True, help='輸出的參數與雜湊 JSON（新檔）')
    args = parser.parse_args()
    samples = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))['samples']
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for cond_id, label, params in CONDITIONS:
        for index, sample in enumerate(samples):
            # 每張圖、每個條件各自從固定種子開始，互不影響。
            rng = np.random.default_rng(SEED + index)
            with Image.open(B3B2/'samples'/sample['file']) as source:
                image = apply(source.convert('L'), params, rng)
            name = f'{cond_id}__{sample["id"]}.png'
            path = args.output_dir/name
            image.save(path, format='PNG', optimize=False)
            outputs.append(dict(condition=cond_id, sample=sample['id'], file=name,
                                bytes=path.stat().st_size,
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = dict(
        note='模擬掃描，不等於真實掃描機成像。固定參數與種子；輸出圖以 SHA-256 核對。',
        seed=SEED,
        seed_rule='每張圖使用 default_rng(SEED + 樣本索引)，樣本索引依 B3b2 samples.json 順序',
        conditions=[dict(id=i, label=l, params=p) for i, l, p in CONDITIONS],
        source_samples_sha256={s['id']: s['sha256'] for s in samples},
        outputs=outputs,
    )
    with args.manifest.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

"""B3b4 補充的旋轉劣化：以 expand=True 旋轉，不裁切內容。

背景：B3b3 的 degrade_scan.py 旋轉時未使用 expand=True，旋轉後四角與邊緣內容被裁掉，
查驗指出兩個旋轉條件的錯誤數幾乎相同，較可能是裁切造成，不能當作模型優劣依據。
本腳本只新增兩個 expand=True 的旋轉條件（0.8 度、2.0 度），與 B3b3 的條件並列報告，
不改寫 B3b3 已存的腳本、manifest 與結果檔。

沿用 B3b3 的固定種子規則；旋轉本身沒有亂數，種子規則只為了與 B3b3 一致。
這仍是模擬，不等於真實掃描機成像。只讀 B3b2 的固定 PNG，輸出寫到 repo 外的目錄。
"""
import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image
import numpy as np

HERE = Path(__file__).resolve().parent
B3B2 = HERE.parent/'b3b2-expanded-ocr-evaluation-2026-11-20'
SEED = 20261120  # 與 B3b3 相同，方便對照

# 只有兩個新條件。id 加上 -expand 後綴，避免與 B3b3 的 rotate-0.8 混淆。
CONDITIONS = [
    ('rotate-0.8-expand', '輕微旋轉 0.8 度（白底，expand=True 不裁切）', {'rotate': 0.8}),
    ('rotate-2.0-expand', '明顯旋轉 2.0 度（白底，expand=True 不裁切）', {'rotate': 2.0}),
]


def apply(image, params):
    # expand=True 讓畫布隨旋轉後的外框擴大，原內容完整保留；白色補底。
    return image.rotate(params['rotate'], resample=Image.Resampling.BICUBIC, expand=True, fillcolor=255)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='repo 外的輸出目錄')
    parser.add_argument('--manifest', type=Path, required=True, help='輸出的參數與雜湊 JSON（新檔）')
    args = parser.parse_args()
    samples = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))['samples']
    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = []
    for cond_id, label, params in CONDITIONS:
        for sample in samples:
            with Image.open(B3B2/'samples'/sample['file']) as source:
                image = apply(source.convert('L'), params)
            name = f'{cond_id}__{sample["id"]}.png'
            path = args.output_dir/name
            image.save(path, format='PNG', optimize=False)
            outputs.append(dict(condition=cond_id, sample=sample['id'], file=name, size=list(image.size),
                                bytes=path.stat().st_size,
                                sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = dict(
        note='模擬掃描，不等於真實掃描機成像。expand=True 旋轉，不裁切；輸出圖以 SHA-256 核對。',
        seed=SEED,
        conditions=[dict(id=i, label=l, params=p, expand=True) for i, l, p in CONDITIONS],
        source_samples_sha256={s['id']: s['sha256'] for s in samples},
        outputs=outputs,
    )
    with args.manifest.open('x', encoding='utf-8') as stream:
        json.dump(manifest, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

"""粗略的單執行緒推論時間比較（僅供參考，不是效能基準）。

對 B3b2 的 9 張原始合成圖逐張執行完整 RapidOCR 流程（偵測、方向分類、識別），
只替換識別權重；每個模型跑 3 輪，取每張圖的中位數後加總。
候選權重不在 repo 內，由參數指定目錄，檔案 SHA-256 需與 B3b evaluation-inputs.json 相符。
"""
import argparse
import json
import statistics
import time
from pathlib import Path

from PIL import Image
import numpy as np
from rapidocr_onnxruntime import RapidOCR

HERE = Path(__file__).resolve().parent
B3B2 = HERE.parent/'b3b2-expanded-ocr-evaluation-2026-11-20'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--v4', type=Path, required=True)
    parser.add_argument('--v5', type=Path, required=True)
    parser.add_argument('--v6', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    samples = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))['samples']
    images = []
    for s in samples:
        with Image.open(B3B2/'samples'/s['file']) as im:
            images.append(np.asarray(im.convert('RGB'))[:, :, ::-1].copy())
    result = {}
    for name, path in (('v4-current', args.v4), ('v5-rapid-mobile', args.v5), ('v6-rapid-small', args.v6)):
        engine = RapidOCR(rec_model_path=str(path), intra_op_num_threads=1, inter_op_num_threads=1)
        per_image = []
        for img in images:
            times = []
            for _ in range(3):
                t0 = time.perf_counter()
                engine(img)
                times.append(time.perf_counter() - t0)
            per_image.append(statistics.median(times))
        result[name] = dict(total_median_seconds_9_images=round(sum(per_image), 3),
                            mean_per_image_seconds=round(sum(per_image)/len(per_image), 3))
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(dict(note='同一環境、單執行緒、CPUExecutionProvider，僅供參考。', results=result),
                  stream, ensure_ascii=False, indent=2)
        stream.write('\n')


if __name__ == '__main__':
    main()

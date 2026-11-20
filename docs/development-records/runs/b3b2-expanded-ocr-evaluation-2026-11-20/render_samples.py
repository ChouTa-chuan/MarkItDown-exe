"""離線重繪 B3b2 的自製測試圖，保留字型和版面作為可追溯輸入。"""
import argparse
from functools import lru_cache
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
WIDTH, HEIGHT = 1180, 560
INK = 20


def render(sample, font, output):
    """先畫固定底圖，之後依參考文字原來的閱讀順序繪製。"""
    with Image.new('L', (WIDTH, HEIGHT), 255) as image:
        draw = ImageDraw.Draw(image)
        lines = sample['reference'].splitlines()

        def write(text, x, y, right=1114, *, size=28, style='body', fill=INK):
            face = font(sample['language'], style, size)
            _, _, ink_right, ink_bottom = draw.textbbox((x, y), text, font=face, anchor='lt')
            if ink_right > right or ink_bottom > HEIGHT - 20:
                raise ValueError(f'文字超出版面：{sample["id"]} {text}')
            draw.text((x, y), text, font=face, fill=fill, anchor='lt')

        match sample['layout']:
            case 'body':
                write(lines[0], 66, 51, size=42, style='bold')
                for i, line in enumerate(lines[1:-1]):
                    write(line, 68, 132 + i * 43)
                draw.line((66, 476, 1114, 476), fill=190, width=1)
                write(lines[-1], 68, 496, size=18, style='sans', fill=56)
            case 'table':
                write(lines[0], 66, 42, size=36, style='bold')
                columns = (56, 417, 655, 889, 1124)
                rows = lines[1:-1]
                bottom = 126 + 42 * len(rows)
                draw.rectangle((columns[0], 126, columns[-1], 168), fill=232)
                for x in columns:
                    draw.line((x, 126, x, bottom), fill=172, width=1)
                for i in range(len(rows) + 1):
                    y = 126 + i * 42
                    draw.line((columns[0], y, columns[-1], y), fill=172, width=1)
                for i, line in enumerate(rows):
                    cells = line.split('\t')
                    if len(cells) != 4:
                        raise ValueError(f'表格每列應有四欄：{sample["id"]}')
                    for cell, x, limit in zip(cells, columns[:-1], columns[1:], strict=True):
                        write(cell, x + 11, 137 + i * 42, limit - 8, size=22,
                              style='bold' if i == 0 else 'sans')
                write(lines[-1], 68, 502, size=17, style='sans', fill=64)
            case 'heading':
                draw.rectangle((48, 29, 1135, 164), fill=239)
                write(lines[0], 69, 50, size=46, style='bold')
                write(lines[1], 71, 118, size=25, style='sans')
                for line, y, size, style in zip(lines[2:], (199, 256, 335, 402, 454),
                                                (34, 28, 27, 20, 17),
                                                ('bold', 'body', 'sans', 'sans', 'sans'), strict=True):
                    write(line, 71, y, size=size, style=style, fill=48 if size <= 20 else INK)
                draw.line((70, 386, 1114, 386), fill=194, width=1)
            case _:
                raise ValueError(f'未知版面：{sample["layout"]}')
        with output.open('xb') as png:
            image.save(png, format='PNG', optimize=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--font-dir', type=Path, default=Path('/usr/share/fonts'))
    args = parser.parse_args()
    plan = json.loads((HERE/'samples.json').read_text(encoding='utf-8'))

    @lru_cache
    def font(language, style, size):
        key = plan['font_styles'][language][style]
        record = plan['fonts'][key]
        return ImageFont.truetype(args.font_dir/record['path'], size,
                                  index=plan['font_indices'][language])

    for record in plan['fonts'].values():
        path = args.font_dir/record['path']
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            raise ValueError(f'字型與固定來源不符：{path.name}')

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for sample in plan['samples']:
        path = args.output_dir/sample['file']
        render(sample, font, path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if sample.get('sha256', digest) != digest:
            raise ValueError(f'重繪像素檔與固定樣本 SHA-256 不符：{path.name}')
        print(digest, path.name)


if __name__ == '__main__':
    main()

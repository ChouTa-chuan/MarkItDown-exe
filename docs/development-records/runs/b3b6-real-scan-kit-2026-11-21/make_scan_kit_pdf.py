"""B3b6：把 B3b2 的 9 張固定合成圖排成 A4 列印用 PDF，供使用者印出後實體掃描。

設計重點：
- 一頁一段，頁序固定為 B3b2 samples.json 的順序（繁中內文、表格、標題；簡中；英文）。
  第 N 頁就是檔名 0N 的樣本，README 的對照表以同一順序為準。
- 每張圖以固定實際寬度 170 mm 放在 A4 頁面中央（300 dpi 下約 2008 px），等比縮放。
  列印時要選「實際大小」，不可縮放，否則小字的實際尺寸會與評估前提不符。
- 頁面上不印任何額外文字（頁碼、ID、頁尾），避免 OCR 讀進無關文字影響評分。
- 只用 Pillow 的 save(save_all=True)，不新增相依套件。建立時間與標題固定，
  讓同一輸入在同一 Pillow 版本下產生位元組相同的 PDF，輸出 sha256 寫入 README 與 manifest。
- 來源圖先核對 samples.json 的 SHA-256，不符就停止，避免用錯檔案生成測試包。
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from PIL import Image

HERE = Path(__file__).resolve().parent
B3B2 = HERE.parent/'b3b2-expanded-ocr-evaluation-2026-11-20'

DPI = 300
PAGE_SIZE = (2480, 3508)   # A4 在 300 dpi 下的像素尺寸（210 × 297 mm）
IMAGE_WIDTH_MM = 170       # 圖片在紙上的實際寬度，列印時須以「實際大小」輸出
# PDF 的建立與修改時間固定，確保重跑時位元組一致。
FIXED_TIME = time.gmtime(1795219200)  # 2026-11-21 00:00 UTC


def load_verified_samples():
    """讀 B3b2 的樣本清單，逐張核對 SHA-256 與大小；不符就丟出錯誤。"""
    plan = json.loads((B3B2/'samples.json').read_text(encoding='utf-8'))
    pages = []
    for sample in plan['samples']:
        path = B3B2/'samples'/sample['file']
        data = path.read_bytes()
        if len(data) != sample['bytes'] or hashlib.sha256(data).hexdigest() != sample['sha256']:
            raise ValueError(f'來源圖與 samples.json 不符：{path.name}')
        pages.append(dict(id=sample['id'], path=path))
    if len(pages) != 9:
        raise ValueError(f'樣本數應為 9，實際為 {len(pages)}')
    return pages


def layout_for(source_size):
    """回傳圖片在頁面上的寬高與左上角座標（像素）。寬度依 170 mm 換算後取整數。"""
    width = round(IMAGE_WIDTH_MM*DPI/25.4)
    height = round(width*source_size[1]/source_size[0])
    x = (PAGE_SIZE[0]-width)//2
    y = (PAGE_SIZE[1]-height)//2
    return width, height, x, y


def build_page(source_path):
    """把一張來源圖放到白底 A4 頁面中央，回傳灰階頁面影像。"""
    with Image.open(source_path) as source:
        gray = source.convert('L')
        width, height, x, y = layout_for(gray.size)
        scaled = gray.resize((width, height), Image.Resampling.LANCZOS)
    page = Image.new('L', PAGE_SIZE, 255)
    page.paste(scaled, (x, y))
    return page


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='輸出的 PDF 路徑')
    args = parser.parse_args()
    pages = [build_page(item['path']) for item in load_verified_samples()]
    first, rest = pages[0], pages[1:]
    # resolution 讓 Pillow 寫出的頁面尺寸為 A4；title 與時間固定，確保可重現。
    first.save(
        args.output, format='PDF', save_all=True, append_images=rest,
        resolution=DPI, title='MarkItDown real scan test kit', creator='make_scan_kit_pdf.py',
        creationDate=FIXED_TIME, modDate=FIXED_TIME,
    )
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    print(json.dumps(dict(output=str(args.output), pages=len(pages), bytes=args.output.stat().st_size,
                          sha256=digest), ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

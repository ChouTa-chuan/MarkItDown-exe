"""Synthetic quality comparison; never represents real-document accuracy."""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from desktop_app.onnx_ocr import OnnxOCR
from desktop_app.pdf_pipeline import _run_ocr


def distance(left,right):
    row=list(range(len(right)+1))
    for i,a in enumerate(left,1):
        next_row=[i]
        for j,b in enumerate(right,1):
            next_row.append(min(row[j]+1,next_row[-1]+1,row[j-1]+(a!=b)))
        row=next_row
    return row[-1]

parser=argparse.ArgumentParser()
parser.add_argument('--font',type=Path,default=Path('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'))
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
expected='繁體中文文件測試\n會議紀錄與資料轉換'
with Image.new('RGB',(1600,600),'white') as image:
    ImageDraw.Draw(image).multiline_text((80,100),expected,font=ImageFont.truetype(str(args.font),72),fill='black',spacing=30)
    engine=OnnxOCR('cpu',1)
    try: onnx_text,onnx_warning=engine.recognize(image)
    finally: engine.close()
    tesseract_text,tesseract_warning=_run_ocr(image,lambda:None,lambda text:None,200)
reference=''.join(expected.split())
results={}
for name,text,warning in [('onnx_cpu',onnx_text,onnx_warning),('tesseract_cpu',tesseract_text,tesseract_warning)]:
    compact=''.join(text.split())
    errors=distance(reference,compact)
    results[name]={'text':text,'character_edits':errors,'reference_characters':len(reference),'character_error_rate':errors/len(reference),'warning':warning}
args.output.write_text(json.dumps({'sample':'synthetic clean two-line Traditional Chinese, NotoSansCJK-Bold 72px','reference':expected,'scope':'one sample only; not a general accuracy claim','results':results},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({name:item['character_error_rate'] for name,item in results.items()}))

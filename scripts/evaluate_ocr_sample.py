"""以固定合成樣本比較 OCR 差異；結果不代表真實文件的一般準確率。"""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from desktop_app.onnx_ocr import OnnxOCR
from desktop_app.pdf_pipeline import _run_ocr
from desktop_app.quality import compare_ocr


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
fixtures=[('meeting','繁體中文文件測試\n會議紀錄與資料轉換'),
          ('amount_date','發票總額10250元\n日期20261105'),
          ('negation','本案不可批准\n請勿刪除原始資料'),
          ('english','DOCUMENT SCAN TEST\nInvoice total 12345')]
samples=[]
engine=OnnxOCR('cpu',1)
try:
    for name,expected in fixtures:
        with Image.new('RGB',(1600,600),'white') as image:
            ImageDraw.Draw(image).multiline_text((80,100),expected,font=ImageFont.truetype(str(args.font),72),fill='black',spacing=30)
            onnx_text,onnx_warning=engine.recognize(image)
            primary,primary_warning=_run_ocr(image,lambda:None,lambda text:None,200)
        reference=''.join(expected.split());results={}
        for backend,text,warning in [('onnx_cpu',onnx_text,onnx_warning),('tesseract_cpu',primary,primary_warning)]:
            errors=distance(reference,''.join(text.split()))
            results[backend]={'text':text,'character_edits':errors,'reference_characters':len(reference),'character_error_rate':errors/len(reference),'warning':warning}
        comparison=compare_ocr(primary,onnx_text)
        samples.append({'name':name,'reference':expected,'results':results,'crosscheck':{'agrees':comparison.agrees,'warning':comparison.warning,'primary_text_unchanged':comparison.primary==primary}})
finally:engine.close()
report={'sample':'synthetic clean two-line text, NotoSansCJK-Bold 72px','reference':samples[0]['reference'],'results':samples[0]['results'],'scope':'four synthetic samples only; not a general accuracy claim','samples':samples}
args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({sample['name']:{name:item['character_error_rate'] for name,item in sample['results'].items()} for sample in samples}))

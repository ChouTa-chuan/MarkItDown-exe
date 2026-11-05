"""Exercise the actual bundled binary, not only its launch or open process."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import os

parser = argparse.ArgumentParser()
parser.add_argument("executable", type=Path)
parser.add_argument("--crosscheck", action="store_true", help="Also validate dual-engine OCR; requires local Tesseract")
parser.add_argument("--acceptance-report", type=Path, help="Keep the public-PDF acceptance JSON")
args = parser.parse_args()
executable = args.executable.resolve()
subprocess.run([str(executable), "--verify-model-manifest"], check=True, timeout=30)
subprocess.run([str(executable), "--verify-help-assets"], check=True, timeout=30)
subprocess.run([str(executable), "--verify-onnx-models"], check=True, timeout=60)
with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    source = root / "中文來源.txt"
    output = root / "中文輸出.md"
    source.write_text("# 繁體中文\n\n測試內容\n", encoding="utf-8")
    subprocess.run([str(executable), "--cli", str(source), str(output), "--reserve-mib", "0",
                    "--ram-budget-mib", "2048"], check=True, timeout=60)
    assert output.read_bytes() == source.read_bytes()
    from reportlab.pdfgen import canvas
    pdf = root / "input.pdf"
    markdown = root / "pdf.md"
    document = canvas.Canvas(str(pdf))
    document.drawString(72, 700, "Frozen PDF conversion verification 12345")
    document.save()
    subprocess.run([str(executable), "--cli", str(pdf), str(markdown), "--reserve-mib", "0",
                    "--ram-budget-mib", "2048"], check=True, timeout=90)
    assert "Frozen PDF conversion verification 12345" in markdown.read_text(encoding="utf-8")
    merged=root/'merged.pdf';merged_output=root/'merged.md'
    document=canvas.Canvas(str(merged))
    for x in (50,350):document.line(x,660,x,780)
    document.line(200,660,200,740)
    for y in (660,740,780):document.line(50,y,350,y)
    document.line(200,700,350,700)
    document.drawString(60,755,'MergedHeader')
    document.drawString(60,715,'LeftSpan')
    document.drawString(210,715,'RightOne')
    document.drawString(210,675,'RightTwo')
    document.save()
    subprocess.run([str(executable),'--cli',str(merged),str(merged_output),'--reserve-mib','0',
                    '--ram-budget-mib','2048'],check=True,timeout=90)
    table_text=merged_output.read_text(encoding='utf-8')
    assert 'colspan="2"' in table_text and 'rowspan="2"' in table_text
    assert table_text.count('LeftSpan')==1 and table_text.count('RightTwo')==1
    continued=root/'continued.pdf';continued_output=root/'continued.md'
    document=canvas.Canvas(str(continued),pagesize=(600,800))
    for bottom,label in [(20,'CONTINUED_ONE'),(660,'CONTINUED_TWO')]:
        for x in (50,300,550):document.line(x,bottom,x,bottom+100)
        for y in (bottom,bottom+50,bottom+100):document.line(50,y,550,y)
        document.drawString(60,bottom+70,'Item');document.drawString(310,bottom+70,'Amount')
        document.drawString(60,bottom+20,label);document.drawString(310,bottom+20,'12345')
        document.showPage()
    document.save()
    subprocess.run([str(executable),'--cli',str(continued),str(continued_output),'--reserve-mib','0',
                    '--ram-budget-mib','2048'],check=True,timeout=90)
    continued_text=continued_output.read_text(encoding='utf-8')
    assert 'possible-table-continuation: p1-t1 -> p2-t1' in continued_text
    assert continued_text.count('| Item | Amount |')==2
    assert continued_text.count('CONTINUED_ONE')==1 and continued_text.count('CONTINUED_TWO')==1
    borderless=root/'borderless.pdf';borderless_output=root/'borderless.md'
    document=canvas.Canvas(str(borderless),pagesize=(600,800))
    for index,row in enumerate([('Item','Qty','Amount'),('Alpha','2','123.45'),('Beta','5','9000')]):
        for x,value in zip((50,300,450),row):document.drawString(x,700-index*30,value)
    document.save()
    subprocess.run([str(executable),'--cli',str(borderless),str(borderless_output),'--reserve-mib','0',
                    '--ram-budget-mib','2048'],check=True,timeout=90)
    borderless_text=borderless_output.read_text(encoding='utf-8')
    assert 'inferred-borderless-table: p1-b1' in borderless_text
    assert '| Alpha | 2 | 123.45 |' in borderless_text and borderless_text.count('Alpha')==1
    continued_borderless=root/'continued-borderless.pdf';continued_borderless_output=root/'continued-borderless.md'
    document=canvas.Canvas(str(continued_borderless),pagesize=(600,800))
    for page,base in [(1,100),(2,760)]:
        for index,row in enumerate([('Item','Qty','Amount'),(f'UNRULED_PAGE_{page}','2','123.45'),('','5','9000')]):
            for x,value in zip((50,300,450),row):
                if value:document.drawString(x,base-index*30,value)
        document.showPage()
    document.save()
    subprocess.run([str(executable),'--cli',str(continued_borderless),str(continued_borderless_output),
                    '--reserve-mib','0','--ram-budget-mib','2048'],check=True,timeout=90)
    continued_borderless_text=continued_borderless_output.read_text(encoding='utf-8')
    assert 'possible-table-continuation: p1-b1 -> p2-b1' in continued_borderless_text
    assert continued_borderless_text.count('|  | 5 | 9000 |')==2
    for label in ('UNRULED_PAGE_1','UNRULED_PAGE_2'):assert continued_borderless_text.count(label)==1
    columns=root/'columns.pdf';columns_output=root/'columns.md'
    document=canvas.Canvas(str(columns),pagesize=(600,800))
    document.drawCentredString(300,770,'FULL WIDTH TITLE')
    for index in range(6):
        document.drawString(40,700-index*30,f'Left column line {index}')
        document.drawString(360,700-index*30,f'Right column line {index}')
    document.drawCentredString(300,400,'FULL WIDTH FOOTER');document.save()
    subprocess.run([str(executable),'--cli',str(columns),str(columns_output),
                    '--reserve-mib','0','--ram-budget-mib','2048'],check=True,timeout=90)
    columns_text=columns_output.read_text(encoding='utf-8')
    positions=[columns_text.index(label) for label in ('FULL WIDTH TITLE','Left column line 0',
               'Left column line 5','Right column line 0','Right column line 5','FULL WIDTH FOOTER')]
    assert positions==sorted(positions)
    # Reuse the independent fixture oracle for all four upstream public PDFs.
    # This invokes the actual binary, including exact sparse cells and full
    # alphanumeric conservation; it is more than a process-launch smoke check.
    import sys
    subprocess.run([sys.executable,str(Path(__file__).with_name('check_layout_acceptance.py')),
                    '--executable',str(executable),'--report',str(args.acceptance_report or root/'public-pdf-acceptance.json')],
                   check=True,timeout=180)
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new('RGB',(1600,600),'white')
    font_path=Path(os.environ.get('TEST_LATIN_FONT','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
    font=ImageFont.truetype(str(font_path),72) if font_path.exists() else ImageFont.load_default(size=64)
    ImageDraw.Draw(image).text((80,100),'ONNX SCAN TEST 12345',font=font,fill='black')
    image.save(root/'scan.png');image.close()
    scanned=root/'scan.pdf';scan_output=root/'scan.md'
    document=canvas.Canvas(str(scanned),pagesize=(800,600))
    document.drawImage(str(root/'scan.png'),0,150,800,300);document.save()
    subprocess.run([str(executable),'--cli',str(scanned),str(scan_output),'--ocr-backend','onnx',
                    '--device','cpu','--reserve-mib','0','--ram-budget-mib','2048'],check=True,timeout=120)
    assert 'ONNX SCAN TEST 12345' in scan_output.read_text(encoding='utf-8')
    if args.crosscheck:
        verified=root/'verified.md'
        subprocess.run([str(executable),'--cli',str(scanned),str(verified),'--ocr-backend','onnx_verify',
                        '--device','cpu','--reserve-mib','0','--ram-budget-mib','2048'],check=True,timeout=120)
        text=verified.read_text(encoding='utf-8')
        assert 'ONNX SCAN TEST 12345' in text and '兩引擎' in text
print("Frozen executable text and PDF conversion verified")

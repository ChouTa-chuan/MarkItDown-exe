"""Exercise the actual bundled binary, not only its launch or open process."""
import argparse
from pathlib import Path
import subprocess
import tempfile
import os

parser = argparse.ArgumentParser()
parser.add_argument("executable", type=Path)
parser.add_argument("--crosscheck", action="store_true", help="Also validate dual-engine OCR; requires local Tesseract")
args = parser.parse_args()
executable = args.executable.resolve()
subprocess.run([str(executable), "--verify-model-manifest"], check=True, timeout=30)
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

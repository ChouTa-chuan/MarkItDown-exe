"""Exercise the actual bundled binary, not only its launch or open process."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("executable", type=Path)
args = parser.parse_args()
executable = args.executable.resolve()
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
print("Frozen executable text and PDF conversion verified")

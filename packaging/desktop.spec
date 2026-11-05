# Platform-native PyInstaller build. Windows EXE must be built on Windows.
from pathlib import Path
from importlib.util import find_spec
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
datas, binaries, hiddenimports = collect_all("magika")
hiddenimports += collect_submodules("markitdown")
if find_spec("rapidocr_onnxruntime"):
    ocr_data, ocr_binaries, ocr_imports = collect_all("rapidocr_onnxruntime")
    datas += ocr_data
    binaries += ocr_binaries
    hiddenimports += ocr_imports
for package in ("markitdown", "magika", "mammoth", "pdfplumber", "python-pptx", "openpyxl"):
    datas += copy_metadata(package)
datas += [(str(root / "THIRD_PARTY_NOTICES"), "."),
          (str(root / "src/desktop_app/data/ocr-models.json"), "desktop_app/data"),
          (str(root / "vendor/markitdown/LICENSE"), "licenses/markitdown")]
analysis = Analysis([str(root / "packaging/desktop_entry.py")],
    pathex=[str(root / "src")], binaries=binaries, datas=datas,
    hiddenimports=hiddenimports, excludes=["PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets"],
    noarchive=False)
pyz = PYZ(analysis.pure)
exe = EXE(pyz, analysis.scripts, [], exclude_binaries=True,
          name="MarkItDownDesktop", console=False, upx=False)
bundle = COLLECT(exe, analysis.binaries, analysis.datas,
                 name="MarkItDownDesktop", upx=False)

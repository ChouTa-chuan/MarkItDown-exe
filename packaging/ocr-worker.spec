# C07 專用 CPU worker；依目前平台建置，不把 Linux 產物當成 Windows EXE。
from pathlib import Path
import os
import sys
import tempfile
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, copy_metadata

root=Path(SPECPATH).parent
assets=Path(os.environ.get('MARKITDOWN_WORKER_ASSETS',str(root/'build/ocr-worker-assets')))
if not (assets/'installed-manifest.json').is_file():raise RuntimeError('Run prepare_worker_assets.py first')
datas,binaries,hiddenimports=collect_all('rapidocr_onnxruntime')
binaries+=collect_dynamic_libs('onnxruntime')
for package in ('rapidocr-onnxruntime','onnxruntime','numpy','opencv-python','Pillow','psutil'):
    datas+=copy_metadata(package)
datas += [(str(root/'src/desktop_app/data/worker-health.png'),'desktop_app/data'),
          (str(root/'src/desktop_app/data/worker-health.json'),'desktop_app/data'),
          (str(assets),'worker-assets')]
analysis=Analysis([str(root/'packaging/ocr_worker_entry.py')],pathex=[str(root/'src')],
    binaries=binaries,datas=datas,hiddenimports=hiddenimports,
    excludes=['PySide6','tkinter','matplotlib','pandas','scipy','torch','tensorflow','magika','markitdown'],noarchive=False)
sys.path.insert(0, str(root/'scripts'))
from prepare_worker_assets import native_notices
from bundle_filters import drop_opencv_ffmpeg
# OCR 只處理圖片：排除 OpenCV 內附的 FFmpeg 影片外掛；須在記錄 binary 來源之前做。
analysis.binaries, dropped_ffmpeg = drop_opencv_ffmpeg(analysis.binaries)
# 套件 hook 也可能把它當資料檔收集，兩邊都過濾。
analysis.datas, dropped_ffmpeg_data = drop_opencv_ffmpeg(analysis.datas)
print('Excluded OpenCV FFmpeg plugin:', dropped_ffmpeg + dropped_ffmpeg_data)
native_directory=tempfile.TemporaryDirectory(prefix='markitdown-worker-native-')
native_root=Path(native_directory.name)/'notices'
native_notices(analysis.binaries,native_root)
analysis.datas += [('worker-assets/native/'+path.relative_to(native_root).as_posix(),str(path),'DATA')
                  for path in native_root.rglob('*') if path.is_file()]
pyz=PYZ(analysis.pure)
exe=EXE(pyz,analysis.scripts,[],exclude_binaries=True,name='MarkItDownOCRWorker',console=True,upx=False)
bundle=COLLECT(exe,analysis.binaries,analysis.datas,name='MarkItDownOCRWorker',upx=False)

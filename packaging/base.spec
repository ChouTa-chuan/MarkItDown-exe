# C04 基本開發包；可帶同平台四語 OCR，Windows 仍須原生建置與驗收。
from pathlib import Path
import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, copy_metadata

root = Path(SPECPATH).parent
sys.path.insert(0, str(root/'scripts'))
from prepare_base_assets import refresh_manifest
from prepare_worker_assets import native_notices
from bundle_filters import drop_untracked_openssl
from desktop_app.build_profile import load_profile, verify_assets

assets = Path(os.environ['MARKITDOWN_BASE_ASSETS'])
profile = load_profile(assets)
if profile is None: raise RuntimeError('Run prepare_base_assets.py in the isolated base build environment first')
if profile['platform'] != {'linux':'linux','win32':'windows'}.get(sys.platform):
    raise RuntimeError('Profile assets must be prepared for the native build platform')
verify_assets(profile, assets)
datas, binaries, hiddenimports = collect_all('magika')
hiddenimports += collect_submodules('markitdown')
for name in [*profile['runtime_packages'], 'markitdown-desktop', 'markitdown']:
    datas += copy_metadata(name)
if profile['native_ocr_integrated']:
    from desktop_app.bundled_ocr import validate_payload
    native = validate_payload(assets/'native', expected_platform=profile['platform'], assets=profile['assets'])
    engine = assets/'native'/native['entrypoint']
    # 原生入口交由 BINARY dependency analysis；不要再以 DATA 重複收集。
    binaries += [(str(engine), 'desktop_app/data/native/bin')]
    datas += [(str(p), 'desktop_app/data/'+p.parent.relative_to(assets).as_posix())
              for p in assets.rglob('*') if p.is_file() and p != engine]
else:
    datas += [(str(assets), 'desktop_app/data')]
datas += [(str(root/'THIRD_PARTY_NOTICES'), '.')]
analysis = Analysis([str(root/'packaging/desktop_entry.py')], pathex=[str(root/'src')],
    binaries=binaries, datas=datas, hiddenimports=hiddenimports,
    excludes=['rapidocr_onnxruntime','cv2','pyclipper','shapely','yaml','docx','reportlab',
              'PySide6.QtWebEngineCore','PySide6.QtWebEngineWidgets','tkinter','pytest'], noarchive=False)
# 排除 Qt OpenSSL TLS 外掛及它從建置機系統路徑帶進來、來源不可追溯的 OpenSSL；
# 必須在記錄 binary 來源之前做，隨包清單才與實際內容一致。
analysis.binaries, dropped_openssl = drop_untracked_openssl(analysis.binaries)
print('Excluded untracked OpenSSL binaries:', dropped_openssl)
# 保存此輪真正收集的 binary 來源；更新資產雜湊後再交給 COLLECT。
native_root = assets/'licenses/native'
native_notices(analysis.binaries, native_root)
refresh_manifest(assets)
analysis.datas += [('desktop_app/data/'+p.relative_to(assets).as_posix(),str(p),'DATA')
                  for p in native_root.rglob('*') if p.is_file()]
pyz = PYZ(analysis.pure)
name = 'MarkItDownBase' if profile['native_ocr_integrated'] else 'MarkItDownBaseCore'
# frozen 會隔離外部 Python 環境；直接固定 UTF-8 mode，讓四語 CLI／子程序診斷不依賴系統 locale。
exe = EXE(pyz, analysis.scripts, [('X utf8', None, 'OPTION')], exclude_binaries=True, name=name, console=True, upx=False)
bundle = COLLECT(exe, analysis.binaries, analysis.datas, name=name, upx=False)

"""開發者模型下載入口，與桌面使用相同的版本與完整性驗證流程。"""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from desktop_app.models import install

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='下載繁中／英文 OCR 模型與授權，約 6.4 MB')
    parser.add_argument('directory', type=Path)
    install(parser.parse_args().directory, progress=print)

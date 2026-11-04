"""Developer entry to the same verified model manager used by the desktop UI."""
import argparse
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from desktop_app.models import install

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='下載繁中／英文 OCR 模型與授權，約 6.4 MB')
    parser.add_argument('directory', type=Path)
    install(parser.parse_args().directory, progress=print)

"""基本包自有 MIT 原文與套件的對照；只關閉自有原文缺口，不核准第三方再散布。"""
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
OWN_PACKAGE = 'markitdown-desktop'
OWN_LICENSE = 'licenses/markitdown-desktop/LICENSE'


def stage_own_license(root, staged):
    """保留現有安裝路徑與原始位元組，原文缺少時停止建置。"""
    original = root/'LICENSE'
    if not original.is_file() or original.is_symlink():
        raise FileNotFoundError('缺少自有程式授權原文：'+str(original))
    if not original.stat().st_size:
        raise ValueError('Empty own MIT original')
    destination = staged/OWN_LICENSE
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(original, destination)


def verify_own_license(assets, packages, *, root=ROOT):
    """已隨包全文必須指回自有套件，且與固定來源相同；不能拿它替其他套件補原文。"""
    own = [row for row in packages if row['name'] == OWN_PACKAGE]
    if len(own) != 1:
        raise ValueError('Own MIT binding requires exactly one application package')
    notices = own[0].get('notice_files')
    if not isinstance(notices, list) or notices.count(OWN_LICENSE) != 1:
        raise ValueError('Missing or duplicate own MIT notice binding')
    for row in packages:
        if row['name'] == OWN_PACKAGE:
            continue
        references = [*row.get('notice_files', []),
                      *[p['path'] for p in row.get('supplemental_sources', [])]]
        # Windows 路徑不分大小寫；別名仍不得讓自有 MIT 變成第三方套件的原文。
        if any(isinstance(p, str) and p.casefold() == OWN_LICENSE.casefold() for p in references):
            raise ValueError('Own MIT notice bound to another package: '+row['name'])
    original, bundled = root/'LICENSE', assets/OWN_LICENSE
    for path in (original, bundled):
        if not path.is_file() or path.is_symlink() or not path.stat().st_size:
            raise ValueError('Missing, linked or empty own MIT original: '+str(path))
    if hashlib.sha256(original.read_bytes()).digest() != hashlib.sha256(bundled.read_bytes()).digest():
        raise ValueError('Own MIT original differs from selected project source')
    return True

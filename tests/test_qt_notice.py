"""Qt／LGPL 與自有 MIT 授權的隨包說明：檔案、雜湊、路徑與產生內容。

prepare() 需要完整隔離的 Windows／Linux 建置環境，無法在一般測試執行；
這裡改驗證它所呼叫的最小單元（stage_*、base_guide、refresh_manifest）。
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from prepare_base_assets import (OWN_LICENSE, QT_NOTICE, QT_NOTICE_LINE, base_guide, refresh_manifest,
                                 stage_own_license, stage_qt_notice)

DATA = ROOT/'src/desktop_app/data'
# 安裝後前綴；依據 docs/development-records/runs/ci-full-reports-2026-11-12/
# windows-base-validation-reports.zip 內 installer/base-install-catalog.json 的實際安裝清單。
INSTALLED_DATA = '_internal\\desktop_app\\data\\'


def installed(path):
    return INSTALLED_DATA+path.replace('/', '\\')


class QtNoticeTests(unittest.TestCase):
    def setUp(self):
        self.text = (DATA/'licenses'/QT_NOTICE).read_text(encoding='utf-8')
        inventory = json.loads((DATA/'licenses/windows/inventory.json').read_text(encoding='utf-8'))
        self.packages = {p['name']:p for p in inventory['packages']}

    def test_notice_and_license_are_staged_and_hashed(self):
        with tempfile.TemporaryDirectory() as temporary:
            staged = Path(temporary)
            (staged/'licenses').mkdir()
            (staged/'build-profile.json').write_text('{}', encoding='utf-8')
            stage_qt_notice(DATA, staged)
            stage_own_license(ROOT, staged)
            refresh_manifest(staged)
            assets = json.loads((staged/'build-profile.json').read_text())['assets']
            for name in ('licenses/'+QT_NOTICE, OWN_LICENSE):
                self.assertEqual(assets[name], hashlib.sha256((staged/name).read_bytes()).hexdigest())
            self.assertEqual((staged/OWN_LICENSE).read_bytes(), (ROOT/'LICENSE').read_bytes())

    def test_missing_own_license_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(FileNotFoundError):
                stage_own_license(Path(temporary), Path(temporary)/'out')

    def test_guide_contains_notice_lines_with_and_without_native(self):
        for native in (False, True):
            lines = base_guide('0.0.0', [dict(name='x', version='1')], native)
            self.assertIn(QT_NOTICE_LINE, lines)
            self.assertTrue(any(OWN_LICENSE in line for line in lines))
        self.assertIn('licenses/'+QT_NOTICE, QT_NOTICE_LINE)
        self.assertIn('licenses/'+QT_NOTICE, (DATA/'third-party.md').read_text(encoding='utf-8'))

    def test_paths_in_notice_match_prepared_layout(self):
        # Qt DLL 位置：同一份安裝清單中的 _internal/PySide6/Qt6Core.dll。
        self.assertIn('_internal\\PySide6\\', self.text)
        self.assertIn('LGPL-3.0', self.text)
        self.assertIn('待補', self.text)
        for name in ('pyside6-essentials', 'shiboken6'):
            package = self.packages[name]
            self.assertEqual(package['version'], '6.12.0')
            for ref in package['supplemental_sources']:
                self.assertTrue((DATA/'licenses/windows'/ref['path']).is_file())
                self.assertIn(installed('licenses/'+ref['path']), self.text)
                self.assertIn(ref['url'], self.text)
            # prepare() 把 wheel 內授權放在 installed/<name>/original/<wheel 內路徑>。
            for notice in package['wheel_notice_files']:
                inside = notice.split('/wheel/', 1)[1]
                self.assertIn(installed('licenses/installed/'+name+'/original/'+inside), self.text)
            self.assertIn(installed('licenses/installed/'+name+'/METADATA'), self.text)
        self.assertIn(installed(OWN_LICENSE), self.text)

    def test_third_party_markdown_matches_render(self):
        # 原始碼樹的 third-party.md 與 licenses/index.html 由 license_inventory.py 的 render() 產生，兩者必須逐字相同；基本包內的 third-party.md 另由 base_guide() 產生。
        sys.path.insert(0, str(ROOT/'scripts'))
        import license_inventory
        inventory = json.loads((DATA/'licenses/windows/inventory.json').read_text(encoding='utf-8'))
        with tempfile.TemporaryDirectory() as temporary:
            markdown = Path(temporary)/'third-party.md'
            license_inventory.render(inventory, markdown, Path(temporary)/'index.html')
            self.assertEqual(markdown.read_bytes(), (DATA/'third-party.md').read_bytes())
            self.assertEqual((Path(temporary)/'index.html').read_bytes(), (DATA/'licenses/index.html').read_bytes())


if __name__ == '__main__':
    unittest.main()

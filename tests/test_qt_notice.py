"""Qt／LGPL 與自有 MIT 授權的隨包說明：檔案、雜湊、路徑與產生內容。

prepare() 需要完整隔離的 Windows／Linux 建置環境，無法在一般測試執行；
這裡改驗證它所呼叫的最小單元（stage_*、base_guide、refresh_manifest）。
"""
import hashlib
import contextlib
import io
import os
import json
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
from prepare_base_assets import (OWN_LICENSE, QT_NOTICE, QT_NOTICE_LINE, base_guide, refresh_manifest,
                                 stage_own_license, stage_qt_notice)
import qt_sources

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
            for name in ('licenses/'+QT_NOTICE, 'licenses/'+qt_sources.STAGED, OWN_LICENSE):
                self.assertEqual(assets[name], hashlib.sha256((staged/name).read_bytes()).hexdigest())
            self.assertEqual((staged/OWN_LICENSE).read_bytes(), (ROOT/'LICENSE').read_bytes())
            source_map = json.loads((staged/'licenses'/qt_sources.STAGED).read_text())
            self.assertTrue(source_map['release_source_map_verified'])
            self.assertFalse(source_map['redistribution_approved'])
            self.assertFalse(source_map['binary_reproduction_verified'])
            self.assertLess(len(json.dumps(qt_sources.public_summary(source_map)).encode()), 3900)

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
        self.assertNotIn('**待補**', self.text)
        self.assertIn(installed('licenses/'+qt_sources.STAGED), self.text)
        catalog = qt_sources.load_catalog()
        for key in ('qt5_commit', 'qtbase_commit', 'pyside_commit'):
            self.assertIn(catalog[key], self.text)
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

    def test_windows_controller_preserves_and_publishes_the_child_qt_report(self):
        from run_windows_base_ci import record_qt_sources
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            assets = root/'assets'
            reports = root/'reports'
            (assets/'licenses').mkdir(parents=True)
            reports.mkdir()
            # 合成 Windows 觀測只測傳遞契約，不作原生 Windows 證據。
            observed = dict(platform='Windows', qt_version='6.12.0', pyside_version='6.12.0',
                            shiboken_version='6.12.0', qt_build='fixture', core_extension_sha256='0'*64)
            report = qt_sources.stage(ROOT, assets/'licenses'/qt_sources.STAGED, observed)
            stdout = io.StringIO()
            with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), contextlib.redirect_stdout(stdout):
                record_qt_sources(assets, reports)
            annotation = stdout.getvalue().strip().split('::', 2)
            self.assertEqual(annotation[1], 'notice title=Qt release sources')
            self.assertEqual(json.loads(annotation[2]), qt_sources.public_summary(report))
            self.assertEqual((assets/'licenses'/qt_sources.STAGED).read_bytes(),
                             (reports/'qt-release-sources.json').read_bytes())

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


class QtSourceTests(unittest.TestCase):
    """變異來源與實際 runtime 版本，防止只有相同標籤就被認為已對應。"""
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.directory = self.root/'packaging/qt'/qt_sources.VERSION
        shutil.copytree(ROOT/'packaging/qt'/qt_sources.VERSION, self.directory)
        dest = self.root/'src/desktop_app/data/licenses/windows'
        dest.mkdir(parents=True)
        shutil.copyfile(DATA/'licenses/windows/inventory.json', dest/'inventory.json')

    def test_altered_original_and_relabelled_qt_version_are_rejected(self):
        catalog = qt_sources.load_catalog(self.root)
        path = self.directory/'sources/qtbase/.cmake.conf'
        path.write_bytes(path.read_bytes().replace(b'"6.12.0"', b'"6.12.1"'))
        with self.assertRaisesRegex(ValueError, 'fingerprint mismatch'):
            qt_sources.load_catalog(self.root)
        # 即使把本地 hash 重算，也不能把不同版來源當成 6.12.0。
        data = path.read_bytes()
        row = next(r for r in catalog['evidence_files'] if r['path'] == 'sources/qtbase/.cmake.conf')
        row.update(sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
                   git_blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest())
        (self.directory/'catalog.json').write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'source version declaration'):
            qt_sources.load_catalog(self.root)

    def test_module_commit_must_match_the_official_supermodule_gitlink(self):
        catalog = qt_sources.load_catalog(self.root)
        catalog['modules']['qtsvg'] = '0'*40
        (self.directory/'catalog.json').write_text(json.dumps(catalog))
        with self.assertRaisesRegex(ValueError, 'gitlink mismatch'):
            qt_sources.load_catalog(self.root)

    def test_different_loaded_qt_cannot_use_the_release_source_map(self):
        output = self.root/'result.json'
        # 合成觀測僅驗拒絕契約，不當成 Windows 執行結果。
        observed = dict(qt_version='6.12.1', pyside_version='6.12.0', shiboken_version='6.12.0')
        with self.assertRaisesRegex(ValueError, 'runtime differs'):
            qt_sources.stage(self.root, output, observed)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()

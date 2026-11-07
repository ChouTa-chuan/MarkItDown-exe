"""C04 相依拆分：extras／平台、缺閉包及證據變動的反例；不模擬 Windows 執行。"""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import packaging_profiles as profiles


def package(version='1.0', dependencies=(), python=None):
    return dict(version=version, requires_dist=list(dependencies), requires_python=python)


class ClosureTests(unittest.TestCase):
    def environment(self, target='linux'):
        return profiles.marker_environment(target, '3.12.14')

    def test_transitive_extra_arrives_after_first_visit(self):
        metadata = {'a': package(dependencies=['shared']), 'b': package(dependencies=['shared[ocr]']),
                    'shared': package(dependencies=['model; extra == "ocr"']), 'model': package()}
        names, edges = profiles.closure(['a', 'b'], metadata, self.environment())
        self.assertEqual(names, ['a', 'b', 'model', 'shared'])
        self.assertIn(['shared', 'model'], edges)

    def test_platform_markers_are_evaluated_for_target(self):
        metadata = {'tool': package(dependencies=['windows; sys_platform == "win32"', 'linux; sys_platform == "linux"']),
                    'windows': package(), 'linux': package()}
        self.assertEqual(profiles.closure(['tool'], metadata, self.environment())[0], ['linux', 'tool'])
        self.assertEqual(profiles.closure(['tool'], metadata, self.environment('windows'))[0], ['tool', 'windows'])

    def test_version_conflict_does_not_reselect(self):
        with self.assertRaisesRegex(ValueError, '固定版本不符'):
            profiles.closure(['a>=2'], {'a': package()}, self.environment())

    def test_missing_transitive_dependency_is_fatal(self):
        with self.assertRaisesRegex(ValueError, '閉包缺少套件'):
            profiles.closure(['a'], {'a': package(dependencies=['missing'])}, self.environment())

    def test_python_requires_python_and_direct_urls_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Python 版本不符'):
            profiles.closure(['a'], {'a': package(python='>=3.13')}, self.environment())
        with self.assertRaisesRegex(ValueError, '外部直連'):
            profiles.closure(['a @ https://example.invalid/a.whl'], {'a': package()}, self.environment())

    def test_cycles_terminate_without_duplicate_edges(self):
        names, edges = profiles.closure(['a'], {'a': package(dependencies=['b']), 'b': package(dependencies=['a'])}, self.environment())
        self.assertEqual(names, ['a', 'b']); self.assertEqual(len(edges), 3)

    def test_parent_extra_not_reinterpreted_on_child(self):
        metadata = {'a': package(dependencies=['b; extra == "ocr"']),
                    'b': package(dependencies=['unused; extra == "ocr"']), 'unused': package()}
        self.assertEqual(profiles.closure(['a[ocr]'], metadata, self.environment())[0], ['a', 'b'])


class ProfileTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        for name in ['packaging', 'src/desktop_app/data/licenses/windows']:
            shutil.copytree(ROOT/name, self.root/name)
        for name in ['pyproject.toml', 'vendor/markitdown/pyproject.toml']:
            path = self.root/name; path.parent.mkdir(parents=True, exist_ok=True); shutil.copyfile(ROOT/name, path)

    def test_real_profiles_keep_magika_runtime_and_omit_ocr_and_test_tools(self):
        report = profiles.verify_profiles(self.root)
        self.assertFalse(report['release_ready']); self.assertFalse(report['windows_executed'])
        for key, profile in report['profiles'].items():
            self.assertIn('onnxruntime', profile['packages'])
            self.assertNotIn('rapidocr-onnxruntime', profile['packages'])
            self.assertNotIn('reportlab', profile['packages'])
            self.assertIn(['magika', 'onnxruntime'], profile['dependency_edges'])
            self.assertEqual('pyinstaller' in profile['packages'], key.endswith('build'))
            self.assertEqual('pywin32-ctypes' in profile['packages'], key == 'windows-build')

    def test_changed_generated_hash_rejected(self):
        path = self.root/'packaging/profiles/base-linux-runtime.txt'
        path.write_text(path.read_text().replace('--hash=sha256:', '--hash=sha256:0', 1))
        with self.assertRaisesRegex(ValueError, '輸出已過期'):
            profiles.verify_profiles(self.root)

    def test_changed_windows_wheel_metadata_rejected(self):
        path = self.root/'packaging/profiles/metadata-windows.json'
        data = json.loads(path.read_text()); data['packages']['magika']['requires_dist'] = []
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, 'wheel metadata 不符'):
            profiles.verify_profiles(self.root)

    def test_added_onnx_ocr_extra_fails_base_exclusion(self):
        path = self.root/'packaging/profiles/base.json'
        data = json.loads(path.read_text()); data['application_extras'].append('onnx'); path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, '混入選配'):
            profiles.verify_profiles(self.root)

    def test_original_notice_tampering_rejected(self):
        (self.root/'src/desktop_app/data/licenses/windows/magika/METADATA').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'Notice changed'):
            profiles.verify_profiles(self.root)

    def test_parent_lock_change_requires_metadata_refresh(self):
        path = self.root/'packaging/requirements-linux.txt'; path.write_text(path.read_text()+'\n# changed\n')
        with self.assertRaisesRegex(ValueError, '上位鎖定已變動'):
            profiles.verify_profiles(self.root)

    def test_missing_or_unpinned_or_duplicate_hashes_rejected(self):
        path = self.root/'bad.txt'
        for text in ['a==1', 'a>=1 --hash=sha256:'+'0'*64,
                     'a==1 --hash=sha256:'+'0'*64+'\na==1 --hash=sha256:'+'1'*64,
                     'a==1 --hash=sha256:'+'0'*64+' --index-url=https://example.invalid']:
            path.write_text(text)
            with self.assertRaises(ValueError): profiles.read_lock(path)

    def test_release_ready_cannot_be_claimed_by_changing_config(self):
        path = self.root/'packaging/profiles/base.json'; data = json.loads(path.read_text())
        data['release_ready'] = True; path.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError, '不得標記基本包可發行'):
            profiles.verify_profiles(self.root)

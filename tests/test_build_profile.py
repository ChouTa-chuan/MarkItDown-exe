"""基本 frozen profile 的資產／能力與失敗報告；合成清單不冒充打包實測。"""
import hashlib
import json
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

from desktop_app import build_profile as bp
from desktop_app import diagnostics

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from prepare_base_assets import is_notice_entry


class BuildProfileTests(unittest.TestCase):
    def test_notice_directory_does_not_collect_python_or_cache(self):
        self.assertTrue(is_notice_entry('pkg.dist-info/licenses/Apache-2.0.txt'))
        self.assertTrue(is_notice_entry('pkg/COPYING'))
        for path in ['pkg/licenses/__init__.py','pkg/licenses/_spdx.py',
                     'pkg/licenses/__pycache__/module.pyc','pkg/licenses/module.pyo',
                     '../LICENSE','/LICENSE','pkg/module.py']:
            self.assertFalse(is_notice_entry(path),path)

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        files = ['user-guide.md','third-party.md','base-runtime-lock.txt',
                 'licenses/python-runtime/LICENSE.txt','licenses/installed/manifest.json']
        self.profile = dict(schema_version=1,id='base',source_version='0.9.0',runtime_packages={'psutil':'7.2.2'},
            local_packages={'markitdown-desktop':'0.9.0','markitdown':'0.1.9'},
            native_ocr_required=True,native_ocr_integrated=False,release_ready=False,notice_packages=3,assets={})
        for name in files:
            p = self.root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text('合成測試資產')
            self.profile['assets'][name] = hashlib.sha256(p.read_bytes()).hexdigest()
        self.save()
        root_patch = patch('desktop_app.build_profile.data_root',return_value=self.root)
        root_patch.start(); self.addCleanup(root_patch.stop)

    def save(self):
        (self.root/'build-profile.json').write_text(json.dumps(self.profile))

    def test_no_embedded_profile_keeps_legacy_behavior(self):
        (self.root/'build-profile.json').unlink(); self.assertIsNone(bp.load_profile())

    def test_profile_assets_match_and_help_uses_selected_inventory(self):
        self.assertEqual(bp.load_profile(),self.profile)
        self.assertIn('基本版資產',diagnostics.verify_help())

    def test_missing_asset_fails(self):
        (self.root/'user-guide.md').unlink()
        with self.assertRaisesRegex(RuntimeError,'資產缺少'): bp.verify_assets(self.profile)

    def test_changed_license_fails(self):
        (self.root/'licenses/python-runtime/LICENSE.txt').write_text('changed')
        with self.assertRaisesRegex(RuntimeError,'雜湊不符'): bp.verify_assets(self.profile)

    def test_asset_link_is_rejected(self):
        path=self.root/'third-party.md'; path.unlink(); path.symlink_to(self.root/'user-guide.md')
        with self.assertRaises(RuntimeError): bp.verify_assets(self.profile)

    def test_missing_required_asset_reference_is_rejected(self):
        del self.profile['assets']['user-guide.md']; self.save()
        with self.assertRaisesRegex(ValueError,'必要手冊'): bp.load_profile()

    def test_paths_and_hashes_are_validated(self):
        for name,digest in [('../outside','0'*64),('/absolute','0'*64),('a\\b','0'*64),('a','wrong')]:
            self.profile['assets'][name]=digest; self.save()
            with self.assertRaises(ValueError): bp.load_profile()
            del self.profile['assets'][name]

    def test_readiness_and_native_ocr_cannot_be_claimed(self):
        for key in ['release_ready','native_ocr_integrated']:
            self.profile[key]=True; self.save()
            with self.assertRaises(ValueError): bp.load_profile()
            self.profile[key]=False

    def test_notice_count_must_match_selected_packages(self):
        self.profile['notice_packages']=40; self.save()
        with self.assertRaisesRegex(ValueError,'套件數不符'): bp.load_profile()

    def test_runtime_versions_and_forbidden_modules(self):
        versions={**self.profile['runtime_packages'],**self.profile['local_packages']}
        with patch.object(bp.metadata,'version',side_effect=lambda name:versions[name]),patch.object(bp.util,'find_spec',return_value=None):
            self.assertIn('固定 runtime',bp.verify_runtime(self.profile))
        versions['psutil']='0.0'
        with patch.object(bp.metadata,'version',side_effect=lambda name:versions[name]):
            with self.assertRaisesRegex(RuntimeError,'版本不符'): bp.verify_runtime(self.profile)
        versions['psutil']='7.2.2'
        with patch.object(bp.metadata,'version',side_effect=lambda name:versions[name]),patch.object(bp.util,'find_spec',side_effect=lambda name:object() if name=='cv2' else None):
            with self.assertRaisesRegex(RuntimeError,'cv2'): bp.verify_runtime(self.profile)

    def report(self,scope):
        with patch.object(bp,'verify_runtime',return_value='synthetic version check'), \
             patch.object(diagnostics,'_convert',side_effect=lambda source,target,backend='tesseract':
                          (target.write_bytes(source.read_bytes()) or '') if source.suffix=='.txt' else 'INSTALLATION PDF CHECK 12345 route: native'), \
             patch('desktop_app.onnx_ocr.verify_models') as onnx:
            # 文字轉換以真正寫入檔案供 byte comparison；此處不冒充 spawn／PDF 推論。
            result=diagnostics.collect_report(scope=scope)
            onnx.assert_not_called(); return result

    def test_core_diagnostics_pass_without_claiming_full_base(self):
        report=self.report('core'); self.assertTrue(report['complete']); self.assertTrue(report['core_complete'])
        self.assertEqual(len(report['checks']),4); self.assertFalse(report['release_ready'])
        self.assertEqual(report['requested_scope'],'core')

    def test_full_diagnostics_fail_missing_native_without_external_probe(self):
        report=self.report('full'); self.assertFalse(report['complete']); self.assertTrue(report['core_complete'])
        self.assertEqual(report['checks'][-1]['name'],'bundled_tesseract_bilingual')
        self.assertIn('C03',report['checks'][-1]['detail'])

    def test_core_failure_stays_failed(self):
        (self.root/'user-guide.md').unlink(); report=self.report('core')
        self.assertFalse(report['complete']); self.assertFalse(report['core_complete'])

    def test_core_scope_requires_explicit_embedded_profile(self):
        (self.root/'build-profile.json').unlink()
        with self.assertRaises(ValueError): diagnostics.collect_report(scope='core')

    def test_malformed_profile_saves_failure_report(self):
        (self.root/'build-profile.json').write_text('{broken')
        target=self.root/'failure.json'
        self.assertEqual(diagnostics.main(['--report',str(target)]),1)
        report=json.loads(target.read_text()); self.assertFalse(report['complete'])
        self.assertEqual(report['checks'][0]['name'],'build_profile')

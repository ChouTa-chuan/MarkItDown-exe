"""A9 內含元件目錄契約：真實資料必須通過；每一種錯誤輸入都必須被拒絕。

全部反例都在記憶體中的複本上修改，不改 repo 內的目錄、登記表或 A6 輸入。
"""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import embedded_components as embedded
import redistribution_gates as gates

CATALOG_PATH = 'packaging/embedded/base-windows.json'


class EmbeddedCatalogTests(unittest.TestCase):
    def setUp(self):
        self.catalog = gates.read_json(ROOT/CATALOG_PATH)
        self.entries = gates.read_json(gates.REGISTRY)['profiles']['base']['entries']
        self.report = gates.read_json(ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json')

    def check(self, catalog=None, entries=None):
        return embedded.check_profile(catalog if catalog is not None else self.catalog, catalog_path=CATALOG_PATH,
                                      entries=entries if entries is not None else self.entries, report=self.report, root=ROOT)

    def assertRejects(self, message, catalog=None, entries=None):
        with self.assertRaisesRegex(ValueError, message):
            self.check(catalog=catalog, entries=entries)

    def wheel(self, catalog, dist):
        return next(w for w in catalog['wheels'] if w['distribution'] == dist)

    def component(self, catalog, dist, cid):
        return next(c for c in self.wheel(catalog, dist)['components'] if c['id'] == cid)

    # 正例：真實目錄與登記表的綁定
    def test_real_catalog_covers_base_wheel_natives_exactly(self):
        summary = self.check()
        self.assertEqual(summary['wheels'], 10)
        self.assertEqual(summary['native_files'], 81)
        self.assertEqual(summary['components'], 54)
        # unknown 元件所屬條目必須是 open；evidence_complete 的條目只能是版本已知的 wheel
        closed = {e['id'] for e in self.entries if e['id'].startswith('base-wheels-') and e['status'] != 'open'}
        self.assertEqual(closed, {'base-wheels-charset-normalizer', 'base-wheels-psutil'})
        unknown = self.check()['unknown_components']
        self.assertEqual(len(unknown), len(set(unknown)))

    def test_pillow_string_evidence_components_stay_unknown(self):
        """Pillow 的 .pyd 字串顯示的元件沒有版本與原文，條目必須保持 open。"""
        for cid in ('raqm', 'fribidi', 'libaom', 'dav1d', 'libyuv'):
            component = self.component(self.catalog, 'pillow', cid)
            self.assertEqual(component['version_basis'], 'unknown')
            self.assertIsNone(component['version'])
            self.assertEqual(component['notices'], [])
        pillow = next(e for e in self.entries if e['id'] == 'base-wheels-pillow')
        self.assertEqual(pillow['status'], 'open')

    def test_real_catalog_pins_lock_and_wheel_hashes(self):
        lock = embedded.read_lock(ROOT/embedded.LOCK_PATH)
        for wheel in self.catalog['wheels']:
            self.assertEqual(wheel['version'], lock[wheel['distribution']]['version'])
            self.assertIn(wheel['sha256'], lock[wheel['distribution']]['hashes'])

    def test_version_basis_values_are_used_as_documented(self):
        bases = {c['version_basis'] for w in self.catalog['wheels'] for c in w['components']}
        self.assertEqual(bases, {'wheel-declared', 'runtime-observed', 'unknown'})

    def test_cryptography_openssl_uses_windows_runtime_api_and_original(self):
        component=self.component(self.catalog,'cryptography','openssl')
        proof=gates.read_json(ROOT/component['version_source'])
        self.assertEqual(component['version_basis'],'runtime-observed')
        self.assertEqual(proof['observed']['platform'],'win32')
        self.assertEqual(proof['observed']['version'],component['version'])
        self.assertTrue(component['notices'])

    def test_cryptography_runtime_proof_rejects_linux_wrong_binary_or_version(self):
        from cryptography_notice import load
        component=self.component(self.catalog,'cryptography','openssl')
        wheel=self.wheel(self.catalog,'cryptography')
        proof=gates.read_json(ROOT/component['version_source'])
        native=next(r for r in self.report['classification_input']['report']['native_files']
                    if r['file']=='cryptography/hazmat/bindings/_rust.pyd')
        for changes in [dict(platform='linux'),dict(binary_sha256='0'*64),dict(version='4.0.4')]:
            broken=copy.deepcopy(proof)
            broken['observed'].update(changes)
            with self.assertRaises(ValueError):
                embedded.check_crypto_observation(component,wheel,broken,native,load())
        catalog=copy.deepcopy(self.catalog)
        self.component(catalog,'cryptography','openssl')['version_basis']='wheel-declared'
        self.assertRejects('cannot be wheel-declared',catalog=catalog)

    # 反例：原生檔列入與漏列
    def test_rejects_missing_native_file(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['native_files'] = []
        self.assertRejects('Registry native files differ', catalog=catalog)

    def test_rejects_duplicate_native_file(self):
        catalog = copy.deepcopy(self.catalog)
        natives = self.component(catalog, 'charset-normalizer', 'charset-normalizer')['native_files']
        natives.append(natives[0])
        self.assertRejects('listed more than once', catalog=catalog)

    def test_rejects_native_file_missing_from_source_review(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['native_files'] = ['psutil/_fake_windows.pyd']
        self.assertRejects('not in the A6 input', catalog=catalog)

    def test_rejects_native_file_of_another_distribution(self):
        catalog = copy.deepcopy(self.catalog)
        moved = self.component(catalog, 'psutil', 'psutil')['native_files']
        self.component(catalog, 'charset-normalizer', 'charset-normalizer')['native_files'].extend(moved)
        self.component(catalog, 'psutil', 'psutil')['native_files'] = []
        self.assertRejects('belongs to another distribution', catalog=catalog)

    # 反例：wheel 名稱、版本與鎖檔 hash
    def test_rejects_wheel_version_differing_from_lock(self):
        catalog = copy.deepcopy(self.catalog)
        self.wheel(catalog, 'numpy')['version'] = '2.5.3'
        self.assertRejects('Wheel version differs from lock', catalog=catalog)

    def test_rejects_wheel_hash_not_in_lock(self):
        catalog = copy.deepcopy(self.catalog)
        self.wheel(catalog, 'numpy')['sha256'] = '0' * 64
        self.assertRejects('Wheel hash is not locked', catalog=catalog)

    def test_rejects_wheel_filename_differing_from_catalog(self):
        catalog = copy.deepcopy(self.catalog)
        self.wheel(catalog, 'numpy')['filename'] = 'numpy-2.5.3-cp312-cp312-win_amd64.whl'
        self.assertRejects('Wheel filename differs', catalog=catalog)

    # 反例：授權原文 hash 與路徑
    def test_rejects_notice_hash_mismatch(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['notices'][0]['sha256'] = '1' * 64
        self.assertRejects('Notice hash mismatch', catalog=catalog)

    def test_rejects_notice_outside_license_directory(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['notices'][0]['path'] = 'docs/README.md'
        self.assertRejects('outside the license directory', catalog=catalog)

    def test_rejects_notice_path_traversal(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['notices'][0]['path'] = (
            'src/desktop_app/data/licenses/windows/../../../../README.md')
        self.assertRejects('outside the license directory', catalog=catalog)

    # 反例：版本依據分級
    def test_rejects_version_basis_outside_allowed_values(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['version_basis'] = 'guessed'
        self.assertRejects('outside allowed values', catalog=catalog)

    def test_rejects_unknown_basis_that_carries_a_version(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'numpy', 'numpy-lapack')['version'] = '3.12.0'
        self.assertRejects('Unknown version must not carry a version', catalog=catalog)

    def test_rejects_declared_basis_without_version_source(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['version_source'] = None
        self.assertRejects('Declared version has no source', catalog=catalog)

    def test_rejects_unknown_component_in_closed_entry(self):
        """把 charset-normalizer 的元件改為 unknown：原本關閉的條目必須被拒絕，不可靜默保留。"""
        catalog = copy.deepcopy(self.catalog)
        component = self.component(catalog, 'charset-normalizer', 'charset-normalizer')
        component['version_basis'] = 'unknown'
        component['version'] = None
        component['version_source'] = None
        self.assertRejects('must stay open', catalog=catalog)

    # 反例：登記條目與目錄的對應
    def test_rejects_entry_that_references_catalog_without_wheel(self):
        entries = copy.deepcopy(self.entries)
        extra = next(e for e in entries if e['id'] == 'base-archives')
        extra['evidence'] = [{'path': CATALOG_PATH, 'sha256': embedded.sha_file(ROOT/CATALOG_PATH)}]
        self.assertRejects('Registry entries referencing the catalog differ', entries=entries)

    def test_rejects_registry_entry_native_drift(self):
        entries = copy.deepcopy(self.entries)
        entry = next(e for e in entries if e['id'] == 'base-wheels-psutil')
        entry['native_files'] = []
        self.assertRejects('Registry native files differ', entries=entries)

    def test_rejects_catalog_wheel_without_registry_entry(self):
        entries = copy.deepcopy(self.entries)
        entries = [e for e in entries if e['id'] != 'base-wheels-psutil']
        self.assertRejects('Registry entries referencing the catalog differ', entries=entries)

    # 反例：目錄結構與來源
    def test_rejects_extra_key_in_component(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['guess'] = 'x'
        self.assertRejects('Unexpected or missing keys', catalog=catalog)

    def test_rejects_non_https_upstream(self):
        catalog = copy.deepcopy(self.catalog)
        self.component(catalog, 'psutil', 'psutil')['upstream'] = 'http://example.invalid/psutil'
        self.assertRejects('Upstream must be an https URL', catalog=catalog)

    def test_rejects_catalog_for_another_profile(self):
        catalog = copy.deepcopy(self.catalog)
        catalog['profile'] = 'cpu'
        self.assertRejects('Catalog profile must be base', catalog=catalog)

    def test_rejects_catalog_bound_to_other_source_commit(self):
        catalog = copy.deepcopy(self.catalog)
        catalog['source_commit'] = '0' * 40
        self.assertRejects('Catalog source differs', catalog=catalog)

    def test_rejects_two_wheel_own_components(self):
        catalog = copy.deepcopy(self.catalog)
        own = self.component(catalog, 'pandas', 'fast-float')
        own['kind'] = 'wheel-own'
        self.assertRejects('Exactly one wheel-own', catalog=catalog)


class GateIntegrationTests(unittest.TestCase):
    """閘門層的整合：目錄存在時，三旗標仍然全部為 false，且 CLI 可以正常退出。"""

    def test_base_gate_reports_catalog_and_keeps_flags_false(self):
        report = gates.read_json(ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json')
        result = gates.assess(report, gates.read_json(gates.REGISTRY))
        self.assertFalse(result['runtime_sbom_complete'])
        self.assertFalse(result['redistribution_approved'])
        self.assertFalse(result['release_ready'])
        self.assertEqual(result['embedded_catalogs'][0]['catalog'], CATALOG_PATH)
        self.assertEqual(result['embedded_catalogs'][0]['wheels'], 10)

    def test_cpu_gate_has_no_catalog_and_still_passes(self):
        report = gates.read_json(ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17/cpu-source-review.json')
        result = gates.assess(report, gates.read_json(gates.REGISTRY))
        self.assertEqual(result['embedded_catalogs'], [])
        self.assertFalse(result['runtime_sbom_complete'])


if __name__ == '__main__':
    unittest.main()

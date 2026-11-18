"""隨包已知缺口揭露檔（A13b）：必須與目錄推導一致、符合 A12c 的 accepted_gaps 格式，並有人讀說明。

為什麼要測「一致」：揭露檔由 scripts/known_gaps.py 從 A12 固定候選與元件目錄推導。目錄或候選一旦變動，
推導結果就與檔案不同，這裡會失敗，提醒重新產生；不能靠手改檔案繞過。
"""
import collections
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT/'src/desktop_app/data'
sys.path.insert(0, str(ROOT/'scripts'))
import known_gaps as subject
import prepare_base_assets as prepare
import redistribution_gates as gates

# A13 決定時的缺口數：8 個 base-wheels 條目共 22 個（A12d 之後）、base-cpython 的 libffi 1 個、
# base-qt 的未知 attribution 84 個加上 opengl32sw.dll 1 個（共 85）。總數 108。
EXPECTED_FAMILIES = {'wheels': 22, 'cpython': 1, 'qt': 85}


class KnownGapsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = gates.read_json(subject.DEFAULT_REPORT)
        cls.registry = gates.read_json(gates.REGISTRY)
        cls.text, cls.markdown = subject.render(cls.report, cls.registry)
        cls.accepted = json.loads(cls.text)['accepted_gaps']

    def test_committed_files_match_the_catalog_derivation(self):
        self.assertEqual(subject.JSON_PATH.read_text(encoding='utf-8'), self.text)
        self.assertEqual(subject.MARKDOWN_PATH.read_text(encoding='utf-8'), self.markdown)
        self.assertEqual(subject.main(['--check']), 0)

    def test_check_fails_when_the_disclosure_is_stale_or_missing(self):
        stale = json.loads(self.text)
        stale['accepted_gaps']['base-qt'] = stale['accepted_gaps']['base-qt'][1:]
        with tempfile.TemporaryDirectory() as temporary:
            json_copy, md_copy = Path(temporary)/'known-gaps.json', Path(temporary)/'known-gaps.md'
            json_copy.write_text(json.dumps(stale), encoding='utf-8')
            md_copy.write_text(self.markdown, encoding='utf-8')
            with patch.object(subject, 'JSON_PATH', json_copy), patch.object(subject, 'MARKDOWN_PATH', md_copy):
                self.assertEqual(subject.main(['--check']), 1)
            with patch.object(subject, 'JSON_PATH', Path(temporary)/'absent.json'), \
                    patch.object(subject, 'MARKDOWN_PATH', md_copy):
                self.assertEqual(subject.main(['--check']), 1)

    def test_gap_counts_match_the_a13_inventory(self):
        self.assertEqual(sum(len(v) for k, v in self.accepted.items() if k.startswith('base-wheels-')),
                         EXPECTED_FAMILIES['wheels'])
        self.assertEqual(self.accepted['base-cpython'], ['cpython/libffi'])
        self.assertEqual(len(self.accepted['base-qt']), EXPECTED_FAMILIES['qt'])
        self.assertEqual(len(self.accepted), 10)
        self.assertEqual(sum(len(v) for v in self.accepted.values()), 108)

    def test_disclosure_shape_matches_the_gate_contract(self):
        data = json.loads(self.text)
        self.assertEqual(set(data), {'schema_version', 'accepted_gaps'})
        self.assertIs(type(data['schema_version']), int)
        self.assertEqual(data['schema_version'], 1)
        base_ids = {entry['id'] for entry in self.registry['profiles']['base']['entries']}
        self.assertTrue(set(data['accepted_gaps']) <= base_ids)
        for key, values in data['accepted_gaps'].items():
            self.assertRegex(key, r'^[a-z0-9-]+$')
            gates.validate_gap_ids(values)
            self.assertEqual(values, sorted(values))
            self.assertEqual(len(values), len(set(values)))

    def test_every_gap_has_a_human_description_and_the_table_is_complete(self):
        for values in self.accepted.values():
            for gap in values:
                self.assertIn('| '+gap+' |', self.markdown)
        self.assertIn('共 108 項。', self.markdown)

    def test_derivation_follows_the_source_review(self):
        # 候選中 libffi 若已有執行期觀測，就不再是缺口；推導結果必須跟著變，不能沿用舊清單。
        changed = copy.deepcopy(self.report)
        for row in changed['classification_input']['report']['cpython_components']['files']:
            if row['component'] == 'libffi':
                row['observed_version'] = row['declared_version']
                row['version_status'] = 'runtime-observed'
        accepted = subject.derive(changed, self.registry)
        self.assertNotIn('base-cpython', accepted)
        self.assertEqual(subject.derive(self.report, self.registry), self.accepted)

    def test_limitations_text_keeps_every_a13_6_item(self):
        text = (DATA/'licenses'/prepare.LIMITATIONS_MD).read_text(encoding='utf-8')
        for phrase in ['測試版非正式版', 'ONNX 繁體中文準確度有已知缺口', '內建 Tesseract 不受影響', 'RAM 為軟性預算',
                       '未在乾淨 Windows 10／11 實機完整驗收', 'GPU 未在實卡驗證', 'known-gaps.json',
                       '安裝程式與 tesseract.exe 無程式碼簽章', 'GitHub Issues']:
            self.assertIn(phrase, text)

    def test_disclosure_files_exist_and_are_linked_from_the_guide(self):
        for name in prepare.DISCLOSURE_FILES:
            self.assertTrue((DATA/'licenses'/name).is_file(), name)
        joined = '\n'.join(prepare.base_guide('0.0.0', [dict(name='x', version='1')], False))
        self.assertIn(prepare.KNOWN_GAPS_MD, joined)
        self.assertIn(prepare.KNOWN_GAPS_JSON, joined)
        self.assertIn(prepare.LIMITATIONS_MD, joined)


if __name__ == '__main__':
    unittest.main()

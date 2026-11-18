"""A8 登記與推導契約；全關閉情境是合成狀態，不能當作實際授權或 Windows 驗收。"""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import redistribution_gates as gates


class GateTests(unittest.TestCase):
    def setUp(self):
        self.registry = gates.read_json(gates.REGISTRY)
        path = ROOT/'docs/development-records/runs/a12-fixed-review-2026-11-18'
        self.reports = {p:gates.read_json(path/(p+'-source-review.json')) for p in ('base', 'cpu')}
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temp = Path(temporary.name)

    def assess(self, profile='base'):
        return gates.assess(self.reports[profile], self.registry)

    DECISION_ROW = '| 2026-01-02 | 使用者決定 | 合成決定：僅供測試 |'
    ARCHIVE = 'docs/history/status/2026-01-02-synthetic.md'

    def write(self, name, text):
        path = self.temp/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return dict(path=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def synthetic_closed(self):
        """只以合成證據測條件分層，不改專案中的登記／決定／舊報告。"""
        proof = self.write('evidence.txt', 'synthetic evidence')
        stage_c = self.write('docs/development-records/runs/stage-c-synthetic/result.txt', 'synthetic stage C')
        text = '# 合成存檔\n\n## C. 其他\n\n| x |\n\n## D. 規則與決定\n\n| 日期 | 來源 | 內容 |\n'+self.DECISION_ROW+'\n\n## E. 其他\n'
        decision = dict(self.write(self.ARCHIVE, text), quote=self.DECISION_ROW)
        for profile in self.registry['profiles'].values():
            for entry in profile['entries']:
                evidence = [stage_c] if entry['id'].endswith('-clean-machine-manual') else [proof]
                entry.update(status='user_approved', evidence=evidence, decision_source=decision)

    def decision_assess(self, text, quote, path=None):
        """以合成存檔檢查單一決定出處；只有 reference 的決定規則被觸發。"""
        ref = dict(self.write(path or self.ARCHIVE, text), quote=quote)
        gates.reference(ref, self.temp, decision=True)

    def test_actual_a6_profiles_have_exact_coverage_and_false_flags(self):
        for profile in ('base', 'cpu'):
            with self.subTest(profile=profile):
                result = self.assess(profile)
                native = self.reports[profile]['classification_input']['report']['native_files']
                self.assertEqual(set(result['coverage']['native_files']), {x['file'] for x in native})
                self.assertEqual(set(result['coverage']['review_reasons']), set(self.reports[profile]['review_reasons']))
                self.assertTrue(result['unclosed_obligations'])
                self.assertTrue(all(result[f] is False for f in gates.FLAGS))

    def test_new_native_file_is_rejected(self):
        raw = self.reports['base']['classification_input']['report']
        raw['native_files'].append(dict(raw['native_files'][0], file='unregistered.dll'))
        with self.assertRaisesRegex(ValueError, 'exactly one obligation: unregistered.dll'):
            self.assess()

    def test_new_reason_is_rejected(self):
        name = 'unregistered-review'
        self.reports['base']['classification_input']['report']['candidate_inventory']['files'][0]['review_reasons'].append(name)
        self.reports['base']['review_reasons'][name] = 1
        with self.assertRaisesRegex(ValueError, 'exactly one obligation: '+name):
            self.assess()

    def test_overlapping_native_assignments_are_rejected(self):
        name = self.reports['base']['classification_input']['report']['native_files'][0]['file']
        entry = next(e for e in self.registry['profiles']['base']['entries'] if e['id']=='base-cpython')
        entry['native_files'].append(name)
        with self.assertRaisesRegex(ValueError, r'exactly one obligation: .*\(2\)'):
            self.assess()

    def test_overlapping_reason_assignments_are_rejected(self):
        self.registry['profiles']['base']['entries'][1]['review_reasons'].append('source-owner-unresolved')
        with self.assertRaisesRegex(ValueError, r'exactly one obligation: source-owner-unresolved \(2\)'):
            self.assess()

    def test_approval_without_recorded_decision_is_rejected(self):
        entry = self.registry['profiles']['base']['entries'][0]
        entry['status'] = 'user_approved'
        # 明確提供有效工程證據，讓本反例只測使用者決定出處。
        entry['evidence'] = [dict(path='LICENSE', sha256=hashlib.sha256((ROOT/'LICENSE').read_bytes()).hexdigest())]
        with self.assertRaisesRegex(ValueError, 'approval without decision source'):
            self.assess()

    def test_decision_hash_and_quotation_are_verified(self):
        self.synthetic_closed()
        entry = self.registry['profiles']['base']['entries'][0]
        original = copy.deepcopy(entry['decision_source'])
        for changes in (dict(sha256='0'*64), dict(quote='沒有記錄的核准'), dict(path='../outside'),
                        dict(path='evidence.txt'), dict(path='STATUS.md')):
            with self.subTest(changes=changes):
                entry['decision_source'] = dict(original, **changes)
                with self.assertRaises(ValueError):
                    gates.assess(self.reports['base'], self.registry, root=self.temp)

    def test_decision_source_accepts_only_user_row_in_section_d_of_archive(self):
        row = self.DECISION_ROW
        good = '## D. 決定\n'+row+'\n## E\n'
        self.decision_assess(good, row)
        outside = '## C. 其他\n'+row+'\n## D. 決定\n| x |\n## E\n'+row+'\n'
        other_source = '| 2026-01-02 | 協調者 | 合成決定 |'
        cases = {
            'substring': (good, row[2:20], None),
            'single character': (good, 'M', None),
            'not in section D': (outside, row, None),
            'source column not user': ('## D. 決定\n'+other_source+'\n', other_source, None),
            'status file': (good, row, 'STATUS.md'),
            'not archive path': (good, row, 'docs/history/other/2026-01-02-x.md'),
            'bad archive name': (good, row, 'docs/history/status/notes.md'),
            'section named Data': ('## Data\n'+row+'\n', row, None),
            'inside code fence': ('## C. 其他\n```\n## D. 偽造\n'+row+'\n```\n', row, None),
            'invalid date': ('## D. 決定\n| 2026-99-99 | 使用者決定 | 合成 |\n', '| 2026-99-99 | 使用者決定 | 合成 |', None),
        }
        for name, (text, quote, path) in cases.items():
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.decision_assess(text, quote, path)

    def test_stale_registry_selectors_are_rejected(self):
        entry = next(e for e in self.registry['profiles']['base']['entries'] if e['id']=='base-cpython')
        entry['native_files'].append('not-in-input.dll')
        with self.assertRaisesRegex(ValueError, 'stale selector in native_files'):
            self.assess()
        entry['native_files'].pop()
        entry['review_reasons'].append('no-such-reason')
        with self.assertRaisesRegex(ValueError, 'stale selector in review_reasons'):
            self.assess()

    def test_clean_machine_closure_needs_stage_c_evidence(self):
        self.synthetic_closed()
        entry = next(e for e in self.registry['profiles']['base']['entries'] if e['id']=='base-clean-machine-manual')
        entry['evidence'] = [self.write('evidence.txt', 'synthetic evidence')]
        with self.assertRaisesRegex(ValueError, 'stage-c evidence'):
            gates.assess(self.reports['base'], self.registry, root=self.temp)

    def test_registry_structure_is_closed(self):
        self.synthetic_closed()
        def mutate(name):
            registry = copy.deepcopy(self.registry)
            entry = registry['profiles']['base']['entries'][0]
            if name == 'top':
                registry['unknown_key'] = 1
            elif name == 'profile':
                registry['profiles']['base']['unknown_key'] = 1
            elif name == 'entry':
                entry['unknown_key'] = 1
            elif name == 'evidence':
                entry['evidence'][0]['unknown_key'] = 1
            elif name == 'decision':
                entry['decision_source']['unknown_key'] = 1
            elif name == 'schema':
                registry['schema_version'] = 1
            elif name == 'schema-float':
                registry['schema_version'] = 2.0
            return registry
        for name in ('top', 'profile', 'entry', 'evidence', 'decision', 'schema', 'schema-float'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                gates.assess(self.reports['base'], mutate(name), root=self.temp)

    def test_closed_status_without_evidence_is_rejected(self):
        self.registry['profiles']['base']['entries'][0].update(status='evidence_complete')
        with self.assertRaisesRegex(ValueError, 'without evidence'):
            self.assess()

    def test_flags_are_derived_not_constant(self):
        self.synthetic_closed()
        for profile in ('base', 'cpu'):
            result = gates.assess(self.reports[profile], self.registry, root=self.temp)
            self.assertTrue(all(result[f] is True for f in gates.FLAGS))
            self.assertEqual(result['unclosed_obligations'], [])

    def test_base_does_not_require_cpu_obligations_to_close(self):
        original_cpu = copy.deepcopy(self.registry['profiles']['cpu'])
        self.synthetic_closed()
        self.registry['profiles']['cpu'] = original_cpu
        base = gates.assess(self.reports['base'], self.registry, root=self.temp)
        cpu = gates.assess(self.reports['cpu'], self.registry, root=self.temp)
        self.assertTrue(all(base[f] is True for f in gates.FLAGS))
        self.assertTrue(all(cpu[f] is False for f in gates.FLAGS))

    def test_engineering_completion_does_not_grant_redistribution(self):
        self.synthetic_closed()
        e = next(e for e in self.registry['profiles']['base']['entries'] if e['id']=='base-redistribution-decision')
        e['status'] = 'evidence_complete'
        result = gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.assertTrue(result['runtime_sbom_complete'])
        self.assertFalse(result['redistribution_approved'])
        self.assertFalse(result['release_ready'])

    def test_redistribution_does_not_replace_clean_machine_and_manual_acceptance(self):
        self.synthetic_closed()
        e = next(e for e in self.registry['profiles']['base']['entries'] if e['id']=='base-clean-machine-manual')
        e['status'] = 'open'
        result = gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.assertTrue(result['runtime_sbom_complete'])
        self.assertTrue(result['redistribution_approved'])
        self.assertFalse(result['release_ready'])

    def test_mandatory_decision_and_acceptance_entries_cannot_be_removed(self):
        for suffix in ('-redistribution-decision', '-clean-machine-manual'):
            with self.subTest(suffix=suffix):
                registry = copy.deepcopy(self.registry)
                entries = registry['profiles']['base']['entries']
                entries[:] = [e for e in entries if e['id']!='base'+suffix]
                with self.assertRaises(ValueError):
                    gates.assess(self.reports['base'], registry)

    def test_source_identity_and_summary_are_not_silently_reinterpreted(self):
        original = copy.deepcopy(self.reports['base'])
        self.reports['base']['selection']['source_commit'] = '0'*40
        with self.assertRaisesRegex(ValueError, 'Source differs'):
            self.assess()
        self.reports['base'] = original
        self.reports['base']['review_reasons']['source-owner-unresolved'] += 1
        with self.assertRaisesRegex(ValueError, 'summary differs'):
            self.assess()

    def test_counts_and_inputs_remain_unchanged(self):
        before = copy.deepcopy((self.reports, self.registry))
        for profile in ('base', 'cpu'):
            result = self.assess(profile)
            self.assertGreater(result['input_inventory_summary']['unresolved_files'], 0)
            self.assertEqual(result['input_inventory_summary'], self.reports[profile]['inventory_summary'])
        self.assertEqual((self.reports, self.registry), before)

    def test_duplicate_json_keys_are_rejected(self):
        path = self.temp/'duplicate.json'
        path.write_text('{"schema_version":1,"schema_version":2}')
        with self.assertRaisesRegex(ValueError, 'Duplicate JSON key'):
            gates.read_json(path)

    def test_cli_reads_real_evidence_and_refuses_overwrite_or_partial_output(self):
        report = ROOT/'docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json'
        output = self.temp/'gates.json'
        command = [sys.executable, str(ROOT/'scripts/redistribution_gates.py'), '--source-review', str(report), '--output', str(output)]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(output.read_text())['release_ready'])
        old = output.read_bytes()
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(output.read_bytes(), old)
        invalid = self.temp/'invalid.json'
        invalid.write_text('{"profile":"base","accepted":false}')
        missing = self.temp/'must-not-exist.json'
        bad = command[:-4]+['--source-review', str(invalid), '--output', str(missing)]
        self.assertNotEqual(subprocess.run(bad, capture_output=True).returncode, 0)
        self.assertFalse(missing.exists())


if __name__ == '__main__':
    unittest.main()

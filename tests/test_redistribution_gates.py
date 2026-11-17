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
        path = ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17'
        self.reports = {p:gates.read_json(path/(p+'-source-review.json')) for p in ('base', 'cpu')}
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.temp = Path(temporary.name)

    def assess(self, profile='base'):
        return gates.assess(self.reports[profile], self.registry)

    def synthetic_closed(self):
        """只以合成證據測條件分層，不改專案中的登記／決定／舊報告。"""
        (self.temp/'evidence.txt').write_text('synthetic evidence')
        quote = '合成使用者決定：僅供測試'
        (self.temp/'decision.md').write_text(quote, encoding='utf-8')
        proof = dict(path='evidence.txt', sha256=hashlib.sha256((self.temp/'evidence.txt').read_bytes()).hexdigest())
        decision = dict(path='decision.md', sha256=hashlib.sha256((self.temp/'decision.md').read_bytes()).hexdigest(), quote=quote)
        for profile in self.registry['profiles'].values():
            for entry in profile['entries']:
                entry.update(status='user_approved', evidence=[proof], decision_source=decision)

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
        for changes in (dict(sha256='0'*64), dict(quote='沒有記錄的核准'), dict(path='../outside')):
            with self.subTest(changes=changes):
                entry['decision_source'] = dict(original, **changes)
                with self.assertRaises(ValueError):
                    gates.assess(self.reports['base'], self.registry, root=self.temp)

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
        report = ROOT/'docs/development-records/runs/a6-fixed-review-2026-11-17/base-source-review.json'
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

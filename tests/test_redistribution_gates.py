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


def committed_sha256(commit, path):
    """取得歷史提交中該路徑的 bytes 並回傳 sha256；git 失敗或提交不存在即拋出例外（不 skip）。

    歷史證據的 pin 是「當時那個提交裡的檔案內容」，所以對提交驗證，而不是對工作樹；
    工作樹之後改動（例如 base.spec 的打包變更）不應使歷史紀錄失效。
    """
    gates.safe_name(path)
    done = subprocess.run(['git', 'show', f'{commit}:{path}'], cwd=ROOT, capture_output=True, check=True)
    return hashlib.sha256(done.stdout).hexdigest()


def evidence_commit(path):
    """回傳新增該證據檔的提交（歷史上最早的一筆）。

    快照型證據（例如 A12b 的 origin-known-review.json）的 supporting_evidence pin，是建立快照當時
    各檔案的內容，不一定等於登記表的 source_commit（b17d51b）：Microsoft 目錄在候選之後才改寫。
    因此對照建立該證據的提交，而不是 source_commit。
    """
    relative = Path(path).resolve().relative_to(ROOT).as_posix()
    done = subprocess.run(['git', 'log', '--diff-filter=A', '--format=%H', '--', relative],
                          cwd=ROOT, capture_output=True, text=True, check=True)
    commits = done.stdout.split()
    if not commits:
        raise AssertionError('No commit adds ' + relative)
    return commits[-1]


class GateTests(unittest.TestCase):
    def setUp(self):
        self.registry = gates.read_json(gates.REGISTRY)
        path = ROOT/'docs/development-records/runs/a13b-fixed-review-2026-11-18'
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
        for profile in ('base', 'cpu'):
            source = 'a'*40
            def entry(suffix, gate_flags, native=None, reasons=None):
                return dict(id=profile+suffix, title='合成義務', native_files=native or [],
                            review_reasons=reasons or [], file_groups=[], required_evidence=['合成證據'],
                            evidence=[stage_c] if suffix == '-clean-machine-manual' else [proof],
                            status='user_approved', requires_user_decision=True, decision_source=decision,
                            gates=gate_flags, accepted_gaps=[])
            self.registry['profiles'][profile] = dict(source_commit=source, entries=[
                entry('-source', list(gates.FLAGS[:2]), ['test.dll'], ['synthetic-review']),
                entry('-redistribution-decision', [gates.FLAGS[1]]),
                entry('-clean-machine-manual', [gates.FLAGS[2]])])
            self.reports[profile] = dict(check='candidate-source-review', schema_version=1, accepted=True,
                profile=profile, selection=dict(source_commit=source), review_reasons={'synthetic-review':1},
                inventory_summary={'synthetic':True}, classification_input=dict(report=dict(
                    profile=profile, source_commit=source, native_files=[dict(file='test.dll')],
                    candidate_inventory=dict(files=[dict(path='_internal/test.dll', sha256='1'*64,
                                                         review_reasons=['synthetic-review'])]))))

    def decision_assess(self, text, quote, path=None):
        """以合成存檔檢查單一決定出處；只有 reference 的決定規則被觸發。"""
        ref = dict(self.write(path or self.ARCHIVE, text), quote=quote)
        gates.reference(ref, self.temp, decision=True)

    def gap_fixture(self, profile='base', *, embedded=False):
        """全為合成資料；包內路徑與真實 base／worker 佈局相同，但不產生產品或真實核准。"""
        self.synthetic_closed()
        entry = self.registry['profiles'][profile]['entries'][0]
        raw = self.reports[profile]['classification_input']['report']
        identity = 'sample/libfoo' if embedded else 'cpython/libffi'
        entry['accepted_gaps'] = [identity]
        raw['cpython_components'] = dict(files=[] if embedded else [dict(
            file='test.dll', component='libffi', observed_version=None,
            declared_version='3.4.4', version_status='build-declaration-only')])
        name = 'src/desktop_app/data/licenses/known-gaps.json'
        disclosure = self.write(name, json.dumps(dict(schema_version=1, accepted_gaps={entry['id']:[identity]})))
        entry['evidence'].append(disclosure)
        prefix = '_internal/desktop_app/data/licenses/' if profile == 'base' else '_internal/worker-assets/licenses/'
        raw['candidate_inventory']['files'].append(dict(path=prefix+'known-gaps.json',
            sha256=disclosure['sha256'], review_reasons=['synthetic-review']))
        self.reports[profile]['review_reasons']['synthetic-review'] += 1
        next(e for e in self.registry['profiles'][profile]['entries']
             if e['id'].endswith('-clean-machine-manual'))['status'] = 'open'
        if embedded:
            self.assertEqual(profile, 'base')
            raw['native_files'][0]['distributions'] = [dict(name='sample', version='1')]
            lock = self.write('packaging/profiles/base-windows-runtime.txt', 'sample==1 --hash=sha256:'+'f'*64+'\n')
            source = self.write('docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json',
                                json.dumps(self.reports[profile]))
            inventory = self.write('src/desktop_app/data/licenses/windows/inventory.json', '{"files":{}}')
            def component(cid, kind, unknown=False):
                return dict(id=cid, name=cid, kind=kind, version=None if unknown else '1',
                    version_basis='unknown' if unknown else 'wheel-declared',
                    version_source=None if unknown else 'METADATA', upstream='https://example.invalid/source',
                    license='synthetic', notices=[], native_files=[] if unknown else ['test.dll'], note='合成')
            catalog = dict(schema_version=1, profile='base', source_commit='a'*40, scope='合成目錄',
                lock=lock, source_review=source, inventory=inventory, wheels=[dict(distribution='sample', version='1',
                    filename='sample-1-py3-none-win_amd64.whl', sha256='f'*64, registry_entry=entry['id'],
                    components=[component('sample', 'wheel-own'), component('libfoo', 'bundled', True)])])
            entry['evidence'].insert(0, self.write('packaging/embedded/base-windows.json', json.dumps(catalog)))
        return entry, raw

    def test_schema3_requires_unique_typed_gap_lists(self):
        for value in (None, {}, 'x', [True], [''], ['x', 'x'], ['x\ny'], [' x']):
            with self.subTest(value=value):
                self.synthetic_closed()
                self.registry['profiles']['base']['entries'][0]['accepted_gaps'] = value
                with self.assertRaisesRegex(ValueError, 'accepted_gaps'):
                    gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.synthetic_closed()
        del self.registry['profiles']['base']['entries'][0]['accepted_gaps']
        with self.assertRaisesRegex(ValueError, 'missing keys'):
            gates.assess(self.reports['base'], self.registry, root=self.temp)

    def test_disclosed_gap_positive_for_base_and_cpu_keeps_strict_complete_false(self):
        for profile in ('base', 'cpu'):
            with self.subTest(profile=profile):
                entry, _ = self.gap_fixture(profile)
                entry['evidence'].insert(0, self.write('src/desktop_app/data/licenses/other-gaps.json',
                    json.dumps(dict(schema_version=1, accepted_gaps={'other-entry':['other/id']}))))
                result = gates.assess(self.reports[profile], self.registry, root=self.temp)
                self.assertFalse(result['runtime_sbom_complete'])
                self.assertTrue(result['runtime_sbom_disclosed'])
                self.assertTrue(result['redistribution_approved'])
                self.assertFalse(result['release_ready'])
                self.assertEqual(result['accepted_gaps'], {entry['id']:['cpython/libffi']})
                self.assertEqual(result['blocked_by_gate']['runtime_sbom_complete'], [entry['id']])
                self.assertEqual(result['gate_dependencies']['redistribution_approved'], ['runtime_sbom_disclosed'])

    def test_rejects_gap_set_different_from_catalog(self):
        for profile in ('base', 'cpu'):
            for values in ([], ['unrelated/id'], ['cpython/libffi', 'extra/id']):
                with self.subTest(profile=profile, values=values):
                    entry, _ = self.gap_fixture(profile)
                    entry['accepted_gaps'] = values
                    with self.assertRaisesRegex(ValueError, 'differs from catalog'):
                        gates.assess(self.reports[profile], self.registry, root=self.temp)

    def test_unknown_closure_needs_user_approval_decision_and_requirement(self):
        for profile in ('base', 'cpu'):
            for changes in (dict(status='evidence_complete'), dict(decision_source=None),
                            dict(requires_user_decision=False), dict(status='open')):
                with self.subTest(profile=profile, changes=changes):
                    entry, _ = self.gap_fixture(profile)
                    entry.update(changes)
                    with self.assertRaises(ValueError):
                        gates.assess(self.reports[profile], self.registry, root=self.temp)

    def test_rejects_missing_disclosure_or_wrong_candidate_bytes(self):
        for profile in ('base', 'cpu'):
            for case in ('missing evidence', 'outside license dir', 'absent candidate', 'wrong hash'):
                with self.subTest(profile=profile, case=case):
                    entry, raw = self.gap_fixture(profile)
                    if case == 'missing evidence':
                        entry['evidence'].pop()
                    elif case == 'outside license dir':
                        entry['evidence'][-1] = self.write('docs/disclosure.json', json.dumps(dict(
                            schema_version=1, accepted_gaps={entry['id']:entry['accepted_gaps']})))
                    elif case == 'absent candidate':
                        raw['candidate_inventory']['files'].pop()
                        self.reports[profile]['review_reasons']['synthetic-review'] -= 1
                    else:
                        raw['candidate_inventory']['files'][-1]['sha256'] = '0'*64
                    with self.assertRaisesRegex(ValueError, 'disclosure|Disclosure'):
                        gates.assess(self.reports[profile], self.registry, root=self.temp)

    def test_disclosure_contents_must_list_the_actual_gaps(self):
        for data in ({'unrelated':'data'}, dict(schema_version=1, accepted_gaps={}),
                     dict(schema_version=1, accepted_gaps={'base-source':['wrong/id']}),
                     dict(schema_version=1, accepted_gaps={'base-source':['cpython/libffi']}, extra=True),
                     dict(schema_version=True, accepted_gaps={'base-source':['cpython/libffi']})):
            with self.subTest(data=data):
                entry, raw = self.gap_fixture()
                ref = self.write(entry['evidence'][-1]['path'], json.dumps(data))
                entry['evidence'][-1] = ref
                raw['candidate_inventory']['files'][-1]['sha256'] = ref['sha256']
                with self.assertRaises(ValueError):
                    gates.assess(self.reports['base'], self.registry, root=self.temp)

    def test_build_declaration_is_not_made_complete_by_a_version_string(self):
        entry, raw = self.gap_fixture()
        raw['cpython_components']['files'][0]['observed_version'] = '3.4.4'
        result = gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.assertFalse(result['runtime_sbom_complete'])
        self.assertEqual(result['unknown_components'][entry['id']], ['cpython/libffi'])

    def test_known_only_entry_cannot_claim_accepted_gaps(self):
        self.synthetic_closed()
        self.registry['profiles']['base']['entries'][0]['accepted_gaps'] = ['invented/id']
        with self.assertRaisesRegex(ValueError, 'without catalog gaps'):
            gates.assess(self.reports['base'], self.registry, root=self.temp)

    def test_embedded_unknown_can_close_only_through_full_disclosure_validation(self):
        entry, _ = self.gap_fixture(embedded=True)
        result = gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.assertFalse(result['runtime_sbom_complete'])
        self.assertTrue(result['runtime_sbom_disclosed'])
        self.assertTrue(result['redistribution_approved'])
        self.assertEqual(result['unknown_components'], {entry['id']:['sample/libfoo']})
        entry['evidence'].pop()
        with self.assertRaisesRegex(ValueError, 'Missing packaged gap disclosure'):
            gates.assess(self.reports['base'], self.registry, root=self.temp)
        # 無獨立原生檔的內含元件也不能靠移除來源 gate，讓 open 缺口被 disclosed 忽略。
        entry, _ = self.gap_fixture(embedded=True)
        known = copy.deepcopy(entry)
        known.update(id='base-known-native', review_reasons=[], accepted_gaps=[],
                     evidence=[self.write('evidence.txt', 'synthetic evidence')])
        self.registry['profiles']['base']['entries'].append(known)
        entry.update(native_files=[], gates=['redistribution_approved'], status='open', accepted_gaps=[])
        ref = entry['evidence'][0]
        catalog = gates.read_json(self.temp/ref['path'])
        catalog['wheels'][0]['components'][0]['native_files'] = []
        entry['evidence'][0] = self.write(ref['path'], json.dumps(catalog))
        result = gates.assess(self.reports['base'], self.registry, root=self.temp)
        self.assertFalse(result['runtime_sbom_disclosed'])
        self.assertIn(entry['id'], result['blocked_by_gate']['runtime_sbom_disclosed'])

    def test_existing_catalog_cannot_be_hidden_by_removing_all_its_references(self):
        for path in ('packaging/embedded/base-windows.json', 'packaging/qt/6.12.0/thirdparty/catalog.json'):
            registry = copy.deepcopy(self.registry)
            for entry in registry['profiles']['base']['entries']:
                entry['evidence'] = [r for r in entry['evidence'] if r['path'] != path]
                if not entry['evidence'] and entry['status'] != 'open':
                    # 留一份有效但無關的工程證據，確定反例測到「隱藏目錄」而非更早的缺證據檢查。
                    entry['evidence'] = [dict(path='LICENSE',
                        sha256=hashlib.sha256((ROOT/'LICENSE').read_bytes()).hexdigest())]
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'catalog must remain bound'):
                gates.assess(self.reports['base'], registry)

    def test_reasonless_review_rows_are_allowed_only_for_packaged_disclosures(self):
        files = self.reports['base']['classification_input']['report']['candidate_inventory']['files']
        disclosure = [r for r in files if r['path'] == '_internal/desktop_app/data/licenses/known-gaps.json']
        self.assertEqual(len(disclosure), 1)
        self.assertEqual(disclosure[0]['review_reasons'], [])
        # 無 reason 的揭露列在列檢查通過；之後的失敗（若有）不得來自該列。
        try:
            self.assess()
        except ValueError as error:
            self.assertNotIn('not a packaged disclosure', str(error))
        files.append(dict(disclosure[0], path='_internal/desktop_app/data/licenses/other.json'))
        with self.assertRaisesRegex(ValueError, 'not a packaged disclosure'):
            self.assess()

    def test_actual_gap_lists_are_accepted_exactly_and_include_qt_and_libffi(self):
        base = self.assess()
        cpu = self.assess('cpu')
        # A13b 2b：base 的決定已寫入，揭露清單與推導的未知集合逐條相等；cpu 仍未決定，不得被接受。
        self.assertTrue(base['runtime_sbom_disclosed'])
        self.assertFalse(cpu['runtime_sbom_disclosed'])
        self.assertEqual(cpu['accepted_gaps'], {})
        for result in (base, cpu):
            self.assertEqual(result['registry_schema_version'], 3)
        self.assertEqual(base['unknown_components']['base-cpython'], ['cpython/libffi'])
        self.assertEqual(cpu['unknown_components']['cpu-cpython'], ['cpython/libffi'])
        self.assertIn('qt-native/PySide6/opengl32sw.dll', base['unknown_components']['base-qt'])
        for entry, gaps in base['unknown_components'].items():
            with self.subTest(entry=entry):
                self.assertEqual(sorted(base['accepted_gaps'][entry]), sorted(gaps))

    def test_actual_profiles_have_exact_coverage_and_expected_flags(self):
        for profile in ('base', 'cpu'):
            with self.subTest(profile=profile):
                result = self.assess(profile)
                native = self.reports[profile]['classification_input']['report']['native_files']
                self.assertEqual(set(result['coverage']['native_files']), {x['file'] for x in native})
                self.assertEqual(set(result['coverage']['review_reasons']), set(self.reports[profile]['review_reasons']))
                self.assertTrue(result['unclosed_obligations'])
                # 兩 profile 都不得宣告完整盤點或 release；只有 base 的揭露與再散布由使用者決定推導為 true。
                self.assertIs(result['runtime_sbom_complete'], False)
                self.assertIs(result['release_ready'], False)
        base = self.assess('base')
        self.assertIs(base['runtime_sbom_disclosed'], True)
        self.assertIs(base['redistribution_approved'], True)
        cpu = self.assess('cpu')
        self.assertIs(cpu['runtime_sbom_disclosed'], False)
        self.assertIs(cpu['redistribution_approved'], False)

    def base_entry(self, identifier):
        return next(e for e in self.registry['profiles']['base']['entries'] if e['id'] == identifier)

    def test_user_decision_quote_must_be_the_archived_section_d_row(self):
        self.base_entry('base-microsoft')['decision_source']['quote'] = (
            '| 2026-11-18 | 使用者 A13 決定 | A13-1（base-microsoft）：改寫過的決定內容 |')
        with self.assertRaisesRegex(ValueError, 'Decision quotation'):
            self.assess()

    def test_user_decision_archive_hash_mismatch_is_rejected(self):
        self.base_entry('base-qt')['decision_source']['sha256'] = 'e'*64
        with self.assertRaisesRegex(ValueError, 'Evidence hash mismatch'):
            self.assess()

    def test_accepted_gaps_must_equal_the_derived_unknown_set(self):
        entry = self.base_entry('base-qt')
        entry['accepted_gaps'] = entry['accepted_gaps'][1:]
        with self.assertRaisesRegex(ValueError, 'accepted_gaps differs'):
            self.assess()
        self.setUp()
        self.base_entry('base-qt')['accepted_gaps'].append('synthetic/unknown-extra')
        with self.assertRaisesRegex(ValueError, 'accepted_gaps differs'):
            self.assess()

    def test_user_approved_unknown_entry_needs_the_packaged_disclosure_reference(self):
        entry = self.base_entry('base-wheels-pandas')
        entry['evidence'] = [ref for ref in entry['evidence'] if not ref['path'].endswith('known-gaps.json')]
        with self.assertRaisesRegex(ValueError, 'Missing packaged gap disclosure'):
            self.assess()

    def test_clean_machine_acceptance_stays_open_after_the_decisions(self):
        self.assertEqual(self.base_entry('base-clean-machine-manual')['status'], 'open')
        self.assertIs(self.assess()['release_ready'], False)


    def test_a12b_origin_known_assessment_covers_the_preserved_rows(self):
        """逐列來源對照是工程證據，不重寫分類器的 origin-known 或替代授權決定。"""
        path = ROOT/'docs/development-records/runs/a12b-evidence-wiring-2026-11-18/origin-known-review.json'
        proof = gates.read_json(path)
        # 逐列快照釘在建立它的 A12 候選（2555687）；比對對象也必須是同一候選的審閱，
        # 不能拿目前候選（b17d51b）的位元組與它比對。
        report = gates.read_json(ROOT/'docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json')
        pin_commit = evidence_commit(path)
        self.assertEqual(proof['source_commit'], '2555687eafc931600f30265f7bd290331cd49a0f')
        self.assertEqual(proof['source_commit'], report['selection']['source_commit'])
        expected = {r['path']:r for r in report['classification']['files'] if r['status'] == 'origin-known'}
        actual = {r['path']:r for r in proof['rows']}
        self.assertEqual(set(actual), set(expected))
        self.assertEqual(len(proof['rows']), len(expected))
        self.assertFalse(proof['redistribution_approved'])
        gates.reference(proof['source_review'], ROOT)
        native = {r['file']:r for r in report['classification_input']['report']['native_files']}
        for name, row in actual.items():
            self.assertEqual((row['sha256'], row['category'], row['original_status']),
                             (expected[name]['sha256'], expected[name]['category'], 'origin-known'))
            self.assertTrue(row['reason'].strip())
            self.assertIs(row['source_attribution_assessed'], True)
            for ref in row['supporting_evidence']:
                self.assertEqual(committed_sha256(pin_commit, ref['path']), ref['sha256'], ref['path'])
            if name.removeprefix('_internal/') in native:
                source = native[name.removeprefix('_internal/')]
                self.assertEqual(row['details']['source_sha256'], source['source_sha256'])
                self.assertEqual(row['details']['bundled_sha256'], row['sha256'])
            if row['category'] == 'cpython-component-evidence':
                self.assertEqual(row['details']['component_evidence']['version_status'], 'build-declaration-only')
                self.assertIsNone(row['details']['component_evidence']['observed_version'])
                self.assertEqual(row['remaining_obligation'], 'base-cpython')

    def test_a12b_supporting_pin_counterexamples_are_rejected(self):
        """反例：記憶體中改掉 pin 的 hash，或指向不存在的提交，比對都必須失敗。"""
        path = ROOT/'docs/development-records/runs/a12b-evidence-wiring-2026-11-18/origin-known-review.json'
        proof = gates.read_json(path)
        commit = evidence_commit(path)
        ref = next(r for row in proof['rows'] for r in row['supporting_evidence'])
        self.assertEqual(committed_sha256(commit, ref['path']), ref['sha256'])
        with self.assertRaises(AssertionError):
            self.assertEqual(committed_sha256(commit, ref['path']), '0'*64, ref['path'])
        with self.assertRaises(subprocess.CalledProcessError):
            committed_sha256('0'*40, ref['path'])
        with self.assertRaises(ValueError):
            committed_sha256(commit, '../outside')

    def test_newly_wired_evidence_with_changed_hash_is_rejected(self):
        """接好路徑不等於驗收通過；每一類新引用都必須真的檢查 bytes 的 hash。"""
        for identity in ('base-source-attribution', 'base-archives', 'base-own-mit-binding',
                         'base-cpython', 'base-tesseract-models', 'base-microsoft'):
            with self.subTest(identity=identity):
                registry = copy.deepcopy(self.registry)
                entry = next(e for e in registry['profiles']['base']['entries'] if e['id'] == identity)
                self.assertTrue(entry['evidence'])
                entry['evidence'][-1]['sha256'] = '0'*64
                with self.assertRaisesRegex(ValueError, 'Evidence hash mismatch'):
                    gates.assess(self.reports['base'], registry)

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
                registry['schema_version'] = 3.0
            return registry
        for name in ('top', 'profile', 'entry', 'evidence', 'decision', 'schema', 'schema-float'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                gates.assess(self.reports['base'], mutate(name), root=self.temp)

    def test_closed_status_without_evidence_is_rejected(self):
        self.registry['profiles']['base']['entries'][0].update(status='evidence_complete', evidence=[])
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
        original_report = copy.deepcopy(self.reports['cpu'])
        self.synthetic_closed()
        self.registry['profiles']['cpu'] = original_cpu
        self.reports['cpu'] = original_report
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
        self.assertTrue(result['runtime_sbom_disclosed'])
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
        report = ROOT/'docs/development-records/runs/a13b-fixed-review-2026-11-18/base-source-review.json'
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

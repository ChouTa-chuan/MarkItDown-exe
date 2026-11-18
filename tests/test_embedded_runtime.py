"""A12d 觀測的邊界：合成 Windows 收據只測判定，不代表本機真的跑過 Windows。"""
import base64
import copy
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import embedded_runtime as runtime
import embedded_components as embedded


class RuntimeObservationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.native = dict(file='lxml/etree.cp312-win_amd64.pyd', source_sha256='1'*64, bundled_sha256='1'*64,
                           distributions=[dict(name='lxml', version='6.1.3')])
        self.source = dict(selection=dict(source_commit='a'*40), classification_input=dict(report=dict(native_files=[self.native])))
        name = 'docs/development-records/runs/synthetic/base-source-review.json'
        path = self.root/name
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(self.source))
        versions = {'lxml':'6.1.3', 'pillow':'13.0.0', 'numpy':'2.5.4'}
        rows = [dict(component=identity, distribution_version=versions[identity.split('/')[0]], api=api,
                     status='unavailable', version=None, raw_value=None, binary=None, reason='合成未觀測')
                for identity, (api, _) in runtime.APIS.items()]
        self.record = next(r for r in rows if r['component']=='lxml/libxml2')
        self.record.update(status='observed', version='2.14.6', raw_value=[2,14,6], reason=None,
                           binary=dict(file=self.native['file'],sha256='1'*64))
        self.proof = dict(check='embedded-runtime-observation', schema_version=1, platform='win32',
            observed_source='b'*40,basis_review=dict(path=name,sha256=runtime.sha(path)),basis_source='a'*40,
            records=rows,not_probed=[],accepted=True,redistribution_approved=False)
        self.component = dict(id='libxml2',version='2.14.6')
        self.wheel = dict(distribution='lxml',version='6.1.3')

    def test_version_apis_do_not_substitute_outer_package_versions(self):
        self.assertEqual(runtime.version_tuple([2,14,6]), '2.14.6')
        text = 'dav1d [dec]:1.5.3-0-gabcdef, aom [enc]:3.14.1'
        self.assertEqual(runtime.codec_version(text,'aom'),'3.14.1')
        self.assertEqual(runtime.codec_version(text,'dav1d'),'1.5.3-0-gabcdef')
        self.assertIsNone(runtime.codec_version('aom [enc]:3.14.1','dav1d'))
        for value in ([0,0,0], [2,1], [2,True,6], [2,-1,6]):
            with self.subTest(value=value), self.assertRaises(ValueError):
                runtime.version_tuple(value)

    def test_unobserved_wrong_api_owner_and_raw_version_are_rejected(self):
        native = {self.native['file']:self.native}
        versions = {'lxml':'6.1.3'}
        runtime.validate_record(self.record,native,versions)
        for changes in (dict(status='unavailable'),dict(api='etree.LIBXML_COMPILED_VERSION'),
                        dict(distribution_version='6.1.4'),dict(raw_value=[2,15,0]),dict(version='guessed')):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                runtime.validate_record(dict(self.record,**changes),native,versions)
        wrong = copy.deepcopy(native)
        wrong[self.native['file']]['distributions'][0]['name']='other'
        with self.assertRaisesRegex(ValueError,'another distribution'):
            runtime.validate_record(self.record,wrong,versions)

    def test_both_original_and_new_candidate_bytes_must_match_the_windows_receipt(self):
        runtime.check_component(self.component,self.wheel,self.proof,self.source,self.root)
        for key in ('source_sha256','bundled_sha256'):
            with self.subTest(key=key):
                source = copy.deepcopy(self.source)
                source['classification_input']['report']['native_files'][0][key]='0'*64
                with self.assertRaisesRegex(ValueError,'candidate bytes'):
                    runtime.check_component(self.component,self.wheel,self.proof,source,self.root)
        proof = copy.deepcopy(self.proof)
        proof['records'][0].update(status='unavailable',version=None)
        with self.assertRaisesRegex(ValueError,'not been runtime observed'):
            runtime.check_component(self.component,self.wheel,proof,self.source,self.root)
        proof = copy.deepcopy(self.proof)
        proof['basis_review']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'basis fingerprint'):
            runtime.check_component(self.component,self.wheel,proof,self.source,self.root)

    def test_windows_success_and_complete_api_record_set_are_required(self):
        runtime.validate_report(self.proof)
        for changes in (dict(platform='linux'),dict(accepted=False),dict(redistribution_approved=True),
                        dict(observed_source='unknown'),dict(records=self.proof['records'][:-1]),
                        dict(records=self.proof['records']+[self.record])):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                runtime.validate_report(dict(self.proof,**changes))
        proof = copy.deepcopy(self.proof)
        proof['records'][-1]['status']='error'
        with self.assertRaisesRegex(ValueError,'contains errors'):
            runtime.validate_report(proof)

    def test_public_receipt_is_bounded_complete_and_hash_verified(self):
        receipt = runtime.receipt(self.proof)
        self.assertEqual(runtime.decode(receipt),self.proof)
        for changes in (dict(sha256='0'*64),dict(extra=True),dict(encoding='other')):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                runtime.decode(dict(receipt,**changes))
        data = b'x'*(64*1024+1)
        bomb = dict(receipt,sha256=hashlib.sha256(data).hexdigest(),data=base64.b64encode(gzip.compress(data)).decode())
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            runtime.decode(bomb)

    def test_catalog_cannot_mark_a_component_observed_without_a_recorded_observation(self):
        catalog = json.loads((ROOT/runtime.CATALOG).read_text())
        registry = json.loads((ROOT/'packaging/redistribution/obligations.json').read_text())
        component = next(c for w in catalog['wheels'] if w['distribution']=='numpy'
                         for c in w['components'] if c['id']=='numpy-lapack')
        component.update(version_basis='runtime-observed',version='3.12.1',
                         version_source='docs/development-records/runs/not-observed/windows.json')
        report = json.loads((ROOT/catalog['source_review']['path']).read_text())
        with self.assertRaisesRegex(ValueError,'missing evidence reference'):
            embedded.check_profile(catalog,catalog_path=runtime.CATALOG,entries=registry['profiles']['base']['entries'],
                                   report=report,root=ROOT)

    def test_real_windows_receipt_binds_the_observed_components_in_the_catalog(self):
        """真實 A12d 證據：收據解回與證據檔相同，目錄中 runtime-observed 的元件恰為觀測到的項目（含 A9b 的 OpenSSL）。"""
        evidence = ROOT/'docs/development-records/runs/a12d-runtime-versions-2026-11-18/embedded-runtime-decoded.json'
        annotations = json.loads((evidence.parent/'annotations.json').read_text(encoding='utf-8'))
        receipts = [a for a in annotations if a.get('title') == 'embedded runtime observation']
        self.assertEqual(len(receipts), 1)
        self.assertEqual(runtime.decode(json.loads(receipts[0]['message'])), json.loads(evidence.read_text(encoding='utf-8')))
        catalog = json.loads((ROOT/runtime.CATALOG).read_text(encoding='utf-8'))
        registry = json.loads((ROOT/'packaging/redistribution/obligations.json').read_text(encoding='utf-8'))
        report = json.loads((ROOT/catalog['source_review']['path']).read_text(encoding='utf-8'))
        summary = embedded.check_profile(catalog, catalog_path=runtime.CATALOG,
                                         entries=registry['profiles']['base']['entries'], report=report, root=ROOT)
        observed = {w['distribution']+'/'+c['id'] for w in catalog['wheels'] for c in w['components']
                    if c['version_basis'] == 'runtime-observed'}
        self.assertEqual(observed, {'lxml/libxml2', 'lxml/libxslt', 'pillow/libaom', 'pillow/dav1d',
                                    'numpy/numpy-lapack', 'cryptography/openssl'})
        # 觀測沒有涵蓋的項目保持 unknown：libexslt、raqm、FriBidi 與 libyuv。
        for identity in ('lxml/libexslt', 'pillow/raqm', 'pillow/fribidi', 'pillow/libyuv'):
            self.assertIn(identity, summary['unknown_components'])

    def test_catalog_level_rejects_changed_evidence_bytes_in_a_scratch_copy(self):
        """目錄層反例：在暫存副本改證據檔的 lxml libxml2 原生檔 sha256，repo 內檔案不動。

        第一種只改證據檔：登記條目仍釘住原檔 hash，應先被 hash 不符拒絕。
        第二種連登記條目的 hash 一起改：證據與 A12 候選 bytes 不符，應由 check_component 拒絕。
        """
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        scratch = Path(temporary.name)
        files = ('packaging/embedded/base-windows.json', 'packaging/profiles/base-windows-runtime.txt',
                 'packaging/redistribution/obligations.json',
                 'docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json',
                 'docs/development-records/runs/a12d-runtime-versions-2026-11-18/embedded-runtime-decoded.json')
        for name in files:
            (scratch/name).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT/name, scratch/name)
        shutil.copytree(ROOT/'src/desktop_app/data/licenses/windows', scratch/'src/desktop_app/data/licenses/windows')
        catalog = json.loads((scratch/runtime.CATALOG).read_text(encoding='utf-8'))
        registry = json.loads((scratch/'packaging/redistribution/obligations.json').read_text(encoding='utf-8'))
        entries = registry['profiles']['base']['entries']
        report = json.loads((scratch/catalog['source_review']['path']).read_text(encoding='utf-8'))
        evidence_path = 'docs/development-records/runs/a12d-runtime-versions-2026-11-18/embedded-runtime-decoded.json'
        proof = json.loads((scratch/evidence_path).read_text(encoding='utf-8'))
        next(r for r in proof['records'] if r['component'] == 'lxml/libxml2')['binary']['sha256'] = '0'*64
        (scratch/evidence_path).write_text(json.dumps(proof, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

        def check(pins):
            return embedded.check_profile(catalog, catalog_path=runtime.CATALOG, entries=pins, report=report, root=scratch)

        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            check(entries)
        # 同一份證據檔也被 numpy、pillow 條目釘住，三處 hash 都要同步才能走到候選 bytes 的判定。
        pinned = copy.deepcopy(entries)
        for entry in pinned:
            for ref in entry['evidence']:
                if ref['path'] == evidence_path:
                    ref['sha256'] = runtime.sha(scratch/evidence_path)
        with self.assertRaisesRegex(ValueError, 'candidate bytes'):
            check(pinned)


if __name__ == '__main__':
    unittest.main()

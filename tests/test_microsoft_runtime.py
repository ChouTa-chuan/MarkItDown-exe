"""A10 反例：來源變動、漏檔、比較值造假與 metadata 截斷都不可冒充證據。"""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import microsoft_runtime as ms


class MicrosoftProbeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.bundle = self.root/'bundle'
        self.redist = self.root/'VC/Redist/MSVC/14.44/x64/Microsoft.VC143.CRT'
        self.redist.mkdir(parents=True)
        self.names = ms.targets()
        rows = []
        for index, name in enumerate(self.names):
            file = self.bundle/'_internal'/name
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(('synthetic runtime '+str(index)).encode())
            reference = self.redist/ms.official_name(name)
            reference.write_bytes(b'synthetic official comparison')
            rows.append(dict(file=name, source_directory=str(file.parent), origin='python-runtime',
                             distributions=[], bundled_sha256=ms.digest(file), source_sha256=ms.digest(file)))
        self.review = dict(profile='base', accepted=True, selection=dict(source_commit='a'*40),
                           classification_input=dict(report=dict(native_files=rows)))
        basis = self.root/ms.BASIS_PATH
        basis.parent.mkdir(parents=True)
        basis.write_text(json.dumps(self.review))
        registry = self.root/'packaging/redistribution/obligations.json'
        registry.parent.mkdir(parents=True)
        registry.write_text(json.dumps(dict(profiles=dict(base=dict(entries=[dict(id='base-microsoft',native_files=self.names)])))))
        self.identities = lambda paths: {p:dict(company='Microsoft Corporation',file_version='14.0.0.0',
                                                 signature_status='Valid',signer='CN=Microsoft, O=Microsoft Corporation') for p in paths}

    def probe(self):
        with patch.object(ms.sys, 'platform', 'win32'):
            return ms.probe(self.bundle, self.review, root=self.root, redist=self.redist, identity=self.identities)

    def test_each_renamed_copy_is_separate_and_mismatch_is_not_approval(self):
        report = self.probe()
        ms.validate_probe(report)
        self.assertEqual(len(report['files']),14)
        self.assertEqual(sum(r['renamed'] for r in report['files']),2)
        self.assertEqual(sum(r['matches_official'] for r in report['files']),0)
        self.assertTrue(all(report[f] is False for f in ms.FLAGS))

    def test_rejects_mutated_bundle(self):
        (self.bundle/'_internal'/self.names[0]).write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError,'differs from provenance'):
            self.probe()

    def test_rejects_missing_runtime(self):
        (self.bundle/'_internal'/self.names[0]).unlink()
        with self.assertRaisesRegex(ValueError,'Missing runtime'):
            self.probe()

    def test_rejects_missing_official_reference(self):
        (self.redist/ms.official_name(self.names[0])).unlink()
        with self.assertRaisesRegex(ValueError,'reference missing'):
            self.probe()

    def test_a6_mismatch_does_not_reuse_historical_identity(self):
        path = self.root/ms.BASIS_PATH
        basis = json.loads(path.read_text())
        basis['classification_input']['report']['native_files'][0]['bundled_sha256'] = 'b'*64
        path.write_text(json.dumps(basis))
        report = self.probe()
        self.assertFalse(report['files'][0]['matches_a6'])
        self.assertEqual(report['files'][0]['identity']['file_version'],'14.0.0.0')

    def test_failed_signature_stays_an_explicit_gap(self):
        self.identities = lambda paths: {p:dict(identity_error='Signature query failed') for p in paths}
        report = self.probe()
        self.assertIn('identity_error',report['files'][0]['identity'])
        self.assertNotIn('signature_status',report['files'][0]['identity'])

    def test_transport_roundtrip_rejects_missing_duplicate_and_out_of_range_parts(self):
        report = self.probe()
        parts = ms.encoded_parts(report)
        self.assertEqual(ms.decode_parts(parts),report)
        for broken in ([],parts[:-1],parts+[parts[0]], [{**p,'part':len(parts)+1} for p in parts]):
            with self.assertRaises(ValueError):
                ms.decode_parts(broken)

    def test_transport_rejects_changed_digest_or_source(self):
        parts = ms.encoded_parts(self.probe())
        for key,value in [('sha256','0'*64),('source_commit','b'*40)]:
            broken = [{**p,key:value} for p in parts]
            with self.assertRaises(ValueError):
                ms.decode_parts(broken)

    def test_rejects_forged_official_match_and_renamed_marker(self):
        report = self.probe()
        for key,value in [('matches_official',True),('official_sha256','b'*64),('renamed',True)]:
            broken = copy.deepcopy(report)
            broken['files'][0][key] = value
            with self.assertRaises(ValueError):
                ms.validate_probe(broken)

    def test_probe_cannot_publish_product_approval(self):
        for flag in ms.FLAGS:
            report = self.probe()
            report[flag] = True
            with self.assertRaisesRegex(ValueError,'Invalid Microsoft probe'):
                ms.encoded_parts(report)

    def test_missing_or_duplicate_copy_is_rejected(self):
        for action in ('missing','duplicate'):
            report = self.probe()
            if action == 'missing':
                report['files'].pop()
            else:
                report['files'][-1] = report['files'][0]
            with self.assertRaises(ValueError):
                ms.validate_probe(report)

    def catalog_fixture(self):
        report = self.probe()
        def pin(name, value):
            path = self.root/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(json.dumps(value))
            return dict(path=name,sha256=ms.digest(path))
        probe_ref = pin('evidence/probe.json',report)
        notice = pin('evidence/terms.txt','Synthetic terms, not legal evidence')
        import embedded_components
        lock_path = 'packaging/profiles/base-windows-runtime.txt'
        target = self.root/lock_path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/lock_path).read_bytes())
        lock = embedded_components.read_lock(target)
        containers = {d:dict(version=lock[d]['version'],sha256=sorted(lock[d]['hashes'])[0])
                      for d in ['numpy','pandas','pyside6-essentials','shiboken6']}
        catalog = dict(schema_version=1,profile='base',registry_entry='base-microsoft',
                       source_commit=self.review['selection']['source_commit'],
                       basis=dict(path=ms.BASIS_PATH,sha256=ms.digest(self.root/ms.BASIS_PATH)),
                       probe=probe_ref,files=report['files'],references=report['references'],
                       lock=dict(path=lock_path,sha256=ms.digest(target)),containers=containers,
                       version_basis='pe-version-resource',documents=[dict(snapshot=notice)],
                       unverified_terms=False,legal_approval=False)
        entry = dict(native_files=self.names,requires_user_decision=True,status='evidence_complete',
                     evidence=[dict(path=ms.CATALOG_PATH,sha256='0'*64)])
        return catalog, entry

    def test_catalog_binds_fourteen_copies_and_does_not_require_matching_newer_redist(self):
        catalog, entry = self.catalog_fixture()
        result = ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)
        self.assertEqual(result['identity_gaps'],[])
        self.assertEqual(result['official_matches'],0)
        self.assertFalse(result['legal_approval'])

    def test_catalog_rejects_missing_copy_and_changed_observation(self):
        for mode in ('missing','changed'):
            catalog, entry = self.catalog_fixture()
            if mode == 'missing':
                catalog['files'].pop()
            else:
                catalog['files'][0]['identity']['file_version'] = 'invented'
            with self.assertRaises(ValueError):
                ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)

    def test_catalog_rejects_changed_terms_and_probe_bytes(self):
        for target in ('documents','probe'):
            catalog, entry = self.catalog_fixture()
            ref = catalog['probe'] if target == 'probe' else catalog['documents'][0]['snapshot']
            (self.root/ref['path']).write_text('changed')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):
                ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)

    def test_catalog_cannot_close_with_signature_gap_or_unverified_terms(self):
        self.identities = lambda paths: {p:dict(identity_error='Signature query failed') for p in paths}
        catalog, entry = self.catalog_fixture()
        with self.assertRaisesRegex(ValueError,'must stay open'):
            ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)
        entry['status'] = 'open'
        self.assertTrue(ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)['identity_gaps'])
        catalog['unverified_terms'] = True
        entry['status'] = 'evidence_complete'
        with self.assertRaises(ValueError):
            ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)

    def test_catalog_rejects_unlocked_wheel_container(self):
        catalog, entry = self.catalog_fixture()
        catalog['containers']['numpy']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError,'differs from lock'):
            ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)

    def test_catalog_preserves_a13_user_decision_requirement(self):
        catalog, entry = self.catalog_fixture()
        entry['requires_user_decision'] = False
        with self.assertRaisesRegex(ValueError,'A13 user decision'):
            ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)
        entry['requires_user_decision'] = True
        catalog['legal_approval'] = True
        with self.assertRaisesRegex(ValueError,'premature legal approval'):
            ms.check_catalog(catalog,report=self.review,entry=entry,root=self.root)

    def test_installed_terms_preserve_original_bytes_and_exclude_unrelated_license(self):
        english = self.root/'Licenses/1033/license.txt'
        english.parent.mkdir(parents=True)
        raw = b'MICROSOFT SOFTWARE LICENSE TERMS\r\nMICROSOFT VISUAL STUDIO ENTERPRISE 2022\r\nOriginal terms\r\n'
        english.write_bytes(raw)
        (english.parent/'license.other.txt').write_text('Third party license')
        result = ms.installed_terms(self.redist)
        self.assertEqual(len(result['documents']),1)
        import base64
        self.assertEqual(base64.b64decode(result['documents'][0]['content_base64']),raw)

    def source_fixture(self, version='1'):
        from types import SimpleNamespace
        basis = self.root/ms.BASIS_PATH
        report = json.loads(basis.read_text())
        for row in report['classification_input']['report']['native_files']:
            row.update(origin='installed-wheel',distributions=[dict(name='synthetic',version='1')])
        basis.write_text(json.dumps(report))
        return SimpleNamespace(version=version,locate_file=lambda name:self.bundle/'_internal'/name)

    def test_source_reconstruction_is_explicit_and_hash_bound_to_a6(self):
        dist = self.source_fixture()
        with patch.object(ms.sys,'platform','win32'), patch.object(ms,'find_vc_redist',return_value=self.redist), \
             patch.object(ms.importlib.metadata,'distribution',return_value=dist), patch.object(ms,'describe',self.identities):
            report = ms.probe_sources(self.review['selection'],root=self.root)
        ms.validate_probe(report)
        self.assertEqual(report['observation_scope'],'installed-source-reconstruction')
        self.assertTrue(all(r['matches_a6'] for r in report['files']))
        self.assertTrue(all(report[f] is False for f in ms.FLAGS))

    def test_source_reconstruction_rejects_other_wheel_version(self):
        dist = self.source_fixture(version='2')
        with patch.object(ms.sys,'platform','win32'), patch.object(ms,'find_vc_redist',return_value=self.redist), \
             patch.object(ms.importlib.metadata,'distribution',return_value=dist), \
             self.assertRaisesRegex(ValueError,'differs from A6'):
            ms.probe_sources(self.review['selection'],root=self.root)

    def test_repository_catalog_is_wired_to_gates_and_preserves_qt_signer_findings(self):
        import redistribution_gates as gates
        registry = gates.read_json(gates.REGISTRY)
        report = gates.read_json(ROOT/ms.BASIS_PATH)
        result = gates.assess(report,registry)
        self.assertEqual(result['microsoft_catalogs'][0]['files'],14)
        self.assertTrue(all(result[f] is False for f in ms.FLAGS))
        entry = next(e for e in registry['profiles']['base']['entries'] if e['id']=='base-microsoft')
        self.assertTrue(entry['requires_user_decision'])
        self.assertEqual(entry['status'],'open')
        catalog = gates.read_json(ROOT/ms.CATALOG_PATH)
        qt_signed = [r for r in catalog['files'] if 'O=The QT Company Oy' in r['identity'].get('signer','')]
        self.assertEqual(len(qt_signed),9)
        self.assertTrue(all(r['identity']['signature_status']=='Valid' for r in qt_signed))
        self.assertEqual(set(result['microsoft_catalogs'][0]['identity_gaps']),{r['file'] for r in qt_signed})

    def test_probe_refuses_non_windows(self):
        with patch.object(ms.sys,'platform','linux'), self.assertRaisesRegex(ValueError,'requires Windows'):
            ms.probe(self.bundle,self.review,root=self.root,redist=self.redist)


if __name__ == '__main__':
    unittest.main()

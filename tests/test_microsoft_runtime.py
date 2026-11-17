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

    def test_probe_refuses_non_windows(self):
        with patch.object(ms.sys,'platform','linux'), self.assertRaisesRegex(ValueError,'requires Windows'):
            ms.probe(self.bundle,self.review,root=self.root,redist=self.redist)


if __name__ == '__main__':
    unittest.main()

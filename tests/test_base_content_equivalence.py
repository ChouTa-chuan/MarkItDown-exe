"""固定候選逐檔對照與有期限的 repo 證據退路。使用合成資料。"""
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
from base_content_equivalence import compare, provenance_input, sha_json, DATA
from python_archive_inventory import zip_members
from candidate_inventory import snapshot
from base_test_build import SOURCE, write


class ContentEquivalenceTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.bundle = self.root/'bundle'
        self.generated = DATA+'native/source.json'
        self.other_generated = DATA+'licenses/native/python-modules.json'
        self.put('app.dll', b'original')
        self.put(self.generated, b'old receipt')
        self.put(self.other_generated, b'original manifest')
        self.original = dict(source_commit=SOURCE, profile='base', host_platform='win32', accepted=True,
                             **self.rebuilt())
        self.file = self.root/'bundle-provenance.json'
        write(self.file,self.original)
        self.review = dict(selection=dict(source_commit=SOURCE), inventory_summary=dict(files=3),
                           pure_modules_sha256=sha_json(self.original['python_archives']['pure_modules']),
                           inventory_sha256=sha_json(self.original['candidate_inventory']),
                           provenance_report_sha256=hashlib.sha256(self.file.read_bytes()).hexdigest())

    def put(self, name, data):
        path = self.bundle/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

    def rebuilt(self, pure=None):
        return dict(candidate_inventory=dict(files=snapshot(self.bundle)),
                    python_archives=dict(pure_modules=pure or {'modules':['fixed']}))

    def check(self):
        _, source = provenance_input(self.root,self.review,SOURCE)
        return compare(self.bundle,self.rebuilt(),self.review,source)

    def test_complete_inventory_accepts_documented_generated_delta(self):
        self.put(self.generated,b'new receipt')
        result = self.check()
        self.assertEqual(result['mode'],'full-inventory')
        self.assertTrue(result['full_path_set_verified'])
        delta, = result['changed_generated_files']
        self.assertEqual(delta['path'],self.generated)
        self.assertTrue(delta['reason'])
        self.assertNotEqual(delta['original']['sha256'],delta['rebuilt']['sha256'])

    def test_extra_and_missing_path_rejected_even_with_equal_count(self):
        self.put('extra.bin',b'extra')
        with self.assertRaisesRegex(ValueError,'count'):
            self.check()
        (self.bundle/'app.dll').unlink()
        with self.assertRaisesRegex(ValueError,'paths differ'):
            self.check()
        (self.bundle/'extra.bin').unlink()
        with self.assertRaisesRegex(ValueError,'count'):
            self.check()

    def test_modified_ordinary_file_rejected(self):
        self.put('app.dll',b'changed!')
        with self.assertRaisesRegex(ValueError,'Unexpected changed files: app.dll'):
            self.check()

    def test_generated_file_outside_exact_allowlist_rejected(self):
        self.put(self.other_generated,b'other manifest')
        with self.assertRaisesRegex(ValueError,'Unexpected changed files: .*python-modules.json'):
            self.check()

    def test_only_confirmed_pinned_record_is_exempt(self):
        self.put(self.other_generated,b'new install metadata')
        self.review['classification'] = dict(files=[dict(path=self.other_generated,
                                                          category='installer-generated-record', status='gap')])
        with self.assertRaisesRegex(ValueError,'Unexpected changed files'):
            self.check()
        self.review['classification']['files'][0]['status']='confirmed'
        # 固定分類有誤時仍不得把任意非 RECORD 路徑當成例外。
        with self.assertRaisesRegex(ValueError,'Unexpected changed files'):
            self.check()
        record_path = '_internal/example-1.0.dist-info/RECORD'
        self.put(self.other_generated,b'original manifest')
        self.put(record_path,b'original record')
        original = self.rebuilt()
        self.review['inventory_summary']['files'] = 4
        self.review['classification']['files'][0]['path'] = record_path
        self.put(record_path,b'rebuilt record')
        result = compare(self.bundle,self.rebuilt(),self.review,original)
        self.assertEqual([r['path'] for r in result['changed_generated_files']],[record_path])

    def test_base_library_rejects_changed_member_paths(self):
        archive = self.bundle/'_internal/base_library.zip'
        def zip_with(name,data):
            with zipfile.ZipFile(archive,'w') as z:
                z.writestr(name,data)
        zip_with('same.pyc',b'old')
        original = self.rebuilt()
        self.review['inventory_summary']['files'] = 4
        self.review['classification_input'] = dict(report=dict(python_archives=dict(
            base_library=dict(members=zip_members(archive)))))
        zip_with('other.pyc',b'old')
        with self.assertRaisesRegex(ValueError,'member paths differ'):
            compare(self.bundle,self.rebuilt(),self.review,original)
        zip_with('same.pyc',b'new')
        with self.assertRaisesRegex(ValueError,'member size or CRC differs'):
            compare(self.bundle,self.rebuilt(),self.review,original)
        with zipfile.ZipFile(archive,'w') as z:
            z.writestr(zipfile.ZipInfo('same.pyc',(1980,1,1,0,0,0)),b'old')
        result = compare(self.bundle,self.rebuilt(),self.review,original)
        self.assertEqual(result['base_library_member_changes'],[])
        self.assertEqual([r['path'] for r in result['changed_generated_files']],['_internal/base_library.zip'])

    def test_mismatched_original_provenance_sha_rejected_before_parsing(self):
        self.file.write_bytes(b'not JSON')
        with self.assertRaisesRegex(ValueError,'Original provenance SHA-256 mismatch'):
            self.check()

    def test_changed_pure_module_digest_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'Pure modules SHA-256 mismatch'):
            compare(self.bundle,self.rebuilt({'modules':['changed']}),self.review,self.original)

    def test_retained_review_rejects_early_use_and_discloses_weaker_scope(self):
        rows = self.original['candidate_inventory']['files']
        kept = [dict(r, category='repo-blob', status='confirmed') for r in rows if r['path'] != self.other_generated]
        self.review.update(classification=dict(files=kept), packages=[],
                           classification_input=dict(report=dict(native_files=[],candidate_inventory=dict(files=[]))))
        kwargs = dict(bundle=self.bundle,rebuilt=self.rebuilt(),review=self.review,original=None)
        with self.assertRaisesRegex(ValueError,'after the baseline deadline'):
            compare(**kwargs,now=datetime(2026,11,24,tzinfo=timezone.utc))
        after = datetime(2026,11,26,tzinfo=timezone.utc)
        result = compare(**kwargs,now=after)
        self.assertEqual(result['mode'],'retained-review')
        self.assertFalse(result['full_path_set_verified'])
        self.assertIsNone(result['original_provenance_sha256'])
        self.assertEqual(result['counts']['compared_paths'],2)
        self.put('app.dll',b'changed!')
        with self.assertRaisesRegex(ValueError,'Unexpected changed files: app.dll'):
            compare(self.bundle,self.rebuilt(),self.review,None,now=after)

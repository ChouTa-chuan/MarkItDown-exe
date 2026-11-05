import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

spec=importlib.util.spec_from_file_location('license_inventory',Path(__file__).parents[1]/'scripts/license_inventory.py')
inventory=importlib.util.module_from_spec(spec);spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root=Path(directory.name);self.wheels=self.root/'wheels';self.wheels.mkdir()
        self.extra=self.root/'extra';self.extra.mkdir();(self.extra/'sources.json').write_text('[]')
        self.output=self.root/'output';self.lock=self.root/'lock.txt'

    def wheel(self,notice=True,unsafe=False,nested=False):
        path=self.wheels/'fixture-1.0-py3-none-any.whl'
        with zipfile.ZipFile(path,'w') as z:
            z.writestr('fixture-1.0.dist-info/METADATA','Name: fixture\nVersion: 1.0\nLicense: MIT\n')
            if notice:z.writestr('../LICENSE' if unsafe else 'fixture-1.0.dist-info/licenses/LICENSE','Test fixture notice')
            if nested:z.writestr('fixture/vendor/other.dist-info/METADATA','Name: other\nVersion: 2\n')
        self.lock.write_text('fixture==1.0 \\\n    --hash=sha256:'+hashlib.sha256(path.read_bytes()).hexdigest()+'\n')

    def generate(self):
        return inventory.generate(self.lock,self.wheels,self.extra,self.output)

    def test_complete_inventory_and_nested_metadata(self):
        self.wheel(nested=True);report=self.generate()
        self.assertEqual(report['package_count'],1)
        self.assertEqual(inventory.verify(self.lock,self.output)['package_count'],1)

    def test_locked_hash_mismatch_cleans_staging(self):
        self.wheel();self.lock.write_text('fixture==1.0 --hash=sha256:'+'0'*64)
        with self.assertRaises(ValueError):self.generate()
        self.assertFalse(self.output.exists())
        self.assertFalse(list(self.root.glob('.license-*')))

    def test_missing_package_is_not_silently_omitted(self):
        self.wheel();self.lock.write_text(self.lock.read_text()+'missing==1.0 --hash=sha256:'+'1'*64)
        with self.assertRaises(ValueError):self.generate()
        self.assertFalse(self.output.exists())

    def test_notice_tampering_rejected(self):
        self.wheel();report=self.generate()
        path=report['packages'][0]['wheel_notice_files'][0]
        (self.output/path).write_text('changed')
        with self.assertRaises(ValueError):inventory.verify(self.lock,self.output)

    def test_missing_notice_rejected(self):
        self.wheel(notice=False)
        with self.assertRaises(ValueError):self.generate()
        self.assertFalse(self.output.exists())

    def test_archive_traversal_rejected(self):
        self.wheel(unsafe=True)
        with self.assertRaises(ValueError):self.generate()
        self.assertFalse(self.output.exists())
        self.assertFalse((self.root/'LICENSE').exists())

    def test_stale_lock_rejected(self):
        self.wheel();self.generate();self.lock.write_text(self.lock.read_text()+'# changed\n')
        with self.assertRaises(ValueError):inventory.verify(self.lock,self.output)

    def test_existing_user_directory_preserved(self):
        self.wheel();self.output.mkdir();note=self.output/'user.txt';note.write_text('keep')
        with self.assertRaises(ValueError):self.generate()
        self.assertEqual(note.read_text(),'keep')

    def test_real_windows_catalog_covers_lock(self):
        root=Path(__file__).parents[1]
        report=inventory.verify(root/'packaging/requirements-windows.txt',root/'src/desktop_app/data/licenses/windows')
        self.assertEqual(report['package_count'],58)
        self.assertTrue(any(p['name']=='pyside6-essentials' and len(p['supplemental_sources'])>=2 for p in report['packages']))

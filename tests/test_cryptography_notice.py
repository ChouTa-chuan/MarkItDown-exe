"""A9b 原文缺失／竄改／錯綁與真正 OpenSSL API 的版本契約。"""
import copy
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import cryptography_notice as notice


class CryptographyNoticeTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        shutil.copytree(ROOT/'packaging/cryptography',self.root/'packaging/cryptography')
        source = 'src/desktop_app/data/licenses/windows/supplemental/cryptography.txt'
        target = self.root/source
        target.parent.mkdir(parents=True)
        target.write_bytes((ROOT/source).read_bytes())
        self.assets = self.root/'assets'
        target = self.assets/notice.NOTICE
        target.parent.mkdir(parents=True)
        target.write_bytes((ROOT/source).read_bytes())
        self.observation = dict(platform='linux',distribution_version='50.0.2',version='4.0.3',
                                version_text='OpenSSL 4.0.3 29 Sep 2026',version_number=0x40000030,
                                binary='_rust.synthetic',binary_sha256='a'*64,api='synthetic test, not a Windows observation')
        self.packages = [dict(name='cryptography',version='50.0.2',supplemental_sources=[dict(path=notice.NOTICE,sha256=notice.sha(target))])]
        notice.stage(self.root,self.assets,self.packages,self.observation)

    def test_real_current_platform_api_observation(self):
        observation = notice.observe()
        notice.validate_observation(observation,notice.load())
        self.assertEqual(observation['platform'],sys.platform)
        self.assertEqual(observation['version'],'4.0.3')
        self.assertNotEqual(observation['binary_sha256'],'a'*64)

    def test_original_missing_or_changed_is_rejected(self):
        profile = notice.load(self.root)
        original = self.root/profile['notice']['path']
        for content in (None,b'changed original'):
            if content is None:
                original.unlink()
            else:
                original.write_bytes(content)
            with self.assertRaisesRegex(ValueError,'original missing or changed'):
                notice.load(self.root)

    def test_bundled_original_missing_or_changed_is_rejected(self):
        path = self.assets/notice.NOTICE
        for content in (None,b'changed bundled text'):
            if content is None:
                path.unlink()
            else:
                path.write_bytes(content)
            with self.assertRaisesRegex(ValueError,'original missing or changed'):
                notice.verify(self.assets,self.packages,root=self.root)

    def test_wrong_or_missing_package_binding_is_rejected(self):
        for packages in ([],[dict(name='foreign',version='1',supplemental_sources=self.packages[0]['supplemental_sources'])],
                         [dict(self.packages[0],supplemental_sources=[])]):
            with self.assertRaises(ValueError):
                notice.verify(self.assets,packages,root=self.root)
        packages=self.packages+[dict(name='foreign',version='1',supplemental_sources=self.packages[0]['supplemental_sources'])]
        with self.assertRaisesRegex(ValueError,'wrong package'):
            notice.verify(self.assets,packages,root=self.root)

    def test_runtime_text_number_and_expected_version_must_agree(self):
        for edits in [dict(version='4.0.4'),dict(version_text='OpenSSL 4.0.2'),dict(version_number=0x40000020),
                      dict(distribution_version='49.0.0')]:
            with self.assertRaises(ValueError):
                notice.stage(self.root,self.assets,self.packages,dict(self.observation,**edits))

    def test_official_tag_or_notice_hash_cannot_be_swapped(self):
        path=self.root/notice.PROFILE
        p=notice.load(self.root)
        for edits in [dict(openssl_commit='b'*40),dict(openssl_tag='openssl-4.0.2')]:
            path.write_text(json.dumps(dict(p,**edits)))
            with self.assertRaises(ValueError):
                notice.load(self.root)

    def test_report_cannot_grant_redistribution_or_change_source(self):
        path=self.assets/notice.REPORT
        original=json.loads(path.read_text())
        for changes in [dict(redistribution_approved=True),dict(openssl_tag='openssl-4.0.2'),dict(openssl_commit='b'*40)]:
            path.write_text(json.dumps(dict(original,**changes)))
            with self.assertRaisesRegex(ValueError,'Invalid bundled'):
                notice.verify(self.assets,self.packages,root=self.root)

    def test_supplemental_inventory_binds_original_to_cryptography(self):
        from license_inventory import verify
        i=verify(ROOT/'packaging/requirements-windows.txt',ROOT/'src/desktop_app/data/licenses/windows')
        package=next(p for p in i['packages'] if p['name']=='cryptography')
        source=next(s for s in package['supplemental_sources'] if s['path']=='supplemental/cryptography.txt')
        self.assertEqual(source['component_version'],'4.0.3')
        self.assertEqual(source['sha256'],notice.load()['notice']['sha256'])


if __name__=='__main__':
    unittest.main()

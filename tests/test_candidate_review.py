"""固定候選、來源重分類、完整性與 metadata 保存；全部為合成檔案，不當 Windows 實證。"""
import contextlib
import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import candidate_review as subject
from candidate_inventory import snapshot


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


class ReviewTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.repo = self.root/'repo'
        (self.repo/'src/desktop_app/data').mkdir(parents=True)
        (self.repo/'notice.txt').write_bytes(b'original notice\r\n')
        (self.repo/'pyproject.toml').write_text('[project]\nversion="0.0.0"\n')
        (self.repo/subject.classifier.MODEL_MANIFEST).write_text(json.dumps({'files':{'eng':digest(b'model')}}))
        self.git('init', '-q')
        self.git('-c', 'core.autocrlf=false', 'add', '-A')
        self.git('-c', 'user.name=test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                 'commit', '-q', '-m', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()
        self.bundle = self.root/'bundle'
        contents = {'_internal/notice.txt':b'original notice\r\n', '_internal/model':b'model',
            '_internal/desktop_app/data/licenses/native/cpython-components.json':b'{}',
            '_internal/meta/METADATA':b'Name: demo\nVersion: 1\nProject-URL: Repository, https://example.invalid/repo\n'}
        for name, raw in contents.items():
            p = self.bundle/name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
        files = snapshot(self.bundle)
        for row in files:
            known = row['path'].endswith('METADATA')
            row.update(role='data-or-generated', owners=[{'name':'demo','version':'1'}] if known else [],
                       review_reasons=[] if known else ['source-owner-unresolved'])
        summary = dict(files=len(files), bytes=sum(r['bytes'] for r in files), unresolved_files=3,
                       runtime_sbom_complete=False, redistribution_approved=False, release_ready=False)
        self.report = dict(profile='base', source_commit=self.commit, source_version='0.0.0',
            accepted=True, host_platform='win32', inventory_reverified=True,
            redistribution_approved=False, release_ready=False, native_files=[],
            packages=[dict(name='demo', version='1', metadata_path='_internal/meta/METADATA',
                metadata_sha256=digest(contents['_internal/meta/METADATA']), notices=[])],
            candidate_inventory=dict(files=files, summary=summary),
            python_archives=dict(base_library=dict(path='_internal/base_library.zip', members=[{'name':'os.pyc'}]),
                pure_modules=[dict(name='json', origin='stdlib')], summary=dict(unknown_modules=0)))
        self.reports = self.root/'reports'
        (self.reports/'installer').mkdir(parents=True)
        self.package = self.root/'setup'
        self.package.mkdir()
        self.installer = self.package/'MarkItDownBase-Setup-0.0.0-windows-x64.exe'
        self.installer.write_bytes(b'fixture installer')
        self.save(self.reports/'bundle-provenance.json', self.report)
        self.save(self.reports/'installer/installer-lifecycle.json',
                  dict(accepted=True, installer_sha256=digest(b'fixture installer')))
        self.env = patch.dict(os.environ, {'MARKITDOWN_CANDIDATE_SOURCE':''})
        self.env.start()
        self.addCleanup(self.env.stop)

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], text=True)

    def save(self, path, value):
        path.write_text(json.dumps(value))

    def review(self):
        return subject.make_review('base', self.bundle, self.reports, self.package, self.commit, self.repo)

    def test_fixed_source_requires_exact_clean_head_and_manual_event(self):
        with patch.dict(os.environ, {'MARKITDOWN_CANDIDATE_SOURCE':self.commit,
                                    'GITHUB_EVENT_NAME':'workflow_dispatch'}):
            self.assertTrue(subject.check_source(self.repo, self.commit)['explicitly_pinned'])
            with patch.dict(os.environ, {'GITHUB_EVENT_NAME':'pull_request'}):
                with self.assertRaisesRegex(ValueError, 'workflow_dispatch'):
                    subject.check_source(self.repo, self.commit)
        for source in (self.commit[:7], '0'*40):
            with self.assertRaises(ValueError):
                subject.check_source(self.repo, source)
        (self.repo/'notice.txt').write_bytes(b'changed source')
        with self.assertRaisesRegex(ValueError, 'clean'):
            subject.check_source(self.repo, self.commit)

    def test_review_covers_unresolved_and_is_replayable_without_raw_artifact(self):
        result = self.review()
        self.assertEqual(result['classification']['classified'], 3)
        self.assertEqual(result['classification']['by_category'],
                         {'pinned-model':1, 'project-generated':1, 'repo-blob':1})
        self.assertTrue(subject.replay(result, self.repo))
        self.assertFalse(result['complete_candidate_inventory_embedded'])
        self.assertEqual(result['candidate']['sha256'], digest(b'fixture installer'))
        self.assertEqual(result['packages'][0]['project_urls'], ['Repository, https://example.invalid/repo'])
        for flag in ('runtime_sbom_complete', 'redistribution_approved', 'release_ready'):
            self.assertIs(result[flag], False)

    def test_wrong_source_or_unaccepted_report_is_rejected(self):
        for field, value in [('source_commit','0'*40), ('accepted',False), ('host_platform','linux'),
                             ('source_version','9'), ('redistribution_approved',True)]:
            with self.subTest(field=field):
                self.save(self.reports/'bundle-provenance.json', dict(self.report, **{field:value}))
                with self.assertRaises(ValueError):
                    self.review()

    def test_changed_candidate_package_and_inventory_are_rejected(self):
        self.installer.write_bytes(b'modified installer')
        with self.assertRaisesRegex(ValueError, 'installer'):
            self.review()
        self.installer.write_bytes(b'fixture installer')
        (self.bundle/'_internal/model').write_bytes(b'changed model')
        with self.assertRaisesRegex(ValueError, 'inventory differs'):
            self.review()

    def test_count_mismatch_and_external_metadata_reference_are_rejected(self):
        self.report['candidate_inventory']['summary']['unresolved_files'] = 4
        self.save(self.reports/'bundle-provenance.json', self.report)
        with self.assertRaisesRegex(ValueError, 'declared unresolved'):
            self.review()
        self.report['candidate_inventory']['summary']['unresolved_files'] = 3
        self.report['packages'][0]['metadata_path'] = '../secret'
        self.save(self.reports/'bundle-provenance.json', self.report)
        with self.assertRaisesRegex(ValueError, 'outside'):
            self.review()

    def test_metadata_transport_is_complete_hash_checked_and_bounded(self):
        result = self.review()
        # 確保真的有多片，少一片的反例不能只退化成既有的空清單測試。
        result['fixture_metadata'] = ''.join(hashlib.sha256(str(i).encode()).hexdigest() for i in range(96))
        parts = subject.encoded_parts(result)
        self.assertGreater(len(parts), 1)
        self.assertEqual(subject.decode_parts(parts[::-1]), result)
        with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), contextlib.redirect_stdout(io.StringIO()) as stdout:
            subject.publish(result)
        self.assertTrue(all(len(line.encode())<3900 for line in stdout.getvalue().splitlines()))
        self.assertIn('candidate-review-part', stdout.getvalue())
        for broken in ([], parts[:-1], parts+[parts[0]],
                       [dict(parts[0], part=len(parts)+1), *parts[1:]],
                       [dict(parts[0], sha256='0'*64), *parts[1:]],
                       [dict(parts[0], source_commit='f'*40), *parts[1:]]):
            with self.assertRaises((ValueError, OSError)):
                subject.decode_parts(broken)

    def test_large_metadata_is_paginated_without_dropping_any_part(self):
        result = self.review()
        result['fixture_metadata'] = ''.join(hashlib.sha256(str(i).encode()).hexdigest() for i in range(900))
        parts = subject.encoded_parts(result)
        self.assertGreater(len(parts), 8)
        collected = []
        for page in range(5):
            with patch.dict(os.environ, {'GITHUB_ACTIONS':'true'}), contextlib.redirect_stdout(io.StringIO()) as out:
                subject.publish(result, page)
            lines = out.getvalue().splitlines()
            self.assertLessEqual(len(lines), 8)
            collected.extend(json.loads(line.split('::', 2)[2]) for line in lines)
        self.assertEqual(subject.decode_parts(collected), result)
        with self.assertRaisesRegex(ValueError, 'bounded'):
            subject.publish(result, 5)

    def test_large_full_provenance_has_a_separate_bounded_input_budget(self):
        # CPU 原報告含 ZIP 逐檔資料及冗長授權宣告，不能套用精簡 metadata 的上限。
        self.report['fixture_padding'] = 'a'*9000
        self.save(self.reports/'bundle-provenance.json', self.report)
        with patch.object(subject, 'MAX_JSON', 8192), patch.object(subject, 'MAX_SOURCE_REPORT', 16384):
            result = self.review()
            self.assertEqual(subject.decode_parts(subject.encoded_parts(result)), result)
            self.report['fixture_padding'] = 'a'*20000
            self.save(self.reports/'bundle-provenance.json', self.report)
            with self.assertRaisesRegex(ValueError, 'oversized'):
                self.review()

    def test_replay_detects_relabelled_rows_or_changed_source(self):
        result = self.review()
        result['classification']['files'][0]['status'] = 'gap'
        with self.assertRaisesRegex(ValueError, 'Replayed'):
            subject.replay(result, self.repo)
        result = self.review()
        result['classification_input']['report']['source_commit'] = 'f'*40
        with self.assertRaisesRegex(ValueError, 'source differs'):
            subject.replay(result, self.repo)

    def test_transport_refuses_approval_flags_or_excessive_payload(self):
        result = self.review()
        result['release_ready'] = True
        with self.assertRaisesRegex(ValueError, 'unapproved'):
            subject.encoded_parts(result)
        result['release_ready'] = False
        with patch.object(subject, 'MAX_JSON', 10):
            with self.assertRaisesRegex(ValueError, 'limit'):
                subject.encoded_parts(result)

    def test_cli_refuses_overwrite_and_can_replay_preserved_input(self):
        script = str(Path(subject.__file__))
        command = [sys.executable, script, '--repo', str(self.repo), '--profile','base',
                   '--bundle', str(self.bundle), '--reports', str(self.reports),
                   '--package-directory', str(self.package), '--expected-source', self.commit]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        before = (self.reports/'source-review.json').read_bytes()
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual((self.reports/'source-review.json').read_bytes(), before)
        replay = subprocess.run([sys.executable, script, '--repo', str(self.repo), '--replay',
                                str(self.reports/'source-review.json')], capture_output=True, text=True)
        self.assertEqual(replay.returncode, 0, replay.stderr)


if __name__ == '__main__':
    unittest.main()

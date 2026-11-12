"""未對照來源分類的證據優先序與反例；僅使用合成報告、合成 ZIP 與臨時 Git 樹。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import classify_unresolved_sources as subject


def digest(body):
    return hashlib.sha256(body).hexdigest()


def entry(path, body, role='data-or-generated', reasons=(subject.UNRESOLVED,)):
    return dict(path=path, bytes=len(body), sha256=digest(body), role=role, review_reasons=list(reasons))


def report(files, native=(), packages=(('demo-pkg', '1.2.3'),)):
    return dict(profile='base', source_commit='0' * 40, source_version='0.0.0',
                packages=[dict(name=name, version=version) for name, version in packages],
                native_files=list(native),
                candidate_inventory=dict(files=list(files), summary=dict(unresolved_files=sum(
                    subject.UNRESOLVED in item['review_reasons'] for item in files))))


def native(file, body, origin):
    return dict(file=file, origin=origin, source_sha256=digest(body), bundled_sha256=digest(body))


class ClassificationTests(unittest.TestCase):
    def classify(self, files, **indexes):
        rows = subject.classify(report(files, native=indexes.pop('native', ())), indexes.get('blobs', {}),
                                indexes.get('members', {}), indexes.get('models', {}), indexes.get('payload', {}))
        return {row['path']: row for row in rows}

    def test_only_unresolved_files_are_classified(self):
        rows = self.classify([entry('a.txt', b'a'), entry('b.txt', b'b', reasons=())])
        self.assertEqual(list(rows), ['a.txt'])

    def test_hash_evidence_is_preferred_in_documented_order(self):
        body = b'same bytes'
        rows = self.classify([entry('_internal/x.dll', body, role='native-binary')],
                             blobs={digest(body): ['docs/x']}, members={digest(body): 'm'},
                             native=[native('x.dll', body, 'system-native')])
        self.assertEqual((rows['_internal/x.dll']['category'], rows['_internal/x.dll']['status']),
                         ('repo-blob', 'confirmed'))
        rows = self.classify([entry('_internal/x.dll', body)], members={digest(body): 'm'},
                             models={digest(body): 'eng'}, payload={digest(body): 'p'})
        self.assertEqual(rows['_internal/x.dll']['category'], 'ci-artifact-member')
        rows = self.classify([entry('m', body)], models={digest(body): 'eng'}, payload={digest(body): 'p'})
        self.assertEqual(rows['m']['category'], 'pinned-model')
        rows = self.classify([entry('m', body)], payload={digest(body): 'p'})
        self.assertEqual(rows['m']['category'], 'project-native-payload')

    def test_empty_file_is_not_attributed_and_nearest_repo_path_is_listed_first(self):
        rows = self.classify([entry('_internal/pkg/__init__.py', b''), entry('_internal/licenses/pkg/LICENSE', b'text')],
                             blobs={digest(b''): ['docs/log.txt'],
                                    digest(b'text'): ['docs/old/LICENSE', 'src/data/licenses/pkg/LICENSE', 'src/other/LICENSE']})
        self.assertEqual((rows['_internal/pkg/__init__.py']['category'], rows['_internal/pkg/__init__.py']['evidence']),
                         ('empty-file', []))
        self.assertEqual(rows['_internal/licenses/pkg/LICENSE']['evidence'],
                         ['src/data/licenses/pkg/LICENSE', 'src/other/LICENSE', 'docs/old/LICENSE'])

    def test_system_native_names_are_only_candidates(self):
        files = [entry('_internal/ucrtbase.dll', b'u', role='native-binary'),
                 entry('_internal/libcrypto-3-x64.dll', b'c', role='native-binary'),
                 entry('_internal/mystery.dll', b'm', role='native-binary')]
        rows = self.classify(files, native=[native('ucrtbase.dll', b'u', 'system-native'),
                                            native('libcrypto-3-x64.dll', b'c', 'system-native'),
                                            native('mystery.dll', b'm', 'system-native')])
        self.assertEqual(rows['_internal/ucrtbase.dll']['status'], 'candidate')
        self.assertIn('未驗', rows['_internal/ucrtbase.dll']['note'])
        self.assertEqual(rows['_internal/libcrypto-3-x64.dll']['status'], 'candidate')
        self.assertEqual(rows['_internal/mystery.dll']['status'], 'gap')

    def test_python_runtime_requires_unchanged_hash(self):
        good, changed = native('a.pyd', b'a', 'python-runtime'), native('b.pyd', b'b', 'python-runtime')
        changed['bundled_sha256'] = digest(b'other')
        rows = self.classify([entry('_internal/a.pyd', b'a'), entry('_internal/b.pyd', b'b')], native=[good, changed])
        self.assertEqual(rows['_internal/a.pyd']['status'], 'origin-known')
        self.assertEqual(rows['_internal/b.pyd']['status'], 'gap')

    def test_record_must_match_package_table_version(self):
        rows = self.classify([entry('_internal/demo_pkg-1.2.3.dist-info/RECORD', b'r'),
                              entry('_internal/demo_pkg-9.9.9.dist-info/RECORD', b's'),
                              entry('_internal/other/RECORD', b't')])
        self.assertEqual(rows['_internal/demo_pkg-1.2.3.dist-info/RECORD']['status'], 'confirmed')
        self.assertEqual(rows['_internal/demo_pkg-9.9.9.dist-info/RECORD']['status'], 'gap')
        self.assertEqual(rows['_internal/other/RECORD']['category'], 'unknown')

    def test_generated_archive_and_unknown_are_never_confirmed(self):
        rows = self.classify([entry('_internal/desktop_app/data/third-party.md', b'g'),
                              entry('_internal/worker-assets/python-runtime/LICENSE.txt', b'l'),
                              entry('_internal/base_library.zip', b'z', role='archive'),
                              entry('_internal/whatever.bin', b'w')])
        self.assertEqual(rows['_internal/desktop_app/data/third-party.md']['status'], 'origin-known')
        self.assertEqual(rows['_internal/worker-assets/python-runtime/LICENSE.txt']['category'], 'cpython-license-text')
        self.assertEqual(rows['_internal/base_library.zip']['status'], 'gap')
        self.assertEqual((rows['_internal/whatever.bin']['category'], rows['_internal/whatever.bin']['status']),
                         ('unknown', 'gap'))


class EndToEndTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.repo = self.root / 'repo'
        (self.repo / 'src/desktop_app/data').mkdir(parents=True)
        (self.repo / 'notice.txt').write_bytes(b'original notice\r\n')
        (self.repo / subject.MODEL_MANIFEST).write_text(json.dumps(dict(files={'eng.traineddata': digest(b'model')})))
        self.git('init', '-q')
        # 關閉換行轉換，確認比對的是 commit 內的原位元組。
        self.git('-c', 'core.autocrlf=false', 'add', '-A')
        self.git('-c', 'user.name=test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false',
                 'commit', '-q', '-m', 'fixture')
        self.commit = self.git('rev-parse', 'HEAD').strip()

    def git(self, *arguments):
        return subprocess.run(['git', '-C', str(self.repo), *arguments], check=True, capture_output=True,
                              text=True).stdout

    def archive(self, files):
        data = report(files)
        data['source_commit'] = self.commit
        path = self.root / 'windows-base-validation-reports.zip'
        with zipfile.ZipFile(path, 'w') as archive:
            archive.writestr('bundle-provenance.json', json.dumps(data))
            archive.writestr('acceptance/native-payload.json',
                             json.dumps(dict(files={'bin/tool.exe': dict(sha256=digest(b'tool'))})))
            archive.writestr('acceptance/build-profile.json', json.dumps(dict(python='3.12.0')))
            archive.writestr('installer/catalog.json', b'catalog')
        return path

    def test_git_artifact_model_and_payload_indexes(self):
        path = self.archive([entry('_internal/notice.txt', b'original notice\r\n'),
                             entry('catalog.json', b'catalog'), entry('eng.traineddata', b'model'),
                             entry('tool.exe', b'tool'), entry('unknown', b'?')])
        raw, data, blobs, members, models, payload = subject.load(path, self.repo)
        result = subject.summarize('base', path, raw, data, subject.classify(data, blobs, members, models, payload))
        self.assertTrue(result['accepted'])
        self.assertEqual(result['by_category'], {'ci-artifact-member': 1, 'pinned-model': 1,
                                                 'project-native-payload': 1, 'repo-blob': 1, 'unknown': 1})
        self.assertEqual(result['remaining_gap_or_candidate'], 1)
        self.assertEqual(result['report_sha256'], digest(raw))
        for flag in ('runtime_sbom_complete', 'redistribution_approved', 'release_ready'):
            self.assertIs(result[flag], False)

    def test_count_mismatch_is_not_accepted(self):
        path = self.archive([entry('unknown', b'?')])
        raw, data, blobs, members, models, payload = subject.load(path, self.repo)
        data['candidate_inventory']['summary']['unresolved_files'] = 2
        result = subject.summarize('base', path, raw, data, subject.classify(data, blobs, members, models, payload))
        self.assertFalse(result['accepted'])

    def test_cli_refuses_to_overwrite_existing_output(self):
        path = self.archive([entry('unknown', b'?')])
        output = self.root / 'out.json'
        command = [sys.executable, str(Path(subject.__file__)), '--profile', 'base', '--archive', str(path),
                   '--repo', str(self.repo), '--output', str(output)]
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        before = output.read_bytes()
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(output.read_bytes(), before)


if __name__ == '__main__':
    unittest.main()

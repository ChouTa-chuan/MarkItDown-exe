"""清理收據與變更／替換／連結反例；Linux 測試不當作 Windows handle 刪除證據。"""
from dataclasses import asdict
from pathlib import Path
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import base_temporary_cleanup as temporary


class TemporaryCleanupTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(); self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)/'中文 空格'; self.root.mkdir()
        self.path = self.root/'is-ABC123XYZ0.tmp'; self.path.write_bytes(b'owned installer fixture')

    def capture(self, **changes):
        options = dict(pid=41, stage='first-file', setup_sha256='a'*64, parents={'.'}, protected=set())
        options.update(changes)
        return temporary.capture(self.root, set(), {self.path.name}, **options)

    def test_exact_in_memory_receipt_keeps_original_and_validates(self):
        receipts = self.capture()
        self.assertEqual(receipts[0].path, self.path.name)
        self.assertTrue(temporary.validate_receipts(self.root, receipts))
        self.assertEqual(self.path.read_bytes(), b'owned installer fixture')

    def test_preexisting_case_alias_is_not_owned(self):
        self.assertEqual(temporary.capture(self.root, {self.path.name.upper()}, {self.path.name},
            pid=41, stage='intent', setup_sha256='a'*64, parents={'.'}, protected=set()), [])

    def test_payload_named_like_temporary_is_protected(self):
        with self.assertRaisesRegex(ValueError, 'scope'):
            self.capture(protected={self.path.name.upper()})
        self.assertTrue(self.path.is_file())

    def test_unobserved_files_are_not_added_to_receipt(self):
        unknown = self.root/'is-USER123456.tmp'; unknown.write_bytes(self.path.read_bytes())
        self.assertEqual([item.path for item in self.capture()], [self.path.name])
        self.assertEqual(unknown.read_bytes(), self.path.read_bytes())

    def test_invalid_owner_or_checkpoint_cannot_create_receipt(self):
        for options in [dict(pid=0), dict(pid=True), dict(stage='arbitrary'), dict(setup_sha256='bad')]:
            with self.subTest(options=options), self.assertRaises(ValueError): self.capture(**options)

    def test_unknown_parent_or_unsafe_path_is_rejected(self):
        with self.assertRaises(ValueError): self.capture(parents={'elsewhere'})
        for name in ['../is-ABC123XYZ0.tmp', '/is-ABC123XYZ0.tmp', 'folder\\is-ABC123XYZ0.tmp']:
            with self.subTest(name=name), self.assertRaises(ValueError):
                temporary.capture(self.root, set(), {name}, pid=41, stage='intent',
                    setup_sha256='a'*64, parents={'.'}, protected=set())

    def test_changed_bytes_and_same_bytes_replacement_are_rejected(self):
        receipts = self.capture(); raw = self.path.read_bytes()
        self.path.write_bytes(b'changed user document')
        with self.assertRaises(ValueError): temporary.validate_receipts(self.root, receipts)
        self.path.write_bytes(raw); receipts = self.capture()
        self.path.rename(self.root/'original-kept.bin'); self.path.write_bytes(raw)
        with self.assertRaises(ValueError): temporary.validate_receipts(self.root, receipts)
        self.assertEqual(self.path.read_bytes(), raw)

    def test_hard_link_and_symlink_do_not_grant_cleanup_ownership(self):
        alias = self.root/'link.bin'; os.link(self.path, alias)
        with self.assertRaises(ValueError): self.capture()
        alias.unlink(); target = self.root/'outside.bin'; target.write_bytes(b'user document')
        self.path.unlink(); self.path.symlink_to(target)
        with self.assertRaises(RuntimeError): self.capture()
        self.assertEqual(target.read_bytes(), b'user document')

    def test_serialized_duplicate_or_other_root_receipt_is_rejected(self):
        receipts = self.capture()
        for values in [[asdict(receipts[0])], receipts*2]:
            with self.assertRaises(ValueError): temporary.validate_receipts(self.root, values)
        with self.assertRaises(ValueError): temporary.validate_receipts(self.root.parent, receipts)

    def test_missing_file_is_not_silently_reported_as_cleaned(self):
        receipts = self.capture(); self.path.unlink()
        with self.assertRaises(OSError): temporary.validate_receipts(self.root, receipts)

    def test_non_windows_or_non_ci_cannot_delete(self):
        receipts = self.capture()
        for platform, environment in [('linux', {'GITHUB_ACTIONS':'true','RUNNER_OS':'Windows'}),
                                      ('win32', {'GITHUB_ACTIONS':'false','RUNNER_OS':'Windows'})]:
            with patch.object(temporary.sys, 'platform', platform), patch.dict(os.environ, environment), \
                 patch.object(temporary, '_mark_deleted') as delete:
                with self.assertRaises(RuntimeError): temporary.cleanup(self.root, receipts, quiescent=lambda: True)
                delete.assert_not_called()
        self.assertTrue(self.path.exists())

    def test_running_process_stops_before_any_deletion_handle(self):
        receipts = self.capture()
        with patch.object(temporary.sys, 'platform', 'win32'), \
             patch.dict(os.environ, {'GITHUB_ACTIONS':'true','RUNNER_OS':'Windows'}), \
             patch.object(temporary, '_windows_reader') as opened:
            with self.assertRaisesRegex(RuntimeError, 'not exited'):
                temporary.cleanup(self.root, receipts, quiescent=lambda: False)
            opened.assert_not_called()

    def test_second_file_failure_prevents_first_file_deletion(self):
        receipts = self.capture(); other = self.root/'is-DEF456XYZ0.tmp'; other.write_bytes(b'second')
        receipts += temporary.capture(self.root, set(), {other.name}, pid=42, stage='payload-written',
                                      setup_sha256='b'*64, parents={'.'}, protected=set())
        other.write_bytes(b'changed')
        with patch.object(temporary.sys, 'platform', 'win32'), \
             patch.dict(os.environ, {'GITHUB_ACTIONS':'true','RUNNER_OS':'Windows'}), \
             patch.object(temporary, '_windows_reader', side_effect=lambda path: path.open('rb')), \
             patch.object(temporary, '_mark_deleted') as delete:
            with self.assertRaises(ValueError): temporary.cleanup(self.root, receipts, quiescent=lambda: True)
            delete.assert_not_called()
        self.assertEqual(self.path.read_bytes(), b'owned installer fixture')

    def test_swap_after_preflight_is_rejected_before_marking(self):
        receipts = self.capture(); calls = []
        def reader(path):
            calls.append(path)
            if len(calls) == 2: path.write_bytes(b'swapped after preflight')
            return path.open('rb')
        with patch.object(temporary.sys, 'platform', 'win32'), \
             patch.dict(os.environ, {'GITHUB_ACTIONS':'true','RUNNER_OS':'Windows'}), \
             patch.object(temporary, '_windows_reader', side_effect=reader), \
             patch.object(temporary, '_mark_deleted') as delete:
            with self.assertRaises(ValueError): temporary.cleanup(self.root, receipts, quiescent=lambda: True)
            delete.assert_not_called()
        self.assertEqual(self.path.read_bytes(), b'swapped after preflight')

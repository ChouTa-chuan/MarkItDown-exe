import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from desktop_app.settings import Settings, load_settings, save_settings


class SettingsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.path = Path(directory.name) / "中文設定.json"

    def test_round_trip(self):
        settings = Settings(ram_budget_mib=768, reserve_mib=1024, resource_wait_seconds=5)
        save_settings(settings, self.path)
        self.assertEqual(load_settings(self.path), settings)
        self.assertEqual(settings.policy().budget, 768*1024**2)

    def test_failed_save_preserves_existing(self):
        save_settings(Settings(), self.path)
        previous = self.path.read_bytes()
        with patch("desktop_app.settings.os.replace", side_effect=OSError("disk failure")):
            with self.assertRaises(OSError):
                save_settings(Settings(reserve_mib=0), self.path)
        self.assertEqual(self.path.read_bytes(), previous)
        self.assertEqual(list(self.path.parent.glob(".settings-*")), [])

    def test_future_version_not_overwritten(self):
        self.path.write_text('{"schema_version": 2}')
        with self.assertRaises(ValueError):
            load_settings(self.path)
        self.assertEqual(json.loads(self.path.read_text())["schema_version"], 2)

    def test_bad_values(self):
        for kwargs in [{"ram_budget_mib": True}, {"reserve_mib": -1},
                       {"resource_wait_seconds": float("nan")},
                       {"resource_wait_seconds": float("inf")}, {"schema_version": True}]:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Settings(**kwargs)

    def test_invalid_file_not_silently_reset(self):
        for content in ['[]', '{}', '{"schema_version":1,"unknown":5}', 'broken']:
            self.path.write_text(content)
            with self.subTest(content=content), self.assertRaises(ValueError):
                load_settings(self.path)

    def test_missing_explicit_file_is_error(self):
        with self.assertRaises(FileNotFoundError):
            load_settings(self.path)

    def test_oversized_file(self):
        self.path.write_text(" "*65537)
        with self.assertRaises(ValueError):
            load_settings(self.path)

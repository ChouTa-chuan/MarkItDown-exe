import hashlib
import io
from pathlib import Path
import tempfile
from threading import Event
import unittest
from unittest.mock import patch

from desktop_app import models
from desktop_app.core import Cancelled


class ModelsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        self.content = b"verified model fixture"
        self.spec = {"commit":"test", "files":{"eng.traineddata":hashlib.sha256(self.content).hexdigest()}}
        mocked = patch("desktop_app.models.manifest", return_value=self.spec)
        mocked.start()
        self.addCleanup(mocked.stop)

    def opener(self, url, timeout):
        self.assertTrue(url.startswith("https://raw.githubusercontent.com/"))
        self.assertEqual(timeout, 10)
        return io.BytesIO(self.content)

    def test_download_and_reuse_without_network(self):
        models.install(self.root, opener=self.opener)
        self.assertEqual(models.inspect(self.root), {"eng.traineddata":"valid"})
        models.install(self.root, opener=lambda *a, **k:self.fail("Unexpected network request"))

    def test_bad_download_never_published(self):
        with self.assertRaisesRegex(ValueError, "完整性"):
            models.install(self.root, opener=lambda *a, **k:io.BytesIO(b"corrupt"))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_corrupt_existing_preserved(self):
        path = self.root / "eng.traineddata"
        path.write_bytes(b"user data")
        with self.assertRaises(ValueError):
            models.install(self.root, opener=self.opener)
        self.assertEqual(path.read_bytes(), b"user data")
        self.assertEqual(models.inspect(self.root)[path.name], "corrupt")

    def test_cancel_during_read_cleans_partial_file(self):
        cancel = Event()
        class Response(io.BytesIO):
            def read(self, size):
                cancel.set()
                return super().read(size)
        with self.assertRaises(Cancelled):
            models.install(self.root, cancel, opener=lambda *a, **k:Response(self.content))
        self.assertEqual(list(self.root.iterdir()), [])

    def test_network_error_cleans_file(self):
        class Response(io.BytesIO):
            def read(self, size):
                raise TimeoutError("connection timed out")
        with self.assertRaises(TimeoutError):
            models.install(self.root, opener=lambda *a, **k:Response())
        self.assertEqual(list(self.root.iterdir()), [])

    def test_remove_preserves_unknown_files(self):
        models.install(self.root, opener=self.opener)
        unknown = self.root/"notes.txt"
        unknown.write_text("user file")
        models.remove(self.root)
        self.assertEqual(list(self.root.iterdir()), [unknown])

    def test_remove_corrupt_file_refuses(self):
        target = self.root/"eng.traineddata"
        target.write_text("modified")
        with self.assertRaises(ValueError):
            models.remove(self.root)
        self.assertTrue(target.exists())


class PackagedManifestTests(unittest.TestCase):
    def test_manifest_available_and_pinned(self):
        spec = models.manifest()
        self.assertEqual(len(spec["commit"]), 40)
        self.assertEqual(set(spec["files"]), {"chi_tra.traineddata", "eng.traineddata", "LICENSE"})
        self.assertTrue(all(len(value)==64 for value in spec["files"].values()))

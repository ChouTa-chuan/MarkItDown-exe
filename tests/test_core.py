import tempfile
import unittest
from pathlib import Path
from threading import Event

from desktop_app.application import Runner
from desktop_app.conversion import convert_text
from desktop_app.core import Cancelled, Request, State, UnsupportedFormat
from desktop_app.planning import analyze
from desktop_app.resources import MIB, Policy, Snapshot, snapshot


def roomy():
    return Snapshot(8192*MIB, 4096*MIB, 100*MIB)


class CoreTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.source = self.root / "繁體中文.txt"
        self.source.write_bytes(b"\xef\xbb\xbf" + ("測試\r\n內容\n" * 20000).encode())
        self.destination = self.root / "結果.md"
        self.request = Request(self.source, self.destination)
        self.policy = Policy(budget=1024*MIB, reserve=128*MIB)

    def runner(self, **kwargs):
        return Runner(self.policy, read_snapshot=kwargs.pop("read_snapshot", roomy),
                      poll_seconds=0.01, max_resource_wait=1, **kwargs)

    def test_streaming_and_spawn_preserve_text(self):
        result = self.runner().run(self.request)
        self.assertEqual(result.state, State.COMPLETED, result.message)
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes()[3:])
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    def test_destination_not_overwritten(self):
        self.destination.write_text("original")
        result = self.runner().run(self.request)
        self.assertEqual(result.state, State.FAILED)
        self.assertEqual(self.destination.read_text(), "original")

    def test_publication_race_does_not_overwrite(self):
        def progress(stage):
            if stage == "提交輸出":
                self.destination.write_text("other task")
        with self.assertRaises(FileExistsError):
            convert_text(self.request, lambda: None, progress)
        self.assertEqual(self.destination.read_text(), "other task")
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    def test_invalid_encoding_cleans_partial_file(self):
        self.source.write_bytes(b"\xffinvalid")
        result = self.runner().run(self.request)
        self.assertEqual(result.state, State.FAILED)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    def test_cancel_before_start(self):
        cancel = Event()
        cancel.set()
        self.assertEqual(self.runner().run(self.request, cancel).state, State.CANCELLED)
        self.assertFalse(self.destination.exists())

    def test_cancel_at_checkpoint_cleans_file(self):
        calls = 0
        def checkpoint():
            nonlocal calls
            calls += 1
            if calls == 3:
                raise Cancelled()
        with self.assertRaises(Cancelled):
            convert_text(self.request, checkpoint)
        self.assertFalse(self.destination.exists())
        self.assertEqual(list(self.root.glob(".conversion-*")), [])

    def test_memory_pressure_recovers_before_spawn(self):
        reads = iter([Snapshot(8192*MIB, 0, 100*MIB), roomy()])
        states = []
        def read():
            return next(reads, roomy())
        result = self.runner(read_snapshot=read).run(
            self.request, notify=lambda state, message: states.append(state))
        self.assertEqual(result.state, State.COMPLETED, result.message)
        self.assertIn(State.PAUSED, states)

    def test_low_memory_times_out_without_output(self):
        runner = Runner(self.policy, lambda: Snapshot(8192*MIB, 0, 100*MIB),
                        poll_seconds=0.01, max_resource_wait=0)
        result = runner.run(self.request)
        self.assertEqual(result.state, State.FAILED)
        self.assertIn("等待逾時", result.message)
        self.assertFalse(self.destination.exists())

    def test_running_worker_pauses_and_resumes(self):
        states = []
        running = False
        pressure_reads = 0
        def notify(state, message):
            nonlocal running
            states.append(state)
            if state == State.RUNNING:
                running = True
        def read():
            nonlocal pressure_reads
            if running and pressure_reads < 10:
                pressure_reads += 1
                return Snapshot(8192*MIB, 0, 100*MIB)
            return roomy()
        result = self.runner(read_snapshot=read).run(self.request, notify=notify)
        self.assertEqual(result.state, State.COMPLETED, result.message)
        paused_index = states.index(State.PAUSED)
        self.assertIn(State.RUNNING, states[paused_index + 1:])
        self.assertEqual(self.destination.read_bytes(), self.source.read_bytes()[3:])

    def test_batch_continues_after_failure(self):
        missing = Request(self.root / "missing.txt", self.root / "missing.md")
        outcomes = list(self.runner().batch([missing, self.request]))
        self.assertEqual([x.state for x in outcomes], [State.FAILED, State.COMPLETED])

    def test_unknown_format_fails_explicitly(self):
        source = self.root / "sample.unknown"
        source.write_bytes(b"unknown")
        with self.assertRaises(UnsupportedFormat):
            analyze(Request(source, self.destination))

    def test_source_cannot_be_destination(self):
        with self.assertRaises(ValueError):
            analyze(Request(self.source, self.source))


class ResourceTests(unittest.TestCase):
    def test_budget_includes_existing_process_usage(self):
        self.assertFalse(Policy(budget=105*MIB, reserve=0).admit(roomy(), 8*MIB)[0])

    def test_hysteresis_prevents_early_resume(self):
        policy = Policy(budget=1024*MIB, reserve=128*MIB, resume_margin=64*MIB)
        current = Snapshot(8192*MIB, 150*MIB, 100*MIB)
        self.assertTrue(policy.admit(current, 8*MIB)[0])
        self.assertFalse(policy.admit(current, 8*MIB, resuming=True)[0])

    def test_real_process_memory_monitor(self):
        current = snapshot()
        self.assertGreater(current.total, 0)
        self.assertGreater(current.application, 0)

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            Policy(budget=0)


if __name__ == "__main__":
    unittest.main()

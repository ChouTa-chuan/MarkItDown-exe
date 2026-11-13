"""混合回歸 driver 的接受條件；使用合成結果，不遞迴執行整個測試集。"""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.suite import _ErrorHolder

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_mixed_regression as subject


def Sample():
    """回傳合成的 TestCase 實例；類別定義在函式內，避免被 discovery 當成真正的測試。"""
    class Synthetic(unittest.TestCase):
        def runTest(self):
            pass
    return Synthetic()


def known():
    case = Sample()
    case.id = lambda: subject.KNOWN_EXPECTED_FAILURE
    return case


def result(run, expected=True, **parts):
    value = unittest.TestResult()
    value.testsRun = run
    if expected:
        value.expectedFailures.append((known(), 'trace'))
    for name, items in parts.items():
        getattr(value, name).extend(items)
    return value


class SummaryTests(unittest.TestCase):
    def test_exact_count_with_only_known_expected_failure_is_accepted(self):
        summary = subject.summarize(result(5), 5)
        self.assertTrue(summary['accepted'])
        self.assertEqual((summary['run'], summary['passed']), (5, 4))

    def test_count_skip_and_missing_expected_failure_are_rejected(self):
        self.assertFalse(subject.summarize(result(4), 5)['accepted'])
        self.assertFalse(subject.summarize(result(5, skipped=[(Sample(), 'no tool')]), 5)['accepted'])
        self.assertFalse(subject.summarize(result(5, expected=False), 5)['accepted'])
        self.assertFalse(subject.summarize(result(5, unexpectedSuccesses=[Sample()]), 5)['accepted'])

    def test_load_errors_are_reported_separately_and_never_counted_as_passed(self):
        summary = subject.summarize(result(5, errors=[(_ErrorHolder('setUpClass (x.Y)'), 'trace'),
                                                      (Sample(), 'trace')]), 5)
        self.assertFalse(summary['accepted'])
        self.assertEqual(summary['load_errors'], ['setUpClass (x.Y)'])
        self.assertEqual(len(summary['errors']), 1)
        self.assertEqual(summary['passed'], 3)

    def test_cli_refuses_existing_output_before_running_tests(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / 'result.json'
            output.write_text('kept')
            done = subprocess.run([sys.executable, subject.__file__, '--expected-count', '1', '--output', str(output)],
                                  capture_output=True, timeout=60)
            self.assertNotEqual(done.returncode, 0)
            self.assertEqual(output.read_text(), 'kept')


if __name__ == '__main__':
    unittest.main()

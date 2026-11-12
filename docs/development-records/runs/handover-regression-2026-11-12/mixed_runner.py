"""混合程序完整回歸 driver：輸出原始 unittest 計數，不依賴日誌中的 OK 字樣。"""
import json
import sys
import unittest
from pathlib import Path


def main():
    sys.path.insert(0, str(Path.cwd() / 'scripts'))
    from check_isolated_tests import KNOWN_EXPECTED_FAILURE
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests'))
    expected = [test.id() for test, _ in result.expectedFailures]
    summary = dict(
        run=result.testsRun,
        failures=[test.id() for test, _ in result.failures],
        errors=[test.id() for test, _ in result.errors],
        skipped=[[test.id(), reason] for test, reason in result.skipped],
        expected_failures=expected,
        unexpected_successes=[test.id() for test in result.unexpectedSuccesses])
    summary['passed'] = (result.testsRun - len(result.failures) - len(result.skipped) - len(expected)
                         - len(result.unexpectedSuccesses)
                         - sum(1 for test, _ in result.errors if not test.id().startswith('setUpClass')))
    summary['accepted'] = (result.testsRun == 684 and result.wasSuccessful() and not result.skipped
                           and expected == [KNOWN_EXPECTED_FAILURE])
    Path(sys.argv[1]).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if summary['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

"""單一程序完整回歸 driver：輸出原始 unittest 計數並以真正的 exit code 表示是否接受。

責任與限制：
- 與 check_isolated_tests.py（逐模組獨立程序）互補；兩者都通過才算完整回歸。
- 接受條件固定為：執行數等於 --expected-count、沒有 failure／error／skip／非預期成功，
  且預期失敗恰為既有的 ONNX 繁中品質缺口。預期失敗不是品質通過。
- setUpClass 等載入錯誤不計入 run；摘要另列 load_errors，避免把「沒執行」誤讀成「通過」。
- 測試以 spawn 啟動子程序，入口必須留在 __main__ 保護內。
用法（repo 根目錄）：PYTHONPATH=src:tests python scripts/run_mixed_regression.py --expected-count N --output result.json
"""
import argparse
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from check_isolated_tests import KNOWN_EXPECTED_FAILURE


def summarize(result, expected_count):
    """把 unittest 結果轉成可保存的摘要；passed 只計算真正執行且成功的方法。"""
    expected = [test.id() for test, _ in result.expectedFailures]
    load_errors = [test.id() for test, _ in result.errors if not isinstance(test, unittest.TestCase)]
    method_errors = [test.id() for test, _ in result.errors if isinstance(test, unittest.TestCase)]
    summary = dict(
        expected_count=expected_count, run=result.testsRun,
        failures=[test.id() for test, _ in result.failures],
        errors=method_errors, load_errors=load_errors,
        skipped=[[test.id(), reason] for test, reason in result.skipped],
        expected_failures=expected,
        unexpected_successes=[test.id() for test in result.unexpectedSuccesses])
    summary['passed'] = (result.testsRun - len(summary['failures']) - len(method_errors)
                         - len(summary['skipped']) - len(expected) - len(summary['unexpected_successes']))
    summary['accepted'] = (result.testsRun == expected_count and result.wasSuccessful()
                           and not summary['skipped'] and expected == [KNOWN_EXPECTED_FAILURE])
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--expected-count', required=True, type=int)
    parser.add_argument('--output', required=True, type=Path, help='新的摘要 JSON；已存在則拒絕')
    arguments = parser.parse_args()
    if arguments.output.exists():
        parser.error('Output already exists; regression evidence is never overwritten')
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT / 'tests')))
    summary = summarize(result, arguments.expected_count)
    arguments.output.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: (len(value) if isinstance(value, list) else value) for key, value in summary.items()}))
    return 0 if summary['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

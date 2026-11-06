"""重跑元件基礎／遷移驗收並保存逐項結果；跳過不能列為驗收完成。"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RecordedResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passed_ids = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.passed_ids.append(test.id())


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--check', choices=('C01', 'C02'), default='C01')
    args = parser.parse_args()
    # 使用已安裝的套件，避免把原始碼路徑插入 sys.path 而掩蓋漏打包的新模組。
    sys.path.insert(0, str(ROOT / 'tests'))
    modules = ['test_components'] if args.check == 'C01' else [
        'test_component_migration', 'test_settings', 'test_models', 'test_desktop']
    suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    accepted = (result.wasSuccessful() and result.testsRun > 0 and not result.skipped
                and not result.expectedFailures and not result.unexpectedSuccesses)
    report = dict(recorded_at=datetime.now(timezone.utc).isoformat(),
                  source_version=importlib.metadata.version('markitdown-desktop'),
                  platform=platform.platform(), python=platform.python_version(),
                  check=args.check, accepted=accepted, run=result.testsRun,
                  passed=len(result.passed_ids), skipped=len(result.skipped),
                  failures=len(result.failures), errors=len(result.errors),
                  expected_failures=len(result.expectedFailures),
                  unexpected_successes=len(result.unexpectedSuccesses),
                  passed_tests=result.passed_ids,
                  fixture_scope=('Synthetic payloads, actual filesystem and SQLite; no downloads or engine inference'
                                 if args.check == 'C01' else
                                 'v1-v5 settings, SQLite schema migration, synthetic downloads, desktop text conversion, pinned local models and explicit OCR path checks'),
                  windows_executed=False, gpu_executed=False)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())

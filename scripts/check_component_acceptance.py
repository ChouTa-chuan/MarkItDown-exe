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
    parser.add_argument('--check', choices=('C01', 'C02', 'C03-languages', 'C04-locks', 'C04-build', 'C05', 'C06', 'C07', 'C08', 'C09-flow', 'C10'), default='C01')
    args = parser.parse_args()
    # 使用已安裝的套件，避免把原始碼路徑插入 sys.path 而掩蓋漏打包的新模組。
    sys.path.insert(0, str(ROOT / 'tests'))
    modules = {'C01':['test_components'],
               'C02':['test_component_migration', 'test_settings', 'test_models', 'test_desktop'],
               'C03-languages':['test_languages','test_onboarding','test_settings','test_component_migration',
                                'test_models','test_desktop','test_help_ui','test_core','test_pdf_pipeline'],
               'C04-locks':['test_packaging_profiles','test_license_inventory','test_formats','test_core','test_devices'],
               'C04-build':['test_build_profile','test_diagnostics','test_packaging_profiles','test_license_inventory',
                            'test_formats','test_core','test_devices','test_desktop','test_help_ui'],
               'C05':['test_component_downloads'],
               'C06':['test_component_lifecycle','test_component_downloads'],
               'C07':['test_component_workers','test_component_lifecycle','test_component_downloads'],
               'C08':['test_component_management','test_component_workers','test_component_lifecycle',
                      'test_component_downloads','test_desktop','test_help_ui'],
               'C09-flow':['test_onboarding','test_settings','test_component_migration','test_desktop','test_help_ui','test_core'],
               'C10':['test_managed_conversion','test_component_workers','test_component_lifecycle','test_component_downloads',
                      'test_component_management','test_desktop','test_help_ui','test_borderless','test_tables',
                      'test_table_continuation','test_pdf_pipeline','test_pdf_acceptance','test_devices']}[args.check]
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
                  fixture_scope={
                      'C01':'Synthetic payloads, actual filesystem and SQLite; no downloads or engine inference',
                      'C02':'v1-v5 settings, SQLite schema migration, synthetic downloads, desktop text conversion, pinned local models and explicit OCR path checks',
                      'C03-languages':'Four-language model/preference contracts, v1-v6 settings migration, Qt, local native health and PDF/core regression. New JA/KO model inference and full GUI/CLI acceptance reported separately; no bundled Windows native OCR.',
                      'C04-locks':'Offline Python runtime/build closure for Linux and Windows target markers, original Windows notices and actual core/format/device regressions. Clean isolated base venv acceptance reported separately; not native/frozen/Windows acceptance.',
                      'C04-build':'Embedded base profile, selected asset integrity and core/full self-test semantics; C04 closure, diagnostics, formats/core/device/Qt regressions. Actual frozen acceptance reported separately; full C04/native/Windows gates remain pending.',
                      'C05':'Real Ed25519, filesystem and SQLite; injected HTTP protocol cases, no native engine execution; actual HTTPS checked separately',
                      'C06':'Real ZIP/filesystem/SQLite/kernel locks and spawned process exits, synthetic model health; includes C05 regression, no Windows/GPU or native OCR worker acceptance',
                      'C07':'Versioned IPC, fault/resource fixtures and actual native CPU subprocess; C05/C06 regression included. Frozen isolated-runtime acceptance reported separately; no Windows/GPU',
                      'C08':'Actual Qt offscreen, signed catalog, ZIP/SQLite, synthetic model health and injected HTTP; desktop text and C05-C07 regressions. Separate real frozen CPU GUI acceptance; no Windows/GPU',
                      'C09-flow':'First-run flow, RAM advice, explicit path/preference/CAS protection, Qt and actual local CPU bilingual health; settings/migration/desktop/core regression. Does not close full C09 clean-base-install gate.',
                      'C10':'Managed PDF routing/leases/version/cancellation and fixture worker boundaries; C05-C08 regression and unchanged 63-check layout matrix. Separate actual frozen CPU/Qt managed conversion acceptance; no Windows/GPU.'
                  }[args.check],
                  windows_executed=False, gpu_executed=False)
    if args.check=='C09-flow':
        report['flow_accepted']=accepted
        report['full_c09_complete']=False
        report['base_ocr_bundled']=False
    if args.check in ('C04-locks','C04-build'):
        report['full_c04_complete']=False
        report['native_ocr_bundled']=False
    if args.check=='C03-languages':
        report['full_c03_complete']=False
        report['native_ocr_bundled']=False
    if args.check in ('C06', 'C07', 'C08', 'C10'):
        from test_component_lifecycle import PROCESS_OBSERVATIONS
        report['process_observations'] = PROCESS_OBSERVATIONS
        report['real_process_exit_checks'] = len(PROCESS_OBSERVATIONS)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return 0 if accepted else 1


if __name__ == '__main__':
    raise SystemExit(main())

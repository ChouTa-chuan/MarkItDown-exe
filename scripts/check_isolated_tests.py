"""逐模組執行全回歸，要求所有原生 child 正常結束；混合程序驗證另記。"""
import argparse
from importlib import metadata
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
KNOWN_EXPECTED_FAILURE='test_onnx_ocr.OnnxIntegrationTests.test_traditional_chinese_quality_known_gap'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--expected-count',type=int,required=True)
    parser.add_argument('--module')
    args=parser.parse_args()
    if args.module:
        import unittest
        sys.path.insert(0,str(ROOT/'tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName(args.module)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        value=dict(module=args.module,run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                   skipped=len(result.skipped),expected_failures=[test.id() for test,_ in result.expectedFailures],
                   unexpected_successes=len(result.unexpectedSuccesses),tests_reported_success=result.wasSuccessful())
        args.output.write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
        return 0 if result.wasSuccessful() and result.testsRun and not result.skipped else 1
    if args.expected_count<1 or args.output.exists():parser.error('Use a positive count and a fresh output directory')
    args.output.mkdir(parents=True)
    records=[]
    for path in sorted((ROOT/'tests').glob('test_*.py')):
        module=path.stem;report=args.output/(module+'.json')
        with (args.output/(module+'.log')).open('wb') as log:
            try:
                child=subprocess.run([sys.executable,__file__,'--module',module,'--expected-count',str(args.expected_count),
                      '--output',str(report)],cwd=ROOT,env={**os.environ,'PYTHONFAULTHANDLER':'1'},
                      stdout=log,stderr=subprocess.STDOUT,timeout=240)
                code=child.returncode
            except subprocess.TimeoutExpired:
                code='timeout'
        value=json.loads(report.read_text(encoding='utf-8')) if report.exists() else dict(module=module,run=0)
        value['process_exit']=code;records.append(value)
    count=sum(item['run'] for item in records)
    expected=[name for item in records for name in item.get('expected_failures',[])]
    failed=sum(item.get('failures',0)+item.get('errors',0)+item.get('skipped',0)+item.get('unexpected_successes',0) for item in records)
    accepted=(count==args.expected_count and expected==[KNOWN_EXPECTED_FAILURE] and all(item['process_exit']==0
              and item.get('tests_reported_success') and not item.get('skipped') for item in records))
    value=dict(scope='Actual per-module normal subprocess exits; mixed-process acceptance is recorded separately',
        source_version=metadata.version('markitdown-desktop'),modules=len(records),run=count,
        passed=count-len(expected)-failed,expected_failures=expected,accepted=accepted,
        all_child_exits_zero=all(item['process_exit']==0 for item in records),records=records)
    (args.output/'summary.json').write_text(json.dumps(value,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:item for key,item in value.items() if key!='records'}))
    return 0 if accepted else 1


if __name__=='__main__':raise SystemExit(main())

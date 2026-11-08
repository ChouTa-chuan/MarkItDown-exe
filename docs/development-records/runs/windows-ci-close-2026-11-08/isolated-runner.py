"""逐模組以真正子程序驗證原生擴充測試；不以 os._exit／強制終止繞過 teardown。"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--module')
    args=parser.parse_args()
    repo=args.repo.resolve()
    if args.module:
        import unittest
        sys.path.insert(0,str(repo/'tests'))
        suite=unittest.defaultTestLoader.loadTestsFromName(args.module)
        result=unittest.TextTestRunner(verbosity=2).run(suite)
        document=dict(module=args.module,run=result.testsRun,failures=len(result.failures),errors=len(result.errors),
            skipped=len(result.skipped),expected_failures=[test.id() for test,_ in result.expectedFailures],
            unexpected_successes=len(result.unexpectedSuccesses),tests_reported_success=result.wasSuccessful())
        args.output.write_text(json.dumps(document,indent=2)+'\n',encoding='utf-8')
        return 0 if result.wasSuccessful() and not result.skipped else 1
    if args.output.exists():raise FileExistsError(args.output)
    args.output.mkdir(parents=True)
    records=[]
    for path in sorted((repo/'tests').glob('test_*.py')):
        module=path.stem
        report=args.output/(module+'.json')
        with (args.output/(module+'.log')).open('wb') as log:
            # 每個 child 都必須正常結束；即使先印 OK，非零 process exit 一律不接受。
            child=subprocess.run([sys.executable,__file__,'--repo',str(repo),'--output',str(report),
                                  '--module',module],cwd=repo,env={**os.environ,'PYTHONFAULTHANDLER':'1'},
                                 stdout=log,stderr=subprocess.STDOUT,timeout=240)
        data=json.loads(report.read_text()) if report.exists() else dict(module=module,run=0)
        data['process_exit']=child.returncode
        records.append(data)
    count=sum(record['run'] for record in records)
    expected=[name for record in records for name in record.get('expected_failures',[])]
    accepted=(count==555 and len(expected)==1 and all(record['process_exit']==0
              and record.get('tests_reported_success') and not record.get('skipped') for record in records))
    document=dict(scope='Actual Linux per-module child processes; mixed-process teardown remains separately open; not Windows acceptance',
        modules=len(records),run=count,passed=count-len(expected),expected_failures=expected,
        accepted=accepted,all_child_exits_zero=all(record['process_exit']==0 for record in records),records=records)
    (args.output/'summary.json').write_text(json.dumps(document,indent=2)+'\n')
    print(json.dumps({key:value for key,value in document.items() if key!='records'}))
    return 0 if accepted else 1


if __name__=='__main__':raise SystemExit(main())

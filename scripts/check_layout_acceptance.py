"""重跑 PDF 版面驗收矩陣；跳過或品質預期失敗不能列為矩陣通過。"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
parser=argparse.ArgumentParser()
parser.add_argument('--report',type=Path,required=True)
parser.add_argument('--executable',type=Path,help='Run public fixtures through a built binary')
args=parser.parse_args()


class RecordedResult(unittest.TextTestResult):
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.records=[]

    def addSuccess(self,test):
        super().addSuccess(test);self.records.append({'test':test.id(),'outcome':'passed'})

    def addFailure(self,test,error):
        super().addFailure(test,error);self.records.append({'test':test.id(),'outcome':'failed'})

    def addError(self,test,error):
        super().addError(test,error);self.records.append({'test':test.id(),'outcome':'error'})

    def addSkip(self,test,reason):
        super().addSkip(test,reason);self.records.append({'test':test.id(),'outcome':'skipped','reason':reason})

    def addExpectedFailure(self,test,error):
        super().addExpectedFailure(test,error);self.records.append({'test':test.id(),'outcome':'expected_failure'})

    def addUnexpectedSuccess(self,test):
        super().addUnexpectedSuccess(test);self.records.append({'test':test.id(),'outcome':'unexpected_success'})


names=['test_borderless','test_tables','test_table_continuation','test_pdf_pipeline','test_pdf_acceptance']
if args.executable:
    executable=args.executable.resolve()
    os.environ['MARKITDOWN_ACCEPTANCE_EXECUTABLE']=str(executable)
    names=['test_pdf_acceptance']
else:
    os.environ.pop('MARKITDOWN_ACCEPTANCE_EXECUTABLE',None)
result=unittest.TextTestRunner(verbosity=2,resultclass=RecordedResult).run(unittest.defaultTestLoader.loadTestsFromNames(names))
complete=(result.wasSuccessful() and not result.skipped and not result.expectedFailures)
report={
    'recorded_at':datetime.now(timezone.utc).isoformat(),
    'platform':platform.platform(),'python':platform.python_version(),
    'mode':'frozen-public-fixtures' if args.executable else 'installed-package-acceptance',
    'complete':complete,'run':result.testsRun,'passed':sum(r['outcome']=='passed' for r in result.records),
    'skipped':len(result.skipped),'expected_failures':len(result.expectedFailures),
    'fixtures':{
        'upstream-sparse.pdf':{'pages':2,'alphanumeric_characters':1397,'exact_table_data_rows':[8,10]},
        'upstream-repair.pdf':{'pages':3,'alphanumeric_characters':2188},
        'upstream-receipt.pdf':{'pages':1,'alphanumeric_characters':905},
        'upstream-article.pdf':{'pages':1,'alphanumeric_characters':4254},
    },
    'limits':[
        'Public upstream test fixtures and generated PDFs, not a real-user corpus or general accuracy estimate.',
        'Alphanumeric character counts exclude whitespace and punctuation; separate exact-cell/order/money assertions apply.',
        'Cross-page tables retain repeated headers and data; only possible-continuation hints, no automatic merging.',
        'No Windows or GPU execution in this Linux result.',
    ],
    'checks':result.records,
}
if args.executable:report['executable_sha256']=hashlib.sha256(executable.read_bytes()).hexdigest()
args.report.parent.mkdir(parents=True,exist_ok=True)
args.report.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(f'Acceptance: {report["passed"]}/{report["run"]}; report: {args.report}')
raise SystemExit(0 if complete else 1)

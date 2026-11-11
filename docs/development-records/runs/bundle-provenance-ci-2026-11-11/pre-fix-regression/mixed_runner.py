from pathlib import Path
from importlib import metadata
import json,sys,unittest
root=Path('/workspace/MarkItDown-exe');sys.path.insert(0,str(root/'tests'));sys.path.insert(0,str(root/'scripts'))
from check_isolated_tests import KNOWN_EXPECTED_FAILURE

def main():
    suite=unittest.defaultTestLoader.discover(str(root/'tests'))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    expected=[test.id() for test,_ in result.expectedFailures]
    accepted=(result.testsRun==660 and result.wasSuccessful() and not result.skipped and expected==[KNOWN_EXPECTED_FAILURE])
    value=dict(source_version=metadata.version('markitdown-desktop'),run=result.testsRun,passed=result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped)-len(result.expectedFailures)-len(result.unexpectedSuccesses),failures=[test.id() for test,_ in result.failures],errors=[test.id() for test,_ in result.errors],skipped=[dict(test=test.id(),reason=reason) for test,reason in result.skipped],expected_failures=expected,unexpected_successes=[test.id() for test in result.unexpectedSuccesses],assertions_accepted=accepted,process_exit_verified=False)
    Path('/tmp/markitdown-provenance-full/full-mixed-result.json').write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    raise SystemExit(0 if accepted else 1)

if __name__=="__main__":main()

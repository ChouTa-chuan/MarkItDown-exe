import json, sys, unittest
def main():
    result = unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.discover('tests'))
    print(json.dumps(dict(run=result.testsRun, failures=[t.id() for t,_ in result.failures],
        errors=[t.id() for t,_ in result.errors], expected=[t.id() for t,_ in result.expectedFailures],
        unexpected_success=[t.id() for t in result.unexpectedSuccesses],
        skipped=[(t.id(), r[:80]) for t,r in result.skipped]), ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1
if __name__ == '__main__':
    raise SystemExit(main())

import ctypes,runpy,sys
ctypes.CDLL('/tmp/markitdown-qt-diagnosis/trace.so').install_trace()
sys.argv=['scripts/check_isolated_tests.py','--module','test_component_management','--expected-count','23','--output','/tmp/markitdown-qt-diagnosis/traced.json']
runpy.run_path(sys.argv[0],run_name='__main__')

import subprocess,pathlib,os
root=pathlib.Path('/tmp/markitdown-qt-diagnosis')
for n in range(8):
 p=root/f'lldb-type-{n}.log'
 cmd=['/workspace/markitdown-native-tools/llvm-mingw-20261104-ucrt-ubuntu-22.04-x86_64/bin/lldb','--batch','-o','settings set target.disable-aslr false','-o','run']
 for line in ['thread backtrace -c 8','disassemble -f','register read rbx rbp r12 r13 r14 r15','frame select 1','disassemble -f','image list -o -f']:
  cmd.extend(['-k',line])
 cmd+=['--','/workspace/markitdown-clean-venv/bin/python','scripts/check_isolated_tests.py','--module','test_component_management','--expected-count','23','--output',str(root/'lldb-type.json')]
 with p.open('wb') as f:r=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,env={**os.environ,'QT_QPA_PLATFORM':'offscreen'},timeout=90)
 raw=p.read_text();print(n,'signal SIGSEGV' in raw,flush=True)
 if 'signal SIGSEGV' in raw:
  print(str(p));break

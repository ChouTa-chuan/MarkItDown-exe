"""僅供 IPC 故障測試；不執行 OCR，也不代表獨立推論 runtime 驗收。"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time

parser=argparse.ArgumentParser();parser.add_argument('--job-directory',type=Path,required=True)
parser.add_argument('--guard');parser.add_argument('--scenario',default='valid')
parser.add_argument('--component-version',default='1.0.1');parser.add_argument('--result-version');args=parser.parse_args()
scenario=args.scenario;protocol='1.0.0';output=sys.stdout.buffer
def emit(kind,**values):
    output.write((json.dumps(dict(protocol=protocol,type=kind,**values))+'\n').encode());output.flush()
if scenario=='no_hello':time.sleep(20);raise SystemExit(0)
if scenario=='oversize':output.write(b'x'*16385);output.flush();raise SystemExit(0)
emit('hello',component_id='onnx-cpu-ocr',component_version=args.component_version if scenario!='version' else '9.0.0',
     pid=os.getpid(),frozen=False,device='cpu')
if scenario=='crash':os._exit(17)
raw=os.fdopen(os.dup(sys.stdin.fileno()),'rb',buffering=0)
request=json.loads(raw.readline());job=request['job_id'];cancel=threading.Event();permit=threading.Event();permit.set()
def control():
    while True:
        line=raw.readline()
        if not line:return
        command=json.loads(line)
        if command['type']=='cancel':cancel.set();permit.set()
        elif command['type']=='pause':permit.clear()
        elif command['type']=='resume':permit.set()
threading.Thread(target=control,daemon=True).start()
emit('progress',job_id=job,stage='loading')
if scenario=='flood':
    for _ in range(100):emit('progress',job_id=job,stage='loading')
    time.sleep(20);raise SystemExit(0)
if scenario=='stderr_flood':os.write(2,b'x'*(300*1024));time.sleep(20);raise SystemExit(0)
emit('ready',job_id='b'*32 if scenario=='job' else job,providers=['CPUExecutionProvider']*3)
emit('progress',job_id=job,stage='inference')
if scenario in ('hang','ignore_cancel'):time.sleep(20)
until=time.monotonic()+(0.3 if scenario=='slow' else 0.05)
while time.monotonic()<until or not permit.is_set():
    if cancel.is_set():emit('cancelled',job_id=job,code='cancelled');raise SystemExit(2)
    time.sleep(0.01)
if scenario=='failure':emit('failed',job_id=job,code='fixture_failure');raise SystemExit(1)
value=dict(schema_version=1,protocol=protocol,job_id=job,component_id='onnx-cpu-ocr',component_version=args.result_version or args.component_version,
           actual_device='cpu',providers=['CPUExecutionProvider']*3,text='FAKE WORKER CONTENT',warning='IPC fixture only',
           input_sha256=request['input_sha256'] or 'a'*64,health_passed=request['operation']=='health',
           runtime=dict(python='3.12.0',rapidocr='1.4.4',onnxruntime='fixture',numpy='fixture',opencv='fixture',frozen=False))
data=json.dumps(value).encode();target=args.job_directory/'result.json'
if scenario=='symlink':target.symlink_to(args.job_directory/'input.png');data=(args.job_directory/'input.png').read_bytes()
else:target.write_bytes(data)
emit('progress',job_id=job,stage='export')
emit('completed',job_id=job,result='../outside' if scenario=='escape' else 'result.json',bytes=len(data),
     sha256='0'*64 if scenario=='digest' else hashlib.sha256(data).hexdigest())
if scenario=='tail':emit('progress',job_id=job,stage='loading')
if scenario=='no_exit':time.sleep(20)

"""CPU OCR worker：先取得子程序自己的共享鎖，再載入專屬 runtime 與固定模型。"""
import argparse
import hashlib
from importlib import metadata, resources
import json
import os
from pathlib import Path
from queue import Queue
import sys
import threading

from ..components.locks import file_lock
from ..components.registry import verify_file, _chain
from ..core import Cancelled
from . import protocol as wire


def asset(name):
    return Path(resources.files('desktop_app').joinpath('data',name))


def runtime_info():
    import platform
    return dict(python=platform.python_version(),rapidocr=metadata.version('rapidocr-onnxruntime'),
                onnxruntime=metadata.version('onnxruntime'),numpy=metadata.version('numpy'),
                opencv=metadata.version('opencv-python'),frozen=bool(getattr(sys,'frozen',False)))


def verify_assets(checkpoint):
    if not getattr(sys,'frozen',False):return
    root=Path(sys._MEIPASS)/'worker-assets'
    manifest=json.loads((root/'installed-manifest.json').read_bytes())
    for name,expected in manifest['files'].items():
        checkpoint()
        path=root/name
        wire.require(path.is_relative_to(root) and '..' not in Path(name).parts)
        with path.open('rb') as source:
            digest=hashlib.sha256()
            while block:=source.read(65536):digest.update(block)
        wire.require(digest.hexdigest()==expected,'選配 runtime 授權資產不完整。')
    wire.require((root/'python-runtime/LICENSE.txt').is_file())


def serve(directory, guard, control, input_stream):
    directory = Path(directory).absolute();_chain(directory)
    cancel = threading.Event();permit = threading.Event();permit.set()
    finished = threading.Event();commands = Queue(maxsize=1)
    state = {'job_id':None,'error':False}
    def emit(kind,**values):
        control.write(wire.encode(dict(protocol=wire.PROTOCOL,type=kind,**values)));control.flush()
    def reader():
        try:
            while not finished.is_set():
                raw = input_stream.readline(wire.MAX_FRAME+1)
                if not raw:
                    if not finished.is_set():os._exit(72)  # 父程序失聯，不能留下仍在推論的孤兒。
                    return
                value = wire.command(wire.decode(raw))
                if value['type']=='run':
                    wire.require(state['job_id'] is None,'每個程序僅接受一個工作。')
                    state['job_id'] = value['job_id'];commands.put_nowait(value)
                else:
                    wire.require(value['job_id']==state['job_id'])
                    if value['type']=='pause':permit.clear()
                    elif value['type']=='resume':permit.set()
                    else:cancel.set();permit.set()
        except Exception:
            state['error']=True;cancel.set();permit.set()
            if state['job_id'] is None:os._exit(73)
    def checkpoint():
        while not permit.wait(0.05):
            if cancel.is_set():raise Cancelled('cancelled')
        if cancel.is_set():raise Cancelled('cancelled')
    thread = None
    try:
        # 健康檢查與實際工作共用此鎖；控制端退出後，鎖仍由 worker 自己持有。
        with file_lock(guard,exclusive=False):
            emit('hello',component_id=wire.COMPONENT_ID,component_version=wire.COMPONENT_VERSION,
                 pid=os.getpid(),frozen=bool(getattr(sys,'frozen',False)),device='cpu')
            thread = threading.Thread(target=reader,daemon=True);thread.start()
            request = commands.get()
            job_id = request['job_id'];limits = request['limits']
            checkpoint()
            verify_assets(checkpoint)
            for name in ('OMP_THREAD_LIMIT','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
                os.environ[name]=str(limits['cpu_threads'])
            import psutil
            process=psutil.Process()
            process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name=='nt' else 5)
            emit('progress',job_id=job_id,stage='loading')
            import onnxruntime
            onnxruntime.disable_telemetry_events()
            from ..onnx_ocr import OnnxOCR
            from PIL import Image
            Image.MAX_IMAGE_PIXELS = limits['max_pixels']
            reference=json.loads(asset('worker-health.json').read_bytes())
            verify_file(asset('worker-health.png'),reference['bytes'],reference['sha256'],checkpoint)
            if request['operation']=='health':
                source=asset('worker-health.png');input_hash=reference['sha256']
            else:
                source=directory/'input.png';input_hash=request['input_sha256']
                verify_file(source,request['input_bytes'],input_hash,checkpoint)
            engine=OnnxOCR('cpu',limits['cpu_threads'],checkpoint=checkpoint)
            try:
                providers=[session.get_providers()[0] for session in engine.sessions()]
                wire.require(providers==['CPUExecutionProvider']*3,'實際 session 不是 CPU provider。')
                emit('ready',job_id=job_id,providers=providers)
                checkpoint();emit('progress',job_id=job_id,stage='inference')
                with Image.open(source) as image:
                    wire.require(image.format=='PNG' and image.width*image.height<=limits['max_pixels'],'影像格式或尺寸超限。')
                    text,warning=engine.recognize(image)
            finally:engine.close()
            checkpoint()
            health_passed=request['operation']=='health' and reference['expected'] in ' '.join(text.split())
            if request['operation']=='health' and not health_passed:raise RuntimeError('health failed')
            value=dict(schema_version=1,protocol=wire.PROTOCOL,job_id=job_id,
                component_id=wire.COMPONENT_ID,component_version=wire.COMPONENT_VERSION,
                actual_device='cpu',providers=providers,text=text,warning=warning,input_sha256=input_hash,
                health_passed=health_passed,runtime=runtime_info())
            wire.result(value,job_id)
            data=(json.dumps(value,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8')
            wire.require(len(data)<=limits['max_output_bytes'],'結果超過輸出上限。')
            emit('progress',job_id=job_id,stage='export');checkpoint()
            target=directory/'result.json';_chain(target)
            with target.open('xb') as output:
                output.write(data);output.flush();os.fsync(output.fileno())
            checkpoint();finished.set()
            emit('completed',job_id=job_id,result='result.json',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            return 0
    except Cancelled:
        finished.set();emit('cancelled',job_id=state['job_id'],code='protocol_error' if state['error'] else 'cancelled')
        return 2
    except Exception:
        finished.set();emit('failed',job_id=state['job_id'],code='worker_failed')
        return 1
    finally:finished.set()


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--job-directory',type=Path,required=True)
    parser.add_argument('--guard',type=Path,required=True)
    args=parser.parse_args(argv)
    # 控制通道保留獨立 fd，連原生函式庫寫 stdout 都會導至 stderr，不混入 JSON。
    control=os.fdopen(os.dup(sys.stdout.fileno()),'wb',buffering=0)
    os.dup2(sys.stderr.fileno(),sys.stdout.fileno())
    # daemon 不能持有標準 BufferedReader 的鎖，否則 CPython 結束時可能 abort。
    # 單工作程序使用 raw fd；退出時由 OS 回收，無等待另一個 daemon 關閉 buffered IO。
    if os.name=='nt':
        # Windows實測停在ORT原生匯入，同時背景執行緒正以CRT讀stdin；
        # 改用Win32管道讀取，保留原有reader／EOF／取消語意，不靠延長期限或延後控制處理。
        from .pipe_input import windows_pipe_input
        input_stream=windows_pipe_input(sys.stdin.fileno())
    else:
        input_stream=os.fdopen(os.dup(sys.stdin.fileno()),'rb',buffering=0)
    try:return serve(args.job_directory,args.guard,control,input_stream)
    finally:control.close()


if __name__=='__main__':
    raise SystemExit(main())

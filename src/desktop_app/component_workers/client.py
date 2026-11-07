"""控制端僅處理 IPC、資源與結果檔；不 import ONNX／RapidOCR／NumPy。"""
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
from queue import Empty, Full, Queue
import subprocess
import tempfile
from threading import Event, Thread
import time
import uuid

import psutil

from ..components.registry import _chain, _plain, verify_file
from ..core import Cancelled, Request, State
from ..resources import MIB, snapshot
from ..conversion import _write_chunks
from . import protocol as wire


class WorkerError(RuntimeError):
    """只失敗當次工作；不把子程序 stderr 或文件文字直接塞入例外。"""


@dataclass(frozen=True)
class WorkerOutcome:
    state: State
    message: str
    report: dict | None = None
    pid: int | None = None


def stop_tree(process):
    if process is None or process.poll() is not None:return
    try:
        root=psutil.Process(process.pid)
        children=root.children(recursive=True)
        for child in reversed(children):
            try:child.terminate()
            except psutil.NoSuchProcess:pass
        process.terminate()
        try:process.wait(timeout=1)
        except subprocess.TimeoutExpired:process.kill();process.wait(timeout=2)
        _,alive=psutil.wait_procs(children,timeout=1)
        for child in alive:
            try:child.kill()
            except psutil.NoSuchProcess:pass
        psutil.wait_procs(alive,timeout=1)
    except psutil.NoSuchProcess:
        process.wait(timeout=2)


class WorkerRunner:
    """command 由可信程式 binding 提供，不能從下載目錄讀取任意 shell 命令。"""
    def __init__(self, command, guard, policy, *, estimate_mib=768, cpu_threads=1,
                 timeout=120, handshake_timeout=10, resource_wait=30, cancel_grace=1,
                 read_snapshot=snapshot, require_frozen=True, permit=None):
        if not isinstance(command,tuple) or not command or not all(isinstance(item,str) and item and '\x00' not in item for item in command):
            raise ValueError('工作程序命令須為可信非空參數 tuple。')
        for value in (timeout,handshake_timeout,resource_wait,cancel_grace):
            if type(value) not in (int,float) or not math.isfinite(value) or not 0<value<=600:
                raise ValueError('工作程序等待上限須為 0 至 600 秒內有限正數。')
        if type(estimate_mib) is not int or not 1<=estimate_mib<=65536:
            raise ValueError('工作程序 RAM 預估無效。')
        wire.limits(dict(cpu_threads=cpu_threads,max_pixels=wire.MAX_PIXELS,max_output_bytes=wire.MAX_RESULT))
        if type(require_frozen) is not bool:raise ValueError('獨立 runtime 選項須為布林值。')
        self.command=command;self.guard=Path(guard).absolute();self.policy=policy
        self.estimate_mib=estimate_mib;self.cpu_threads=cpu_threads
        self.timeout=timeout;self.handshake_timeout=handshake_timeout;self.resource_wait=resource_wait
        self.cancel_grace=cancel_grace;self.read_snapshot=read_snapshot;self.require_frozen=require_frozen
        self.permit=permit

    def run(self, source=None, destination=None, *, operation='ocr', cancel=None,
            notify=lambda state,message:None):
        cancel=cancel if cancel is not None else Event()
        process=None;workspace=None;threads=[];transport_error=Event();messages=Queue(maxsize=32)
        controls=Queue(maxsize=8);writer_stop=Event()
        job_id=uuid.uuid4().hex;started=time.monotonic();deadline=started+self.timeout
        def check():
            if cancel.is_set():raise Cancelled('選配工作已取消。')
            if time.monotonic()>=deadline:raise WorkerError('選配工作逾時，已停止該程序。')
        def admission(extra):
            waiting=time.monotonic()
            while True:
                check()
                allowed,reason=self.policy.admit(self.read_snapshot(),extra)
                if self.permit is not None and not self.permit.is_set(): allowed,reason=False,'等待上層 RAM 調度。'
                if allowed:return
                notify(State.PAUSED,reason)
                if time.monotonic()-waiting>=self.resource_wait:raise WorkerError(reason+' 資源等待逾時。')
                cancel.wait(0.05)
        def send(value):
            try:controls.put_nowait(wire.encode(value))
            except Full as exc:raise WorkerError('工作程序控制訊息未消化，停止避免阻塞。') from exc
        def signal(kind):
            if process.poll() is None:send(dict(protocol=wire.PROTOCOL,type=kind,job_id=job_id))
        def stdout_reader():
            count=0
            try:
                while True:
                    line=process.stdout.readline(wire.MAX_FRAME+1)
                    if not line:return
                    count+=1
                    wire.require(count<=64,'工作程序訊息數量超限。')
                    value=wire.event(wire.decode(line));messages.put_nowait(value)
            except Exception:transport_error.set()
        def stderr_reader():
            # 只排空，不把可能含有使用者內容的原生診斷記錄或返回主程序。
            try:
                total=0
                while block:=process.stderr.read(65536):
                    total+=len(block)
                    if total>256*1024:transport_error.set();return
            except (OSError,ValueError):pass
        def stdin_writer():
            try:
                while not writer_stop.is_set():
                    try:raw=controls.get(timeout=0.05)
                    except Empty:continue
                    process.stdin.write(raw);process.stdin.flush()
            except (OSError,ValueError):
                if not writer_stop.is_set():transport_error.set()
        def next_event(until):
            while True:
                check()
                if transport_error.is_set():raise WorkerError('工作程序協定無效或訊息超量。')
                try:return messages.get(timeout=0.05)
                except Empty:
                    if time.monotonic()>=until:raise WorkerError('工作程序握手逾時。')
                    if process.poll() is not None:
                        try:return messages.get(timeout=0.1)
                        except Empty:raise WorkerError(f'工作程序提前結束，exitcode={process.returncode}')
        try:
            wire.require(operation in ('ocr','health'))
            if operation=='ocr':
                source=Path(source).absolute();_chain(source)
                info=_plain(source)
                wire.require(source.is_file() and 0<info.st_size<=wire.MAX_INPUT,'輸入影像檔案無效或超限。')
            if destination is not None and (Path(destination).exists() or Path(destination).is_symlink()):
                raise FileExistsError('輸出已存在，未覆寫。')
            admission((self.estimate_mib+64)*MIB)
            workspace=tempfile.TemporaryDirectory(prefix='markitdown-component-job-')
            directory=Path(workspace.name)
            input_hash=None;input_bytes=0
            if operation=='ocr':
                hasher=hashlib.sha256()
                with source.open('rb') as input_file,(directory/'input.png').open('xb') as output:
                    while block:=input_file.read(65536):
                        check();input_bytes+=len(block)
                        wire.require(input_bytes<=wire.MAX_INPUT,'輸入影像讀取期間超限。')
                        hasher.update(block);output.write(block)
                input_hash=hasher.hexdigest()
            environment={**os.environ,'PYTHONDONTWRITEBYTECODE':'1','PYTHONNOUSERSITE':'1'}
            for key,leaf in (('XDG_CACHE_HOME','cache'),('XDG_CONFIG_HOME','config'),('TMPDIR','temp'),('TEMP','temp'),('TMP','temp')):
                path=directory/leaf;path.mkdir(exist_ok=True);environment[key]=str(path)
            for key in ('PYTHONPATH','PYTHONHOME','LD_PRELOAD'):environment.pop(key,None)
            # frozen 主程式的 loader 路徑不能滲入選配 runtime；proxy／CA 繼續沿用。
            if os.name!='nt':environment['LD_LIBRARY_PATH']=str(Path(self.command[0]).parent/'_internal')
            for key in ('OMP_THREAD_LIMIT','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):
                environment[key]=str(self.cpu_threads)
            process=subprocess.Popen([*self.command,'--job-directory',str(directory),'--guard',str(self.guard)],
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,cwd=directory,
                env=environment,shell=False,close_fds=True,start_new_session=(os.name!='nt'))
            threads=[Thread(target=stdout_reader,daemon=True),Thread(target=stderr_reader,daemon=True),Thread(target=stdin_writer,daemon=True)]
            for thread in threads:thread.start()
            hello=next_event(min(deadline,time.monotonic()+self.handshake_timeout))
            wire.require(hello['type']=='hello' and hello['pid']==process.pid,'工作程序身分或握手順序不符。')
            wire.require(not self.require_frozen or hello['frozen'],'選配工作程序缺少獨立打包 runtime。')
            admission(self.estimate_mib*MIB)
            send(dict(protocol=wire.PROTOCOL,type='run',job_id=job_id,operation=operation,
                input='input.png' if operation=='ocr' else None,input_bytes=input_bytes,input_sha256=input_hash,
                output='result.json',limits=dict(cpu_threads=self.cpu_threads,max_pixels=wire.MAX_PIXELS,max_output_bytes=wire.MAX_RESULT)))
            notify(State.RUNNING,'選配 CPU 工作程序已啟動。')
            phase=0;paused=None;cancel_since=None;terminal=None
            expected=[('progress','loading'),('ready',None),('progress','inference'),('progress','export'),('completed',None)]
            while terminal is None:
                if cancel.is_set():
                    if cancel_since is None:
                        cancel_since=time.monotonic()
                        try:signal('cancel')
                        except WorkerError:pass
                    if time.monotonic()-cancel_since>=self.cancel_grace:raise Cancelled('選配工作已取消。')
                elif time.monotonic()>=deadline:raise WorkerError('選配工作逾時，已停止該程序。')
                else:
                    allowed,reason=self.policy.admit(self.read_snapshot(),0,resuming=paused is not None)
                    if self.permit is not None and not self.permit.is_set(): allowed,reason=False,'等待上層 RAM 調度。'
                    if not allowed:
                        if paused is None:
                            paused=time.monotonic();signal('pause');notify(State.PAUSED,reason)
                        if time.monotonic()-paused>=self.resource_wait:raise WorkerError(reason+' 資源等待逾時。')
                    elif paused is not None:
                        signal('resume');paused=None;notify(State.RUNNING,'資源恢復，繼續選配工作。')
                if transport_error.is_set():
                    if cancel.is_set():raise Cancelled('選配工作已取消。')
                    raise WorkerError('工作程序協定無效或訊息超量。')
                try:value=messages.get(timeout=0.05)
                except Empty:
                    if process.poll() is not None:
                        try:value=messages.get(timeout=0.1)
                        except Empty:raise WorkerError(f'工作程序提前結束，exitcode={process.returncode}')
                    else:continue
                wire.require(value.get('job_id')==job_id,'工作程序回覆錯誤的任務 ID。')
                if value['type']=='cancelled':raise Cancelled('選配工作已取消。') if value['code']=='cancelled' else WorkerError('工作程序拒絕無效控制訊息。')
                if value['type']=='failed':raise WorkerError('選配引擎失敗：'+value['code'])
                wire.require(phase<len(expected) and (value['type'],value.get('stage'))==expected[phase], '工作程序訊息順序不符。')
                phase+=1
                if value['type']=='progress':notify(State.PAUSED if paused is not None else State.RUNNING,'選配工作階段：'+value['stage'])
                if value['type']=='completed':terminal=value
            check()
            try:process.wait(timeout=min(2,max(0.01,deadline-time.monotonic())))
            except subprocess.TimeoutExpired as exc:raise WorkerError('工作程序完成回覆後未退出。') from exc
            writer_stop.set()
            for thread in threads:thread.join(timeout=1)
            wire.require(process.returncode==0 and not transport_error.is_set() and messages.empty(),'工作程序退出或尾端訊息不符。')
            if paused is not None:admission(0)
            target=directory/'result.json'
            verify_file(target,terminal['bytes'],terminal['sha256'],check)
            value=json.loads(target.read_bytes(),object_pairs_hook=wire.unique)
            wire.result(value,job_id)
            wire.require(value['runtime']['frozen']==hello['frozen'])
            if input_hash is not None:wire.require(value['input_sha256']==input_hash,'輸入與結果不相符。')
            if operation=='health':wire.require(value['health_passed'],'真實 CPU OCR 健康檢查未通過。')
            if destination is not None:
                text=value['text']+'\n\n> '+value['warning']+'\n'
                _write_chunks(Request(Path(source) if source else target,Path(destination)),
                              (text[index:index+65536] for index in range(0,len(text),65536)),check,lambda stage:None)
            if destination is None:check()
            return WorkerOutcome(State.COMPLETED,'選配 CPU 推論完成；品質限制保留。',value,process.pid)
        except Cancelled as exc:return WorkerOutcome(State.CANCELLED,str(exc),pid=process.pid if process else None)
        except Exception as exc:return WorkerOutcome(State.FAILED,f'{type(exc).__name__}: {exc}',pid=process.pid if process else None)
        finally:
            writer_stop.set()
            stop_tree(process)
            if process is not None:
                for stream in (process.stdin,process.stdout,process.stderr):
                    if stream is not None:
                        try:stream.close()
                        # 已退出的 worker 可能關閉讀端；close 的緩衝 flush 不能覆蓋原結果，
                        # 也不能讓後續 thread join／私有暫存清理中斷。
                        except (OSError,ValueError):pass
            for thread in threads:thread.join(timeout=1)
            if workspace is not None:workspace.cleanup()

    def batch(self, pairs, *, cancel=None, notify=lambda state,message:None):
        for source,destination in pairs:
            yield self.run(source,destination,cancel=cancel,notify=notify)

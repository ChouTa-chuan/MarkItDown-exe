"""可信 ONNX CPU binding：元件檔案只決定位置，不提供任意啟動命令。"""
import os
from pathlib import Path

from ..capabilities import HealthResult
from ..components.contracts import Version
from ..components.registry import _chain, _plain
from ..resources import Policy, snapshot
from ..core import State, Cancelled
from .client import WorkerRunner
from . import protocol as wire


class CPUWorkerBinding:
    def __init__(self, guard, policy=None, *, read_snapshot=snapshot, cpu_threads=1,
                 timeout=120, cancel=None):
        self.guard=Path(guard).absolute();self.policy=policy or Policy()
        wire.require(self.guard.name=='worker-use.lock' and self.guard.parent.name=='.locks','binding 必須使用元件管理器的 worker guard。')
        self.read_snapshot=read_snapshot;self.cpu_threads=cpu_threads;self.timeout=timeout;self.cancel=cancel

    def runner(self, spec, directory):
        wire.require(Path(directory).absolute().is_relative_to(self.guard.parent.parent),'元件不屬於此 binding 的受管根目錄。')
        wire.require(spec.key==(wire.COMPONENT_ID,wire.COMPONENT_VERSION)
                     and spec.worker_protocols.contains(Version.parse(wire.PROTOCOL)),'沒有此元件／協定的可信 binding。')
        name='MarkItDownOCRWorker.exe' if os.name=='nt' else 'MarkItDownOCRWorker'
        wire.require(any(item.path==name for item in spec.files),'元件未宣告固定入口檔。')
        executable=Path(directory)/name;_chain(executable);_plain(executable)
        wire.require(executable.is_file() and (os.name=='nt' or os.access(executable,os.X_OK)),'元件入口無法執行。')
        return WorkerRunner((str(executable),),self.guard,self.policy,estimate_mib=spec.resources.ram_mib,
            cpu_threads=self.cpu_threads,timeout=self.timeout,read_snapshot=self.read_snapshot,require_frozen=True)

    def health(self, spec, directory, host):
        outcome=self.runner(spec,directory).run(operation='health',cancel=self.cancel)
        # 健康取消須保留取消語意，不能被能力解析誤判為引擎不健康。
        if outcome.state==State.CANCELLED: raise Cancelled(outcome.message)
        return HealthResult(outcome.state==State.COMPLETED and outcome.report['health_passed'],outcome.message)

    def run_managed(self, manager, catalog, source, destination, *, cancel=None, notify=lambda state,message:None):
        wire.require(self.guard==manager.worker_guard_path,'worker 與元件管理器的 guard 不符。')
        with manager.lease(catalog,wire.COMPONENT_ID) as lease:
            return self.runner(lease.spec,lease.directory).run(source,destination,
                cancel=cancel if cancel is not None else self.cancel,notify=notify)

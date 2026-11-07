"""C10：只在 OCR 頁取得可信元件，整份文件與輸出提交期間固定租約／版本。"""
from contextlib import ExitStack
from dataclasses import dataclass
from pathlib import Path
import tempfile
from threading import Event

from ..components.catalog import TrustPolicy
from ..core import Cancelled, State
from ..resources import Policy, snapshot
from .binding import CPUWorkerBinding
from .protocol import COMPONENT_ID, PROTOCOL

CAPABILITY='ocr.onnx.cpu'


@dataclass(frozen=True)
class ManagedContext:
    """只由可信應用服務建立；不從設定／下載清單接受金鑰或任意執行命令。"""
    directory: str
    policy: TrustPolicy | None

    def __post_init__(self):
        if not isinstance(self.directory,str) or '\x00' in self.directory or not Path(self.directory).is_absolute():
            raise ValueError('元件資料根須為可信絕對路徑。')
        if self.policy is not None and not isinstance(self.policy,TrustPolicy):
            raise ValueError('元件來源缺少可信政策。')


class ManagedOCRUnavailable(RuntimeError):
    """只失敗當次文件，呼叫端可明確開管理介面或另選原後端重試。"""


class ManagedOCRSession:
    def __init__(self,context,request,checkpoint,progress,*,policy=None,cancel=None,permit=None,
                 owner_pid=None,resource_wait=30,record_component=lambda evidence:None,resource_event=None):
        self.context=context;self.request=request;self.checkpoint=checkpoint;self.progress=progress
        self.policy=policy or Policy();self.cancel=cancel if cancel is not None else Event()
        self.permit=permit;self.owner_pid=owner_pid;self.resource_wait=resource_wait
        self.stack=ExitStack();self.lease=None;self.service=None;self.manager=None;self.binding=None
        self.record_component=record_component;self.recorded=False
        self.resource_event=resource_event;self.last_event=None;self.health_paused=False

    def notify(self,state,message):
        value=(state,message)
        if value==self.last_event:return
        self.last_event=value
        if self.resource_event is None:self.progress(message)
        else:self.resource_event(state,message)

    def health_notify(self,state,message):
        # 健康階段只回報資源暫停／恢復，頁面 loading 進度維持自己的命名空間。
        if state==State.PAUSED:
            self.health_paused=True;self.notify(state,'健康檢查等待資源：'+message)
        elif self.health_paused:
            self.health_paused=False;self.notify(State.RUNNING,'健康檢查資源恢復。')

    def __enter__(self): return self

    def __exit__(self,*args): return self.stack.__exit__(*args)

    @property
    def provenance(self):
        if self.lease is None:return None
        return dict(component_id=self.lease.spec.component_id,version=str(self.lease.spec.version),protocol=PROTOCOL,device='cpu')

    def _start(self):
        self.checkpoint()
        if self.context is None or self.context.policy is None:
            raise ManagedOCRUnavailable('尚無受信任選配來源；請開啟選配元件管理，或明確另選已備妥的 OCR 後端後重試。')
        if self.request.component_id not in (None,COMPONENT_ID):
            raise ManagedOCRUnavailable('此版本只支援已核准的 ONNX CPU 元件，未改用其他引擎。')
        from ..components.management import ComponentManagement, TrustedSource
        from ..components.registry import ComponentRegistry
        from ..components.lifecycle import ComponentManager
        self.service=ComponentManagement(self.context.directory,source=TrustedSource(self.context.policy))
        registry=ComponentRegistry(self.service.registry_path)
        self.binding=CPUWorkerBinding(registry.directory/'.locks/worker-use.lock',self.policy,
            read_snapshot=lambda:snapshot(self.owner_pid),cpu_threads=self.request.cpu_threads,
            cancel=self.cancel,permit=self.permit,resource_wait=self.resource_wait,notify=self.health_notify)
        self.manager=ComponentManager(registry,self.service.verifier,self.service.host,
                                     {'onnx.cpu.health':self.binding.health},checkpoint=self.checkpoint)
        catalog=self.service._catalog()
        self.lease=self.stack.enter_context(self.manager.lease(catalog,COMPONENT_ID,
            expected_version=self.request.component_version,capability=CAPABILITY))
        self.progress(f'已固定受管 OCR：{COMPONENT_ID} {self.lease.spec.version}／CPU；繁體品質仍需核對。')

    def validate(self,*,for_commit=False):
        self.checkpoint()
        if self.lease is None:return
        catalog=self.service._catalog()
        if catalog.component(*self.lease.spec.key)!=self.lease.spec:
            raise ManagedOCRUnavailable('目前目錄已變更，所選元件未獲核准；未提交輸出。')
        if for_commit:
            self.manager.registry.verify_installation(self.lease.spec,self.checkpoint)
            # 大型驗檔後再次核對到期／撤回，不能用先前的有效狀態提交。
            if self.service._catalog().component(*self.lease.spec.key)!=self.lease.spec:
                raise ManagedOCRUnavailable('提交前元件描述已變更。')
        self.checkpoint()

    def recognize(self,image):
        if self.lease is None:self._start()
        self.validate()
        with tempfile.TemporaryDirectory(prefix='markitdown-managed-page-') as temporary:
            path=Path(temporary)/'page.png';image.save(path,'PNG')
            outcome=self.binding.runner(self.lease.spec,self.lease.directory).run(path,cancel=self.cancel,
                notify=self.notify)
        if not self.recorded:
            # 每份文件只送一次有界執行證據，不將 OCR 全文／圖片塞入父程序佇列。
            report=outcome.report or {}
            self.record_component(dict(**self.provenance,state=outcome.state.value,pid=outcome.pid,
                frozen=report.get('runtime',{}).get('frozen'),providers=report.get('providers',[])))
            self.recorded=True
        if outcome.state==State.CANCELLED: raise Cancelled(outcome.message)
        if outcome.state!=State.COMPLETED:
            raise ManagedOCRUnavailable('受管 OCR 未完成：'+outcome.message+'；請檢查元件或資源後明確重試，未更換引擎。')
        self.validate()
        return outcome.report['text'],outcome.report['warning']

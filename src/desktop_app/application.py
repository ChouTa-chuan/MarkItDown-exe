"""批次應用服務：以 spawn 隔離工作，依 RAM 狀況協作暫停與恢復。"""
import multiprocessing as mp
import os
from queue import Empty
import time
import math
from dataclasses import dataclass
from threading import Event

from .core import Request, State
from .planning import analyze
from .resources import Policy, snapshot
from .workers import worker


@dataclass(frozen=True)
class Outcome:
    request: Request
    state: State
    message: str = ""
    components: tuple[dict, ...] = ()


class Runner:
    def __init__(self, policy: Policy, read_snapshot=snapshot, poll_seconds=0.1,
                 max_resource_wait=30.0, component_context=None):
        if not math.isfinite(poll_seconds) or not math.isfinite(max_resource_wait) or poll_seconds <= 0 or max_resource_wait < 0:
            raise ValueError("輪詢時間必須大於零，等待上限不得為負值。")
        self.policy = policy
        self.read_snapshot = read_snapshot
        self.poll_seconds = poll_seconds
        self.max_resource_wait = max_resource_wait
        self.component_context = component_context

    def run(self, request: Request, cancel: Event | None = None,
            notify=lambda state, message: None) -> Outcome:
        """先做資源准入，執行時持續回壓，結束後回收工作程序與通訊佇列。"""
        cancel = cancel if cancel is not None else Event()
        process = messages = None
        stop = permit = None
        components=[]
        try:
            plan = analyze(request)
            notify(State.QUEUED, plan.explanation)
            waiting_since = None
            while True:
                if cancel.is_set():
                    return Outcome(request, State.CANCELLED, "已取消")
                # 預留子程序直譯器與 psutil 啟動開銷，再決定是否派送。
                allowed, reason = self.policy.admit(self.read_snapshot(),
                    plan.additional_bytes + 64*1024**2)
                if allowed:
                    break
                notify(State.PAUSED, reason)
                waiting_since = waiting_since or time.monotonic()
                if time.monotonic() - waiting_since >= self.max_resource_wait:
                    return Outcome(request, State.FAILED, reason + " 等待逾時，請調整設定或稍後重試。")
                cancel.wait(self.poll_seconds)
            # 固定採 spawn，使 Linux 測試也涵蓋 Windows 的獨立啟動方式。
            context = mp.get_context("spawn")
            stop, permit, messages = context.Event(), context.Event(), context.Queue()
            permit.set()
            process = context.Process(target=worker, args=(request, stop, permit, messages,
                self.component_context,self.policy,os.getpid(),self.max_resource_wait))
            process.start()
            notify(State.RUNNING, "背景工作程序已啟動")
            paused_since = None
            nested_paused = False
            terminal = None
            while True:
                if cancel.is_set():
                    stop.set()
                    permit.set()
                else:
                    # 受管後端由 C07 在載入前准入；此處只量測完整實際程序樹，
                    # 避免原生 runtime 已配置後再重複加算整份模型估計而造成無法恢復。
                    extra=0 if request.ocr_backend=='managed_cpu' else plan.additional_bytes
                    allowed, reason = self.policy.admit(self.read_snapshot(),
                        extra, resuming=paused_since is not None)
                    if not allowed:
                        permit.clear()
                        if paused_since is None:
                            paused_since = time.monotonic()
                            notify(State.PAUSED, reason)
                        if time.monotonic() - paused_since >= self.max_resource_wait:
                            return Outcome(request, State.FAILED, reason + " 等待逾時。")
                    else:
                        permit.set()
                        if paused_since is not None:
                            paused_since = None
                            notify(State.PAUSED if nested_paused else State.RUNNING,
                                   '上層資源恢復，仍等待元件資源。' if nested_paused else "資源恢復，繼續處理")
                try:
                    kind, message = messages.get(timeout=self.poll_seconds)
                    if kind == "progress":
                        notify(State.PAUSED if paused_since is not None or nested_paused else State.RUNNING, message)
                    elif kind=='worker_state':
                        state,detail=message;nested_paused=state==State.PAUSED.value
                        notify(State.PAUSED if paused_since is not None or nested_paused else State.RUNNING,detail)
                    elif kind=='component':
                        if len(components)<8: components.append(message)
                    else:
                        terminal = Outcome(request, State(kind), message,tuple(components))
                        break
                except Empty:
                    if not process.is_alive():
                        # 子程序退出前會沖出佇列資料；退出後再限時讀一次，避免遺漏最後狀態。
                        try:
                            kind, message = messages.get(timeout=0.5)
                        except Empty:
                            return Outcome(request, State.FAILED,
                                           f"工作程序提前結束，exitcode={process.exitcode}")
                        if kind=='component':
                            if len(components)<8: components.append(message)
                        elif kind=='worker_state':
                            state,detail=message;nested_paused=state==State.PAUSED.value
                            notify(State.PAUSED if paused_since is not None or nested_paused else State.RUNNING,detail)
                        elif kind != "progress":
                            terminal = Outcome(request, State(kind), message,tuple(components))
                            break
            return terminal
        except Exception as exc:
            return Outcome(request, State.FAILED, f"{type(exc).__name__}: {exc}")
        finally:
            if process is not None:
                if stop is not None:
                    stop.set()
                    permit.set()
                if process.pid is not None:
                    process.join(timeout=5)
                    if process.is_alive():
                        process.terminate()
                        process.join(timeout=5)
                    if not process.is_alive():
                        process.close()
            if messages is not None:
                messages.close()
                messages.join_thread()

    def batch(self, requests, cancel=None, notify=lambda state, message: None):
        """一次只跑一個工作程序；單一文件失敗不停止其餘批次。"""
        for request in requests:
            yield self.run(request, cancel, notify)

"""Sequential batch service with spawned worker and cooperative RAM backpressure."""
import multiprocessing as mp
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


class Runner:
    def __init__(self, policy: Policy, read_snapshot=snapshot, poll_seconds=0.1,
                 max_resource_wait=30.0):
        if not math.isfinite(poll_seconds) or not math.isfinite(max_resource_wait) or poll_seconds <= 0 or max_resource_wait < 0:
            raise ValueError("輪詢時間必須大於零，等待上限不得為負值。")
        self.policy = policy
        self.read_snapshot = read_snapshot
        self.poll_seconds = poll_seconds
        self.max_resource_wait = max_resource_wait

    def run(self, request: Request, cancel: Event | None = None,
            notify=lambda state, message: None) -> Outcome:
        cancel = cancel if cancel is not None else Event()
        process = messages = None
        stop = permit = None
        try:
            plan = analyze(request)
            notify(State.QUEUED, plan.explanation)
            waiting_since = None
            while True:
                if cancel.is_set():
                    return Outcome(request, State.CANCELLED, "已取消")
                # Allow for interpreter/psutil startup before spawning.
                allowed, reason = self.policy.admit(self.read_snapshot(),
                    plan.additional_bytes + 64*1024**2)
                if allowed:
                    break
                notify(State.PAUSED, reason)
                waiting_since = waiting_since or time.monotonic()
                if time.monotonic() - waiting_since >= self.max_resource_wait:
                    return Outcome(request, State.FAILED, reason + " 等待逾時，請調整設定或稍後重試。")
                cancel.wait(self.poll_seconds)
            context = mp.get_context("spawn")
            stop, permit, messages = context.Event(), context.Event(), context.Queue()
            permit.set()
            process = context.Process(target=worker, args=(request, stop, permit, messages))
            process.start()
            notify(State.RUNNING, "背景工作程序已啟動")
            paused_since = None
            terminal = None
            while True:
                if cancel.is_set():
                    stop.set()
                    permit.set()
                else:
                    allowed, reason = self.policy.admit(self.read_snapshot(),
                        plan.additional_bytes, resuming=paused_since is not None)
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
                            notify(State.RUNNING, "資源恢復，繼續處理")
                try:
                    kind, message = messages.get(timeout=self.poll_seconds)
                    if kind == "progress":
                        notify(State.PAUSED if paused_since is not None else State.RUNNING, message)
                    else:
                        terminal = Outcome(request, State(kind), message)
                        break
                except Empty:
                    if not process.is_alive():
                        # Child exits only after its queue feeder flushes; allow
                        # a final bounded read after observing process exit.
                        try:
                            kind, message = messages.get(timeout=0.5)
                        except Empty:
                            return Outcome(request, State.FAILED,
                                           f"工作程序提前結束，exitcode={process.exitcode}")
                        if kind != "progress":
                            terminal = Outcome(request, State(kind), message)
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
        """One worker at a time; failure of one file does not stop the batch."""
        for request in requests:
            yield self.run(request, cancel, notify)

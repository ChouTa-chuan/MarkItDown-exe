"""Spawn-compatible worker; resource decisions remain in the controller."""
import os
import psutil
from .conversion import convert_document
from .core import Cancelled


def worker(request, cancel, permit, messages):
    def checkpoint():
        while not permit.wait(0.1):
            if cancel.is_set():
                raise Cancelled("已取消")
        if cancel.is_set():
            raise Cancelled("已取消")

    try:
        process = psutil.Process(os.getpid())
        if os.name == "nt":
            process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            process.nice(5)
        convert_document(request, checkpoint, lambda stage: messages.put(("progress", stage)))
        messages.put(("completed", ""))
    except Cancelled as exc:
        messages.put(("cancelled", str(exc)))
    except Exception as exc:
        messages.put(("failed", f"{type(exc).__name__}: {exc}"))

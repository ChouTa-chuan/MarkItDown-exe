"""可由 spawn 啟動的隔離工作程序；資源准入仍由父程序決定。"""
import os
import psutil
from .conversion import convert_document
from .core import Cancelled


def worker(request, cancel, permit, messages):
    def checkpoint():
        # permit 由父程序依 RAM 壓力控制；等待期間仍持續檢查取消。
        while not permit.wait(0.1):
            if cancel.is_set():
                raise Cancelled("已取消")
        if cancel.is_set():
            raise Cancelled("已取消")

    try:
        # 只調整隔離子程序的執行緒與優先權，避免影響桌面父程序。
        threads = str(request.cpu_threads)
        for name in ("OMP_THREAD_LIMIT", "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
            os.environ[name] = threads
        process = psutil.Process(os.getpid())
        if os.name == "nt":
            process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
        else:
            process.nice(5)
        messages.put(("progress", f"工作程序 CPU 執行緒設定上限：{request.cpu_threads}；支援度依原生套件而異。"))
        if request.device == "gpu" and not (request.source.suffix.lower() == ".pdf" and request.quality.value == "precise"):
            messages.put(("progress", "原生格式解析使用 CPU；此步驟沒有 GPU 加速。"))
        summary = convert_document(request, checkpoint, lambda stage: messages.put(("progress", stage)))
        messages.put(("completed", summary or ""))
    except Cancelled as exc:
        messages.put(("cancelled", str(exc)))
    except Exception as exc:
        messages.put(("failed", f"{type(exc).__name__}: {exc}"))

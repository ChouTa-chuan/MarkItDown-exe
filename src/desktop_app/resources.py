"""RAM 准入與遲滯恢復：使用軟性預算，不代表配置記憶體或提供硬上限。"""
from dataclasses import dataclass
import os
import psutil

MIB = 1024**2


@dataclass(frozen=True)
class Snapshot:
    total: int
    available: int
    application: int


@dataclass(frozen=True)
class Policy:
    budget: int | None = None
    reserve: int = 2048 * MIB
    auto_fraction: float = 0.25
    resume_margin: int = 64 * MIB

    def __post_init__(self):
        if self.budget is not None and self.budget <= 0:
            raise ValueError("RAM 預算必須大於零。")
        if self.reserve < 0 or self.resume_margin < 0:
            raise ValueError("保留記憶體與恢復緩衝不得為負值。")
        if not 0 < self.auto_fraction <= 1:
            raise ValueError("自動比例必須介於 0 與 1 之間。")

    def admit(self, snapshot: Snapshot, extra: int, resuming: bool = False):
        if extra < 0:
            raise ValueError("預估記憶體不得為負值。")
        # 預算包含目前程序樹用量與下一步估算；恢復時加上緩衝，避免反覆暫停。
        budget = self.budget if self.budget is not None else int(snapshot.total * self.auto_fraction)
        margin = self.resume_margin if resuming else 0
        if snapshot.available - extra < self.reserve + margin:
            return False, "系統可用 RAM 低於保留需求。"
        if snapshot.application + extra + margin > budget:
            return False, "超出應用程式 RAM 軟性預算。"
        return True, "可執行"


def snapshot(root_pid=None) -> Snapshot:
    # 外部元件巢狀程序也須計入同一應用程式預算，不只量測 PDF 子程序自己。
    root = psutil.Process(os.getpid() if root_pid is None else root_pid)
    usage = 0
    for process in [root, *root.children(recursive=True)]:
        try:
            info = process.memory_info()
            # 優先採私有記憶體／USS，減少共享頁面重複加總；無法量測時停止新派送。
            private = getattr(info, "private", None)
            if private is None:
                private = getattr(process.memory_full_info(), "uss", info.rss)
            usage += private
        except psutil.NoSuchProcess:
            continue
        except psutil.AccessDenied as exc:
            raise RuntimeError("無法量測子程序記憶體，停止新工作。") from exc
    vm = psutil.virtual_memory()
    return Snapshot(vm.total, vm.available, usage)

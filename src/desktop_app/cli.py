"""Development entry point; end-user Qt desktop UI is pending."""
import argparse
import multiprocessing
from pathlib import Path
from threading import Event
import signal

from .application import Runner
from .core import Request, State
from .resources import MIB, Policy


def main():
    parser = argparse.ArgumentParser(description="開發用文字轉換與 RAM 調度驗證")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--ram-budget-mib", type=int)
    parser.add_argument("--reserve-mib", type=int, default=2048)
    parser.add_argument("--resource-wait-seconds", type=float, default=30)
    args = parser.parse_args()
    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
    try:
        policy = Policy(budget=None if args.ram_budget_mib is None else args.ram_budget_mib*MIB,
                        reserve=args.reserve_mib*MIB)
        runner = Runner(policy, max_resource_wait=args.resource_wait_seconds)
        result = runner.run(Request(args.source, args.destination), cancel,
                            lambda state, message: print(f"{state.value}: {message}"))
        print(f"{result.state.value}: {result.message}")
        return 0 if result.state == State.COMPLETED else 1
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        signal.signal(signal.SIGINT, previous)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())

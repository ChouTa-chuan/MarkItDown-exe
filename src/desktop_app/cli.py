"""Development entry point; end-user Qt desktop UI is pending."""
import argparse
import multiprocessing
from pathlib import Path
from threading import Event
import signal

from .application import Runner
from .core import Request, State, Quality
from .settings import Settings, load_settings


def main():
    parser = argparse.ArgumentParser(description="開發用文字轉換與 RAM 調度驗證")
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--settings", type=Path, help="載入版本化的 JSON 資源設定")
    parser.add_argument("--quality", choices=[quality.value for quality in Quality], default="precise")
    parser.add_argument("--ram-budget-mib", type=int)
    parser.add_argument("--reserve-mib", type=int)
    parser.add_argument("--resource-wait-seconds", type=float)
    args = parser.parse_args()
    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
    try:
        saved = load_settings(args.settings) if args.settings else Settings()
        settings = Settings(
            ram_budget_mib=saved.ram_budget_mib if args.ram_budget_mib is None else args.ram_budget_mib,
            reserve_mib=saved.reserve_mib if args.reserve_mib is None else args.reserve_mib,
            resource_wait_seconds=saved.resource_wait_seconds if args.resource_wait_seconds is None
                                  else args.resource_wait_seconds,
        )
        runner = Runner(settings.policy(), max_resource_wait=settings.resource_wait_seconds)
        result = runner.run(Request(args.source, args.destination, Quality(args.quality)), cancel,
                            lambda state, message: print(f"{state.value}: {message}"))
        print(f"{result.state.value}: {result.message}")
        return 0 if result.state == State.COMPLETED else 1
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    finally:
        signal.signal(signal.SIGINT, previous)


if __name__ == "__main__":
    multiprocessing.freeze_support()
    raise SystemExit(main())

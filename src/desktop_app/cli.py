"""開發用命令列入口：與桌面共用設定、轉換任務及 RAM 調度。"""
import argparse
from dataclasses import replace
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
    parser.add_argument("--quality", choices=[quality.value for quality in Quality])
    parser.add_argument("--device", choices=["auto", "cpu", "gpu"])
    parser.add_argument("--cpu-threads", type=int)
    parser.add_argument("--ocr-backend", choices=["tesseract", "onnx", "onnx_verify", "managed_cpu"])
    parser.add_argument('--component-id',help='受管 OCR 元件識別名稱；只適用 managed_cpu')
    parser.add_argument('--component-version',help='固定已啟用版本；不自動切換')
    parser.add_argument("--vram-budget-mib", type=int)
    parser.add_argument("--ram-budget-mib", type=int)
    parser.add_argument("--reserve-mib", type=int)
    parser.add_argument("--resource-wait-seconds", type=float)
    args = parser.parse_args()
    cancel = Event()
    previous = signal.signal(signal.SIGINT, lambda *_: cancel.set())
    try:
        saved = load_settings(args.settings) if args.settings else Settings()
        settings = replace(saved,
            ram_budget_mib=saved.ram_budget_mib if args.ram_budget_mib is None else args.ram_budget_mib,
            reserve_mib=saved.reserve_mib if args.reserve_mib is None else args.reserve_mib,
            resource_wait_seconds=saved.resource_wait_seconds if args.resource_wait_seconds is None
                                  else args.resource_wait_seconds,
            device=saved.device if args.device is None else args.device,
            cpu_threads=saved.cpu_threads if args.cpu_threads is None else args.cpu_threads,
            ocr_backend=saved.ocr_backend if args.ocr_backend is None else args.ocr_backend,
            vram_budget_mib=saved.vram_budget_mib if args.vram_budget_mib is None else args.vram_budget_mib,
            quality=saved.quality if args.quality is None else args.quality,
        )
        context=None
        if settings.ocr_backend=='managed_cpu' and args.settings:
            from .components.management import ComponentManagement
            context=ComponentManagement(args.settings.parent,settings=settings).conversion_context()
        choice=next((item for item in settings.component_preferences if item.capability=='ocr.onnx.cpu'),None)
        component_id=args.component_id or (choice.component_id if choice and settings.ocr_backend=='managed_cpu' else None)
        version=args.component_version or (choice.version if choice and settings.ocr_backend=='managed_cpu' else None)
        runner = Runner(settings.policy(), max_resource_wait=settings.resource_wait_seconds,component_context=context)
        result = runner.run(Request(args.source, args.destination, Quality(settings.quality),
                                    settings.ocr_executable, settings.ocr_data_dir,
                                    settings.device, settings.cpu_threads, settings.ocr_backend,
                                    settings.vram_budget_mib,component_id,version), cancel,
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

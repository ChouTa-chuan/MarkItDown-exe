"""蒐集硬體與後端觀察，明確區分裝置偵測、provider 與真正可用的 GPU。"""
import csv
from dataclasses import dataclass
import io
import shutil
import subprocess


@dataclass(frozen=True)
class GPU:
    uuid: str
    name: str
    total_mib: int
    free_mib: int
    driver: str


@dataclass(frozen=True)
class DeviceReport:
    gpus: tuple[GPU, ...]
    providers: tuple[str, ...]
    notes: tuple[str, ...]


def parse_nvidia_csv(output):
    devices = []
    for row in csv.reader(io.StringIO(output), skipinitialspace=True):
        if not row:
            continue
        if len(row) != 5:
            raise ValueError("無法解析顯卡資訊。")
        uuid, name, total, free, driver = [value.strip() for value in row]
        total, free = int(total), int(free)
        if not uuid or not name or total <= 0 or free < 0 or free > total:
            raise ValueError("顯卡記憶體資訊無效。")
        devices.append(GPU(uuid, name, total, free, driver))
    return tuple(devices)


def probe_devices():
    """限時唯讀查詢顯卡與 provider；此函式不載入模型、不自動開啟 GPU。"""
    notes, gpus, providers = [], (), ()
    executable = shutil.which("nvidia-smi")
    if executable:
        try:
            result = subprocess.run([executable,
                "--query-gpu=uuid,name,memory.total,memory.free,driver_version",
                "--format=csv,noheader,nounits"], capture_output=True, text=True, timeout=5,
                check=True)
            gpus = parse_nvidia_csv(result.stdout)
        except (OSError, ValueError, subprocess.SubprocessError):
            notes.append("NVIDIA 查詢失敗；不能據此判定 GPU 可用。")
    else:
        notes.append("找不到 nvidia-smi；尚未驗證 NVIDIA 裝置，不代表不存在其他廠牌顯卡。")
    try:
        import onnxruntime
        providers = tuple(onnxruntime.get_available_providers())
    except (ImportError, OSError, RuntimeError):
        notes.append("ONNX Runtime provider 無法查詢。")
    notes.append("provider 清單只代表套件能力，不代表模型推論已驗證。")
    notes.append("目前 OCR 後端 Tesseract 僅支援 CPU，偵測到顯卡也不會自動啟用 GPU。")
    return DeviceReport(gpus, providers, tuple(notes))


def ocr_backend(device, backend="tesseract"):
    if device not in {"auto", "cpu", "gpu"}:
        raise ValueError("不支援的運算裝置設定。")
    if backend=='managed_cpu':
        if device=='gpu': raise ValueError('受管 CPU OCR 不支援 GPU；請選擇自動或 CPU。')
        return '受管 CPU OCR：需要 OCR 時才驗證已啟用元件，繁體品質仍為實驗性。'
    if backend in ("onnx", "onnx_verify"):
        return "ONNX OCR：裝置將於模型載入及 session 驗證後回報。"
    if backend != "tesseract":
        raise ValueError("不支援的 OCR 後端。")
    if device == "gpu":
        raise ValueError("目前 Tesseract OCR 不支援 GPU，請選擇自動或 CPU；GPU 模型後端尚未整合。")
    return "CPU／Tesseract（自動模式目前僅有 CPU 後端）" if device == "auto" else "CPU／Tesseract"

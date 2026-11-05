"""Optional RapidOCR adapter. CUDA is checked on every session, never assumed."""
import gc
from importlib import metadata
from pathlib import Path

from .core import Cancelled
from .models import digest

MODEL_HASHES = {
    "ch_PP-OCRv4_det_infer.onnx": "d2a7720d45a54257208b1e13e36a8479894cb74155a5efe29462512d42f49da9",
    "ch_PP-OCRv4_rec_infer.onnx": "48fc40f24f6d2a207a2b1091d3437eb3cc3eb6b676dc3ef9c37384005483683b",
    "ch_ppocr_mobile_v2.0_cls_infer.onnx": "e47acedf663230f8863ff1ab0e64dd2d82b838fceb5957146dab185a89d6215c",
}


def verify_models():
    import rapidocr_onnxruntime
    if metadata.version("rapidocr-onnxruntime") != "1.4.4":
        raise RuntimeError("ONNX OCR 僅驗證 rapidocr-onnxruntime 1.4.4，請使用鎖定版本。")
    directory = Path(rapidocr_onnxruntime.__file__).parent / "models"
    for name, expected in MODEL_HASHES.items():
        if digest(directory/name) != expected:
            raise RuntimeError(f"ONNX OCR 模型完整性驗證失敗：{name}")


def gpu_admission(report, budget_mib):
    if "CUDAExecutionProvider" not in report.providers:
        return False, "目前套件沒有 CUDAExecutionProvider。"
    if len(report.gpus) != 1:
        return False, "目前 CUDA 路由僅支援可查詢的單張 NVIDIA 顯卡。"
    if report.gpus[0].free_mib < budget_mib + 128:
        return False, "可用顯示記憶體不足預算及 128 MiB 保留量。"
    return True, "CUDA 准入通過；仍須建立並驗證推論 session。"


class OnnxOCR:
    def __init__(self, device="cpu", threads=1, vram_budget_mib=768,
                 checkpoint=lambda: None, progress=lambda text: None):
        self.checkpoint = checkpoint
        self.progress = progress
        self.requested_device = device
        self.threads = threads
        self.engine = None
        self.actual_device = "cpu"
        self.notice = "ONNX OCR 結果請核對，模型可能不涵蓋所有繁體字形。"
        if device not in ("auto", "cpu", "gpu"):
            raise ValueError("不支援的裝置。")
        if type(vram_budget_mib) is not int or vram_budget_mib < 192:
            raise ValueError("ONNX GPU 記憶體預算至少 192 MiB。")
        verify_models()
        use_cuda = False
        if device != "cpu":
            from .devices import probe_devices
            use_cuda, reason = gpu_admission(probe_devices(), vram_budget_mib)
            if not use_cuda:
                if device == "gpu":
                    raise RuntimeError(reason)
                progress("自動選擇 CPU：" + reason)
        self.checkpoint()
        self._create(threads)
        if use_cuda:
            failed = False
            try:
                options = {"device_id": 0, "gpu_mem_limit": vram_budget_mib*1024**2//3,
                           "arena_extend_strategy": "kSameAsRequested"}
                self._activate_cuda(options)
                self.actual_device = "cuda"
            except Cancelled:
                self.close()
                raise
            except Exception:
                if device == "gpu":
                    self.close()
                    raise RuntimeError("CUDA 初始化失敗；未自動改用 CPU。") from None
                failed = True
            if failed:
                # Leave the exception scope before releasing the engine so a
                # traceback cannot retain a CUDA session during CPU fallback.
                self.close()
                self.checkpoint()  # Parent RAM admission/backpressure before allocation.
                progress("CUDA 初始化失敗；通過 RAM checkpoint 後建立 CPU 後端。")
                self._create(threads)
        progress("ONNX session：" + ("CUDA 優先，尚待本頁推論" if self.actual_device == "cuda" else "CPU"))

    def _activate_cuda(self, options):
        for session in self.sessions():
            self.checkpoint()
            session.set_providers([("CUDAExecutionProvider", options), "CPUExecutionProvider"])
            session.disable_fallback()
            if session.get_providers()[0] != "CUDAExecutionProvider":
                raise RuntimeError("CUDA session 未啟用，拒絕隱藏的 CPU 回退。")

    def _create(self, threads):
        from rapidocr_onnxruntime import RapidOCR
        self.engine = RapidOCR(intra_op_num_threads=threads, inter_op_num_threads=1,
                               det_use_cuda=False, cls_use_cuda=False, rec_use_cuda=False)

    def sessions(self):
        return (self.engine.text_det.infer.session, self.engine.text_cls.infer.session,
                self.engine.text_rec.session.session)

    def recognize(self, image):
        import numpy as np
        self.checkpoint()
        failed = False
        # Keep RGB: RapidOCR accepts ndarray and performs its own preprocessing.
        try:
            with image.convert("RGB") as rgb:
                result, _ = self.engine(np.asarray(rgb)[:, :, ::-1].copy())
        except Cancelled:
            raise
        except Exception:
            if self.actual_device != "cuda" or self.requested_device != "auto":
                raise
            failed = True
        if failed:
            self.close()
            self.checkpoint()
            self.progress("CUDA 推論失敗；經 RAM checkpoint 後改用 CPU，本頁最多重試一次。")
            self._create(self.threads)
            self.actual_device = "cpu"
            with image.convert("RGB") as rgb:
                result, _ = self.engine(np.asarray(rgb)[:, :, ::-1].copy())
        self.checkpoint()
        if self.actual_device == "cuda":
            if any(session.get_providers()[0] != "CUDAExecutionProvider" for session in self.sessions()):
                raise RuntimeError("推論後發現 CUDA provider 已改變。")
            self.progress("本頁 ONNX 推論完成：CUDA 優先（部分算子可能由 CPU 執行）。")
        else:
            self.progress("本頁 ONNX 推論完成：CPU。")
        rows = result or []
        text = "\n".join(str(row[1]) for row in rows)
        warning = self.notice
        if any(float(row[2]) < 0.8 for row in rows):
            warning += " 部分文字的模型分數偏低。"
        return text, warning

    def close(self):
        self.engine = None
        gc.collect()

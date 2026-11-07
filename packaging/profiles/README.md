# 基本版相依 profile

`base.json` 是功能選擇；`base-{linux,windows}-{runtime,build}.txt` 是原版本／原 SHA-256 的閉包子集。`metadata-*.json` 保存相依證據，`base-closure.json` 列出完整邊與既有 Windows 授權引用。

```bash
python scripts/packaging_profiles.py
python scripts/packaging_profiles.py --generate
```

目前完成 C04 的依賴拆分與 Linux 基本核心打包／自檢兩個子檢核。原生 Tesseract、完整 profile 與 Windows 驗收尚未完成；原 Windows 建置入口仍採完整開發包。不能把這些 lock 當成已可離線 OCR 的 Windows 安裝包。

Magika 仍需要 ONNX Runtime，NumPy 仍供 Excel／核心依賴使用；基本版拆除 RapidOCR 及其 OCR 模型相依，不刪除必要核心 runtime。細節與重現方法見[profile 指南](../../docs/packaging-profiles.md)。

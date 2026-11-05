"""固定版本的 OCR 模型管理：可取消、驗證完整性，匯入模組不會連網。"""
import hashlib
from importlib.resources import files
import json
import os
from pathlib import Path
import tempfile
import urllib.request

from .core import Cancelled


def manifest():
    return json.loads(files("desktop_app").joinpath("data/ocr-models.json").read_text(encoding="utf-8"))


def digest(path):
    # 舊模型單檔上限為 16 MiB；較大的通用元件應使用獨立下載與驗證策略。
    if path.is_symlink() or not path.is_file():
        raise ValueError("模型須為一般檔案，不接受符號連結。")
    if path.stat().st_size > 16*1024**2:
        raise ValueError("模型超過允許大小。")
    result = hashlib.sha256()
    with path.open("rb") as source:
        while block := source.read(65536):
            result.update(block)
    return result.hexdigest()


def inspect(directory):
    result = {}
    for name, expected in manifest()["files"].items():
        path = directory/name
        try:
            result[name] = ("corrupt" if path.is_symlink() else "missing" if not path.exists()
                            else "valid" if digest(path) == expected else "corrupt")
        except (OSError, ValueError):
            result[name] = "corrupt"
    return result


def install(directory, cancel=None, progress=lambda text: None, opener=urllib.request.urlopen):
    """只下載固定清單中的模型與授權；既有內容不符時拒絕覆寫。"""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    spec = manifest()
    def checkpoint():
        if cancel is not None and cancel.is_set():
            raise Cancelled("模型下載已取消。")
    for name, expected in spec["files"].items():
        checkpoint()
        target = directory/name
        if target.exists():
            if digest(target) != expected:
                raise ValueError(f"既有檔案驗證失敗，未覆寫：{name}")
            progress(f"已驗證：{name}")
            continue
        temporary = None
        url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{spec['commit']}/{name}"
        try:
            with opener(url, timeout=10) as response:
                with tempfile.NamedTemporaryFile(dir=directory, prefix=".model-", delete=False) as output:
                    temporary = Path(output.name)
                    total = 0
                    while True:
                        checkpoint()
                        block = response.read(65536)
                        if not block:
                            break
                        total += len(block)
                        if total > 16*1024**2:
                            raise ValueError("模型超過允許大小。")
                        output.write(block)
                        progress(f"下載 {name}：{total//1024} KiB")
                    output.flush()
                    os.fsync(output.fileno())
            checkpoint()
            # 下載至暫存並完整驗證後才啟用；取消或雜湊不符不會留下半成品。
            if digest(temporary) != expected:
                raise ValueError(f"下載完整性驗證失敗：{name}")
            os.link(temporary, target)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    progress("模型及授權已全部驗證完成。")


def remove(directory):
    """只移除已辨識且未修改的受管檔案，保留未知資料。"""
    for name, expected in manifest()["files"].items():
        target = directory/name
        if target.is_symlink():
            raise ValueError(f"不移除符號連結：{name}")
        if target.exists() and digest(target) != expected:
            raise ValueError(f"檔案已被修改，未移除：{name}")
    for name in manifest()["files"]:
        (directory/name).unlink(missing_ok=True)

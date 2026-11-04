import os
from pathlib import Path
import tempfile

from .core import Request


def convert_text(request: Request, checkpoint, progress=lambda stage: None):
    """Checkpoint may pause or cancel at bounded text-processing boundaries."""
    destination = request.destination.resolve()
    checkpoint()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                dir=destination.parent, prefix=".conversion-", suffix=".tmp", delete=False) as output:
            temporary = Path(output.name)
            progress("轉換文字")
            with request.source.open(encoding="utf-8-sig", newline="") as source:
                while True:
                    checkpoint()
                    block = source.read(64*1024)
                    if not block:
                        break
                    output.write(block)
            output.flush()
            os.fsync(output.fileno())
        checkpoint()
        progress("提交輸出")
        # Same-volume exclusive publication. Unsupported filesystems fail
        # explicitly instead of falling back to overwriting existing output.
        os.link(temporary, destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)

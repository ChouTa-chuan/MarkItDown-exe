"""轉接既有 Tesseract 模型：只讀引用舊目錄，明確新建的受管目錄才可維護。"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path

from .. import models
from .registry import IntegrityError, _chain, _plain

OWNER_FILE = '.markitdown-model-owner.json'


@dataclass(frozen=True)
class LegacyModelAssessment:
    directory: str
    states: tuple[tuple[str, str], ...]
    owned: bool
    reference_id: str | None

    @property
    def models_available(self):
        return bool(self.states) and all(state == 'valid' for _, state in self.states)

    @property
    def engine_ready(self):
        # 只核對模型資料；引擎載入／真正推論屬 C03／C07，不冒充 C01 ready。
        return False


class LegacyModelsAdapter:
    """managed 是呼叫端允許新建專用目錄，不等於已有資料的所有權證據。"""

    def __init__(self, directory, registry=None, *, managed=False):
        self.directory = Path(directory).absolute()
        self.registry = registry
        self.managed = managed
        self.spec = models.manifest()
        self.manifest_hash = hashlib.sha256(json.dumps(self.spec, sort_keys=True).encode()).hexdigest()

    @property
    def _receipt(self):
        return dict(schema_version=1, purpose='markitdown-legacy-models',
                    directory=str(self.directory), manifest_hash=self.manifest_hash)

    def owns_directory(self):
        if not self.managed:
            return False
        try:
            _chain(self.directory)
            path = self.directory / OWNER_FILE
            _plain(path)
            if not path.is_file() or path.stat().st_size > 8192:
                return False
            return json.loads(path.read_bytes()) == self._receipt
        except (OSError, ValueError, IntegrityError):
            return False

    def can_install(self):
        if not self.managed:
            return False
        try:
            _chain(self.directory)
            return self.owns_directory() or not self.directory.exists() or (
                self.directory.is_dir() and next(self.directory.iterdir(), None) is None)
        except (OSError, IntegrityError):
            return False

    def observe(self):
        """重讀可信固定清單，登錄僅存觀察；未知檔案保留，不從 DB 取得所有權。"""
        try:
            _chain(self.directory)
            states = models.inspect(self.directory)
        except (OSError, IntegrityError):
            states = {name: 'corrupt' for name in self.spec['files']}
        owned = self.owns_directory()
        reference = None
        if self.registry is not None:
            origin = 'managed' if owned else 'legacy' if self.managed else 'external'
            reference = self.registry.record_model_reference(self.directory, origin, self.manifest_hash, states)
        return LegacyModelAssessment(str(self.directory), tuple(sorted(states.items())), owned,
                                     reference.reference_id if reference else None)

    def _claim_empty(self):
        if not self.can_install():
            raise PermissionError('既有／外部模型目錄只讀，請使用新的程式模型目錄。')
        self.directory.mkdir(parents=True, exist_ok=True)
        if self.owns_directory():
            return
        # 僅在明確下載時認領空目錄；收據不表示下載完成，取消後可沿用舊下載器續做。
        if next(self.directory.iterdir(), None) is not None:
            raise PermissionError('模型目錄已有資料，未接管或覆寫。')
        with (self.directory / OWNER_FILE).open('xb') as output:
            output.write((json.dumps(self._receipt, ensure_ascii=False, sort_keys=True) + '\n').encode())
            output.flush()
            os.fsync(output.fileno())

    def install(self, cancel=None, progress=lambda text: None, opener=None):
        self._claim_empty()
        options = {} if opener is None else {'opener': opener}
        # 原下載器的固定來源、16 MiB 限制、取消、暫存驗證與既有檔拒絕覆寫繼續沿用。
        models.install(self.directory, cancel, progress, **options)
        return self.observe()

    def remove(self):
        if not self.owns_directory():
            raise PermissionError('未確認所有權的模型不提供移除；外部與舊目錄保持原樣。')
        models.remove(self.directory)
        return self.observe()

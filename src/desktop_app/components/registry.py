"""本機 SQLite 元件登錄：持久化狀態與不可變描述，不下載、不解壓或刪除元件。"""
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import stat

from .contracts import ComponentSpec, ComponentState

MAX_COMPONENTS = 256
MAX_SPEC_BYTES = 256 * 1024


class RegistryError(RuntimeError):
    """登錄格式、資料完整性或本機儲存失敗，不靜默重設已有資料。"""


class ConcurrentChange(RegistryError):
    """檢查期間資料已被其他操作更新，舊結果不得覆蓋新狀態。"""


class IntegrityError(RegistryError):
    """包檔或安裝內容與固定描述不符。"""


def canonical_spec(spec):
    raw = json.dumps(spec.to_dict(), ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    if len(raw.encode('utf-8')) > MAX_SPEC_BYTES:
        raise RegistryError('元件描述超過登錄大小上限。')
    return raw


def _plain(path):
    """不接受符號連結與 Windows junction／reparse point。"""
    info = path.lstat()
    if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
        raise IntegrityError('受管理路徑不可含連結或 junction。')
    return info


def _chain(path):
    for item in (*reversed(path.parents), path):
        if item.exists() or item.is_symlink():
            _plain(item)


def verify_file(path, expected_size, expected_hash, checkpoint=lambda: None):
    """固定緩衝串流驗證；拒絕巨大替換檔，取消時不回寫驗證成功。"""
    _chain(path)
    info = _plain(path)
    if not stat.S_ISREG(info.st_mode) or info.st_size != expected_size:
        raise IntegrityError('檔案類型或大小與描述不符。')
    digest = hashlib.sha256()
    with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0)), 'rb') as source:
        before = os.fstat(source.fileno())
        total = 0
        while True:
            checkpoint()
            block = source.read(65536)
            if not block:
                break
            total += len(block)
            if total > expected_size:
                raise IntegrityError('驗證時檔案大小改變。')
            digest.update(block)
        after = os.fstat(source.fileno())
    identity = lambda value: (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns)
    if identity(info) != identity(before) or identity(before) != identity(after) or total != expected_size:
        raise IntegrityError('驗證期間檔案遭變更。')
    if digest.hexdigest() != expected_hash:
        raise IntegrityError('檔案 SHA-256 與描述不符。')


@dataclass(frozen=True)
class ComponentRecord:
    spec: ComponentSpec
    state: ComponentState
    archive_path: str | None
    installed: bool
    reason: str
    generation: int
    checked_at: str


class ComponentRegistry:
    """登錄只保存上次觀察；可用性必須透過 CapabilityResolver 重新取得證據。"""

    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        _chain(self.directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        self.database = self.directory / 'component-registry.sqlite3'
        self.payloads = self.directory / 'components'
        if self.database.exists():
            _plain(self.database)
            if self.database.stat().st_size > 128 * 1024**2:
                raise RegistryError('登錄檔超過讀取上限。')
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if version == 0 and not tables:
                db.execute('''CREATE TABLE components (
                    component_id TEXT NOT NULL, version TEXT NOT NULL,
                    spec_json TEXT NOT NULL, spec_hash TEXT NOT NULL,
                    state TEXT NOT NULL, archive_path TEXT,
                    installed INTEGER NOT NULL, reason TEXT NOT NULL,
                    generation INTEGER NOT NULL, checked_at TEXT NOT NULL,
                    PRIMARY KEY (component_id, version))''')
                db.execute('PRAGMA user_version=1')
            elif version != 1 or tables != {'components'}:
                raise RegistryError('不支援的登錄版本或資料表，原檔未重設。')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(components)')}
            if columns != {'component_id', 'version', 'spec_json', 'spec_hash', 'state', 'archive_path',
                           'installed', 'reason', 'generation', 'checked_at'}:
                raise RegistryError('元件登錄欄位不符合目前契約。')
            count, length = db.execute('SELECT COUNT(*), COALESCE(MAX(length(spec_json)), 0) FROM components').fetchone()
            if count > MAX_COMPONENTS or length > MAX_SPEC_BYTES:
                raise RegistryError('登錄內容超過限制。')

    @contextmanager
    def _connection(self):
        _chain(self.directory)
        if self.database.exists() or self.database.is_symlink():
            if not stat.S_ISREG(_plain(self.database).st_mode):
                raise RegistryError('元件登錄須為一般檔案。')
        db = None
        try:
            db = sqlite3.connect(self.database, timeout=5)
            db.row_factory = sqlite3.Row
            with db:
                yield db
        except sqlite3.Error as exc:
            raise RegistryError('元件登錄讀寫失敗，沒有重設資料。') from exc
        finally:
            if db is not None:
                db.close()

    def register(self, spec):
        """相同 ID／版號的描述固定；未經下載、驗證或健康檢查仍為 missing。"""
        raw = canonical_spec(spec)
        digest = hashlib.sha256(raw.encode()).hexdigest()
        with self._connection() as db:
            db.execute('BEGIN IMMEDIATE')
            previous = db.execute('SELECT spec_json FROM components WHERE component_id=? AND version=?', spec.key).fetchone()
            if previous is not None:
                if previous['spec_json'] != raw:
                    raise RegistryError('相同元件版本不能替換成另一份描述。')
            else:
                if db.execute('SELECT COUNT(*) FROM components').fetchone()[0] >= MAX_COMPONENTS:
                    raise RegistryError('元件登錄數量已達上限。')
                db.execute('INSERT INTO components VALUES (?,?,?,?,?,?,?,?,?,?)',
                           (*spec.key, raw, digest, ComponentState.MISSING.value, None, 0, '', 0, ''))
        return self.get(*spec.key)

    def get(self, component_id, version):
        with self._connection() as db:
            row = db.execute('SELECT * FROM components WHERE component_id=? AND version=?', (component_id, str(version))).fetchone()
        if row is None:
            return None
        try:
            raw = row['spec_json']
            if not isinstance(raw, str) or len(raw.encode()) > MAX_SPEC_BYTES or hashlib.sha256(raw.encode()).hexdigest() != row['spec_hash']:
                raise RegistryError('登錄描述的雜湊不符。')
            spec = ComponentSpec.from_dict(json.loads(raw))
            if spec.key != (component_id, str(version)) or row['installed'] not in (0, 1) or type(row['generation']) is not int or row['generation'] < 0:
                raise RegistryError('登錄識別或狀態欄位無效。')
            if not isinstance(row['reason'], str) or len(row['reason']) > 2048 or not isinstance(row['checked_at'], str) or len(row['checked_at']) > 64:
                raise RegistryError('登錄說明或時間格式無效。')
            if row['archive_path'] is not None and (not isinstance(row['archive_path'], str) or len(row['archive_path']) > 4096):
                raise RegistryError('登錄的包檔位置無效。')
            return ComponentRecord(spec, ComponentState(row['state']), row['archive_path'], bool(row['installed']),
                                   row['reason'], row['generation'], row['checked_at'])
        except (ValueError, TypeError, KeyError, RecursionError) as exc:
            raise RegistryError('元件登錄內容無效。') from exc

    def installation_path(self, spec):
        return self.payloads / spec.component_id / str(spec.version)

    def _update(self, record, state, reason='', *, archive_path=None, installed=None):
        """以世代號比對寫入，禁止先前慢速檢查覆蓋並行更新；不暴露任意 SQL。"""
        with self._connection() as db:
            changed = db.execute('''UPDATE components SET state=?, archive_path=?, installed=?, reason=?,
                generation=generation+1, checked_at=? WHERE component_id=? AND version=? AND generation=?''',
                (state.value, archive_path if archive_path is not None else record.archive_path,
                 int(record.installed if installed is None else installed), str(reason)[:2048],
                 datetime.now(timezone.utc).isoformat(), *record.spec.key, record.generation))
            if changed.rowcount != 1:
                raise ConcurrentChange('元件在檢查期間已更新，請重新取得狀態。')
        return self.get(*record.spec.key)

    def record_download(self, spec, archive):
        record = self.get(*spec.key)
        if record is None or record.spec != spec or record.installed:
            raise RegistryError('下載登錄需要相符描述，且不能直接覆蓋已安裝版本。')
        path = Path(archive).absolute()
        _chain(path)
        info = _plain(path)
        if not stat.S_ISREG(info.st_mode) or info.st_size != spec.download_bytes:
            raise IntegrityError('下載檔案尚未完整。')
        return self._update(record, ComponentState.DOWNLOADED, archive_path=str(path))

    def verify_download(self, spec, checkpoint=lambda: None):
        record = self.get(*spec.key)
        if record is None or record.spec != spec or record.state not in (ComponentState.DOWNLOADED, ComponentState.VERIFIED):
            raise RegistryError('必須先登錄完整下載檔。')
        try:
            verify_file(Path(record.archive_path), spec.download_bytes, spec.package_sha256, checkpoint)
        except (OSError, IntegrityError) as exc:
            return self._update(record, ComponentState.CORRUPT, str(exc))
        return self._update(record, ComponentState.VERIFIED)

    def verify_installation(self, spec, checkpoint=lambda: None):
        """安裝內容完整列舉；額外檔案、符號連結、缺檔與大小漂移都不通過。"""
        directory = self.installation_path(spec)
        _chain(directory)
        if not stat.S_ISDIR(_plain(directory).st_mode):
            raise IntegrityError('找不到元件安裝目錄。')
        expected = {item.path for item in spec.files}
        actual = set()
        entries = 0
        def walk_error(error):
            raise error
        for parent, dirs, files in os.walk(directory, followlinks=False, onerror=walk_error):
            checkpoint()
            for name in (*dirs, *files):
                entries += 1
                if entries > 8192:
                    raise IntegrityError('安裝目錄超過列舉上限。')
                _plain(Path(parent) / name)
            for name in files:
                actual.add((Path(parent) / name).relative_to(directory).as_posix())
        if actual != expected:
            raise IntegrityError('安裝檔案清單不符，存在缺檔或額外檔案。')
        for item in spec.files:
            checkpoint()
            verify_file(directory / item.path, item.size, item.sha256, checkpoint)

    def record_installation(self, spec, checkpoint=lambda: None):
        record = self.get(*spec.key)
        if record is None or record.spec != spec or record.state != ComponentState.VERIFIED:
            raise RegistryError('只有已驗證的下載才能登錄安裝內容。')
        try:
            self.verify_installation(spec, checkpoint)
        except (OSError, IntegrityError) as exc:
            return self._update(record, ComponentState.CORRUPT, str(exc))
        return self._update(record, ComponentState.INSTALLED, installed=True)

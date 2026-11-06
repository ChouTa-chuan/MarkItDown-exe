"""元件維護日誌與 active 指標；獨立 SQLite schema 1，不改 C02 登錄格式。"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import stat

from .contracts import ComponentSpec, ComponentState, Version
from .registry import _chain, _plain, canonical_spec


class LifecycleError(RuntimeError):
    """安裝、所有權或恢復證據不足；保留資料並明確拒絕操作。"""


def spec_hash(spec):
    return hashlib.sha256(canonical_spec(spec).encode()).hexdigest()


class LifecycleStore:
    def __init__(self, directory):
        self.directory = Path(directory).absolute()
        self.database = self.directory/'lifecycle.sqlite3'
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            version = db.execute('PRAGMA user_version').fetchone()[0]
            tables = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            if version == 0 and not tables:
                db.execute('CREATE TABLE owned (component_id TEXT, version TEXT, spec_hash TEXT NOT NULL, token TEXT NOT NULL, PRIMARY KEY(component_id,version))')
                db.execute('CREATE TABLE active (component_id TEXT PRIMARY KEY, version TEXT NOT NULL, previous_version TEXT)')
                db.execute('CREATE TABLE journal (token TEXT PRIMARY KEY, data TEXT NOT NULL)')
                db.execute('PRAGMA user_version=1')
            elif version != 1 or tables != {'owned','active','journal'}:
                raise LifecycleError('不支援的維護資料庫，原檔未重設。')
            expected = {'owned':{'component_id','version','spec_hash','token'},
                        'active':{'component_id','version','previous_version'},'journal':{'token','data'}}
            for table,columns in expected.items():
                if {row['name'] for row in db.execute(f'PRAGMA table_info({table})')} != columns:
                    raise LifecycleError('維護資料庫欄位不符，未重設。')
                if db.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0] > 256:
                    raise LifecycleError('維護資料庫筆數超限。')

    @contextmanager
    def connection(self):
        _chain(self.directory)
        self.directory.mkdir(parents=True,exist_ok=True)
        if self.database.exists() or self.database.is_symlink():
            info = _plain(self.database)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 128*1024**2:
                raise LifecycleError('維護資料庫類型或大小無效。')
        db = None
        try:
            db = sqlite3.connect(self.database, timeout=5)
            db.row_factory = sqlite3.Row
            with db:yield db
        except sqlite3.Error as exc:
            raise LifecycleError('維護資料庫讀寫失敗，沒有清空資料。') from exc
        finally:
            if db is not None:db.close()

    def owned(self, spec):
        with self.connection() as db:
            row = db.execute('SELECT * FROM owned WHERE component_id=? AND version=?',spec.key).fetchone()
        if row is None:return None
        if row['spec_hash'] != spec_hash(spec) or not isinstance(row['token'],str) or not re.fullmatch('[0-9a-f]{32}',row['token']):
            raise LifecycleError('元件所有權紀錄不符，未接管原資料。')
        return dict(row)

    def owned_keys(self):
        with self.connection() as db:
            return tuple((row[0],row[1]) for row in db.execute('SELECT component_id,version FROM owned'))

    def active(self):
        with self.connection() as db:
            result = {}
            for row in db.execute('SELECT * FROM active'):
                Version.parse(row['version'])
                if row['previous_version'] is not None:Version.parse(row['previous_version'])
                result[row['component_id']] = (row['version'],row['previous_version'])
            return result

    @staticmethod
    def validate_journal(value):
        if not isinstance(value,dict) or set(value) != {
                'schema_version','token','operation','spec','previous_record','had_payload','phase'}:
            raise LifecycleError('維護日誌欄位不符。')
        if (type(value['schema_version']) is not int or value['schema_version'] != 1
                or not isinstance(value['token'],str) or not re.fullmatch('[0-9a-f]{32}',value['token'])
                or value['operation'] not in ('install','repair','remove') or value['phase'] not in ('preparing','committed')
                or type(value['had_payload']) is not bool):
            raise LifecycleError('維護日誌識別或狀態不符。')
        if value['operation']=='install' and value['had_payload']:
            raise LifecycleError('新安裝不能接管既有目標。')
        spec = ComponentSpec.from_dict(value['spec'])
        old = value['previous_record']
        if old is not None:
            if not isinstance(old,dict) or set(old) != {'state','installed','reason'} or type(old['installed']) is not bool:
                raise LifecycleError('維護日誌原狀態無效。')
            ComponentState(old['state'])
            if not isinstance(old['reason'],str) or len(old['reason']) > 2048:
                raise LifecycleError('維護日誌原說明無效。')
        return spec

    def journals(self):
        with self.connection() as db:
            rows = db.execute('SELECT * FROM journal').fetchall()
        if len(rows)>256:raise LifecycleError('維護日誌數量超限。')
        result = []
        for row in rows:
            try:
                if not isinstance(row['data'],str) or len(row['data'].encode())>300*1024:
                    raise LifecycleError('維護日誌大小無效。')
                value = json.loads(row['data'])
                self.validate_journal(value)
                if value['token'] != row['token']:raise LifecycleError('維護日誌 token 不符。')
                result.append(value)
            except (ValueError,TypeError,RecursionError) as exc:
                raise LifecycleError('維護日誌損毀，沒有清空或刪檔。') from exc
        return tuple(result)

    def begin(self, value):
        self.validate_journal(value)
        raw = json.dumps(value,ensure_ascii=False,sort_keys=True)
        if len(raw.encode())>300*1024:raise LifecycleError('維護日誌超限。')
        with self.connection() as db:
            if db.execute('SELECT COUNT(*) FROM journal').fetchone()[0]>=256:
                raise LifecycleError('維護日誌已滿。')
            db.execute('INSERT INTO journal VALUES (?,?)',(value['token'],raw))

    @staticmethod
    def _activate(db, spec):
        row = db.execute('SELECT version,previous_version FROM active WHERE component_id=?',(spec.component_id,)).fetchone()
        previous = None if row is None else row['previous_version'] if row['version']==str(spec.version) else row['version']
        db.execute('INSERT INTO active VALUES (?,?,?) ON CONFLICT(component_id) DO UPDATE SET version=excluded.version, previous_version=excluded.previous_version',
                   (spec.component_id,str(spec.version),previous))

    def activate(self, spec):
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            self._activate(db,spec)

    def commit(self, value):
        spec = self.validate_journal(value)
        value = {**value,'phase':'committed'}
        with self.connection() as db:
            db.execute('BEGIN IMMEDIATE')
            if value['operation']=='remove':
                db.execute('DELETE FROM owned WHERE component_id=? AND version=?',spec.key)
                db.execute('DELETE FROM active WHERE component_id=? AND version=?',spec.key)
            else:
                db.execute('INSERT INTO owned VALUES (?,?,?,?) ON CONFLICT(component_id,version) DO UPDATE SET spec_hash=excluded.spec_hash,token=excluded.token',
                           (*spec.key,spec_hash(spec),value['token']))
                self._activate(db,spec)
            db.execute('UPDATE journal SET data=? WHERE token=?',
                       (json.dumps(value,ensure_ascii=False,sort_keys=True),value['token']))

    def finish(self, token):
        with self.connection() as db:db.execute('DELETE FROM journal WHERE token=?',(token,))

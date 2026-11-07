"""C09：離線建議、唯讀引擎檢查與有版本的首次設定；不下載或接管模型。"""
from dataclasses import dataclass, replace
import hashlib
from importlib import resources
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import tempfile
from threading import Event
import time

from ..core import Cancelled
from .. import models
from ..resources import MIB, snapshot
from ..settings import Settings, _read, load_settings, save_settings

ONBOARDING_VERSION = 1


@dataclass(frozen=True)
class RamAdvice:
    total_mib: int
    available_mib: int
    automatic_budget_mib: int
    reserve_mib: int


def recommend_ram(observation):
    if observation.total <= 0 or not 0 <= observation.available <= observation.total:
        raise ValueError('記憶體量測無效；不產生 RAM 建議。')
    total = max(1, observation.total//MIB)
    return RamAdvice(total, observation.available//MIB, max(1,total//4), min(2048,max(128,total//8)))


@dataclass(frozen=True)
class EngineObservation:
    ready: bool
    executable: str | None
    data_dir: str | None
    origin: str
    version: str
    languages: tuple[str, ...]
    samples: tuple[tuple[str,str], ...]
    message: str


@dataclass(frozen=True)
class SetupReport:
    ram: RamAdvice
    engine: EngineObservation
    existing_settings: bool


def native_command(command, cancel, *, timeout=12):
    """有界原生探針：只處理合成影像，stdout/stderr 不用無界 PIPE，不回傳原生錯誤內容。"""
    if cancel.is_set(): raise Cancelled('首次檢查已取消。')
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        child = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=output, stderr=errors,
            shell=False, env={**os.environ,'OMP_THREAD_LIMIT':'1','OMP_NUM_THREADS':'1'},
            creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        started = time.monotonic()
        try:
            while child.poll() is None:
                if cancel.wait(0.025): raise Cancelled('首次檢查已取消。')
                if time.monotonic()-started > timeout: raise RuntimeError('基本引擎檢查逾時。')
                if max(os.fstat(output.fileno()).st_size,os.fstat(errors.fileno()).st_size)>65536:
                    raise RuntimeError('基本引擎診斷輸出超過限制。')
            if cancel.is_set(): raise Cancelled('首次檢查已取消。')
            if child.returncode != 0: raise RuntimeError(f'基本引擎執行失敗，exitcode={child.returncode}。')
            output.seek(0); raw=output.read(65537)
            if len(raw)>65536 or os.fstat(errors.fileno()).st_size>65536: raise RuntimeError('基本引擎輸出超過限制。')
            return raw.decode('utf-8',errors='replace')
        finally:
            if child.poll() is None:
                child.terminate()
                try: child.wait(timeout=1)
                except subprocess.TimeoutExpired: child.kill(); child.wait(timeout=2)


def probe_engine(settings, directory, cancel, check=lambda:None, *, which=shutil.which):
    """明確路徑失效不回退；自動候選只讀本機，不查網路或安裝選配。"""
    executable=settings.ocr_executable
    origin='使用者既有設定' if executable is not None else '本機 PATH'
    data=settings.ocr_data_dir
    version=''; languages=(); samples=[]
    try:
        check()
        if executable is not None:
            candidate=Path(executable)
            executable=str(candidate.absolute()) if candidate.is_file() else which(executable)
        else: executable=which('tesseract')
        if not executable: raise RuntimeError('找不到基本 Tesseract 引擎；可繼續文字轉換，掃描 OCR 仍待設定。')
        executable=str(Path(executable).absolute())
        if data is not None:
            if not Path(data).is_dir(): raise RuntimeError('已指定的模型目錄不存在，未改用其他目錄。')
        else:
            for candidate in (Path(directory)/'models/tesseract-managed',Path(directory)/'models/tesseract'):
                if candidate.is_dir() and all(value=='valid' for value in models.inspect(candidate).values()):
                    data=str(candidate.absolute()); break
            if data is None and os.environ.get('TESSDATA_PREFIX'):
                data=os.environ['TESSDATA_PREFIX']
        data_args=['--tessdata-dir',data] if data is not None else []
        version=native_command([executable,'--version'],cancel,timeout=5).splitlines()[0][:200]
        if not version.lower().startswith('tesseract '): raise RuntimeError('指定程式未回報 Tesseract 版本。')
        check()
        language_text=native_command([executable,'--list-langs',*data_args],cancel,timeout=5)
        languages=tuple(sorted(set(line.strip() for line in language_text.splitlines()[1:] if line.strip())))
        if not {'chi_tra','eng'}<=set(languages): raise RuntimeError('基本 OCR 須具備 chi_tra 與 eng；未自動下載或改成其他引擎。')
        from PIL import Image
        from ..pdf_pipeline import _normalize_ocr_image
        asset_root=Path(resources.files('desktop_app').joinpath('data'))
        for name,manifest_name in (('worker-health.png','worker-health.json'),('setup-chinese.png','setup-chinese.json')):
            check()
            reference=json.loads((asset_root/manifest_name).read_bytes()); path=asset_root/name
            if hashlib.sha256(path.read_bytes()).hexdigest()!=reference['sha256']: raise RuntimeError('合成健康樣本完整性異常。')
            expected=reference.get('expected',reference.get('reference'))
            with tempfile.TemporaryDirectory(prefix='markitdown-setup-health-') as temporary:
                source=Path(temporary)/'health.png'
                with Image.open(path) as image:
                    prepared,dpi=_normalize_ocr_image(image,144)
                    try: prepared.save(source)
                    finally: prepared.close()
                text=native_command([executable,str(source),'stdout','-l','chi_tra+eng','--dpi',str(dpi),'--psm','11',*data_args],cancel)
            if ''.join(expected.split()) not in ''.join(text.split()): raise RuntimeError('基本 OCR 合成健康樣本未達目標，請稍後重新檢查。')
            samples.append((name,text))
        check()
        return EngineObservation(True,executable,data,origin,version,languages,tuple(samples),
            '本機 CPU 引擎及繁中／英文合成辨識通過；不代表任意文件準確率或 Windows 基本包已驗收。')
    except Cancelled: raise
    except Exception as exc:
        return EngineObservation(False,executable,data,origin,version,languages,tuple(samples),f'{type(exc).__name__}: {exc}')


class SetupSession:
    def __init__(self,path,*,settings=None,expected_settings=None):
        self.path=Path(path)
        if self.path.is_symlink(): raise ValueError('首次設定不寫入符號連結設定檔。')
        if self.path.exists() and not stat.S_ISREG(self.path.stat().st_mode): raise ValueError('設定須為一般檔案。')
        self.raw=_read(self.path) if self.path.exists() else None
        # 損毀／未來設定不自動重設；保留原文，由既有載入規則拒絕。
        saved=load_settings(self.path) if self.raw is not None else Settings()
        if expected_settings is not None and saved != expected_settings:
            raise ValueError('設定在其他視窗已變更，請先重新載入；原檔未覆寫。')
        self.settings=settings if settings is not None else saved
        self.existing=self.raw is not None

    @property
    def due(self):
        return self.settings.onboarding_version<ONBOARDING_VERSION

    def inspect(self,cancel=None,*,read_snapshot=snapshot,probe=probe_engine):
        cancel=cancel if cancel is not None else Event()
        def check():
            if cancel.is_set(): raise Cancelled('首次檢查已取消。')
        check(); observation=read_snapshot(); advice=recommend_ram(observation)
        effective=self.settings if self.existing else replace(self.settings,reserve_mib=advice.reserve_mib)
        def admitted():
            check(); allowed,reason=effective.policy().admit(read_snapshot(),256*MIB)
            if not allowed: raise RuntimeError(reason+' 基本引擎檢查尚未完成，可稍後重試。')
        # RAM 不足也能返回建議與未就緒原因，不阻擋文字功能或儲存完成標記。
        try: admitted(); engine=probe(effective,self.path.parent,cancel,admitted)
        except Cancelled: raise
        except Exception as exc: engine=EngineObservation(False,None,None,'未啟動','',(),(),str(exc))
        check(); return SetupReport(advice,engine,self.existing)

    def complete(self,report,*,apply_ram=False,apply_engine=False):
        if not isinstance(report,SetupReport): raise ValueError('請先完成本機檢查。')
        result=replace(self.settings,onboarding_version=max(ONBOARDING_VERSION,self.settings.onboarding_version))
        if apply_ram: result=replace(result,ram_budget_mib=None,reserve_mib=report.ram.reserve_mib)
        if apply_engine and report.engine.ready:
            # 即使勾選自動填入，也不取代已明確指定的引擎／目錄或 OCR 後端。
            result=replace(result,ocr_executable=result.ocr_executable if result.ocr_executable is not None else report.engine.executable,
                           ocr_data_dir=result.ocr_data_dir if result.ocr_data_dir is not None else report.engine.data_dir)
        save_settings(result,self.path,expected_raw=self.raw)
        self.raw=_read(self.path); self.settings=result
        return result

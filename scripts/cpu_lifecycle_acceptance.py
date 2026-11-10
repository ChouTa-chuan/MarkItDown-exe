"""對已安裝的真 CPU bundle 驗證維護；合成文件與取消停點僅限 CI 自有目錄。"""
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
from threading import Event

from desktop_app.components.archives import verify_tree
from desktop_app.components.contracts import ComponentState
from desktop_app.components.lifecycle_store import LifecycleError
from desktop_app.components.locks import ComponentBusy
from desktop_app.components.registry import IntegrityError
from desktop_app.core import Cancelled


def require(value, message):
    if not value:raise AssertionError(message)


def digest(path):
    with Path(path).open('rb') as source:return hashlib.file_digest(source,'sha256').hexdigest()


def rejected(error, operation):
    """必須收到指定失敗；一般例外或靜默成功均不能當作拒絕證據。"""
    try:operation()
    except error:return
    raise AssertionError('Maintenance unexpectedly succeeded: '+error.__name__)


def acceptance(manager, catalog, spec, archive, root, report_path):
    root=Path(root);archive=Path(archive);report_path=Path(report_path)
    require(not report_path.exists(),'Use a fresh lifecycle report')
    target=manager.registry.installation_path(spec)
    active=manager.store.active();archive_hash=digest(archive)
    document=root/'使用者合成文件.md';settings=root/'使用者合成設定.json'
    # 不讀取或擷取使用者真實文件，兩個檔案均由本次驗收獨有的空目錄建立。
    fixtures={document:'保留合成文件\n'.encode(),settings:b'{"fixture":true}\n'}
    for path,data in fixtures.items():
        with path.open('xb') as output:output.write(data)
    report=dict(accepted=False,checks_passed=0,checks=[],scope='same-version-cpu-component-maintenance',
        process_termination_executed=False,cross_version_executed=False,
        clean_machine_accepted=False,gpu_executed=False,release_ready=False)

    def stable():
        verify_tree(target,spec)
        require(manager.store.active()==active,'Active version changed')
        require(not manager.store.journals(),'Unfinished maintenance transaction')
        record=manager.registry.get(*spec.key)
        require(record.state==ComponentState.READY and record.installed,'Registry not ready')
        require(digest(archive)==archive_hash,'Original cached archive changed')
        for path,data in fixtures.items():require(path.read_bytes()==data,'Synthetic user data changed')

    def reuse():manager.install(catalog,*spec.key,archive)

    def incompatible():
        previous=manager.host
        try:
            manager.host=replace(previous,architecture='arm64')
            rejected(LifecycleError,lambda:manager.repair(catalog,*spec.key,archive))
        finally:manager.host=previous

    def leased():
        with manager.lease(catalog,spec.component_id):
            rejected(ComponentBusy,lambda:manager.repair(catalog,*spec.key,archive))
            rejected(ComponentBusy,lambda:manager.remove(*spec.key))

    def bad_archive():
        bad=root/'故意損壞的副本.zip'
        with archive.open('rb') as source,bad.open('xb') as output:shutil.copyfileobj(source,output)
        with bad.open('r+b') as output:
            original=output.read(1);require(original,'Empty source archive')
            output.seek(0);output.write(bytes([original[0]^1]))
        rejected(IntegrityError,lambda:manager.repair(catalog,*spec.key,bad))

    def cancel_after_publish():
        cancel=Event();previous=manager.fault;stages=[]
        def fault(stage):
            previous(stage);stages.append(stage)
            if stage=='published':cancel.set()
        try:
            manager.fault=fault
            rejected(Cancelled,lambda:manager.repair(catalog,*spec.key,archive,cancel=cancel))
            require('published' in stages,'Repair did not reach the cancellation point')
        finally:manager.fault=previous

    def damaged_payload():
        # 只改自己安裝的公開測試影像；完整性檢查須先拒絕，不能執行損壞程式。
        item=next((item for item in spec.files if item.path.endswith('/worker-health.png')),spec.files[0])
        path=target/item.path
        with path.open('r+b') as output:
            original=output.read(1);require(original,'Empty corruption fixture')
            output.seek(0);output.write(bytes([original[0]^1]))
        rejected(IntegrityError,lambda:manager.check_health(catalog,*spec.key))
        manager.repair(catalog,*spec.key,archive)
        manager.check_health(catalog,*spec.key)

    def unknown_file():
        unknown=target/'不可接管的合成文件.md';data=b'unknown synthetic document\n'
        with unknown.open('xb') as output:output.write(data)
        rejected(IntegrityError,lambda:manager.remove(*spec.key))
        require(unknown.read_bytes()==data,'Unknown file removed or modified')
        # 只有本次建立、且仍完全相同的 fixture 才由驗收程式取回；產品不刪未知資料。
        unknown.unlink()

    def remove_reinstall():
        manager.remove(*spec.key)
        require(not target.exists(),'Idle component directory remains')
        require(spec.component_id not in manager.store.active(),'Removed component remains active')
        for path,data in fixtures.items():require(path.read_bytes()==data,'Removal changed synthetic data')
        require(digest(archive)==archive_hash,'Removal changed cached package')
        manager.install(catalog,*spec.key,archive)

    cases=[('existing install revalidated',reuse),('incompatible architecture rejected',incompatible),
        ('active lease blocks repair and removal',leased),('bad archive preserves installation',bad_archive),
        ('cancel after publish restores previous payload',cancel_after_publish),
        ('damaged payload rejected and repaired with real health',damaged_payload),
        ('unknown file blocks removal and remains unchanged',unknown_file),
        ('idle removal preserves synthetic data and cache then reinstalls',remove_reinstall)]
    report_path.parent.mkdir(parents=True,exist_ok=True)
    def save():report_path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    save()
    try:
        stable()
        for label,operation in cases:
            report['current_check']=label;operation();stable()
            report['checks'].append(label);report['checks_passed']=len(report['checks']);save()
        report.update(accepted=True,synthetic_data_preserved=True,archive_unchanged=True,
            payload_verified=True,journals_empty=True)
        report.pop('current_check',None);save()
    except Exception as exc:
        report['error']=type(exc).__name__+': '+str(exc);save();raise
    return report

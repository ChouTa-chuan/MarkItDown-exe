"""基本安裝包的受管檔案清單；只驗完整性，不作簽章或再散布核准。"""
import json
from pathlib import Path
import re

from desktop_app.components.contracts import Version, relative_path
from desktop_app.components.registry import _chain, verify_file
from desktop_app.native_assets import file_hash

CATALOG = 'base-install-catalog.json'
ENTRY = 'MarkItDownBase.exe'
APP_ID = '{DB61BCA4-7678-4BEA-9140-27B548460D75}'
MAX_FILES = 20000


def encoded(document):
    return (json.dumps(document,ensure_ascii=False,indent=2)+'\n').encode('utf-8')


def validate(document):
    if (document.get('schema_version')!=1 or document.get('profile')!='base'
            or document.get('platform')!='windows-x64' or document.get('entrypoint')!=ENTRY
            or document.get('release_ready') is not False):
        raise ValueError('基本安裝清單契約不符。')
    Version.parse(document['app_version'])
    records=document['files']
    if not isinstance(records,list) or not 1<=len(records)<=MAX_FILES:raise ValueError('安裝清單數量不符。')
    seen=set()
    for item in records:
        name=relative_path(item['path'])
        if (name.casefold() in seen or name.casefold()==CATALOG or re.fullmatch(r'unins\d{3}\..*',name,re.I)
                or type(item['bytes']) is not int or not 0<=item['bytes']<=128*1024**2
                or not re.fullmatch('[0-9a-f]{64}',item['sha256'])):
            raise ValueError('清單有重複、保留名稱或不合法的 digest／size。')
        seen.add(name.casefold())
    if ENTRY.casefold() not in seen:raise ValueError('基本程式入口缺少。')
    return document


def create(directory,version):
    directory=Path(directory)
    _chain(directory)
    Version.parse(version)
    target=directory/CATALOG
    if target.exists():raise FileExistsError(target)
    profile=json.loads((directory/'_internal/desktop_app/data/build-profile.json').read_text(encoding='utf-8'))
    if (profile.get('id')!='base' or profile.get('platform')!='windows'
            or profile.get('native_ocr_integrated') is not True or profile.get('source_version')!=version):
        raise ValueError('須使用同版 Windows 內含四語基本包。')
    records=[]
    for path in sorted(directory.rglob('*')):
        _chain(path)
        if path.is_file():
            digest,size=file_hash(path)
            records.append(dict(path=path.relative_to(directory).as_posix(),bytes=size,sha256=digest))
    document=validate(dict(schema_version=1,profile='base',platform='windows-x64',entrypoint=ENTRY,
                           app_version=version,release_ready=False,files=records))
    with target.open('xb') as output:output.write(encoded(document))
    return document


def verify(directory,expected,*,allowed_extras=None,installed=False):
    """信任同次建置保留的 expected，不重新信任安裝目錄內可被更改的清單。"""
    directory=Path(directory)
    validate(expected)
    _chain(directory/CATALOG)
    if (directory/CATALOG).read_bytes()!=encoded(expected):raise ValueError('安裝清單遭變更。')
    names=set()
    for item in expected['files']:
        names.add(item['path'].casefold())
        verify_file(directory/item['path'],item['bytes'],item['sha256'])
    extras=allowed_extras or {}
    for name,(digest,size) in extras.items():
        relative_path(name)
        if name.casefold() in names or name.casefold()==CATALOG:raise ValueError('額外檔案不可覆蓋受管契約。')
        verify_file(directory/name,size,digest)
    for path in directory.rglob('*'):
        _chain(path)
        if not path.is_file():continue
        name=path.relative_to(directory).as_posix()
        if name==CATALOG or name.casefold() in names or name in extras:continue
        if installed and re.fullmatch(r'unins\d{3}\.(exe|dat|msg)',name):continue
        raise ValueError('出現未列入清單的檔案：'+name)
    return len(expected['files'])


def assert_managed_removed(directory,expected):
    """移除以受管檔案為準；不能要求使用者留在安裝目錄的文件一併被刪除。"""
    directory=Path(directory)
    validate(expected)
    for name in [CATALOG,*[item['path'] for item in expected['files']]]:
        path=directory/name
        _chain(path)
        if path.exists():raise ValueError('受管檔案仍存在：'+name)
    return True

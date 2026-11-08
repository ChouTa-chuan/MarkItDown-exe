"""C03 原生資產靜態檢查：不載入 DLL、不執行 EXE，也不把來源 hash 當成授權核准。"""
import hashlib
from pathlib import Path
import re
import struct

from .components.contracts import relative_path
from .components.registry import _chain,IntegrityError

MAX_FILE_BYTES=128*1024**2
MAX_RUNTIME_BYTES=512*1024**2
SYSTEM_DLLS=frozenset(('advapi32','avrt','bcrypt','bcryptprimitives','cabinet','comctl32','comdlg32',
    'crypt32','cryptbase','d2d1','dbghelp','dnsapi','dwrite','dwmapi','gdi32','gdiplus','imm32','iphlpapi',
    'kernel32','kernelbase','msimg32','msvcrt','netapi32','normaliz','ntdll','ole32','oleacc','oleaut32',
    'powrprof','propsys','psapi','rpcrt4','secur32','setupapi','shell32','shlwapi','shcore','user32',
    'userenv','usp10','uxtheme','version','winhttp','wininet','winmm','winspool','wintrust','ws2_32','wtsapi32','wldap32'))


class NativeAssetError(ValueError):
    """來源、PE 或依賴不符時停止，不能改用 PATH 裡的不明 DLL。"""


def file_hash(path,limit=MAX_FILE_BYTES):
    path=Path(path)
    try:_chain(path)
    except IntegrityError as exc:raise NativeAssetError('原生來源不可含連結或 junction。') from exc
    if not path.is_file() or path.is_symlink() or path.stat().st_size>limit:
        raise NativeAssetError('原生來源須為有界的一般檔案。')
    result=hashlib.sha256();size=0
    with path.open('rb') as source:
        for block in iter(lambda:source.read(65536),b''):
            size+=len(block)
            if size>limit:raise NativeAssetError('原生來源超過大小限制。')
            result.update(block)
    return result.hexdigest(),size


def inspect_pe(data):
    """只解析 AMD64 PE32+ 的 import／delay-import；對 RVA、字串與終止項設界限。"""
    def read(fmt,offset):
        if offset<0 or offset+struct.calcsize(fmt)>len(data):raise NativeAssetError('PE 欄位超出檔案。')
        return struct.unpack_from(fmt,data,offset)
    if len(data)>MAX_FILE_BYTES or len(data)<64 or data[:2]!=b'MZ':raise NativeAssetError('不是有界 PE 檔案。')
    pe=read('<I',0x3c)[0]
    if pe<64 or data[pe:pe+4]!=b'PE\0\0':raise NativeAssetError('PE 簽名不符。')
    machine,count=read('<HH',pe+4);opt_size,flags=read('<HH',pe+20);opt=pe+24
    if machine!=0x8664 or read('<H',opt)[0]!=0x20b:raise NativeAssetError('需要 AMD64 PE32+，不接受 x86 或 ARM。')
    directories=read('<I',opt+108)[0]
    if not 1<=count<=96 or not 0<=directories<=16 or opt_size<112+directories*8:
        raise NativeAssetError('PE 目錄或區段數無效。')
    headers=read('<I',opt+60)[0];sections=[]
    for index in range(count):
        offset=opt+opt_size+index*40
        virtual_size,rva,raw_size,raw=read('<IIII',offset+8)
        if raw+raw_size>len(data):raise NativeAssetError('PE 區段超出檔案。')
        sections.append((rva,virtual_size,raw,raw_size))
    def position(rva,size):
        if size<0:raise NativeAssetError('PE 長度無效。')
        if 0<rva<headers and rva+size<=min(headers,len(data)):return rva
        matches=[raw+rva-start for start,virtual,raw,length in sections
                 if start<=rva<start+max(virtual,length) and rva-start+size<=length]
        if len(matches)!=1:raise NativeAssetError('PE RVA 無法唯一對應實檔區段。')
        return matches[0]
    def dll_name(rva):
        start=position(rva,1);end=data.find(b'\0',start,min(len(data),start+261))
        if end<0:raise NativeAssetError('DLL 名稱缺少有界終止。')
        position(rva,end-start+1)
        try:name=data[start:end].decode('ascii').lower()
        except UnicodeDecodeError as exc:raise NativeAssetError('DLL 名稱不是 ASCII。') from exc
        if not re.fullmatch(r'[a-z0-9][a-z0-9_.+-]{0,250}\.dll',name) or '..' in name:
            raise NativeAssetError('DLL 名稱不合法：'+repr(name))
        return name
    imports=set();delayed=set()
    for index,width,names_offset,target in [(1,20,12,imports),(13,32,4,delayed)]:
        if directories<=index:continue
        rva,size=read('<II',opt+112+index*8)
        if not rva and not size:continue
        if not rva or size<width:raise NativeAssetError('PE 相依目錄不完整。')
        position(rva,size);terminated=False
        for offset in range(0,min(size,1024*width),width):
            if offset+width>size:break
            address=position(rva+offset,width);fields=read('<'+'I'*(width//4),address)
            if not any(fields):terminated=True;break
            if index==13 and fields[0]!=1:raise NativeAssetError('只接受 RVA 格式的延遲匯入。')
            target.add(dll_name(read('<I',address+names_offset)[0]))
        if not terminated:raise NativeAssetError('PE 相依描述未在限制內終止。')
    return dict(machine='AMD64',format='PE32+',is_dll=bool(flags&0x2000),imports=sorted(imports),delay_imports=sorted(delayed))


def is_system_dll(name):
    return (name.lower().removesuffix('.dll') in SYSTEM_DLLS
            or re.fullmatch(r'(?:api|ext)-ms-win-[a-z0-9-]+\.dll',name.lower()) is not None)


def inspect_windows_assets(installer,directory,pin):
    if (pin.get('schema_version')!=1 or pin.get('id')!='tesseract-windows-x64'
            or pin.get('redistribution_approved') is not False):
        raise NativeAssetError('原生來源契約無效；本契約不提供再散布核准。')
    expected=pin['installer'];digest,size=file_hash(installer)
    if digest!=expected['sha256'] or size!=expected['bytes']:raise NativeAssetError('安裝來源與固定官方資產不符。')
    directory=Path(directory)
    try:_chain(directory)
    except IntegrityError as exc:raise NativeAssetError('原生目錄不可含連結或 junction。') from exc
    if not directory.is_dir():raise NativeAssetError('原生來源目錄不存在。')
    files=pin['runtime_files'];notices=pin['notice_files']
    if not isinstance(files,dict) or not 1<=len(files)<=128:raise NativeAssetError('原生檔案清單無效。')
    known={};observations={};total=0
    for name,record in files.items():
        relative_path(name)
        if '/' in name or not re.fullmatch(r'[A-Za-z0-9_.+-]+\.(?:dll|exe)',name,re.I):
            raise NativeAssetError('原生執行檔須位於固定根目錄。')
        if name.casefold() in known:raise NativeAssetError('Windows 檔名大小寫衝突。')
        path=directory/name;digest,size=file_hash(path);total+=size
        if digest!=record['sha256'] or size!=record['bytes']:raise NativeAssetError('原生檔案完整性不符：'+name)
        if total>MAX_RUNTIME_BYTES:raise NativeAssetError('原生檔案總容量超過限制。')
        with path.open('rb') as source:payload=source.read(MAX_FILE_BYTES+1)
        if len(payload)!=size or hashlib.sha256(payload).hexdigest()!=digest:
            raise NativeAssetError('PE 解析前原生檔案已變動。')
        observation=inspect_pe(payload)
        if observation['is_dll']!=(path.suffix.lower()=='.dll'):raise NativeAssetError('PE 檔案類型不符：'+name)
        known[name.casefold()]=name;observations[name]=observation
    for name,record in notices.items():
        relative_path(name);digest,size=file_hash(directory/name,8*1024**2)
        if digest!=record['sha256'] or size!=record['bytes']:raise NativeAssetError('原始授權／說明不符：'+name)
    entry=pin['entrypoint']
    if entry not in observations or observations[entry]['is_dll']:raise NativeAssetError('原生入口不在固定 EXE 清單。')
    visited=set();queue=[entry];system=set();edges=[]
    while queue:
        name=queue.pop(0)
        if name in visited:continue
        visited.add(name)
        for dependency in sorted(set(observations[name]['imports']+observations[name]['delay_imports'])):
            if dependency in known:
                child=known[dependency];edges.append([name,child]);queue.append(child)
            elif is_system_dll(dependency):system.add(dependency)
            else:raise NativeAssetError('相依 DLL 不在固定目錄或 Windows 系統清單：'+dependency)
    # Apache 原文只對已確認的 Tesseract 主程式／DLL 提供證據，不套用到其他 DLL。
    confirmed=pin.get('license_evidence',{})
    for name,notice in confirmed.items():
        if name not in files or notice not in notices:raise NativeAssetError('授權證據引用不在固定清單。')
    missing=sorted(name for name in visited if name not in confirmed)
    return dict(check='C03-native-static',inspection_complete=True,version=pin['version'],
        installer_sha256=expected['sha256'],runtime_file_count=len(files),runtime_bytes=total,
        files=observations,reachable_files=sorted(visited),unused_candidates=sorted(set(files)-visited),
        dependency_edges=sorted(edges),windows_system_imports=sorted(system),missing_license_evidence=missing,
        redistribution_approved=False,bundle_allowed=False,authenticode_verified=False,
        dynamic_loading_verified=False,windows_executed=False,native_ocr_bundled=False,full_c03_complete=False)


def require_bundle_permission(report):
    # 本契約只支援未核准候選檔；修改 JSON 報告旗標不能當成授權核准。
    raise NativeAssetError('原生候選檔尚未核准封裝：逐 DLL 原始授權／來源與再散布審查仍待完成。')

"""Offline, hash-verified inventory of the exact Windows dependency lock."""
import argparse
import email
from html import escape
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import tempfile
import zipfile
from urllib.parse import quote

PROJECT=Path(__file__).resolve().parents[1]
LICENSES=PROJECT/'src/desktop_app/data/licenses'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def canonical(name):
    return re.sub(r'[-_.]+','-',name).lower()


def read_lock(path):
    result={};current=None
    for line in path.read_text().splitlines():
        match=re.match(r'^([A-Za-z0-9_.-]+)==([^\s\\;]+)',line)
        if match:
            current=canonical(match[1]);result[current]={'version':match[2],'hashes':[]}
        for value in re.findall(r'--hash=sha256:([0-9a-f]{64})',line):
            if current is None:raise ValueError('Hash without package')
            result[current]['hashes'].append(value)
    if not result or any(not row['hashes'] for row in result.values()):
        raise ValueError('Incomplete hashed lock')
    return result


def safe_path(name):
    path=PurePosixPath(name)
    if path.is_absolute() or '..' in path.parts or '\\' in name or ':' in name:
        raise ValueError('Unsafe archive path')
    return path


def is_notice(name):
    return any(term in name.lower() for term in ('license','licence','copying','notice','copyright'))


def _generate(lock,wheels,supplements,output):
    required=read_lock(lock)
    if output.exists():raise ValueError('Output exists: generate to a fresh directory for review')
    packages=[];seen=set();stored={}
    def save(relative,data):
        safe_path(relative)
        target=output/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        stored[relative]=sha(data)
    sources=json.loads((supplements/'sources.json').read_text())
    supplemental={}
    for record in sources:
        if 'error' in record:raise ValueError('Unresolved supplemental source')
        content=(supplements/(record['name']+'.txt')).read_bytes()
        if sha(content)!=record['sha256']:raise ValueError('Supplement hash mismatch')
        relative='supplemental/'+record['name']+'.txt';save(relative,content)
        supplemental[record['name']]={**record,'path':relative}
    for wheel in sorted(wheels.glob('*.whl')):
        with zipfile.ZipFile(wheel) as archive:
            metadata_files=[name for name in archive.namelist() if name.endswith('.dist-info/METADATA') and len(PurePosixPath(name).parts)==2]
            if len(metadata_files)!=1:raise ValueError('Ambiguous wheel metadata')
            metadata_raw=archive.read(metadata_files[0]);metadata=email.message_from_bytes(metadata_raw)
            name=canonical(metadata['Name']);version=metadata['Version']
            if name not in required or name in seen:raise ValueError('Unexpected or duplicate wheel: '+name)
            digest=sha(wheel.read_bytes())
            if version!=required[name]['version'] or digest not in required[name]['hashes']:
                raise ValueError('Wheel differs from lock: '+name)
            seen.add(name);notices=[]
            save(name+'/METADATA',metadata_raw)
            for item in archive.infolist():
                if item.is_dir() or not is_notice(item.filename):continue
                safe_path(item.filename)
                if (item.external_attr>>16)&0o170000==0o120000:raise ValueError('Notice cannot be a symlink')
                if item.file_size>5*1024**2:raise ValueError('Oversized notice')
                relative=name+'/wheel/'+item.filename
                save(relative,archive.read(item));notices.append(relative)
            extra=[]
            if name in supplemental:extra.append(supplemental[name])
            if name in ('pyside6-essentials','shiboken6'):
                extra.extend(supplemental[key] for key in ('qt-lgpl3','qt-gpl3'))
            if not notices and not extra:raise ValueError('Missing notice evidence: '+name)
            classifiers=[value for value in metadata.get_all('Classifier',[]) if value.startswith('License ::')]
            packages.append({'name':name,'version':version,'wheel':wheel.name,'wheel_sha256':digest,
                'license_expression':metadata.get('License-Expression'), 'license_field':metadata.get('License'),
                'license_classifiers':classifiers,'project_urls':metadata.get_all('Project-URL',[]),
                'wheel_notice_files':notices,'supplemental_sources':extra})
    if seen!=set(required):raise ValueError('Missing locked packages: '+','.join(sorted(set(required)-seen)))
    result={'scope':'Windows CPython 3.12 locked development/runtime dependency superset; not a native-binary legal clearance',
            'lock_sha256':sha(lock.read_bytes()),'package_count':len(packages),'packages':packages,
            'files':stored,'notes':['Cobble wheel has no license text; official source README declares BSD-2-Clause.',
             'Magika supplement is standard Apache-2.0 text at a pinned official source commit, not a claim of matching release source.',
             'Qt wheel includes a commercial notice; original LGPL/GPL license texts are supplemented from its versioned source.',
             'Windows final native-binary inventory and Qt redistribution obligations must be checked after Windows build.']}
    save('supplemental/sources.json',(json.dumps(sources,indent=2)+'\n').encode())
    result['files']=dict(stored)
    (output/'inventory.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return result


def generate(lock,wheels,supplements,output):
    if output.exists():raise ValueError('Output exists: generate to a fresh directory for review')
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent,prefix='.license-') as directory:
        staged=Path(directory)/'inventory'
        report=_generate(lock,wheels,supplements,staged)
        os.replace(staged,output)
    return report


def verify(lock,output):
    inventory=json.loads((output/'inventory.json').read_text())
    required=read_lock(lock)
    if inventory['package_count']!=len(required) or len(inventory['packages'])!=len(required):
        raise ValueError('Inventory count mismatch')
    if inventory['lock_sha256']!=sha(lock.read_bytes()):raise ValueError('Inventory lock is stale')
    if {(p['name'],p['version']) for p in inventory['packages']}!={(name,row['version']) for name,row in required.items()}:
        raise ValueError('Inventory package coverage mismatch')
    for name,digest in inventory['files'].items():
        safe_path(name)
        if sha((output/name).read_bytes())!=digest:raise ValueError('Notice changed: '+name)
    for package in inventory['packages']:
        if package['wheel_sha256'] not in required[package['name']]['hashes']:
            raise ValueError('Recorded artifact hash is not locked')
        if not package['wheel_notice_files'] and not package['supplemental_sources']:
            raise ValueError('Notice evidence is missing')
        referenced=package['wheel_notice_files']+[record['path'] for record in package['supplemental_sources']]
        if any(path not in inventory['files'] for path in referenced):
            raise ValueError('Notice evidence is not covered by file hashes')
    return inventory


def render(inventory,markdown,html):
    title='第三方授權清單（開發預覽版）'
    introduction=[f'# {title}', '',f'已盤點 Windows Python 3.12 鎖定檔的 {inventory["package_count"]} 個套件，包含開發／建置相依的上位集合；不表示每個套件都會被打包。',
      '', '原始 METADATA、wheel 內授權、官方補充原文、來源 URL 與 SHA-256 均保存在 licenses/windows。HTML 索引位於 licenses/index.html。',
      '', '## 另列元件', '',
      '- Microsoft MarkItDown 0.1.9：MIT；來源提交及原始 LICENSE 保留於 vendor/markitdown。',
      '- CPython：實際建置直譯器的 LICENSE.txt 隨包保存在 licenses/python-runtime，不用其他版本文字代替。',
      '- Tesseract 語言資料：固定提交 Apache-2.0，原文與來源在 licenses/models。Tesseract 執行檔尚未隨 Windows 包發佈。',
      '- RapidOCR／PP-OCR 模型：屬固定版本套件，使用其 Apache-2.0 宣告，模型 SHA-256 在 onnx_ocr.py。',
      '- 本應用程式尚未選定公開發佈的原始碼授權；不可自行假設它與上游相同。',
      '', '## 特別注意', '',
      '- Qt/PySide6/Shiboken：保留 wheel 商業授權提示，另附官方版本的 LGPLv3/GPLv3 原文；採用哪種授權及其義務須在發佈前落實。',
      '- LGPL 路徑需保留動態函式庫替換能力、通知、對應來源取得方式及所需修改資訊；不可把單一封裝方式當成自動合規。',
      '- Cobble：wheel 缺授權全文，保留官方 README 的 BSD-2-Clause 宣告、作者 metadata 及標準 BSD 文字；不代填未知著作權聲明。',
      '- Magika 補充文件是固定官方來源的標準 Apache-2.0 原文，不宣稱該提交是本 wheel 的對應來源版本。',
      '- 完整 Windows 二進位檔尚未建置，原生 DLL／MS runtime、Qt 義務及最終發佈授權審核仍是發佈門檻。這份清單不是法律認證。',
      '', '## 鎖定套件', '', '| 套件 | 版本 | 套件宣告（原文另附） |', '| --- | --- | --- |']
    rows=[]
    for package in inventory['packages']:
        declaration=package['license_expression'] or package['license_field'] or '; '.join(package['license_classifiers']) or '見原文'
        declaration=' '.join(declaration.split())
        if len(declaration)>180:declaration=declaration[:177]+'...'
        introduction.append('| '+package['name']+' | '+package['version']+' | '+escape(declaration).replace('|','\\|')+' |')
        notice_paths=package['wheel_notice_files']+[record['path'] for record in package['supplemental_sources']]
        links=' '.join(f'<a href="windows/{quote(path,safe="/")}">原文 {number}</a>' for number,path in enumerate(notice_paths,1))
        rows.append('<tr><td>'+escape(package['name'])+'</td><td>'+escape(package['version'])+'</td><td>'+escape(declaration)+'</td><td>'+links+'</td></tr>')
    markdown.parent.mkdir(parents=True,exist_ok=True);markdown.write_text('\n'.join(introduction)+'\n',encoding='utf-8')
    html.write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>'+title+'</title><style>body{font:16px/1.6 system-ui;margin:30px;max-width:1300px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:10px;text-align:left}input{padding:12px;width:95%;margin:15px 0}a{display:inline-block;margin:4px}tr[hidden]{display:none}</style>'
        '<h1>'+title+'</h1><p>'+str(inventory['package_count'])+' 個鎖定套件，附原文與補充來源。此為開發依賴清單，不代表最終 Windows 原生檔發佈審核完成。完整說明見應用程式「第三方授權」。</p>'
        '<label>搜尋套件／授權 <input id="search" type="search"></label><table><thead><tr><th>套件</th><th>版本</th><th>宣告</th><th>授權文件</th></tr></thead><tbody>'+''.join(rows)+'</tbody></table>'
        '<script>document.getElementById("search").addEventListener("input",e=>{const q=e.target.value.toLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLowerCase().includes(q));});</script></html>',encoding='utf-8')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--lock',type=Path,default=Path('packaging/requirements-windows.txt'))
    parser.add_argument('--output',type=Path,default=LICENSES/'windows')
    parser.add_argument('--wheels',type=Path)
    parser.add_argument('--supplements',type=Path)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--render',action='store_true')
    args=parser.parse_args()
    if args.verify or args.render:report=verify(args.lock,args.output)
    else:
        if args.wheels is None or args.supplements is None:parser.error('Provide wheels and supplements')
        report=generate(args.lock,args.wheels,args.supplements,args.output)
    if args.render:render(report,PROJECT/'src/desktop_app/data/third-party.md',LICENSES/'index.html')
    print(f"Verified {report['package_count']} locked packages and {len(report['files'])} notice/metadata files")

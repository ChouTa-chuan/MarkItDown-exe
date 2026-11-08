"""離線檢查固定 Windows 原生來源；預設只檢查，不執行／安裝／核准封裝。"""
import argparse
from datetime import datetime,timezone
from importlib import metadata
import json
from pathlib import Path
import re
import subprocess

from desktop_app.native_assets import inspect_windows_assets,require_bundle_permission,NativeAssetError
from desktop_app.diagnostics import write_report

ROOT=Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--installer',type=Path,required=True)
    parser.add_argument('--directory',type=Path,required=True,help='已解開的固定來源根目錄；不會執行安裝程式')
    parser.add_argument('--report',type=Path,required=True)
    parser.add_argument('--release-metadata',type=Path,help='原始 GitHub expanded_assets 頁，獨立核對發布 digest')
    parser.add_argument('--objdump',type=Path,help='可信建置工具；可另核對入口與主 DLL 的 import 表')
    parser.add_argument('--require-redistribution',action='store_true',help='要求可封裝；目前候選來源必須被阻擋')
    args=parser.parse_args()
    if args.report.exists() or args.report.is_symlink():parser.error('報告已存在；請選新路徑。')
    pin=json.loads((ROOT/'packaging/native/tesseract-windows.json').read_text())
    try:
        report=inspect_windows_assets(args.installer,args.directory,pin)
        checks=['installer fixed SHA-256 and bytes','56 fixed AMD64 PE payloads',
                'entry dependency closure without PATH fallback','original pinned notices']
        if args.release_metadata:
            text=args.release_metadata.read_text(encoding='utf-8')
            name=args.installer.name
            digest=re.search(r'aria-label="Copy to clipboard digest for '+re.escape(name)+r'"[^>]*value="sha256:([0-9a-f]{64})"',text)
            if digest is None or digest[1]!=pin['installer']['sha256']:raise NativeAssetError('發布頁 digest 與固定來源不符。')
            checks.append('official published digest independently matched')
        if args.objdump:
            crosschecks=[]
            for name in ['tesseract.exe','libtesseract-5.dll']:
                reference=subprocess.run([str(args.objdump),'-p',str(args.directory/name)],capture_output=True,text=True,timeout=20,check=True)
                imports=sorted(set(value.lower() for value in re.findall(r'DLL Name:\s+([^\s]+)',reference.stdout)))
                expected=sorted(set(report['files'][name]['imports']+report['files'][name]['delay_imports']))
                if imports!=expected:raise NativeAssetError('獨立 PE 解析器結果不符：'+name)
                crosschecks.append(dict(file=name,imports=imports))
            report['objdump_crosschecks']=crosschecks;checks.append('independent objdump imports agree')
        try:require_bundle_permission(report)
        except NativeAssetError as exc:
            report['bundle_block_reason']=str(exc);checks.append('unreviewed DLL licenses block bundling')
        else:raise NativeAssetError('候選來源不應被核准。')
        report.update(source_version=metadata.version('markitdown-desktop'),recorded_at=datetime.now(timezone.utc).isoformat(),
                      checks=checks,checks_passed=len(checks),accepted=True,scope='Static source/intake mechanism only; no Windows execution or redistribution acceptance')
        write_report(report,args.report)
        print(f"Inspection checks: {len(checks)}; PE files: {report['runtime_file_count']}; reachable: {len(report['reachable_files'])}; license gaps: {len(report['missing_license_evidence'])}; bundle blocked")
        return 1 if args.require_redistribution else 0
    except (ValueError,OSError,subprocess.SubprocessError) as exc:
        write_report(dict(source_version=metadata.version('markitdown-desktop'),accepted=False,inspection_complete=False,
                          bundle_allowed=False,windows_executed=False,error=f'{type(exc).__name__}: {exc}'),args.report)
        return 1


if __name__=='__main__':raise SystemExit(main())

"""記錄隨包原生檔「從哪裡來、是誰發行」的可驗證資料；只蒐集證據，不判定授權。

責任：對不是由已安裝 wheel 提供的原生檔（建置用 CPython 目錄或系統路徑收集的 DLL），
記下來源目錄、PE 版本資源（公司、產品、檔案版本）與 Windows 數位簽章狀態及簽署者。
先前的報告只有雜湊，無法分辨檔名像 Microsoft runtime 的 DLL 是否真由 Microsoft 發行。

限制：
- 簽章只能在 Windows 以 PowerShell 的 Get-AuthenticodeSignature 查詢；其他平台該欄位留空。
- 任何一項讀取失敗都只在該檔記下 identity_error，不讓建置失敗；缺資料代表「未證實」，
  判讀時不能當成通過。
- 來源目錄是建置機上的路徑，只供追溯，不代表使用者電腦上的位置。
"""
import collections
import json
import subprocess
import sys
from pathlib import Path

SIGNATURE_SCRIPT = (
    "$ErrorActionPreference='Stop';"
    "$rows=@($input | ForEach-Object { $s=Get-AuthenticodeSignature -LiteralPath $_;"
    " [pscustomobject]@{path=$_;status=[string]$s.Status;"
    "signer=$(if($s.SignerCertificate){$s.SignerCertificate.Subject}else{$null})} });"
    "ConvertTo-Json -InputObject $rows -Compress")


def version_resource(path):
    """讀 PE 版本資源；沒有 pefile 或檔案沒有版本資源時回傳空 dict。"""
    try:
        import pefile
    except ImportError:
        return {}
    pe = pefile.PE(str(path), fast_load=True)
    try:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY['IMAGE_DIRECTORY_ENTRY_RESOURCE']])
        values = {}
        for group in getattr(pe, 'FileInfo', None) or []:
            for entry in group:
                for table in getattr(entry, 'StringTable', None) or []:
                    for key, value in table.entries.items():
                        values[key.decode('utf-8', 'replace')] = value.decode('utf-8', 'replace').strip()
        return {name: values[key] for name, key in (('company', 'CompanyName'), ('product', 'ProductName'),
                                                    ('file_version', 'FileVersion')) if values.get(key)}
    finally:
        pe.close()


def signatures(paths, runner=subprocess.run):
    """一次查詢多個檔案的簽章；回傳 {路徑字串: (狀態, 簽署者)}。非 Windows 回傳空 dict。"""
    if sys.platform != 'win32' or not paths:
        return {}
    done = runner(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', SIGNATURE_SCRIPT],
                  input='\n'.join(str(path) for path in paths) + '\n', capture_output=True, text=True,
                  encoding='utf-8', timeout=300)
    if done.returncode != 0:
        raise RuntimeError('Signature query failed: ' + done.stderr.strip()[-300:])
    return {row['path']: (row['status'], row['signer']) for row in json.loads(done.stdout or '[]')}


def describe(paths, sign=signatures, version=version_resource):
    """回傳 {Path: 身分資料}；每個檔案各自容錯。"""
    result = {Path(path): dict(source_directory=str(Path(path).parent)) for path in paths}
    try:
        signed = sign([str(path) for path in result])
        signature_error = None
    except Exception as error:  # 查不到簽章時仍保留其餘欄位，並明確記下原因。
        signed, signature_error = {}, f'{type(error).__name__}: {error}'[:200]
    for path, row in result.items():
        try:
            row.update(version(path))
        except Exception as error:
            row['identity_error'] = f'{type(error).__name__}: {error}'[:200]
        if str(path) in signed:
            row['signature_status'], row['signer'] = signed[str(path)]
        elif signature_error:
            row['identity_error'] = signature_error
    return result


def summarize(files):
    """把逐檔身分資料壓成公開摘要用的分組，避免摘要過長；逐檔明細仍在完整報告。"""
    groups = collections.Counter()
    for row in files:
        if row.get('origin') in ('system-native', 'python-runtime'):
            groups[(row['origin'], row.get('source_directory') or '', row.get('company') or '',
                    row.get('signature_status') or '', row.get('signer') or '')] += 1
    return [dict(origin=origin, source_directory=directory, company=company, signature_status=status,
                 signer=signer, files=count)
            for (origin, directory, company, status, signer), count in sorted(groups.items())]

"""列出打包進執行檔的 Python 程式層級成員清單，補上 runtime SBOM 在「程式碼」這一層的缺口。

責任：
- `pure_modules`：把 PyInstaller 的 pure TOC（會被壓進 PYZ 的純 Python 模組）逐模組列出，
  記下來源檔的 SHA-256、大小，以及它屬於標準庫、已安裝套件、本專案或來源不明。
- `zip_members`：列出實際 `_internal/base_library.zip` 的每個成員（名稱、未壓縮大小、CRC），
  並拒絕重複名稱、絕對路徑與含 `..` 的成員。
- `summarize`：把上述清單壓成公開 CI 摘要用的小結構；逐項明細只留在完整報告。
- `write_pure_manifest` 在 spec 執行（建置）時寫出 `python-modules.json`；
  `load_manifest` 在建置後檢核時讀回並驗證格式。

限制：
- 只證明「哪些來源檔被收進來、各自的雜湊」，不判定授權，也不代表 runtime SBOM 已完成。
- 套件歸屬只認已安裝套件 RECORD 對到的同一路徑，且必須剛好一個套件；其他一律 `unknown`，
  不用路徑名稱（例如資料夾叫 site-packages/foo）猜套件。
- 讀不到來源檔不讓建置失敗：該筆標為 `unknown` 並記下原因，缺資料代表「未證實」。
- PYZ 內存放的是編譯後的 bytecode；這裡記錄的是對應的來源檔，不是 PYZ 內部位元組。

設計原因：PyInstaller 的 TOC 條目是 (模組名, 來源路徑, 類型)，建置機上的路徑在使用者電腦上
沒有意義，所以清單只保存雜湊與歸屬結論，不保存絕對路徑。
"""
import collections
import json
import re
import sysconfig
import zipfile
from pathlib import Path

from build_provenance import distribution_sources, sha256
from candidate_inventory import canonical

SCHEMA_VERSION = 1
ORIGINS = ('stdlib', 'distribution', 'application', 'unknown')
MAX_UNKNOWN_NAMES = 10
MAX_NAME_LENGTH = 80
_DIGEST = re.compile('[0-9a-f]{64}')
# 基本包不在使用者電腦編譯或安裝 Python 套件；建置環境仍保留 setuptools。
# 與 base.spec 共用排除根，防止只把 namespace 隱藏成「已知」卻繼續帶入建置工具。
BASE_EXCLUDED_MODULES = ('setuptools',)


def verify_base_runtime_modules(modules):
    """以完整模組邊界拒絕基本包的建置工具；套件歸屬與 namespace 都不能繞過。"""
    forbidden = sorted(row['name'] for row in modules
                       if any(row['name'] == root or row['name'].startswith(root + '.')
                              for root in BASE_EXCLUDED_MODULES))
    if forbidden:
        raise ValueError('Build-only modules present in base runtime: ' + ', '.join(forbidden[:10]))


def _resolve_roots(roots):
    return [Path(root).resolve() for root in roots if root]


def _inside(path, roots):
    return any(path.is_relative_to(root) for root in roots)


def pure_modules(pure_toc, stdlib_roots, site_roots, application_roots, owners=None):
    """回傳依模組名排序的逐模組清單。

    pure_toc：(模組名, 來源路徑, 類型) 的序列。
    owners：{已解析的來源檔路徑: [{name, version}, ...]}，通常來自 build_provenance.distribution_sources()；
    省略時沒有任何模組能確定套件歸屬，位於 site 目錄下的都會是 unknown。
    判定順序為 本專案 → site-packages → 標準庫：site-packages 常位於標準庫目錄之下，必須先排除。
    """
    stdlib, site, application = (_resolve_roots(roots) for roots in (stdlib_roots, site_roots, application_roots))
    owners = owners or {}
    rows = []
    for entry in pure_toc:
        name, source = str(entry[0]), entry[1]
        kind = str(entry[2]) if len(entry) > 2 else ''
        row = dict(name=name, kind=kind, origin='unknown', source_sha256=None, source_bytes=None)
        rows.append(row)
        # modulegraph 以字串 '-' 表示 namespace package（沒有來源檔）；不可當檔名解析，
        # 否則目前目錄剛好有同名檔時會算出錯誤的雜湊。
        if not source or source == '-':
            row['reason'] = 'namespace-package' if source == '-' else 'no-source-path'
            continue
        try:
            path = Path(source).resolve()
            row['source_bytes'] = path.stat().st_size
            row['source_sha256'] = sha256(path)
        except (OSError, ValueError) as error:
            row.update(source_bytes=None, source_sha256=None, reason='source-unreadable:' + type(error).__name__)
            continue
        if _inside(path, application):
            row['origin'] = 'application'
        elif _inside(path, site):
            found = {(canonical(item['name']), item['version']) for item in owners.get(path, [])}
            if len(found) == 1:
                package, version = next(iter(found))
                row.update(origin='distribution', distribution=package, version=version)
            else:
                row['reason'] = 'ambiguous-record-owner' if found else 'no-record-owner'
        elif _inside(path, stdlib):
            row['origin'] = 'stdlib'
        else:
            row['reason'] = 'outside-known-roots'
    return sorted(rows, key=lambda row: row['name'])


def zip_members(path):
    """列出 zip 成員（名稱、未壓縮大小、CRC）；名稱重複、絕對路徑或含 .. 時丟出 ValueError。"""
    members, seen = [], set()
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            name = info.filename
            parts = re.split(r'[\\/]', name)
            if not name or name.startswith(('/', '\\')) or re.match('[A-Za-z]:', name):
                raise ValueError('Absolute zip member name: ' + name)
            if '..' in parts:
                raise ValueError('Zip member escapes archive: ' + name)
            if name in seen:
                raise ValueError('Duplicate zip member: ' + name)
            seen.add(name)
            members.append(dict(name=name, bytes=info.file_size, crc32=format(info.CRC, '08x')))
    return sorted(members, key=lambda member: member['name'])


def summarize(modules, base_library_members):
    """公開摘要：各 origin 的模組數、unknown 的數量與最多 10 個名稱、base_library 成員數。"""
    counts = collections.Counter(row['origin'] for row in modules)
    unknown = sorted(row['name'] for row in modules if row['origin'] == 'unknown')
    return dict(pure_modules=len(modules),
                by_origin={origin: counts.get(origin, 0) for origin in ORIGINS},
                unknown_modules=len(unknown),
                unknown_names=[name[:MAX_NAME_LENGTH] for name in unknown[:MAX_UNKNOWN_NAMES]],
                base_library_members=len(base_library_members))


def write_pure_manifest(pure_toc, output, application_roots=(), owners=None):
    """建置時（spec）呼叫：以目前 Python 的標準庫與 site 目錄為界，寫出 python-modules.json。"""
    stdlib = [sysconfig.get_path('stdlib'), sysconfig.get_path('platstdlib')]
    site = [sysconfig.get_path('purelib'), sysconfig.get_path('platlib')]
    modules = pure_modules(pure_toc, stdlib, site, application_roots,
                           distribution_sources() if owners is None else owners)
    report = dict(schema_version=SCHEMA_VERSION,
                  scope='Pure Python modules compiled into the executable archive (source file fingerprints); '
                        'not a license determination',
                  modules=modules)
    Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return modules


def load_manifest(path):
    """建置後檢核時讀回 python-modules.json；格式不符、重複或空清單都丟出 ValueError。"""
    report = json.loads(Path(path).read_text(encoding='utf-8'))
    modules = report.get('modules')
    if report.get('schema_version') != SCHEMA_VERSION or not isinstance(modules, list) or not modules:
        raise ValueError('Invalid or empty Python module manifest')
    names = set()
    for row in modules:
        name = row.get('name')
        if not isinstance(name, str) or not name or name in names or row.get('origin') not in ORIGINS:
            raise ValueError('Invalid Python module entry: ' + str(name))
        names.add(name)
        digest = row.get('source_sha256')
        if row['origin'] == 'unknown' and not (isinstance(row.get('reason'), str) and row['reason']):
            raise ValueError('Unknown module without reason: ' + name)
        if digest is not None and not (isinstance(digest, str) and _DIGEST.fullmatch(digest)):
            raise ValueError('Invalid module fingerprint: ' + name)
        if row['origin'] != 'unknown' and (digest is None or type(row.get('source_bytes')) is not int):
            raise ValueError('Module without source fingerprint: ' + name)
        if row['origin'] == 'distribution' and not (row.get('distribution') and row.get('version')):
            raise ValueError('Distribution module without package identity: ' + name)
    return modules

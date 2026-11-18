"""基本包 wheel 內含第三方元件目錄的檢核（A9）。

為什麼獨立成小模組：目錄（packaging/embedded/base-windows.json）只負責「原生檔屬於哪個內含元件」，
由 redistribution_gates.assess 呼叫本模組，把目錄與三個輸入綁在一起檢查，不另建第二套旗標規則。

本模組檢查的事：
- 鎖檔：每個 wheel 的名稱、版本與 sha256 必須是 packaging/profiles/base-windows-runtime.txt 鎖定的值。
- A6 source-review：目錄列出的原生檔必須存在於 A6 輸入，且屬於該 wheel 的套件。
- 登記表：每個 wheel 的原生檔必須與它指定的條目完全相同（不多、不少、不重複）；
  目錄綁定的條目必須在 evidence 引用目錄，且所有引用目錄的條目都要對得上目錄中的 wheel。
- 授權原文：列出的原文路徑必須在 repo 內（src/desktop_app/data/licenses/windows），hash 與 inventory.json 一致，
  缺檔或改內容即拒絕。這是 repo 內可重驗的部分。
- 版本依據分級只允許 wheel-declared（wheel 內文字檔或 METADATA 宣告）、runtime-observed（實際載入觀測）、unknown。
  版本 unknown 的元件保持 open，或交由 gates 驗證使用者接受及候選隨包揭露；不把接受缺口當成版本已知。

本模組不做的事（限制，不能當成已驗證）：
- wheel-declared 的 version_source 只記 wheel 內檔案路徑與欄位；A9b runtime-observed 則核對 Windows API JSON、原生檔與原文 hash。repo 內沒有 wheel 本體，無法自動重驗宣告字串是否存在；
  這一點需要重新下載 wheel 人工比對，之後若要自動化，必須把宣告檔一併保存進 repo。
- 不判定元件清單是否完整、不判定 upstream 網址是否正確，也不判定授權是否足夠；這些由人工審閱並留在目錄中。
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PREFIX = 'packaging/embedded/'
LOCK_PATH = 'packaging/profiles/base-windows-runtime.txt'
LICENSES_PREFIX = 'src/desktop_app/data/licenses/windows/'
INVENTORY_KEY = LICENSES_PREFIX + 'inventory.json'
BASIS_VALUES = ('wheel-declared', 'runtime-observed', 'unknown')
KIND_VALUES = ('wheel-own', 'bundled')
# 封閉結構：未知鍵一律拒絕，避免目錄夾帶未被檢核的資料。
TOP_KEYS = {'schema_version', 'profile', 'source_commit', 'scope', 'lock', 'source_review', 'inventory', 'wheels'}
PIN_KEYS = {'path', 'sha256'}
WHEEL_KEYS = {'distribution', 'version', 'filename', 'sha256', 'registry_entry', 'components'}
COMPONENT_KEYS = {'id', 'name', 'kind', 'version', 'version_basis', 'version_source', 'upstream', 'license',
                  'notices', 'native_files', 'note'}
NOTICE_KEYS = {'path', 'sha256'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canon(name):
    return re.sub(r'[-_.]+', '-', name).lower()


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def exact_keys(value, allowed, label):
    require(isinstance(value, dict), 'Not an object: ' + label)
    require(set(value) == allowed, 'Unexpected or missing keys in ' + label + ': '
            + ', '.join(sorted(set(value) ^ allowed)))


def read_lock(path):
    """解析雜湊鎖定檔；每個套件必須至少有一個 sha256，否則視為不完整。"""
    result = {}
    current = None
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.match(r'^([A-Za-z0-9_.-]+)==([^\s\\;]+)', line)
        if match:
            current = canon(match[1])
            result[current] = {'version': match[2], 'hashes': set()}
        for value in re.findall(r'--hash=sha256:([0-9a-f]{64})', line):
            require(current is not None, 'Hash without package')
            result[current]['hashes'].add(value)
    require(result and all(row['hashes'] for row in result.values()), 'Incomplete hashed lock')
    return result


def check_pin(ref, expected_path, root, label):
    """鎖檔、source-review 與 inventory 三個輸入都要 hash 綁定。"""
    exact_keys(ref, PIN_KEYS, label)
    require(ref['path'] == expected_path, label + ' path differs from the pinned input')
    path = root/ref['path']
    require(path.is_file() and not path.is_symlink(), 'Missing pinned input: ' + ref['path'])
    require(sha_file(path) == ref['sha256'], label + ' hash mismatch')


def check_notice(ref, root, inventory_files, label):
    """授權原文必須在 repo 內，hash 與 inventory.json 一致；缺檔或改內容拒絕。"""
    exact_keys(ref, NOTICE_KEYS, label)
    path_text = ref['path']
    require(path_text.startswith(LICENSES_PREFIX) and '..' not in path_text.split('/')
            and '\\' not in path_text and not path_text.startswith('/'), 'Notice outside the license directory: ' + path_text)
    path = root/path_text
    require(path.is_file() and not path.is_symlink() and path.resolve().is_relative_to(root.resolve()),
            'Missing or external notice file: ' + path_text)
    digest = sha_file(path)
    require(digest == ref['sha256'], 'Notice hash mismatch: ' + path_text)
    key = path_text[len(LICENSES_PREFIX):]
    require(inventory_files.get(key) == digest, 'Notice is not recorded in inventory.json: ' + path_text)


def check_crypto_observation(component, wheel, proof, source_row, profile):
    """A9b 版本來自真實 Windows API；證據原生檔必須就是 A6 的同一份 bytes。"""
    from cryptography_notice import validate_observation
    require(proof.get('check') == 'cryptography-openssl' and proof.get('redistribution_approved') is False
            and proof.get('openssl_tag') == profile['openssl_tag'] and proof.get('openssl_commit') == profile['openssl_commit'],
            'Invalid cryptography runtime evidence')
    observed = proof['observed']
    validate_observation(observed,profile)
    require(observed['platform'] == 'win32' and observed['binary'] == '_rust.pyd',
            'Cryptography catalog needs Windows runtime evidence')
    require(observed['distribution_version'] == wheel['version'] and observed['version'] == component['version'],
            'Cryptography catalog version differs from runtime')
    require(observed['binary_sha256'] == source_row['source_sha256'] == source_row['bundled_sha256'],
            'Cryptography runtime evidence differs from A6 binary')
    require(proof['notice_sha256'] == profile['notice']['sha256']
            and dict(path=profile['notice']['path'],sha256=profile['notice']['sha256']) in component['notices'],
            'Cryptography runtime notice binding differs')


def check_profile(catalog, *, catalog_path, entries, report, root=ROOT, gap_validator=None):
    """檢核一份目錄與所屬 profile 的登記條目，回傳摘要；任何不符都拋出 ValueError。

    catalog_path：目錄在 repo 內的相對路徑（登記條目的 evidence 必須引用它）。
    entries：該 profile 的登記條目（已通過 redistribution_gates 的結構檢查）。
    report：該 profile 的固定候選 source-review。
    gap_validator：gates 提供的揭露式關閉檢核；獨立呼叫未提供時，未知元件仍只能 open。
    目錄層只產生缺口 id，決定出處與隨包證據的規則集中在 gates，避免兩套判定。
    """
    require(catalog_path.startswith(CATALOG_PREFIX), 'Catalog must live under ' + CATALOG_PREFIX)
    exact_keys(catalog, TOP_KEYS, 'catalog')
    require(type(catalog['schema_version']) is int and catalog['schema_version'] == 1, 'Unsupported catalog schema_version')
    require(catalog['profile'] == 'base', 'Catalog profile must be base')
    source = report.get('selection', {}).get('source_commit')
    require(catalog['source_commit'] == source, 'Catalog source differs from the source-review')
    check_pin(catalog['lock'], LOCK_PATH, root, 'lock')
    check_pin(catalog['source_review'], 'docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json',
              root, 'source_review')
    check_pin(catalog['inventory'], INVENTORY_KEY, root, 'inventory')
    require(isinstance(catalog['scope'], str) and catalog['scope'].strip(), 'Missing catalog scope')
    lock = read_lock(root/LOCK_PATH)
    inventory_files = json.loads((root/INVENTORY_KEY).read_text(encoding='utf-8'))['files']

    # A6 輸入：原生檔與其套件（exact 路徑比對，不做通配）。
    # 沒有 wheel 擁有者的原生檔（例如系統工具）記為 None，目錄列入時因套件不符而拒絕。
    review_native = {}
    for row in report['classification_input']['report']['native_files']:
        owners = row.get('distributions') or []
        review_native[row['file']] = canon(owners[0]['name']) if owners else None

    require(isinstance(catalog['wheels'], list) and catalog['wheels'], 'Catalog has no wheels')
    by_entry = {}
    seen_natives = set()
    unknown_components = []
    component_total = 0
    for wheel in catalog['wheels']:
        exact_keys(wheel, WHEEL_KEYS, 'wheel')
        dist = wheel['distribution']
        require(dist == canon(dist) and dist in lock, 'Wheel is not in the lock: ' + dist)
        require(wheel['version'] == lock[dist]['version'], 'Wheel version differs from lock: ' + dist)
        require(wheel['sha256'] in lock[dist]['hashes'], 'Wheel hash is not locked: ' + dist)
        name, _, rest = wheel['filename'].partition('-')
        version = rest.split('-', 1)[0]
        require(canon(name) == dist and version == wheel['version'] and wheel['filename'].endswith('.whl'),
                'Wheel filename differs from the catalog: ' + wheel['filename'])
        entry_id = wheel['registry_entry']
        require(entry_id not in by_entry, 'Duplicate registry entry in catalog: ' + entry_id)
        components = wheel['components']
        require(isinstance(components, list) and components, 'No components for ' + dist)
        require(sum(c.get('kind') == 'wheel-own' for c in components) == 1, 'Exactly one wheel-own component per wheel: ' + dist)
        wheel_natives = []
        unknown = []
        seen_components = set()
        for component in components:
            exact_keys(component, COMPONENT_KEYS, 'component ' + str(component.get('id')))
            cid = component['id']
            require(isinstance(cid, str) and re.fullmatch(r'[a-z0-9][a-z0-9-]*', cid), 'Invalid component id: ' + str(cid))
            require(cid not in seen_components, 'Duplicate component id: ' + cid)
            seen_components.add(cid)
            require(component['kind'] in KIND_VALUES, 'Invalid component kind: ' + cid)
            basis = component['version_basis']
            require(basis in BASIS_VALUES, 'Version basis outside allowed values: ' + cid)
            require(isinstance(component['name'], str) and component['name'].strip(), 'Missing name: ' + cid)
            require(isinstance(component['license'], str) and component['license'].strip(), 'Missing license: ' + cid)
            require(isinstance(component['upstream'], str) and component['upstream'].startswith('https://'),
                    'Upstream must be an https URL: ' + cid)
            if basis == 'unknown':
                require(component['version'] is None and component['version_source'] is None,
                        'Unknown version must not carry a version: ' + cid)
                unknown.append(dist + '/' + cid)
            else:
                require(isinstance(component['version'], str) and component['version'].strip(),
                        'Declared version is missing: ' + cid)
                require(isinstance(component['version_source'], str) and component['version_source'].strip(),
                        'Declared version has no source: ' + cid)
            if dist == 'cryptography' and cid == 'openssl':
                require(basis in ('unknown','runtime-observed'), 'OpenSSL cannot be wheel-declared from a binary string')
                if basis == 'runtime-observed':
                    from cryptography_notice import load as crypto_profile, PROFILE
                    path_text = component['version_source']
                    require(path_text.startswith('docs/development-records/runs/') and '..' not in path_text.split('/')
                            and '\\' not in path_text, 'Invalid cryptography observation path')
                    entry = next((e for e in entries if e['id']==entry_id),None)
                    pin = next((r for r in entry['evidence'] if r['path']==path_text),None) if entry else None
                    require(pin is not None, 'Cryptography observation missing evidence reference')
                    check_pin(pin,path_text,root,'cryptography runtime observation')
                    proof=json.loads((root/path_text).read_text(encoding='utf-8'))
                    require(proof['profile_sha256']==sha_file(root/PROFILE), 'Cryptography profile differs from observation')
                    native=next(r for r in report['classification_input']['report']['native_files']
                                if r['file']=='cryptography/hazmat/bindings/_rust.pyd')
                    check_crypto_observation(component,wheel,proof,native,crypto_profile(root))
            elif basis == 'runtime-observed':
                from embedded_runtime import check_component
                path_text = component['version_source']
                require(path_text.startswith('docs/development-records/runs/') and '..' not in path_text.split('/')
                        and '\\' not in path_text, 'Invalid embedded runtime observation path')
                entry = next((e for e in entries if e['id'] == entry_id), None)
                pin = next((r for r in entry['evidence'] if r['path'] == path_text), None) if entry else None
                require(pin is not None, 'Embedded runtime observation missing evidence reference')
                check_pin(pin, path_text, root, 'embedded runtime observation')
                check_component(component, wheel, json.loads((root/path_text).read_text(encoding='utf-8')), report, root)
            require(isinstance(component['notices'], list), 'Invalid notices list: ' + cid)
            for index, notice in enumerate(component['notices']):
                check_notice(notice, root, inventory_files, 'notice ' + cid + '[' + str(index) + ']')
            natives = component['native_files']
            require(isinstance(natives, list) and all(isinstance(n, str) for n in natives), 'Invalid native list: ' + cid)
            for native in natives:
                require(native in review_native, 'Native file is not in the A6 input: ' + native)
                require(review_native[native] == dist, 'Native file belongs to another distribution: ' + native)
                require(native not in seen_natives, 'Native file listed more than once: ' + native)
                seen_natives.add(native)
            wheel_natives.extend(natives)
        by_entry[entry_id] = dict(distribution=dist, natives=sorted(wheel_natives), unknown=unknown,
                                  components=len(components))
        component_total += len(components)
        unknown_components.extend(unknown)

    # 登記條目：目錄的 wheel 與條目一一對應，原生檔必須完全相同。
    entries_by_id = {}
    for entry in entries:
        require(entry['id'] not in entries_by_id, 'Duplicate registry entry: ' + entry['id'])
        entries_by_id[entry['id']] = entry
    referencing = {e['id'] for e in entries if any(ref.get('path') == catalog_path for ref in e['evidence'])}
    require(referencing == set(by_entry), 'Registry entries referencing the catalog differ from catalog wheels: '
            + ', '.join(sorted(referencing ^ set(by_entry))))
    for entry_id, info in by_entry.items():
        entry = entries_by_id[entry_id]
        require(sorted(entry['native_files']) == info['natives'],
                'Registry native files differ from the catalog for ' + entry_id)
        if info['unknown']:
            require(entry['status'] == 'open' or gap_validator is not None,
                    'Entry with unknown component must stay open without a gap validator: ' + entry_id)
            if gap_validator is not None:
                gap_validator(entry, info['unknown'])
    # 目錄涵蓋的原生檔與引用條目的原生檔合計相同，沒有漏列也沒有多列。
    referenced_natives = sorted(n for e in entries if e['id'] in by_entry for n in e['native_files'])
    require(referenced_natives == sorted(seen_natives), 'Catalog natives differ from referenced registry natives')
    return dict(catalog=catalog_path, wheels=len(by_entry), components=component_total,
                native_files=len(seen_natives), unknown_components=sorted(unknown_components),
                unknown_by_entry={key:sorted(value['unknown']) for key,value in by_entry.items() if value['unknown']})

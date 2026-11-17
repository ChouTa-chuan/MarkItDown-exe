"""只讀義務登記與 source-review，推導三旗標；不改候選、盤點與原始報告。"""
import argparse
import collections
import datetime
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

import embedded_components

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT/'packaging/redistribution/obligations.json'
FLAGS = ('runtime_sbom_complete', 'redistribution_approved', 'release_ready')
STATUSES = ('open', 'evidence_complete', 'user_approved')
SCHEMA_VERSION = 2
# 封閉結構：鍵集合依 obligations.json 實際使用的欄位訂定，未知鍵一律拒絕，避免夾帶未被檢核的資料。
TOP_KEYS = {'schema_version', 'description', 'profiles'}
PROFILE_KEYS = {'source_commit', 'entries'}
ENTRY_REQUIRED = {'id', 'title', 'native_files', 'review_reasons', 'file_groups', 'required_evidence',
                  'evidence', 'status', 'requires_user_decision', 'gates'}
ENTRY_KEYS = ENTRY_REQUIRED | {'decision_source'}
EVIDENCE_KEYS = {'path', 'sha256'}
DECISION_KEYS = EVIDENCE_KEYS | {'quote'}
# 決定出處只認固定存檔（STATUS.md 會持續改動，hash 會失效，所以不接受）。
DECISION_PATH = re.compile(r'docs/history/status/\d{4}-\d{2}-\d{2}-[a-z0-9][a-z0-9-]*\.md')
# D 節中使用者親自做的決定列：來源欄須以「使用者」開頭。
DECISION_LINE = re.compile(r'\| \d{4}-\d{2}-\d{2} \| 使用者[^|]*\| .+ \|')
# 大階段 C（乾淨機與人工驗收）的證據目錄前綴；目前不存在，故 release_ready 在大階段 C 之前不可能為 true。
STAGE_C_PREFIX = 'docs/development-records/runs/stage-c-'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: '+key)
        result[key] = value
    return result


def read_json(path):
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= 4*1024*1024,
            'Missing, linked or oversized JSON: '+str(path))
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=no_duplicate_keys)


def safe_name(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name
            and not PurePosixPath(name).is_absolute() and all(p not in ('', '.', '..') for p in name.split('/')),
            'Unsafe relative path: '+str(name))
    return name.casefold()


def reference(ref, root, *, decision=False):
    """證據必須可重驗；決定還須引用已保存原文。這不驗證作者身分，仍須人工查驗。"""
    require(isinstance(ref, dict), 'Missing evidence/decision reference')
    name = ref.get('path')
    safe_name(name)
    path = root/name
    require(path.is_file() and not any(p.is_symlink() for p in (path, *path.parents))
            and path.resolve().is_relative_to(root.resolve()), 'Missing or external evidence: '+name)
    digest = ref.get('sha256')
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    require(isinstance(digest, str) and re.fullmatch('[0-9a-f]{64}', digest) and actual == digest,
            'Evidence hash mismatch: '+name)
    if decision:
        quote = ref.get('quote')
        require(isinstance(quote, str) and DECISION_PATH.fullmatch(name),
                'Decision source must be a fixed docs/history/status archive: '+name)
        require(decision_line_exists(path.read_text(encoding='utf-8'), quote),
                'Decision quotation is not a user decision row in section D: '+name)


def decision_line_exists(text, quote):
    """quote 必須是存檔 D 節內「完整的一行」，且來源欄以「使用者」開頭。

    只做格式與位置限制，不證明該行真的出自使用者；來源仍須人工查驗。
    """
    require(DECISION_LINE.fullmatch(quote) is not None, 'Decision quotation is not a user decision row')
    try:
        datetime.date.fromisoformat(quote[2:12])
    except ValueError:
        raise ValueError('Decision quotation has an invalid date') from None
    in_section = False
    in_fence = False
    for line in text.split('\n'):
        line = line.rstrip('\r')
        # 程式碼區塊內的標題或表格列不算存檔原文，避免藉圍欄偽造 D 節。
        if line.startswith('```'):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if line.startswith('## '):
            in_section = re.match(r'## D(?:[.．\s]|$)', line) is not None
        elif in_section and line == quote:
            return True
    return False


def exact_keys(value, allowed, label, required=None):
    """物件必須是 dict，且鍵集合落在允許集合內（含必要鍵）。"""
    require(isinstance(value, dict), 'Not an object: '+label)
    require(set(value) <= allowed and set(value) >= (allowed if required is None else required),
            'Unexpected or missing keys in '+label+': '+', '.join(sorted(set(value) ^ allowed)))


def validate_registry(registry, root):
    exact_keys(registry, TOP_KEYS, 'registry')
    require(type(registry['schema_version']) is int and registry['schema_version'] == SCHEMA_VERSION, 'Unsupported registry schema_version')
    require(isinstance(registry['profiles'], dict) and set(registry['profiles']) == {'base', 'cpu'},
            'Registry requires base and cpu profiles')
    ids = set()
    for profile, config in registry['profiles'].items():
        exact_keys(config, PROFILE_KEYS, 'profile '+profile)
        require(isinstance(config.get('source_commit'), str)
                and re.fullmatch('[0-9a-f]{40}', config['source_commit']), 'Invalid registry source')
        entries = config.get('entries')
        require(isinstance(entries, list) and entries, 'Empty obligations: '+profile)
        for e in entries:
            exact_keys(e, ENTRY_KEYS, 'obligation entry', ENTRY_REQUIRED)
            identity = e.get('id')
            require(isinstance(identity, str) and re.fullmatch('[a-z0-9-]+', identity)
                    and identity not in ids, 'Invalid/duplicate obligation id')
            ids.add(identity)
            require(isinstance(e.get('title'), str) and e['title'].strip(), 'Missing obligation title')
            for key in ('native_files', 'review_reasons', 'file_groups', 'required_evidence', 'evidence', 'gates'):
                require(isinstance(e.get(key), list), 'Invalid obligation list: '+key)
            for key in ('native_files', 'review_reasons', 'file_groups', 'required_evidence', 'gates'):
                require(all(isinstance(v, str) and v.strip() for v in e[key])
                        and len(e[key]) == len(set(e[key])), 'Invalid/duplicate selectors: '+identity)
            for name in e['native_files']:
                safe_name(name)
            require(e['required_evidence'] and e['gates'] and set(e['gates']) <= set(FLAGS),
                    'Missing evidence requirements or invalid gates: '+identity)
            require(e.get('status') in STATUSES and type(e.get('requires_user_decision')) is bool,
                    'Invalid obligation status: '+identity)
            for ref in e['evidence']:
                exact_keys(ref, EVIDENCE_KEYS, 'evidence reference')
                reference(ref, root)
            if e['status'] != 'open':
                require(e['evidence'], 'Closed status without evidence: '+identity)
            if e.get('decision_source') is not None:
                exact_keys(e['decision_source'], DECISION_KEYS, 'decision_source')
                reference(e['decision_source'], root, decision=True)
            if e['status'] == 'user_approved':
                require(e.get('decision_source') is not None, 'User approval without decision source: '+identity)
        for flag in FLAGS:
            require(any(flag in e['gates'] for e in entries), 'Gate without obligations: '+flag)
        # 使用者決定與人工驗收不可因只登記工程證據而被省略。
        for flag, suffix in ((FLAGS[1], '-redistribution-decision'), (FLAGS[2], '-clean-machine-manual')):
            mandatory = next((e for e in entries if e['id'] == profile+suffix), None)
            require(mandatory and flag in mandatory['gates'] and mandatory['requires_user_decision'],
                    'Gate missing mandatory user-decision obligation: '+flag)
        # release_ready 綁定大階段 C：clean-machine-manual 關閉時須有 stage-c- 前綴的實機證據。
        manual = next(e for e in entries if e['id'] == profile+'-clean-machine-manual')
        require(manual['status'] == 'open' or any(r['path'].startswith(STAGE_C_PREFIX) for r in manual['evidence']),
                'Clean-machine closure needs stage-c evidence: '+manual['id'])
        for e in entries:
            require(not e['native_files'] or set(FLAGS[:2]) <= set(e['gates']),
                    'Native obligations must cover source and redistribution: '+e['id'])


def coverage(items, entries, key):
    """兩個獨立軸：每個原生檔、每個 reason 各恰好一個條目；沒有優先順序或兜底。

    另做反向檢查：登記表的每個選擇器都必須真的出現在輸入中，避免過期選擇器長期殘留。
    """
    index = collections.defaultdict(list)
    for e in entries:
        for value in e[key]:
            index[safe_name(value) if key == 'native_files' else value].append(e['id'])
    seen = {safe_name(v) if key == 'native_files' else v for v in items}
    for name in index:
        require(name in seen, f'stale selector in {key}: {name}')
    result = {}
    for value in items:
        matches = index[safe_name(value) if key == 'native_files' else value]
        require(len(matches) == 1, f'{key} must match exactly one obligation: {value} ({len(matches)})')
        result[value] = matches[0]
    return result


def assess(report, registry, *, root=ROOT):
    validate_registry(registry, root)
    profile = report.get('profile')
    require(profile in registry['profiles'] and report.get('check') == 'candidate-source-review'
            and report.get('schema_version') == 1 and report.get('accepted') is True, 'Invalid source-review input')
    config = registry['profiles'][profile]
    source = report.get('selection', {}).get('source_commit')
    require(source == config['source_commit'], 'Source differs from registry basis')
    raw = report['classification_input']['report']
    require(raw['profile'] == profile and raw['source_commit'] == source, 'Inconsistent source-review identity')
    native = [r['file'] for r in raw['native_files']]
    require(native and len({safe_name(n) for n in native}) == len(native), 'Empty or duplicate native files')
    files = raw['candidate_inventory']['files']
    require(len({safe_name(r['path']) for r in files}) == len(files), 'Duplicate review paths')
    reasons = collections.Counter()
    for row in files:
        values = row['review_reasons']
        require(isinstance(values, list) and values and all(isinstance(x, str) and x for x in values)
                and len(values) == len(set(values)), 'Invalid review_reasons')
        reasons.update(values)
    require(dict(reasons) == report.get('review_reasons'), 'Review reason summary differs from input rows')
    entries = config['entries']
    mappings = dict(native_files=coverage(native, entries, 'native_files'),
                    review_reasons=coverage(reasons, entries, 'review_reasons'))
    # 內含元件目錄（A9）：由條目的 evidence 找出目錄，逐一與該 profile 的條目與 A6 輸入對齊。
    catalogs = sorted({ref['path'] for e in entries for ref in e['evidence']
                       if ref['path'].startswith(embedded_components.CATALOG_PREFIX)})
    embedded = [embedded_components.check_profile(read_json(root/path), catalog_path=path, entries=entries,
                                                  report=report, root=root) for path in catalogs]
    blocked = {}
    for flag in FLAGS:
        blocked[flag] = [e['id'] for e in entries if flag in e['gates'] and
                         (e['status'] == 'open' or (flag != FLAGS[0] and e['requires_user_decision']
                                                   and e['status'] != 'user_approved'))]
    flags = {FLAGS[0]: not blocked[FLAGS[0]]}
    flags[FLAGS[1]] = flags[FLAGS[0]] and not blocked[FLAGS[1]]
    flags[FLAGS[2]] = flags[FLAGS[1]] and not blocked[FLAGS[2]]
    return dict(check='redistribution-gates', schema_version=1, accepted=True, profile=profile,
                source_commit=source, **flags, blocked_by_gate=blocked,
                gate_dependencies={FLAGS[1]: [FLAGS[0]], FLAGS[2]: [FLAGS[1]]},
                unclosed_obligations=[dict(id=e['id'], status=e['status'], title=e['title'],
                                          required_evidence=e['required_evidence']) for e in entries
                                      if any(e['id'] in ids for ids in blocked.values())],
                coverage=mappings, embedded_catalogs=embedded, input_inventory_summary=report['inventory_summary'],
                scope='Registry review decision for this source; accepted means valid coverage, not product approval')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-review', required=True, type=Path)
    parser.add_argument('--registry', type=Path, default=REGISTRY)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output:
        require(not args.output.exists() and not args.output.is_symlink(), 'Output must be new')
    result = assess(read_json(args.source_review), read_json(args.registry))
    text = json.dumps(result, ensure_ascii=False, indent=2)+'\n'
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            stream.write(text)
    else:
        print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

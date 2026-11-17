"""只讀義務登記與 source-review，推導三旗標；不改候選、盤點與原始報告。"""
import argparse
import collections
import hashlib
import json
from pathlib import Path, PurePosixPath
import re

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT/'packaging/redistribution/obligations.json'
FLAGS = ('runtime_sbom_complete', 'redistribution_approved', 'release_ready')
STATUSES = ('open', 'evidence_complete', 'user_approved')


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
        require(isinstance(quote, str) and quote.strip() and quote in path.read_text(encoding='utf-8'),
                'Missing decision quotation: '+name)


def validate_registry(registry, root):
    require(registry.get('schema_version') == 1 and set(registry.get('profiles', {})) == {'base', 'cpu'},
            'Registry requires base and cpu profiles')
    ids = set()
    for profile, config in registry['profiles'].items():
        require(isinstance(config.get('source_commit'), str)
                and re.fullmatch('[0-9a-f]{40}', config['source_commit']), 'Invalid registry source')
        entries = config.get('entries')
        require(isinstance(entries, list) and entries, 'Empty obligations: '+profile)
        for e in entries:
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
                reference(ref, root)
            if e['status'] != 'open':
                require(e['evidence'], 'Closed status without evidence: '+identity)
            if e.get('decision_source') is not None:
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
        for e in entries:
            require(not e['native_files'] or set(FLAGS[:2]) <= set(e['gates']),
                    'Native obligations must cover source and redistribution: '+e['id'])


def coverage(items, entries, key):
    """兩個獨立軸：每個原生檔、每個 reason 各恰好一個條目；沒有優先順序或兜底。"""
    index = collections.defaultdict(list)
    for e in entries:
        for value in e[key]:
            index[safe_name(value) if key == 'native_files' else value].append(e['id'])
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
                coverage=mappings, input_inventory_summary=report['inventory_summary'],
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

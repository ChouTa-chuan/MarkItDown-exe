"""C04：從既有固定版本建立基本版閉包；離線重驗鎖定與授權，不重新選版。

這是建置工具，不會修改使用者環境，也不把 Python 閉包當作原生打包驗收。
Windows 以已保存的 wheel METADATA 為準；Linux metadata 快照另以乾淨安裝驗證。
"""
import argparse
import email
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import tomllib

from packaging.markers import default_environment
from packaging.requirements import Requirement
from packaging.specifiers import SpecifierSet
from packaging.utils import canonicalize_name

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ('linux', 'windows')
SCOPES = ('runtime', 'build')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read_lock(path):
    """只接受固定版號與 SHA-256；拒絕重複套件及非預期的 pip 選項。"""
    records = {}
    lines = re.sub(r'\\\s*\n', ' ', path.read_text(encoding='utf-8'))
    for line in lines.splitlines():
        line = line.split('#', 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        requirement = Requirement(tokens[0])
        pins = list(requirement.specifier)
        name = canonicalize_name(requirement.name)
        if (requirement.url or requirement.marker or requirement.extras or len(pins) != 1
                or pins[0].operator != '==' or '*' in pins[0].version or name in records):
            raise ValueError('非固定或重複套件：' + name)
        hashes = []
        for token in tokens[1:]:
            match = re.fullmatch(r'--hash=sha256:([0-9a-f]{64})', token)
            if match is None:
                raise ValueError('鎖定選項不受支援：' + token)
            hashes.append(match[1])
        if not hashes or len(set(hashes)) != len(hashes):
            raise ValueError('套件缺少或重複雜湊：' + name)
        records[name] = {'version': pins[0].version, 'hashes': sorted(hashes)}
    if not records:
        raise ValueError('鎖定檔不得為空。')
    return records


def marker_environment(target, python):
    if target not in TARGETS:
        raise ValueError('不支援的 profile 平台。')
    # 必須完全覆蓋會隨建置主機變動的 marker，避免 Linux 產生假的 Windows 閉包。
    return dict(default_environment(), python_version='.'.join(python.split('.')[:2]),
                python_full_version=python, implementation_name='cpython',
                implementation_version=python, platform_python_implementation='CPython',
                os_name='nt' if target == 'windows' else 'posix',
                sys_platform='win32' if target == 'windows' else 'linux',
                platform_system='Windows' if target == 'windows' else 'Linux',
                platform_machine='AMD64' if target == 'windows' else 'x86_64',
                platform_release='', platform_version='', extra='')


def closure(roots, metadata, environment):
    """累積 extras 後重訪相依；同一套件先無 extra、後有 extra 也不能漏算。"""
    queue = [(Requirement(value), '<root>') for value in roots]
    seen = {}
    edges = set()
    while queue:
        requirement, parent = queue.pop(0)
        if requirement.marker and not requirement.marker.evaluate(environment):
            continue
        name = canonicalize_name(requirement.name)
        if requirement.url:
            raise ValueError('profile 不接受外部直連相依：' + name)
        if name not in metadata:
            raise ValueError('閉包缺少套件：' + name)
        package = metadata[name]
        if not requirement.specifier.contains(package['version'], prereleases=True):
            raise ValueError('固定版本不符：' + name)
        if package.get('requires_python') and not SpecifierSet(package['requires_python']).contains(environment['python_full_version']):
            raise ValueError('Python 版本不符：' + name)
        edges.add((parent, name))
        extras = {canonicalize_name(value) for value in requirement.extras}
        previous = seen.get(name)
        if previous is not None and extras <= previous:
            continue
        active_extras = extras | (previous or set())
        seen[name] = active_extras
        for value in package['requires_dist']:
            dependency = Requirement(value)
            if dependency.marker and not any(dependency.marker.evaluate(dict(environment, extra=extra))
                                             for extra in active_extras | {''}):
                continue
            # marker 已在父套件的 extras 範圍內求值，不能再套到子套件的 extra。
            dependency.marker = None
            queue.append((dependency, name))
    return sorted(seen), [list(value) for value in sorted(edges)]


def metadata_record(raw):
    message = email.message_from_bytes(raw)
    return dict(version=message['Version'], requires_python=message.get('Requires-Python'),
                requires_dist=message.get_all('Requires-Dist', []), metadata_sha256=sha(raw))


def load_metadata(root, target):
    parent_path = root / f'packaging/requirements-{target}.txt'
    parent = read_lock(parent_path)
    document = json.loads((root / f'packaging/profiles/metadata-{target}.json').read_text())
    if document['parent_lock_sha256'] != sha(parent_path.read_bytes()):
        raise ValueError('metadata 的上位鎖定已變動。')
    metadata = document['packages']
    if set(metadata) != set(parent):
        raise ValueError('metadata 與上位鎖定套件集合不符。')
    for name, record in metadata.items():
        if record['version'] != parent[name]['version']:
            raise ValueError('metadata 版本不符：' + name)
        if target == 'windows':
            raw = (root / 'src/desktop_app/data/licenses/windows' / name / 'METADATA').read_bytes()
            if record != metadata_record(raw):
                raise ValueError('Windows wheel metadata 不符：' + name)
    return parent, metadata


def root_requirements(root, config, scope):
    values = []
    for name, path in [('application', 'pyproject.toml'), ('markitdown', 'vendor/markitdown/pyproject.toml')]:
        project = tomllib.loads((root / path).read_text())['project']
        values.extend(project['dependencies'])
        for extra in config[name + '_extras']:
            values.extend(project['optional-dependencies'][extra])
    if scope == 'build':
        values.extend(line.split('#', 1)[0].strip() for line in (root / 'packaging/build.in').read_text().splitlines()
                      if line.split('#', 1)[0].strip())
    return values


def render_lock(parent, names, target, scope):
    lines = [f'# 基本版 {target} CPython 3.12 / {scope}：由既有雜湊鎖定及 METADATA 閉包生成。',
             '# python scripts/packaging_profiles.py --generate；原生 OCR 與 Windows 驗收尚未完成。']
    for name in names:
        record = parent[name]
        lines.append(name + '==' + record['version'] + ' \\')
        lines.extend('    --hash=sha256:' + value + (' \\' if index < len(record['hashes']) - 1 else '')
                     for index, value in enumerate(record['hashes']))
    return '\n'.join(lines) + '\n'


def expected_files(root):
    config_path = root / 'packaging/profiles/base.json'
    config = json.loads(config_path.read_text())
    if config['schema_version'] != 1 or config['id'] != 'base' or config['release_ready'] or config['native_ocr_integrated']:
        raise ValueError('本輪只驗相依拆分，不得標記基本包可發行。')
    from license_inventory import verify
    notices_root = root / 'src/desktop_app/data/licenses/windows'
    inventory = verify(root / 'packaging/requirements-windows.txt', notices_root)
    licensed = {record['name']: record for record in inventory['packages']}
    outputs = {}; profiles = {}
    for target in TARGETS:
        parent, metadata = load_metadata(root, target)
        environment = marker_environment(target, config['python'])
        for scope in SCOPES:
            roots = root_requirements(root, config, scope)
            names, edges = closure(roots, metadata, environment)
            forbidden = set(names) & set(config['forbidden_packages'])
            if forbidden:
                raise ValueError('基本版混入選配／測試套件：' + ','.join(sorted(forbidden)))
            lock = render_lock(parent, names, target, scope)
            key = target + '-' + scope
            lock_path = f'packaging/profiles/base-{key}.txt'
            outputs[lock_path] = lock.encode()
            license_files = {}
            for name in names:
                record = licensed[name]
                if record['version'] != metadata[name]['version']:
                    raise ValueError('授權 metadata 版本不符：' + name)
                for path in [name + '/METADATA', *record['wheel_notice_files'],
                             *(source['path'] for source in record['supplemental_sources'])]:
                    license_files[path] = inventory['files'][path]
            profiles[key] = dict(lock=lock_path, lock_sha256=sha(lock.encode()), package_count=len(names),
                packages=names, roots=roots, dependency_edges=edges, marker_environment=environment,
                notice_scope='Windows wheel originals for matching pinned versions; Linux binary licenses not claimed',
                windows_notice_files=license_files)
    report = dict(schema_version=1, profile='base', source_version=tomllib.loads((root/'pyproject.toml').read_text())['project']['version'],
                  config_sha256=sha(config_path.read_bytes()),
                  native_ocr_integrated=False, release_ready=False, windows_executed=False,
                  scope='Python dependency closure and existing Windows notices only; not frozen/native acceptance',
                  profiles=profiles)
    outputs['packaging/profiles/base-closure.json'] = (json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode()
    return outputs, report


def verify_profiles(root=ROOT):
    outputs, report = expected_files(root)
    for path, expected in outputs.items():
        if (root / path).read_bytes() != expected:
            raise ValueError('profile 輸出已過期或被改動：' + path)
    return report


def capture_metadata(root=ROOT):
    """僅開發者明確執行才刷新；Linux 必須使用上位鎖定的 Linux 環境。"""
    import platform
    if platform.system() != 'Linux':
        raise ValueError('目前 Linux metadata 擷取工具必須在 Linux 執行。')
    for target in TARGETS:
        lock = root / f'packaging/requirements-{target}.txt'
        packages = {}
        for name, pin in read_lock(lock).items():
            if target == 'windows':
                raw = (root / 'src/desktop_app/data/licenses/windows' / name / 'METADATA').read_bytes()
            else:
                distribution = importlib.metadata.distribution(name)
                raw = distribution.read_text('METADATA').encode()
            record = metadata_record(raw)
            if record['version'] != pin['version']:
                raise ValueError('擷取環境版本不符：' + name)
            packages[name] = record
        snapshot = dict(schema_version=1, target=target, parent_lock_sha256=sha(lock.read_bytes()),
            source='Saved Windows wheel originals' if target == 'windows' else 'Installed locked Linux development environment; pip check and clean subset installation verified separately',
            packages=packages)
        (root / f'packaging/profiles/metadata-{target}.json').write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--capture-metadata', action='store_true')
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    if args.capture_metadata:
        capture_metadata()
    outputs, report = expected_files(ROOT)
    if args.generate:
        for path, data in outputs.items():
            (ROOT / path).write_bytes(data)
    verify_profiles()
    if args.report:
        from desktop_app.diagnostics import write_report
        write_report(report, args.report)
    for name, profile in report['profiles'].items():
        print(f"Verified base {name}: {profile['package_count']} packages; {len(profile['windows_notice_files'])} original notice/metadata files")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

"""從兩份可信建置清單產生 Inno 升級規則；不信任使用者目錄自行提供的清單。"""
import hashlib
from pathlib import Path, PurePosixPath

from base_install_catalog import CATALOG, encoded, validate, verify
from desktop_app.components.contracts import Version


def plan(target, previous=None):
    validate(target)
    versions = [Version.parse(target['app_version'])]
    removed = []; added = []; obsolete_directories = []
    if previous is not None:
        validate(previous)
        versions.append(Version.parse(previous['app_version']))
        if versions[0] == versions[1]:
            raise ValueError('跨版本規則必須使用兩個不同的真實版本。')
        names = {item['path'].casefold(): item['path'] for item in target['files']}
        for item in previous['files']:
            alias = names.get(item['path'].casefold())
            if alias is not None and alias != item['path']:
                raise ValueError('跨版檔名大小寫別名不明確。')
            if alias is None:
                removed.append(dict(item))
        previous_names = {item['path'].casefold() for item in previous['files']}
        added = [item['path'] for item in target['files'] if item['path'].casefold() not in previous_names]
        def parents(items):
            return {str(parent) for item in items for parent in PurePosixPath(item['path']).parents if str(parent) != '.'}
        target_parents = {name.casefold() for name in parents(target['files'])}
        obsolete_directories = sorted((name for name in parents(removed) if name.casefold() not in target_parents),
                                      key=lambda name: (-len(PurePosixPath(name).parts), name))
    # Inno 使用四段 UInt16 packed version；三段版本只能使用其可精確表示的範圍。
    if any(max(v.major, v.minor, v.patch) > 65535 for v in versions):
        raise ValueError('版本超過 Windows 安裝器數值範圍。')
    return dict(target_version=target['app_version'],
                target_catalog_sha256=hashlib.sha256(encoded(target)).hexdigest(),
                previous_version=previous['app_version'] if previous else '',
                previous_catalog_sha256=hashlib.sha256(encoded(previous)).hexdigest() if previous else '',
                obsolete_files=removed, added_paths=added,
                obsolete_directories=obsolete_directories,
                target_paths=[item['path'] for item in target['files']], automatic_failure_rollback=False)


def write_rules(path, target_directory, target, previous_directory=None, previous=None):
    """編譯前再次核對來源 bytes；產生靜態規則，不將可改寫的安裝 catalog 當授權來源。"""
    verify(target_directory, target)
    if (previous_directory is None) != (previous is None):
        raise ValueError('前版目錄與清單必須成對。')
    if previous is not None:
        verify(previous_directory, previous)
    rules = plan(target, previous)
    # Pascal 的單引號必須加倍；路徑先經既有安全相對路徑契約驗證。
    def literal(value): return "'" + value.replace("'", "''") + "'"
    lines = ['// 由同次建置的可信 source catalog 產生，不可手動替換為 installed catalog。',
             'const',
             '  TargetCatalogHash = ' + literal(rules['target_catalog_sha256']) + ';',
             '  PreviousVersion = ' + literal(rules['previous_version']) + ';',
             '  PreviousCatalogHash = ' + literal(rules['previous_catalog_sha256']) + ';',
             'procedure PopulateObsolete;', 'begin']
    for item in rules['obsolete_files']:
        lines += ['  ObsoleteNames.Add(' + literal(item['path'].replace('/', '\\')) + ');',
                  '  ObsoleteHashes.Add(' + literal(item['sha256']) + ');']
    for name in rules['added_paths']:
        lines.append('  AddedNames.Add(' + literal(name.replace('/', '\\')) + ');')
    for name in rules['target_paths']:
        lines.append('  TargetNames.Add(' + literal(name.replace('/', '\\')) + ');')
    for name in rules['obsolete_directories']:
        lines.append('  ObsoleteDirectories.Add(' + literal(name.replace('/', '\\')) + ');')
    lines += ['end;', '']
    with Path(path).open('x', encoding='utf-8-sig', newline='\n') as output:
        output.write('\n'.join(lines))
    return rules

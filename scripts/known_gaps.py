"""由固定候選的 source-review 與元件目錄推導「隨包揭露檔」（A13b）。

為什麼需要：A12c 規定，含未知或僅有建置宣告的條目要關閉，必須由使用者逐項接受，並且有一份
隨包的揭露檔列出被接受的元件 id。這個檔案不能手打，否則會與目錄脫鉤。本腳本從同一批來源
（A12 固定候選、元件目錄、Qt 目錄）推導缺口清單，寫出兩份內容一致的檔案：

- src/desktop_app/data/licenses/known-gaps.json：機器讀取，格式即 redistribution_gates 的
  validate_gap_acceptance 所需（schema_version 1、accepted_gaps 以義務 id 為鍵，值為元件 id 清單）。
  格式是封閉的，多出任何頂層鍵都會被拒絕，所以人看得懂的說明放在同名的 .md。
- src/desktop_app/data/licenses/known-gaps.md：人讀的對照表（元件名稱、來源、為何未知）。

本腳本只產生檔案，不做使用者決定：寫進揭露檔不代表使用者已接受；接受仍要登記在 obligations.json
的 decision_source 並由 redistribution_gates 的檢核確認。缺口集合的計算與判定共用
redistribution_gates.collect_catalogs，不另寫一套規則，避免兩邊漂移。

用法：
  python scripts/known_gaps.py            寫入兩份檔案
  python scripts/known_gaps.py --check    與現有檔案比對，不同或缺檔即非零退出（測試也用這條規則）
"""
import argparse
import collections
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import embedded_components
import qt_components
import redistribution_gates as gates

ROOT = gates.ROOT
PROFILE = 'base'
DEFAULT_REPORT = ROOT/'docs/development-records/runs/a12-fixed-review-2026-11-18/base-source-review.json'
JSON_PATH = ROOT/'src/desktop_app/data/licenses/known-gaps.json'
MARKDOWN_PATH = ROOT/'src/desktop_app/data/licenses/known-gaps.md'
EMBEDDED_CATALOG = ROOT/embedded_components.CATALOG_PREFIX/'base-windows.json'


def derive(report, registry, *, root=ROOT):
    """回傳 {義務 id: [缺口元件 id 排序後清單]}，只含 base 且確實有缺口的條目。

    以固定候選的 source-review 為依據；與 gates.assess 使用同一個 collect_catalogs，
    並以不檢查揭露的 validator 呼叫（揭露尚未存在時也要能推導）。
    """
    gates.validate_registry(registry, root)
    require_base(report, registry)
    config = registry['profiles'][PROFILE]
    raw = report['classification_input']['report']
    native = [row['file'] for row in raw['native_files']]
    reasons = collections.Counter()
    for row in raw['candidate_inventory']['files']:
        reasons.update(row['review_reasons'])
    collected = gates.collect_catalogs(report, PROFILE, config, root, native, reasons, lambda entry, unknown: None)
    unknown = collected['unknown']
    base_ids = {entry['id'] for entry in config['entries']}
    gates.require(set(unknown) <= base_ids, 'Gap owner is not a base obligation')
    return {key: sorted(values) for key, values in sorted(unknown.items()) if values}


def require_base(report, registry):
    """揭露檔只描述固定候選的 base 來源，來源提交須與登記表基準相同。"""
    gates.require(report.get('profile') == PROFILE, 'Known-gap report must be the base profile')
    gates.require(report.get('selection', {}).get('source_commit') == registry['profiles'][PROFILE]['source_commit'],
                  'Known-gap report source differs from the registry basis')


def disclosure(accepted):
    """封閉格式：只有 schema_version 與 accepted_gaps；鍵排序以保證每次產生的位元組相同。"""
    return {'schema_version': 1, 'accepted_gaps': {key: list(values) for key, values in accepted.items()}}


def describe(report, accepted, *, root=ROOT):
    """為每個缺口 id 組出人讀說明：(義務 id, 元件 id, 名稱, 來源, 為何未知)。

    說明來自同一批來源檔，不手填；找不到說明的 id 直接拒絕，避免揭露檔與說明脫節。
    """
    rows = {}
    embedded = gates.read_json(EMBEDDED_CATALOG)
    for wheel in embedded['wheels']:
        for component in wheel['components']:
            if component['version_basis'] != 'unknown':
                continue
            gap = wheel['distribution']+'/'+component['id']
            rows[gap] = (component['name'], f"wheel {wheel['distribution']} {wheel['version']}",
                         'wheel 內無版本文字檔或 METADATA 宣告；A12d 的 Windows 執行期觀測也未取得版本')
    raw = report['classification_input']['report']
    for row in raw.get('cpython_components', {}).get('files', []):
        if row.get('version_status') in ('unknown', 'build-declaration-only') or not row.get('observed_version'):
            gap = 'cpython/'+row['component']
            reason = (f"CPython 官方只宣告建置版本 {row['declared_version']}，沒有執行期版本觀測"
                      if row.get('version_status') == 'build-declaration-only' else '版本未知')
            rows.setdefault(gap, (row['component'], f"CPython {raw['cpython_components']['cpython_version']} 官方安裝（{row['file']}）", reason))
    qt = gates.read_json(root/qt_components.CATALOG)
    for component in qt['components']:
        rows[component['id']] = (component['name'], f"Qt {qt['version']} 上游來源（{component['qdoc_module']}）",
                                 ('Qt 上游來源未宣告版本' if component['version_basis'] == 'unknown'
                                  else 'Qt 上游來源宣告了版本，但尚未證明已編入 Windows wheel'))
    for native in qt['native_files']:
        if native['version_basis'] == 'unknown':
            rows['qt-native/'+native['file']] = (native['file'], '外部 Mesa 軟體 OpenGL（PySide6 內附）',
                                                 '來源未提供版本，模組來自外部 Mesa')
    out = []
    for obligation, values in accepted.items():
        for gap in values:
            gates.require(gap in rows, 'No human description for gap: '+gap)
            name, source, reason = rows[gap]
            out.append((obligation, gap, name, source, reason))
    return out


def markdown(rows):
    """人讀對照表；由 disclosure 同一批資料產生，與 JSON 一致。"""
    lines = ['# 基本包已知缺口（隨包揭露）', '',
             '本表與同目錄的 known-gaps.json 由 scripts/known_gaps.py 產生，兩者列出的元件 id 完全相同。',
             '列出的是版本未知、只有建置宣告，或來源未證明已編入 Windows wheel 的元件。列入本表不代表已取得',
             '再散布核准；它只說明這些元件目前知道什麼、不知道什麼。', '',
             f'共 {len(rows)} 項。', '',
             '| 義務條目 | 元件 id | 名稱 | 來源或所屬 | 為何未知 |', '| --- | --- | --- | --- | --- |']
    for obligation, gap, name, source, reason in rows:
        cells = [obligation, gap, name, source, reason]
        gates.require(not any('|' in cell for cell in cells), 'Table cell contains a separator: '+gap)
        lines.append('| ' + ' | '.join(cells) + ' |')
    return '\n'.join(lines)+'\n'


def render(report, registry, *, root=ROOT):
    """回傳 (JSON 文字, Markdown 文字)；兩者只由同一次推導產生。"""
    accepted = derive(report, registry, root=root)
    rows = describe(report, accepted, root=root)
    covered = {gap for _, gap, *_ in rows}
    gates.require(covered == {gap for values in accepted.values() for gap in values}, 'Description does not cover every gap')
    text = json.dumps(disclosure(accepted), ensure_ascii=False, indent=2)+'\n'
    return text, markdown(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--source-review', type=Path, default=DEFAULT_REPORT)
    parser.add_argument('--registry', type=Path, default=gates.REGISTRY)
    parser.add_argument('--check', action='store_true', help='只比對，不寫入')
    args = parser.parse_args(argv)
    text, markdown_text = render(gates.read_json(args.source_review), gates.read_json(args.registry))
    if args.check:
        current = JSON_PATH.read_text(encoding='utf-8') if JSON_PATH.is_file() else None
        current_md = MARKDOWN_PATH.read_text(encoding='utf-8') if MARKDOWN_PATH.is_file() else None
        if current != text or current_md != markdown_text:
            print('known-gaps 與目錄推導不一致，請執行 python scripts/known_gaps.py 重新產生')
            return 1
        print('known-gaps 與目錄推導一致')
        return 0
    JSON_PATH.write_text(text, encoding='utf-8')
    MARKDOWN_PATH.write_text(markdown_text, encoding='utf-8')
    print('寫入', JSON_PATH.relative_to(ROOT), 'and', MARKDOWN_PATH.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

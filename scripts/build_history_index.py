"""由既有紀錄自動產生歷史索引 docs/history-index.md；索引是查詢用的，不是開工必讀。

責任與限制：
- 只讀取三種來源並各列一行：證據目錄（docs/development-records/runs/*）、
  歷次現況存檔（docs/history/status/*.md）、決策紀錄（docs/decisions/*.md）。
  不修改任何來源檔，也不複製其內容；細節留在原處，索引只提供「去哪裡找」。
- 證據目錄的 manifest.json 欄位歷來不一致，因此只取確實存在的欄位，缺的留空，
  不從檔名或數字推測結果。日期取目錄名稱結尾的 YYYY-MM-DD。
- 關鍵字來源有二：manifest.json 的 keywords（新證據建立時填），以及
  docs/history/keywords.json 的補充對照表（事後為舊證據補記；與原始證據分開存放，
  讓人看得出哪些是事後加上的判讀）。兩者都沒有就留空。
- 輸出完全由輸入決定且排序固定，因此可用 --check 在 CI 比對：有新紀錄卻沒重新
  產生索引時以非零結束，不需要靠人記得更新。
用法：python scripts/build_history_index.py [--check]
"""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = 'docs/history-index.md'
RUNS = 'docs/development-records/runs'
STATUS = 'docs/history/status'
DECISIONS = 'docs/decisions'
KEYWORDS = 'docs/history/keywords.json'
DATE = re.compile(r'(\d{4}-\d{2}-\d{2})')


def heading(path):
    """回傳 Markdown 第一個標題文字；沒有標題時回傳檔名，避免索引出現空白主題。"""
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('#'):
            return line.lstrip('#').strip()
    return path.stem


def cell(text):
    """表格儲存格內不可有換行或未跳脫的直線符號。"""
    return str(text).replace('|', '／').replace('\n', ' ').strip()


def run_row(directory, extra):
    """把一個證據目錄整理成一列；只使用 manifest 中實際存在的欄位。"""
    manifest_path = directory / 'manifest.json'
    manifest = {}
    if manifest_path.is_file():
        loaded = json.loads(manifest_path.read_text(encoding='utf-8'))
        manifest = loaded if isinstance(loaded, dict) else {}
    readme = directory / 'README.md'
    found = DATE.findall(directory.name)
    source = manifest.get('tested_source') or manifest.get('tested_commit') or ''
    facts = []
    if 'accepted' in manifest:
        facts.append('接受' if manifest['accepted'] else '未接受')
    if manifest.get('windows_executed') is True:
        facts.append('Windows已執行')
    run = manifest.get('full_regression_run') or manifest.get('linux_full_regression_run')
    passed = manifest.get('full_regression_passed') or manifest.get('linux_full_regression_passed')
    if run:
        facts.append(f'回歸{run}／通過{passed}' if passed else f'回歸{run}')
    words = list(manifest.get('keywords') or []) + list(extra.get(directory.name) or [])
    return dict(date=found[-1] if found else '', kind='證據',
                topic=heading(readme) if readme.is_file() else directory.name,
                source=str(source)[:7], facts='、'.join(facts), keywords='、'.join(dict.fromkeys(words)),
                path=f'{RUNS}/{directory.name}/' + ('README.md' if readme.is_file() else ''))


def document_row(path, kind, base):
    found = DATE.findall(path.name)
    return dict(date=found[0] if found else '', kind=kind, topic=heading(path), source='', facts='',
                keywords='', path=f'{base}/{path.name}')


def collect(root):
    extra_path = root / KEYWORDS
    extra = json.loads(extra_path.read_text(encoding='utf-8')) if extra_path.is_file() else {}
    rows = []
    runs = root / RUNS
    if runs.is_dir():
        rows += [run_row(item, extra) for item in sorted(runs.iterdir()) if item.is_dir()]
    status = root / STATUS
    if status.is_dir():
        rows += [document_row(item, '現況存檔', STATUS) for item in sorted(status.glob('*.md'))]
    decisions = root / DECISIONS
    if decisions.is_dir():
        rows += [document_row(item, '決策', DECISIONS) for item in sorted(decisions.glob('*.md'))]
    # 新的在上；沒有日期的決策紀錄排最後，同日再依路徑固定順序。
    return sorted(rows, key=lambda row: (row['date'] == '', [-ord(c) for c in row['date']], row['path']))


def render(rows):
    lines = [
        '# 歷史索引',
        '',
        '由 `scripts/build_history_index.py` 自動產生，**請勿手動編輯**；新增紀錄後重新執行腳本。',
        '這份索引用來查找，不是開工必讀。開工只需要讀 [AGENTS.md](../AGENTS.md) 與 [STATUS.md](../STATUS.md)。',
        '',
        '出錯或需要追溯時：先用日期、主題或關鍵字在下表找到那一筆，再打開它的路徑。',
        '「來源」是當次受測的提交；「結果」只列該筆清單檔實際記錄的欄位，空白表示沒有記錄，不代表通過。',
        '',
        f'共 {len(rows)} 筆。',
        '',
        '| 日期 | 類型 | 主題 | 來源 | 結果 | 關鍵字 | 路徑 |',
        '| --- | --- | --- | --- | --- | --- | --- |',
    ]
    for row in rows:
        relative = row['path'][len('docs/'):]
        lines.append(f"| {row['date']} | {row['kind']} | {cell(row['topic'])} | {row['source']} | "
                     f"{cell(row['facts'])} | {cell(row['keywords'])} | [{relative}]({relative}) |")
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--check', action='store_true', help='只比對，不寫入；不一致時以非零結束')
    parser.add_argument('--root', type=Path, default=ROOT)
    arguments = parser.parse_args()
    text = render(collect(arguments.root))
    target = arguments.root / OUTPUT
    if arguments.check:
        current = target.read_text(encoding='utf-8') if target.is_file() else ''
        if current != text:
            print(f'{OUTPUT} is out of date; run python scripts/build_history_index.py', file=sys.stderr)
            return 1
        print(f'{OUTPUT} is up to date')
        return 0
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding='utf-8', newline='')
    print(target)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

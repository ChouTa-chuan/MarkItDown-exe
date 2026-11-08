"""把已產生的 CI 報告附上 job summary；不推定未執行測試，也不發布安裝包。"""
import argparse
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', type=Path, required=True)
    parser.add_argument('--summary', type=Path, required=True)
    args = parser.parse_args()
    records = {}
    for name in ['build-evidence.json', 'native-inputs/downloads.json', 'windows-build.json', 'acceptance/windows-acceptance.json',
                 'acceptance/core-self-test.json','acceptance/full-self-test.json',
                 'acceptance/relocated-self-test.json']:
        path = args.reports/name
        if path.is_file():
            if path.stat().st_size > 128*1024:
                raise ValueError('CI summary 報告超過限制。')
            records[name] = json.loads(path.read_text(encoding='utf-8'))
    tails = {}
    # 僅列開發管線自身的日誌末段；CI 不處理使用者文件或輸出環境秘密。
    for path in sorted(args.reports.rglob('*.log')):
        if path.stat().st_size > 8*1024**2:
            continue
        tails[path.relative_to(args.reports).as_posix()] = '\n'.join(path.read_text(encoding='utf-8', errors='replace').splitlines()[-35:])[-6000:]
    content = json.dumps(dict(schema_version=1, reports=records, log_tails=tails), ensure_ascii=False, indent=2)
    if len(content.encode('utf-8')) > 900*1024:
        raise ValueError('CI summary 超過平台上限。')
    with args.summary.open('a', encoding='utf-8') as output:
        output.write('\n## Windows 基本包驗證報告\n\n')
        output.write('僅為 CI 開發驗證；乾淨機、人工操作、安裝包與 GPU 尚未驗收。\n\n')
        output.write('<!-- MARKITDOWN_WINDOWS_CI_REPORT -->\n```json\n'+content+'\n```\n')


if __name__ == '__main__':
    main()

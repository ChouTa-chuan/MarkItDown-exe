"""歷史索引產生器：欄位只取實際存在者、排序固定、--check 能擋下過期索引；僅用合成目錄。"""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_history_index as subject


class HistoryIndexTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')
        return path

    def run_directory(self, name, manifest=None, title='標題'):
        self.write(f'{subject.RUNS}/{name}/README.md', f'# {title}\n\n內容\n')
        if manifest is not None:
            self.write(f'{subject.RUNS}/{name}/manifest.json', json.dumps(manifest))

    def rows(self):
        return {row['path']: row for row in subject.collect(self.root)}

    def test_only_recorded_fields_are_reported(self):
        self.run_directory('alpha-2026-01-02', dict(tested_source='a' * 40, accepted=True, windows_executed=True,
                                                    full_regression_run=10, full_regression_passed=9,
                                                    keywords=['互鎖']), title='甲 | 乙')
        self.run_directory('beta-2026-01-03', dict(schema_version=1))
        self.run_directory('gamma-no-date')
        rows = self.rows()
        alpha = rows[f'{subject.RUNS}/alpha-2026-01-02/README.md']
        self.assertEqual((alpha['date'], alpha['source'], alpha['keywords']), ('2026-01-02', 'aaaaaaa', '互鎖'))
        self.assertEqual(alpha['facts'], '接受、Windows已執行、回歸10／通過9')
        beta = rows[f'{subject.RUNS}/beta-2026-01-03/README.md']
        # 清單沒有記錄結果時留空，不能被讀成通過。
        self.assertEqual((beta['facts'], beta['source'], beta['keywords']), ('', '', ''))
        self.assertEqual(rows[f'{subject.RUNS}/gamma-no-date/README.md']['date'], '')
        self.assertNotIn('甲 | 乙', subject.render(subject.collect(self.root)))

    def test_false_acceptance_is_shown_and_supplementary_keywords_are_merged(self):
        self.run_directory('fail-2026-02-01', dict(accepted=False, windows_executed=False, keywords=['路徑']))
        self.write(subject.KEYWORDS, json.dumps({'fail-2026-02-01': ['路徑', 'Inno']}))
        row = self.rows()[f'{subject.RUNS}/fail-2026-02-01/README.md']
        self.assertEqual(row['facts'], '未接受')
        self.assertEqual(row['keywords'], '路徑、Inno')

    def test_status_archives_and_decisions_are_listed_newest_first(self):
        self.run_directory('old-2026-01-01', {})
        self.write(f'{subject.STATUS}/2026-03-01-phase.md', '# 階段現況\n')
        self.write(f'{subject.DECISIONS}/0001-choice.md', '# 決策一\n')
        rows = subject.collect(self.root)
        self.assertEqual([row['kind'] for row in rows], ['現況存檔', '證據', '決策'])
        self.assertEqual(rows[0]['topic'], '階段現況')

    def test_check_detects_stale_index_without_writing(self):
        self.run_directory('one-2026-01-01', {})
        command = [sys.executable, subject.__file__, '--root', str(self.root)]
        self.assertNotEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)
        self.assertFalse((self.root / subject.OUTPUT).exists())
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)
        self.run_directory('two-2026-01-02', {})
        self.assertNotEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)

    def test_repository_index_is_current(self):
        # 真正 repo 的索引必須與來源一致；新增紀錄後忘記重新產生會在這裡失敗。
        root = Path(subject.__file__).resolve().parents[1]
        self.assertEqual((root / subject.OUTPUT).read_text(encoding='utf-8'), subject.render(subject.collect(root)))


if __name__ == '__main__':
    unittest.main()

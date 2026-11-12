"""核對本目錄保存的兩份 Windows CI artifact 原檔。

責任：只讀取 ZIP，不解壓到磁碟；比對 ZIP 自身雜湊、成員 CRC、
bundle-provenance.json 雜湊與 repo 既有公開摘要的 report_sha256，
並重算未對照來源數。任何一項不符即以非零結束，不修正或覆寫摘要。
用法：python verify_archive.py [--write verification.json]
"""
import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUMMARIES = HERE.parent / 'candidate-inventory-ci-2026-11-11'
EXPECTED = {
    'base': dict(run=42982427175, artifact=13838258991,
                 zip_sha256='0808ecd9068d2a926663e9cc05da1b44533ce713654c713a06dc8be548281782'),
    'cpu': dict(run=42982427186, artifact=13839056280,
                zip_sha256='54831b0215cff8185e6fd0544c5be54bc8f57a6b771d76dafdc0e4937bc41a4e'),
}


def check(profile):
    path = HERE / f'windows-{profile}-validation-reports.zip'
    raw = path.read_bytes()
    summary = json.loads((SUMMARIES / f'windows-{profile}-inventory-summary.json').read_bytes())
    with zipfile.ZipFile(path) as archive:
        bad_member = archive.testzip()
        members = len(archive.namelist())
        report_raw = archive.read('bundle-provenance.json')
    report = json.loads(report_raw)
    files = report['candidate_inventory']['files']
    unresolved = sum('source-owner-unresolved' in (item.get('review_reasons') or []) for item in files)
    review = sum(bool(item.get('review_reasons')) for item in files)
    result = dict(
        profile=profile, workflow_run=EXPECTED[profile]['run'], artifact_id=EXPECTED[profile]['artifact'],
        zip_bytes=len(raw), zip_sha256=hashlib.sha256(raw).hexdigest(),
        zip_members=members, zip_crc_ok=bad_member is None,
        report_bytes=len(report_raw), report_sha256=hashlib.sha256(report_raw).hexdigest(),
        public_summary_report_sha256=summary['report_sha256'],
        source_commit=report['source_commit'], source_version=report['source_version'],
        files=len(files), unresolved_files=unresolved, review_files=review,
        runtime_sbom_complete=report['candidate_inventory']['summary']['runtime_sbom_complete'],
        redistribution_approved=report['redistribution_approved'], release_ready=report['release_ready'],
    )
    result['accepted'] = (
        result['zip_sha256'] == EXPECTED[profile]['zip_sha256'] and result['zip_crc_ok']
        and result['report_sha256'] == summary['report_sha256']
        and result['source_commit'] == summary['source_commit']
        and result['files'] == summary['inventory']['files']
        and result['unresolved_files'] == summary['inventory']['unresolved_files']
        and result['review_files'] == summary['inventory']['review_files'])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', type=Path)
    arguments = parser.parse_args()
    results = [check('base'), check('cpu')]
    output = dict(check='ci-full-report-archive', accepted=all(item['accepted'] for item in results),
                  windows_rebuilt=False, results=results)
    text = json.dumps(output, ensure_ascii=False, indent=2) + '\n'
    if arguments.write:
        arguments.write.write_text(text, encoding='utf-8')
    sys.stdout.write(text)
    return 0 if output['accepted'] else 1


if __name__ == '__main__':
    raise SystemExit(main())

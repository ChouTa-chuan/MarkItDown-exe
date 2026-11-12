"""交接文件的路徑、範例語法與當前證據對照；不執行完整產品測試。"""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tomllib
from urllib.parse import unquote


def main():
    root=Path.cwd()
    output=root/'docs/development-records/runs/project-handoff-2026-11-12'
    document=(root/'PROJECT_HANDOFF.md').read_text(encoding='utf-8')
    markdown=['PROJECT_HANDOFF.md','README.md','AGENTS.md','CHANGELOG.md',
              'docs/development-status.md','docs/architecture-guide.md','docs/packaging.md',
              'docs/packaging-profiles.md','docs/development-records/README.md']
    count=0;broken=[]
    for name in markdown:
        path=root/name
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if target.startswith(('https:','http:','#','mailto:')):continue
            target=unquote(target.split('#')[0].strip('<>'))
            if target and not (path.parent/target).exists():broken.append([name,target])
            count+=1
    assert not broken,broken
    # 僅作語法解析，不下載模型、不建立另一套venv、不重跑舊功能驗收。
    blocks=re.findall(r'^```bash\n(.*?)^```',document,re.M|re.S)
    for block in blocks:
        result=subprocess.run(['bash','-n'],input=block,text=True,capture_output=True)
        assert result.returncode==0,result.stderr
    python_blocks=re.findall(r"<<'PY'\n(.*?)\nPY",document,re.S)
    for block in python_blocks:ast.parse(block)
    project=tomllib.loads((root/'pyproject.toml').read_text())['project']
    progress=json.loads((root/'docs/progress.json').read_text())
    validation=json.loads((root/'docs/validation-results.json').read_text())
    assert project['version']==progress['source_version']=='0.19.1'
    for data in (progress,validation):
        assert data['full_regression']['run']==684 and data['full_regression']['passed']==683
        assert data['full_regression']['expected_failures']==1 and data['full_regression']['skipped']==0
        assert data['full_regression']['isolated_modules']==43
        assert data['full_regression']['source_commit']=='cb8f24d8dbbb937c9f1dadeadfe5c93a702650f1'
    rows=dict(re.findall(r'^\| (C\d{2}) [^|]+\| ([^|]+) \|',document,re.M))
    checks=[c for phase in progress['component_rollout']['phases'] for c in phase['checks']]
    assert len(rows)==len(checks)==12
    for check in checks:
        expected=('完成' if check['done'] else
                  str(sum(s['done'] for s in check['subchecks']))+'/'+str(len(check['subchecks']))
                  if check.get('subchecks') else '待驗')
        assert rows[check['id']].strip()==expected,(check['id'],expected)
    assert sum(c['done'] for c in checks)==7
    record=root/'docs/development-records/runs/candidate-inventory-ci-2026-11-11'
    base=json.loads((record/'windows-base-inventory-summary.json').read_text())
    cpu=json.loads((record/'windows-cpu-inventory-summary.json').read_text())
    assert (base['inventory']['files'],cpu['inventory']['files'],cpu['package_inventory']['files'])==(1655,741,742)
    assert (base['inventory']['unresolved_files'],cpu['inventory']['unresolved_files'])==(154,303)
    assert (base['inventory']['review_files'],cpu['inventory']['review_files'])==(191,337)
    assert cpu['package_sha256'] in document
    upstream=json.loads((root/'vendor/markitdown/UPSTREAM.json').read_text())
    assert upstream['version']=='0.1.9' and upstream['license']=='MIT' and not upstream['local_modifications']
    assert upstream['commit'] in document
    snapshots=json.loads((root/'docs/architecture/snapshots.json').read_text())['records']
    assert len(snapshots)==28
    for row in snapshots:
        path=root/'docs/architecture'/row['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==row['file_sha256']
    for name in ('README.md','docs/architecture-guide.md'):
        previous=subprocess.check_output(['git','show','HEAD:'+name],text=True)
        current=(root/name).read_text()
        assert re.findall(r'```mermaid\n(.*?)```',previous,re.S)==re.findall(r'```mermaid\n(.*?)```',current,re.S)
    changed=subprocess.check_output(['git','diff','--name-only','HEAD'],text=True).splitlines()
    assert not [name for name in changed if name.startswith(('src/','vendor/','packaging/','scripts/','tests/','docs/architecture/versions/'))]
    for name in changed:
        if name.startswith('docs/development-records/runs/'):
            assert subprocess.run(['git','cat-file','-e','HEAD:'+name],capture_output=True).returncode!=0,name
    example=json.loads((output/'cli-example.json').read_text())
    assert example['exit_code']==0 and example['exact_unicode_output_matched']
    assert (output/'sample-input.txt').read_bytes()==(output/'sample-output.md').read_bytes()
    report=dict(accepted=True,date_taipei='2026-11-12',document='PROJECT_HANDOFF.md',
                document_sha256=hashlib.sha256(document.encode()).hexdigest(),
                program_version=project['version'],architecture_version='0.4',
                relative_links_checked=count,broken_links=broken,bash_blocks_checked=len(blocks),
                embedded_python_blocks_checked=len(python_blocks),milestones_matched=12,
                completed_milestones=7,functional_baseline_run=684,functional_baseline_passed=683,
                functional_baseline_expected_failures=1,functional_tests_rerun=False,
                architecture_snapshots_unchanged=28,existing_mermaid_blocks_unchanged=True,
                actual_text_cli_example_exit=example['exit_code'],upstream_check_observed=dict(source_files=45,public_pdf_fixtures=4),
                license_check_observed=dict(packages=58,notice_metadata_files=214))
    (output/'document-checks.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(report,ensure_ascii=False))


if __name__=='__main__':main()

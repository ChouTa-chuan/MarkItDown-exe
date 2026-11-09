from pathlib import Path
import subprocess,json,hashlib,re
from urllib.parse import unquote
root=Path('/workspace/MarkItDown-exe');run=root/'docs/development-records/runs/temporary-cleanup-prep-2026-11-09';base='c5f0c01'
def digest(b):return hashlib.sha256(b).hexdigest()
def old(path):return subprocess.run(['git','show',base+':'+path],cwd=root,capture_output=True,check=True).stdout
tracked=subprocess.run(['git','ls-tree','-r','--name-only','-z',base],cwd=root,capture_output=True,check=True).stdout.decode().split('\0');tracked=[p for p in tracked if p]
def unchanged(paths):
 for name in paths:assert (root/name).read_bytes()==old(name),name
 return len(paths)
records=[p for p in tracked if p.startswith('docs/development-records/') and p!='docs/development-records/README.md']
snaps=[p for p in tracked if p.startswith('docs/architecture/versions/')]
locks=[p for p in tracked if p.startswith('packaging/') and (Path(p).name.startswith('requirements') or p.startswith('packaging/profiles/base-')) and Path(p).suffix=='.txt']
licenses=[p for p in tracked if p.startswith('src/desktop_app/data/licenses/')]
results={}
for name in tracked:
 if name.startswith('docs/development-records/') and name.endswith('/manifest.json'):
  data=json.loads((root/name).read_text())
  if 'records' not in data:continue
  for entry in data['records']:
   payload=((root/name).parent/entry['file']).read_bytes();assert digest(payload)==entry['sha256'],(name,entry['file'])
   if 'bytes' in entry:assert len(payload)==entry['bytes'],(name,entry['file'])
  results[name]=len(data['records'])
s=json.loads((root/'docs/architecture/snapshots.json').read_text())
for entry in s['records']:
 payload=(root/'docs/architecture'/entry['file']).read_bytes();assert digest(payload)==entry['file_sha256'],entry['file']
 match=re.search(r'```mermaid\n(.*?)\n```',payload.decode(),re.S)
 assert match and digest(match[1].encode())==entry['diagram_sha256'],entry['file']
quality=[p for p in tracked if p in ['src/desktop_app/data/worker-health.json','src/desktop_app/data/ocr-models.json','tests/fixtures/ocr-traditional-meeting.png'] or p.endswith('ocr-quality-sample.json')]
data_baseline=[p for p in tracked if p.startswith('src/desktop_app/data/')]
links=0
for path in [root/'README.md',root/'CHANGELOG.md',root/'docs/temporary-cleanup-ci.md',root/'docs/development-status.md',root/'docs/development-records/README.md',run/'README.md']:
 for target in re.findall(r'(?<!!)\[[^\]]+\]\(([^)]+)\)',path.read_text()):
  if re.match(r'(?:[a-z]+:|#)',target):continue
  target=unquote(target.split('#')[0].strip('<>'))
  assert (path.parent/target).exists(),(path.relative_to(root),target)
  links+=1
verification=json.loads((run/'verification.json').read_text())
for name,expected in verification['source_hashes'].items():assert digest((root/name).read_bytes())==expected,name
out=dict(previous_manifests_verified=results,previous_committed_record_files_unchanged=unchanged(records),previous_architecture_snapshots_unchanged=unchanged(snaps),architecture_snapshots_verified=len(s['records']),locked_requirements_unchanged=unchanged(locks),original_license_asset_files_unchanged=unchanged(licenses),previous_product_data_files_unchanged=unchanged(data_baseline),traditional_quality_fixture_and_old_health_unchanged=unchanged(quality),relative_markdown_links_verified=links,baseline_commit=base,source_version='0.17.2',completed_date_taipei='2026-11-09',check='CI-owned-temporary-cleanup-preparation',linux_full_regression_accepted=True,windows_executed_this_revision=False,gpu_executed=False,full_c11_complete=False,temporary_cleanup_complete=False)
(run/'integrity.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in out.items() if k!='previous_manifests_verified'},ensure_ascii=False,indent=2))

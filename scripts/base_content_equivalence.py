"""對照固定候選與重建套件，保留實際差異與證據強度。"""
from datetime import datetime, timezone
import hashlib
import json

from candidate_inventory import verify_inventory
from candidate_review import MAX_SOURCE_REPORT, canonical

BASELINE_RUN = 44295039865
BASELINE_ARTIFACT = 'windows-base-validation-reports'
SAVED_ARTIFACT = 'b1b-fixed-baseline-report'
DEADLINE = datetime(2026, 11, 25, 11, 45, tzinfo=timezone.utc)
DATA = '_internal/desktop_app/data/'
# 僅准許已說明的確切路徑。分類或副檔名相同不能自動成為例外。
GENERATED = {
    DATA+'native/source.json': '記錄本次 OCR 輸入建置收據的 SHA-256，已重核收據與固定來源。',
    DATA+'native/manifest.json': '包含本次生成 native/source.json 的指紋；OCR 引擎與模型本身仍逐檔對照。',
    DATA+'licenses/native/manifest.json': '記錄本次 PyInstaller 收集的本機來源目錄；DLL 本身仍逐檔對照。',
    DATA+'build-profile.json': '記錄本次生成資產的 SHA-256；固定版本與資產內容由建置驗收重核。',
    'base-install-catalog.json': '安裝器從本次 bundle 生成路徑及指紋索引，跟隨生成資產差異。',
}


def sha_json(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def provenance_input(directory, review, source):
    matches = list(directory.rglob('bundle-provenance.json'))
    if len(matches) != 1:
        raise ValueError('Expected one original bundle-provenance.json')
    file = matches[0]
    if not file.is_file() or file.is_symlink() or file.stat().st_size > MAX_SOURCE_REPORT:
        raise ValueError('Unsafe original provenance report')
    raw = file.read_bytes()
    if hashlib.sha256(raw).hexdigest() != review['provenance_report_sha256']:
        raise ValueError('Original provenance SHA-256 mismatch')
    baseline = json.loads(raw)
    if (baseline['source_commit'] != source or baseline.get('profile') != 'base'
            or baseline.get('host_platform') != 'win32' or baseline.get('accepted') is not True
            or sha_json(baseline['candidate_inventory']) != review['inventory_sha256']):
        raise ValueError('Original provenance is outside the fixed accepted review')
    return file, baseline


def inventory_index(rows):
    values = {row['path']: {'sha256': row['sha256'], 'bytes': row['bytes']} for row in rows}
    if len({name.casefold() for name in values}) != len(rows):
        raise ValueError('Duplicate inventory path')
    return values


def compare(bundle, rebuilt, review, original, *, now=None, baseline_run=BASELINE_RUN):
    """只將經核對的完整 inventory 視為逐檔對照，退路由使用者指定的期限控制。"""
    inventory = rebuilt['candidate_inventory']
    verify_inventory(bundle, inventory)
    current = inventory_index(inventory['files'])
    pure_sha = sha_json(rebuilt['python_archives']['pure_modules'])
    if pure_sha != review['pure_modules_sha256']:
        raise ValueError('Pure modules SHA-256 mismatch')
    if len(current) != review['inventory_summary']['files']:
        raise ValueError('Rebuilt path count differs from the fixed candidate')

    if original is not None:
        baseline = inventory_index(original['candidate_inventory']['files'])
        if set(baseline) != set(current):
            missing = sorted(set(baseline) - set(current))
            extra = sorted(set(current) - set(baseline))
            raise ValueError(f'Bundle paths differ: missing={missing[:4]}, extra={extra[:4]}')
        mode = 'full-inventory'
        counts = dict(files=len(current))
    else:
        if (now or datetime.now(timezone.utc)) < DEADLINE:
            raise ValueError('Repository-only evidence is allowed after the baseline deadline')
        # 固定分類、原生檔與已保留的揭露、原文列直接對實際 inventory。無完整路徑集合，必須揭露限制。
        classified = review['classification']['files']
        report = review['classification_input']['report']
        native = [dict(path='_internal/'+r['file'], sha256=r['bundled_sha256'], bytes=r['bundled_bytes'])
                  for r in report['native_files']]
        original_notices = [n for p in review['packages'] for n in p['notices']]
        baseline = {}
        for group in (classified, native, original_notices, report['candidate_inventory']['files']):
            for name, fingerprint in inventory_index(group).items():
                if name in baseline and baseline[name] != fingerprint:
                    raise ValueError('Conflicting fixed evidence for '+name)
                baseline[name] = fingerprint
        if not set(baseline) <= set(current):
            raise ValueError('Rebuilt bundle is missing a retained fixed file')
        mode = 'retained-review'
        counts = dict(files=len(current), classified=len(classified), native=len(native),
                      original_notices=len(original_notices), compared_paths=len(baseline))

    changes = sorted(name for name in baseline if baseline[name] != current[name])
    unexpected = [name for name in changes if name not in GENERATED]
    if unexpected:
        raise ValueError('Unexpected changed files: '+', '.join(unexpected[:20]))
    return dict(check='base-content-equivalence', schema_version=1, accepted=True, mode=mode,
                candidate_source=review['selection']['source_commit'], counts=counts, pure_modules_sha256=pure_sha,
                original_provenance_sha256=review['provenance_report_sha256'] if original is not None else None,
                original_provenance_run=BASELINE_RUN if original is not None else None,
                baseline_download_run=baseline_run if original is not None else None,
                rebuilt_inventory_sha256=sha_json(inventory),
                full_path_set_verified=original is not None,
                changed_generated_files=[dict(path=name, reason=GENERATED[name],
                                              original=baseline[name], rebuilt=current[name]) for name in changes])

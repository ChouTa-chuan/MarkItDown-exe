"""C05 實際 HTTPS 驗收：只下載固定官方 LICENSE；測試金鑰不持久化或用於發行。"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
from importlib.metadata import version
from importlib.resources import files
import json
from pathlib import Path
import tempfile

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.components.catalog import CatalogVerifier, TrustPolicy, canonical_json
from desktop_app.components.contracts import ComponentSpec, ComponentState
from desktop_app.components.downloads import DownloadService
from desktop_app.components.registry import ComponentRegistry
from desktop_app.models import manifest
from desktop_app.diagnostics import write_report


def collect_report():
    now = datetime.now(timezone.utc)
    upstream = manifest()
    expected = upstream['files']['LICENSE']
    # 以隨包官方授權原文定義大小，再比對既有上游固定清單，沒有新增未知遠端來源。
    reference = files('desktop_app').joinpath('data/licenses/models/tessdata-fast-Apache-2.0.txt').read_bytes()
    if hashlib.sha256(reference).hexdigest() != expected:
        raise RuntimeError('Bundled upstream license differs from pinned source')
    size = len(reference)
    url = f"https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/{upstream['commit']}/LICENSE"
    bounds = dict(minimum='0.1.0', maximum_exclusive='1.0.0')
    spec = ComponentSpec.from_dict(dict(schema_version=1, component_id='acceptance.tesseract-license',
        version='1.0.0', kind='model', display_name='C05 官方固定授權驗收', source_url=url,
        license_id='Apache-2.0', license_path='LICENSE', package_sha256=expected,
        download_bytes=size, unpacked_bytes=size, files=[dict(path='LICENSE', sha256=expected, size=size)],
        capabilities=['license.tesseract'], platforms=['windows','linux'], architectures=['x86_64','arm64'],
        app_versions=bounds, worker_protocols=bounds, dependencies=[],
        resources=dict(ram_mib=1, vram_mib=0, disk_mib=1), health_check='acceptance.license'))
    private = Ed25519PrivateKey.generate()
    policy = TrustPolicy(1, 'acceptance-catalog', 1,
        {'ephemeral-test-key':private.public_key().public_bytes_raw()},
        frozenset(), ('https://raw.githubusercontent.com',))
    payload = dict(schema_version=1, catalog_id=policy.catalog_id, revision=1, trust_policy_version=1,
        issued_at=(now-timedelta(minutes=1)).strftime('%Y-%m-%dT%H:%M:%SZ'),
        expires_at=(now+timedelta(minutes=10)).strftime('%Y-%m-%dT%H:%M:%SZ'), components=[spec.to_dict()])
    envelope = canonical_json(dict(payload=payload, signature=dict(key_id='ephemeral-test-key',
        algorithm='ed25519', value=base64.b64encode(private.sign(canonical_json(payload))).decode())))
    verifier = CatalogVerifier(policy)
    catalog = verifier.load(envelope)
    with tempfile.TemporaryDirectory(prefix='c05-https-') as directory:
        root = Path(directory)
        registry = ComponentRegistry(root/'registry')
        service = DownloadService(root/'network-cache', verifier, registry)
        downloaded = service.download(catalog, *spec.key)
        if downloaded.path.read_bytes() != reference:
            raise RuntimeError('Actual HTTPS payload mismatch')
        if registry.get(*spec.key).state != ComponentState.VERIFIED:
            raise RuntimeError('Download was not registered as verified')
        service.opener = lambda *a,**k: (_ for _ in ()).throw(RuntimeError('Cache reuse attempted network'))
        cached = service.download(catalog, *spec.key)
        offline_source = root/'外部授權包';offline_source.write_bytes(reference)
        offline = DownloadService(root/'offline-cache',verifier).import_offline(catalog,*spec.key,offline_source)
        if offline_source.read_bytes() != reference or offline.path.read_bytes() != reference:
            raise RuntimeError('Offline source changed or import mismatch')
        checks = [dict(name=name, passed=True) for name in (
            'real_ed25519_signature', 'actual_https_pinned_source', 'exact_size_and_sha256',
            'registry_verified_not_ready', 'cache_reuse_without_network', 'offline_import_source_preserved')]
    return dict(recorded_at=now.isoformat(), source_version=version('markitdown-desktop'), check='C05',
        accepted=True, checks=checks, actual_https=True, public_source=url, bytes=size, sha256=expected,
        signature='Ed25519; ephemeral in-memory test key, not a production trust root',
        resume_over_actual_https_verified=False, resume_protocol_scope='Injected response matrix in unit tests',
        installs_or_executes_component=False, production_catalog_published=False,
        windows_executed=False, gpu_executed=False)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--report', type=Path, required=True)
    args=parser.parse_args()
    if args.report.exists():
        parser.error('Report already exists; choose a new evidence path')
    report=collect_report()
    write_report(report,args.report)
    print('C05 actual HTTPS, cache and offline import: 6/6 passed; no installation or engine execution')


if __name__ == '__main__':
    main()

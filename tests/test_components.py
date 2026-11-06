"""C01 驗收：真實暫存檔、SQLite 與可信測試探針；不宣稱有 Windows／GPU 推論。"""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import base64
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from desktop_app.capabilities import CapabilityResolver, HealthResult, HostContext
from desktop_app.components.contracts import (ComponentSpec, ComponentState as S, ContractError,
                                             Dependency, FileSpec, Version, VersionRange)
from desktop_app.components.registry import ComponentRegistry, ConcurrentChange, IntegrityError, RegistryError, canonical_spec
from desktop_app.core import Cancelled

PACKAGE = b'C01 synthetic package; not an executable'
PAYLOADS = {'data/辨識資料.bin': b'C01 synthetic model', 'LICENSE.txt': b'Synthetic test license'}
HOST = HostContext('linux', 'x86_64', Version.parse('0.2.0'), Version.parse('1.0.0'))


def descriptor(component_id='test-engine', version='1.0.0', **changes):
    """僅供測試的本機描述；example.invalid 不會被下載或當成可信遠端目錄。"""
    bounds = {'minimum': '0.1.0', 'maximum_exclusive': '2.0.0'}
    raw = dict(schema_version=1, component_id=component_id, version=version, kind='engine',
               display_name='測試元件', source_url='https://example.invalid/components/fixture',
               license_id='test-only', license_path='LICENSE.txt', package_sha256=hashlib.sha256(PACKAGE).hexdigest(),
               download_bytes=len(PACKAGE), unpacked_bytes=sum(map(len, PAYLOADS.values())),
               files=[{'path': name, 'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in PAYLOADS.items()],
               capabilities=['ocr.text.zh-hant'], platforms=['linux'], architectures=['x86_64'],
               app_versions=bounds.copy(), worker_protocols=bounds.copy(), dependencies=[],
               resources={'ram_mib': 64, 'vram_mib': 0, 'disk_mib': 1}, health_check='fixture.check', required=False, signature=None)
    raw.update(changes)
    return ComponentSpec.from_dict(raw)


def healthy(spec, directory, host):
    return HealthResult((directory / 'data/辨識資料.bin').read_bytes() == PAYLOADS['data/辨識資料.bin'], '真實讀取合成測試資料')


class ComponentContractTests(unittest.TestCase):
    def test_complete_description_round_trip_with_signature_metadata(self):
        spec = descriptor(signature={'key_id': 'test-key', 'algorithm': 'ed25519',
                                     'value': base64.b64encode(b'x' * 64).decode()})
        self.assertEqual(ComponentSpec.from_dict(json.loads(canonical_spec(spec))), spec)

    def test_numeric_version_order_and_exclusive_maximum(self):
        self.assertGreater(Version.parse('1.10.0'), Version.parse('1.9.0'))
        bounds = VersionRange(Version.parse('1.0.0'), Version.parse('2.0.0'))
        self.assertTrue(bounds.contains(Version.parse('1.0.0')))
        self.assertFalse(bounds.contains(Version.parse('2.0.0')))

    def test_invalid_or_ambiguous_versions_rejected(self):
        for value in ('1.2', '01.2.3', '1.2.3-rc1', 'v1.2.3', '1.2.3 ', '1.2.三', '1.' + '9'*100 + '.0', True):
            with self.subTest(value=value), self.assertRaises(ContractError):
                Version.parse(value)

    def test_future_schema_unknown_and_missing_fields_rejected(self):
        for changes in ({'schema_version': 2}, {'schema_version': True}, {'unknown': 1}, {'kind': 'script'}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):
                descriptor(**changes)
        raw = descriptor().to_dict();del raw['health_check']
        with self.assertRaises(ContractError):ComponentSpec.from_dict(raw)

    def test_nested_unknown_and_invalid_array_shapes_rejected(self):
        for changes in ({'resources': {'ram_mib': 1, 'vram_mib': 0, 'disk_mib': 1, 'execute': 'bad'}},
                        {'capabilities': [{}]}, {'files': 'not-an-array'}, {'dependencies': [{'component_id': 'a'}]}):
            with self.subTest(changes=changes), self.assertRaises(ContractError):descriptor(**changes)

    def test_escaping_and_windows_alias_file_names_rejected(self):
        for name in ('../escape', '/absolute', 'C:/drive', 'bad\\name', 'a//b', 'a/./b', 'CON.txt',
                     'aux/data', 'data.', 'data ', 'LPT1', 'COM¹.txt', 'a:b', 'x?y', 'a\x00b'):
            with self.subTest(name=name), self.assertRaises(ContractError):
                FileSpec(name, '0'*64, 0)
        with self.assertRaises(ContractError):descriptor(component_id='con')

    def test_duplicate_case_paths_and_missing_license_rejected(self):
        raw = descriptor().to_dict();raw['files'].append(dict(raw['files'][0], path=raw['files'][0]['path'].upper()))
        with self.assertRaises(ContractError):ComponentSpec.from_dict(raw)
        with self.assertRaises(ContractError):descriptor(license_path='missing.txt')

    def test_resource_bounds_and_unpacked_limit_rejected(self):
        for value in (-1, True, float('nan'), 2**41):
            with self.subTest(value=value), self.assertRaises(ContractError):
                descriptor(resources={'ram_mib': value, 'vram_mib': 0, 'disk_mib': 1})
        with self.assertRaises(ContractError):descriptor(unpacked_bytes=1)
        with self.assertRaises(ContractError):descriptor(download_bytes=False)

    def test_unsafe_source_urls_rejected(self):
        for url in ('http://example.invalid/a', 'https://user:secret@example.invalid/a',
                    'https://example.invalid/a#fragment', 'https://example.invalid /a', 'file:///tmp/a'):
            with self.subTest(url=url), self.assertRaises(ContractError):descriptor(source_url=url)

    def test_dependency_cycles_at_contract_self_level_and_duplicates_rejected(self):
        dep = {'component_id': 'test-engine', 'versions': {'minimum': '1.0.0', 'maximum_exclusive': '2.0.0'}}
        with self.assertRaises(ContractError):descriptor(dependencies=[dep])
        dep['component_id'] = 'runtime'
        with self.assertRaises(ContractError):descriptor(dependencies=[dep, dep])

    def test_signature_format_does_not_accept_other_algorithms_or_invalid_bytes(self):
        for value in ({'key_id': 'key', 'algorithm': 'none', 'value': ''},
                      {'key_id': 'key', 'algorithm': 'ed25519', 'value': '???'},
                      {'key_id': 'key', 'algorithm': 'ed25519', 'value': base64.b64encode(b'short').decode()}):
            with self.subTest(value=value), self.assertRaises(ContractError):descriptor(signature=value)


class ComponentRegistryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / '中文元件';self.registry = ComponentRegistry(self.root)
        self.spec = descriptor()

    def resolver(self, specs=None, host=HOST, probe=healthy, registry=None, checkpoint=lambda: None):
        return CapabilityResolver(registry or self.registry, specs or [self.spec], host,
                                  {} if probe is None else {'fixture.check': probe}, checkpoint)

    def download(self, spec=None):
        spec = spec or self.spec;self.registry.register(spec)
        archive = self.root / 'cache' / (spec.component_id + '-' + str(spec.version) + '.bin')
        archive.parent.mkdir(parents=True, exist_ok=True);archive.write_bytes(PACKAGE)
        self.registry.record_download(spec, archive)
        return archive

    def install(self, spec=None):
        spec = spec or self.spec;self.download(spec);self.registry.verify_download(spec)
        directory = self.registry.installation_path(spec)
        for name, data in PAYLOADS.items():
            target = directory / name;target.parent.mkdir(parents=True, exist_ok=True);target.write_bytes(data)
        self.assertEqual(self.registry.record_installation(spec).state, S.INSTALLED)
        return directory

    def test_download_and_verified_archive_are_never_available(self):
        self.download()
        self.assertEqual(self.registry.get(*self.spec.key).state, S.DOWNLOADED)
        self.assertFalse(self.resolver().resolve('ocr.text.zh-hant').available)
        self.registry.verify_download(self.spec)
        self.assertEqual(self.registry.get(*self.spec.key).state, S.VERIFIED)
        self.assertFalse(self.resolver().resolve('ocr.text.zh-hant').available)

    def test_directory_and_forged_ready_without_installation_are_not_enough(self):
        record = self.registry.register(self.spec)
        self.registry.installation_path(self.spec).mkdir(parents=True)
        self.registry._update(record, S.READY)
        self.assertFalse(self.resolver().resolve('ocr.text.zh-hant').available)

    def test_installation_requires_verified_package(self):
        self.download()
        with self.assertRaises(RegistryError):self.registry.record_installation(self.spec)

    def test_unknown_health_check_does_not_make_installed_files_ready(self):
        self.install()
        observation = self.resolver(probe=None).assess(self.spec)
        self.assertEqual(observation.state, S.UNHEALTHY)
        self.assertEqual(self.registry.get(*self.spec.key).state, S.UNHEALTHY)

    def test_real_files_and_probe_allow_ready_then_reopen_rechecks_health(self):
        self.install();self.assertTrue(self.resolver().resolve('ocr.text.zh-hant').available)
        reopened = ComponentRegistry(self.root)
        self.assertEqual(reopened.get(*self.spec.key).state, S.READY)
        resolution = self.resolver(registry=reopened, probe=lambda *args: HealthResult(False, '目前不健康')).resolve('ocr.text.zh-hant')
        self.assertFalse(resolution.available)
        self.assertEqual(reopened.get(*self.spec.key).state, S.UNHEALTHY)

    def test_same_id_version_cannot_replace_descriptor(self):
        record = self.registry.register(self.spec)
        with self.assertRaises(RegistryError):self.registry.register(replace(self.spec, display_name='另一份描述'))
        self.assertEqual(self.registry.get(*self.spec.key), record)

    def test_changed_payload_revokes_readiness_even_same_file_size(self):
        directory = self.install();self.assertTrue(self.resolver().assess(self.spec).ready)
        path = directory / 'data/辨識資料.bin';path.write_bytes(b'x' * path.stat().st_size)
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_missing_payload_revokes_readiness(self):
        directory = self.install();(directory / 'LICENSE.txt').unlink()
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_extra_payload_revokes_readiness(self):
        directory = self.install();(directory / 'unknown.dll').write_bytes(b'extra')
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_symlink_payload_and_linked_parent_are_rejected(self):
        directory = self.install();path = directory / 'data/辨識資料.bin';path.unlink()
        outside = self.root / 'outside.bin';outside.write_bytes(PAYLOADS['data/辨識資料.bin'])
        try:path.symlink_to(outside)
        except OSError:self.skipTest('此執行器未提供建立 symlink 權限')
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)
        path.unlink();(directory / 'data').rmdir()
        external = self.root / 'external';external.mkdir();(external / '辨識資料.bin').write_bytes(outside.read_bytes())
        (directory / 'data').symlink_to(external, target_is_directory=True)
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_corrupted_download_never_installs(self):
        archive = self.download();archive.write_bytes(b'x' * len(PACKAGE))
        self.assertEqual(self.registry.verify_download(self.spec).state, S.CORRUPT)
        with self.assertRaises(RegistryError):self.registry.record_installation(self.spec)

    def test_partial_download_and_symlink_archive_are_rejected(self):
        archive = self.download();archive.write_bytes(b'partial')
        with self.assertRaises(IntegrityError):self.registry.record_download(self.spec, archive)
        target = self.root / 'linked.bin'
        try:target.symlink_to(archive)
        except OSError:self.skipTest('此執行器未提供建立 symlink 權限')
        with self.assertRaises(IntegrityError):self.registry.record_download(self.spec, target)

    def test_cancelled_package_check_does_not_mark_verified(self):
        self.download()
        with self.assertRaises(Cancelled):
            self.registry.verify_download(self.spec, lambda: (_ for _ in ()).throw(Cancelled()))
        self.assertEqual(self.registry.get(*self.spec.key).state, S.DOWNLOADED)

    def test_platform_architecture_app_and_protocol_mismatches_are_unavailable(self):
        self.install()
        for host in (replace(HOST, platform='windows'), replace(HOST, architecture='arm64'),
                     replace(HOST, app_version=Version.parse('2.0.0')), replace(HOST, worker_protocol=Version.parse('2.0.0'))):
            with self.subTest(host=host):
                self.assertEqual(self.resolver(host=host).assess(self.spec).state, S.INCOMPATIBLE)
        self.assertTrue(self.resolver().assess(self.spec).ready)

    def test_missing_and_unhealthy_dependency_block_parent_then_recover(self):
        runtime = descriptor('test-runtime', capabilities=['runtime.cpu'])
        parent = replace(self.spec, dependencies=(Dependency(runtime.component_id, VersionRange(Version.parse('1.0.0'), Version.parse('2.0.0'))),))
        self.install(parent);resolver = self.resolver([parent, runtime])
        self.assertFalse(resolver.assess(parent).ready)
        directory = self.install(runtime)
        self.assertTrue(resolver.assess(parent).ready)
        (directory / 'LICENSE.txt').unlink()
        self.assertFalse(resolver.assess(parent).ready)

    def test_dependency_wrong_version_is_not_accepted(self):
        runtime = descriptor('test-runtime', '2.0.0')
        parent = replace(self.spec, dependencies=(Dependency(runtime.component_id, VersionRange(Version.parse('1.0.0'), Version.parse('2.0.0'))),))
        self.install(parent);self.install(runtime)
        self.assertFalse(self.resolver([parent, runtime]).assess(parent).ready)

    def test_circular_dependency_is_bounded_and_unavailable(self):
        bounds = VersionRange(Version.parse('1.0.0'), Version.parse('2.0.0'))
        a = replace(descriptor('a-engine'), dependencies=(Dependency('b-engine', bounds),))
        b = replace(descriptor('b-engine'), dependencies=(Dependency('a-engine', bounds),))
        self.install(a);self.install(b)
        result = self.resolver([a, b]).assess(a)
        self.assertFalse(result.ready);self.assertIn('循環', result.reason)

    def test_versions_use_numeric_order_and_compatible_fallback(self):
        older = descriptor(version='1.9.0')
        newer = replace(descriptor(version='1.10.0'), app_versions=VersionRange(Version.parse('1.0.0'), Version.parse('3.0.0')))
        self.install(older);self.install(newer)
        self.assertEqual(self.resolver([older, newer]).resolve('ocr.text.zh-hant').selected.version, older.version)
        host = replace(HOST, app_version=Version.parse('1.0.0'))
        self.assertEqual(self.resolver([older, newer], host=host).resolve('ocr.text.zh-hant').selected.version, newer.version)

    def test_explicit_engine_does_not_fallback_to_other_ready_provider(self):
        basic = descriptor('basic-engine', required=True);optional = descriptor('optional-engine')
        self.install(basic)
        resolver = self.resolver([basic, optional])
        self.assertEqual(resolver.resolve('ocr.text.zh-hant').selected, basic)
        self.assertFalse(resolver.resolve('ocr.text.zh-hant', component_id='optional-engine').available)
        self.assertFalse(resolver.resolve('ocr.unknown').available)

    def test_unapproved_descriptor_cannot_use_registered_ready_state(self):
        self.install();self.assertTrue(self.resolver().assess(self.spec).ready)
        self.assertFalse(self.resolver().assess(replace(self.spec, display_name='未核准')).ready)

    def test_forged_registry_descriptor_does_not_override_approved_catalog(self):
        self.install()
        altered = replace(self.spec, capabilities=('malicious.capability',))
        raw = canonical_spec(altered)
        with sqlite3.connect(self.registry.database) as db:
            db.execute('UPDATE components SET spec_json=?,spec_hash=?,state=?',
                       (raw, hashlib.sha256(raw.encode()).hexdigest(), 'ready'))
        self.assertFalse(self.resolver().assess(self.spec).ready)
        self.assertFalse(self.resolver().resolve('malicious.capability').available)

    def test_health_exception_wrong_result_and_payload_mutation_fail_closed(self):
        directory = self.install()
        def throwing(*args):raise RuntimeError('not healthy')
        for probe in (throwing, lambda *args: True):
            with self.subTest(probe=probe):self.assertEqual(self.resolver(probe=probe).assess(self.spec).state, S.UNHEALTHY)
        def changing(*args):
            (directory / 'LICENSE.txt').write_bytes(b'changed')
            return HealthResult(True)
        self.assertEqual(self.resolver(probe=changing).assess(self.spec).state, S.CORRUPT)

    def test_cancelled_health_probe_is_not_retried_or_marked_ready(self):
        self.install()
        def cancel(*args):raise Cancelled()
        with self.assertRaises(Cancelled):self.resolver(probe=cancel).assess(self.spec)
        self.assertEqual(self.registry.get(*self.spec.key).state, S.INSTALLED)

    def test_stale_health_result_cannot_overwrite_a_newer_registry_update(self):
        self.install();other = ComponentRegistry(self.root)
        def racing(*args):
            other._update(other.get(*self.spec.key), S.UNHEALTHY, '較新的狀態')
            return HealthResult(True)
        self.assertFalse(self.resolver(probe=racing).assess(self.spec).ready)
        self.assertEqual(self.registry.get(*self.spec.key).reason, '較新的狀態')

    def test_optimistic_generation_rejects_stale_updates(self):
        old = self.registry.register(self.spec)
        self.registry._update(old, S.UNHEALTHY)
        with self.assertRaises(ConcurrentChange):self.registry._update(old, S.READY)

    def test_concurrent_registration_preserves_all_versions(self):
        specs = [descriptor(version=f'1.0.{index}') for index in range(12)]
        with ThreadPoolExecutor(max_workers=4) as pool:
            list(pool.map(lambda item: ComponentRegistry(self.root).register(item), specs))
        self.assertTrue(all(self.registry.get(*item.key) is not None for item in specs))

    def test_future_and_corrupt_registry_do_not_reset_existing_data(self):
        self.registry.register(self.spec)
        with sqlite3.connect(self.registry.database) as db:db.execute('PRAGMA user_version=99')
        before = self.registry.database.read_bytes()
        with self.assertRaises(RegistryError):ComponentRegistry(self.root)
        self.assertEqual(self.registry.database.read_bytes(), before)
        self.registry.database.write_bytes(b'not a sqlite database')
        with self.assertRaises(RegistryError):ComponentRegistry(self.root)
        self.assertEqual(self.registry.database.read_bytes(), b'not a sqlite database')

    def test_invalid_record_state_or_spec_digest_is_not_silently_used(self):
        self.registry.register(self.spec)
        with sqlite3.connect(self.registry.database) as db:db.execute("UPDATE components SET state='unknown'")
        with self.assertRaises(RegistryError):self.registry.get(*self.spec.key)
        with sqlite3.connect(self.registry.database) as db:db.execute("UPDATE components SET state='ready',spec_hash='bad'")
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_registry_blob_cannot_escape_controlled_corruption_result(self):
        self.registry.register(self.spec)
        with sqlite3.connect(self.registry.database) as db:
            db.execute('UPDATE components SET spec_json=?', (sqlite3.Binary(b'not text'),))
        self.assertEqual(self.resolver().assess(self.spec).state, S.CORRUPT)

    def test_unrecognized_sqlite_schema_is_rejected_without_reinitializing(self):
        path = self.root / 'other';path.mkdir()
        database = path / 'component-registry.sqlite3'
        with sqlite3.connect(database) as db:
            db.execute('CREATE TABLE components (spec_json TEXT)');db.execute('PRAGMA user_version=1')
        before = database.read_bytes()
        with self.assertRaises(RegistryError):ComponentRegistry(path)
        self.assertEqual(database.read_bytes(), before)

    def test_linked_registry_root_is_not_taken_over(self):
        target = self.root / 'external-root';target.mkdir()
        link = self.root / 'linked-root'
        try:link.symlink_to(target, target_is_directory=True)
        except OSError:self.skipTest('此執行器未提供建立 symlink 權限')
        with self.assertRaises(IntegrityError):ComponentRegistry(link)
        self.assertFalse((target / 'component-registry.sqlite3').exists())

    def test_invalid_capability_request_or_catalog_rejected(self):
        with self.assertRaises(ContractError):self.resolver().resolve('ocr.text.zh-hant', versions='anything')
        with self.assertRaises(RegistryError):self.resolver([self.spec, self.spec])

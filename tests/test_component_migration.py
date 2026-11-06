"""C02：真實設定備份／SQLite 遷移／所有權隔離，以及原 OCR 路徑規則。"""
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import sqlite3
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from desktop_app.components.legacy_models import LegacyModelsAdapter, OWNER_FILE
from desktop_app.components.registry import ComponentRegistry, RegistryError
from desktop_app.core import Cancelled, Quality, State
from desktop_app.settings import ComponentPreference, Settings, load_settings, save_settings


class MigrationDirectoryTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / '中文開發資料'
        self.root.mkdir()


class SettingsMigrationTests(MigrationDirectoryTests):
    def test_v1_through_v5_preserve_all_values_and_only_save_backs_up(self):
        values = dict(ram_budget_mib=896, reserve_mib=768, resource_wait_seconds=7.5,
                      ocr_executable='C:/自備引擎/tesseract.exe', ocr_data_dir='C:/外部模型',
                      device='cpu', cpu_threads=3, ocr_backend='onnx_verify', vram_budget_mib=512)
        for version in range(1, 6):
            with self.subTest(version=version):
                path = self.root / f'設定-v{version}.json'
                raw = (json.dumps(dict(schema_version=version, **values), ensure_ascii=False, indent=3) + '\n').encode()
                path.write_bytes(raw)
                loaded = load_settings(path)
                self.assertEqual(loaded.schema_version, 6)
                for key, value in values.items():self.assertEqual(getattr(loaded, key), value)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(list(self.root.glob(path.name + '*.bak')), [])
                save_settings(loaded, path)
                backups = list(self.root.glob(path.name + '*.bak'))
                self.assertEqual(len(backups), 1)
                self.assertEqual(backups[0].read_bytes(), raw)
                self.assertEqual(load_settings(path), loaded)
                save_settings(loaded, path)
                self.assertEqual(list(self.root.glob(path.name + '*.bak')), backups)

    def test_new_component_fields_and_quality_round_trip(self):
        saved = Settings(quality='fast', onboarding_version=2, update_channel='preview',
                         allow_optional_downloads=True,
                         component_preferences=(ComponentPreference('ocr.text.zh-hant', 'test-engine', '1.2.0'),))
        path = self.root / '設定.json'
        save_settings(saved, path)
        self.assertEqual(load_settings(path), saved)
        self.assertNotIn('ready', path.read_text())
        self.assertEqual(list(self.root.glob('*.bak')), [])

    def test_invalid_future_or_duplicate_fields_cannot_be_saved_over(self):
        for raw in (b'{"schema_version":99}', b'broken', b'{"schema_version":5,"unknown":1}',
                    b'{"schema_version":99,"schema_version":5}',
                    b'{"schema_version":6,"component_preferences":[{"capability":"ocr.text","component_id":"a","ready":true}]}'):
            with self.subTest(raw=raw):
                path = self.root / 'bad.json';path.write_bytes(raw)
                with self.assertRaises(ValueError):save_settings(Settings(), path)
                self.assertEqual(path.read_bytes(), raw)
                self.assertEqual(list(self.root.glob('*.bak')), [])

    def test_failed_upgrade_replace_preserves_old_and_backup(self):
        path = self.root / '設定.json';raw = b'{"schema_version":5,"cpu_threads":2}';path.write_bytes(raw)
        with patch('desktop_app.settings.os.replace', side_effect=OSError('disk failure')):
            with self.assertRaises(OSError):save_settings(load_settings(path), path)
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(next(self.root.glob('*.bak')).read_bytes(), raw)
        self.assertEqual(list(self.root.glob('.settings-*')), [])

    def test_backup_failure_preserves_old_and_leaves_no_temporary(self):
        path = self.root / '設定.json';raw = b'{"schema_version":3}';path.write_bytes(raw)
        with patch('desktop_app.settings.os.link', side_effect=OSError('no space')):
            with self.assertRaises(OSError):save_settings(load_settings(path), path)
        self.assertEqual(path.read_bytes(), raw)
        self.assertEqual(list(self.root.glob('.settings-*')), [])

    def test_backup_collision_is_preserved_and_not_trusted(self):
        path = self.root / '設定.json';raw = b'{"schema_version":5}';path.write_bytes(raw)
        backup = path.with_name(path.name + '.pre-v5-' + hashlib.sha256(raw).hexdigest()[:16] + '.bak')
        backup.write_bytes(b'user data')
        with self.assertRaises(ValueError):save_settings(load_settings(path), path)
        self.assertEqual(path.read_bytes(), raw);self.assertEqual(backup.read_bytes(), b'user data')

    def test_existing_matching_backup_can_be_reused(self):
        path = self.root / '設定.json';raw = b'{"schema_version":5}';path.write_bytes(raw)
        save_settings(load_settings(path), path)
        backup = next(self.root.glob('*.bak'))
        path.write_bytes(raw)
        save_settings(load_settings(path), path)
        self.assertEqual(backup.read_bytes(), raw)
        self.assertEqual(len(list(self.root.glob('*.bak'))), 1)

    def test_new_options_and_duplicate_preferences_rejected(self):
        preference = ComponentPreference('ocr.text', 'test-engine')
        for fields in ({'onboarding_version':True}, {'onboarding_version':-1}, {'allow_optional_downloads':1},
                       {'quality':'unknown'}, {'update_channel':'unknown'}, {'component_preferences':[preference]},
                       {'component_preferences':(preference, preference)}):
            with self.subTest(fields=fields), self.assertRaises(ValueError):Settings(**fields)
        for fields in ({'capability':'../bad','component_id':'a'},
                       {'capability':'ocr.text','component_id':'a','version':'1.0.0-rc1'}):
            with self.assertRaises(ValueError):ComponentPreference(**fields)

    def test_external_path_text_is_not_normalized_or_taken_over(self):
        path = self.root / 'settings.json'
        saved = Settings(ocr_executable=' C:/自備 引擎/tesseract.exe ', ocr_data_dir='relative/中文模型')
        save_settings(saved, path)
        self.assertEqual(load_settings(path), saved)
        self.assertEqual(set(self.root.iterdir()), {path})

    def test_oversize_save_is_rejected_without_changing_old_file(self):
        path = self.root / '設定.json';save_settings(Settings(), path);old = path.read_bytes()
        with self.assertRaises(ValueError):save_settings(Settings(ocr_data_dir='a'*65536), path)
        self.assertEqual(path.read_bytes(), old)

    def test_save_does_not_overwrite_concurrent_future_schema(self):
        path = self.root / 'settings.json';save_settings(Settings(), path)
        original_fsync = os.fsync
        future = b'{"schema_version":99}'
        def concurrent_update(descriptor):
            original_fsync(descriptor)
            path.write_bytes(future)
        with patch('desktop_app.settings.os.fsync', side_effect=concurrent_update):
            with self.assertRaises(ValueError):save_settings(Settings(reserve_mib=1), path)
        self.assertEqual(path.read_bytes(), future)
        self.assertEqual(list(self.root.glob('.settings-*')), [])


class LegacyAdapterTests(MigrationDirectoryTests):
    def setUp(self):
        super().setUp()
        self.payload = b'verified synthetic model'
        self.license = b'synthetic license'
        self.files = {'eng.traineddata':self.payload, 'chi_tra.traineddata':self.payload, 'LICENSE':self.license}
        self.spec = dict(source='test', commit='test', license='test',
                         files={name:hashlib.sha256(data).hexdigest() for name,data in self.files.items()})
        mocked = patch('desktop_app.models.manifest', return_value=self.spec)
        mocked.start();self.addCleanup(mocked.stop)
        self.registry = ComponentRegistry(self.root / '登錄')
        self.directory = self.root / '模型'

    def opener(self, url, timeout):
        return io.BytesIO(self.files[url.rsplit('/',1)[-1]])

    def seed(self):
        self.directory.mkdir()
        for name,data in self.files.items():(self.directory / name).write_bytes(data)
        (self.directory / '自備筆記.txt').write_text('保留')

    def test_external_verified_models_are_referenced_without_ownership_or_copy(self):
        self.seed();before={p.name:p.read_bytes() for p in self.directory.iterdir()}
        adapter=LegacyModelsAdapter(self.directory,self.registry)
        result=adapter.observe()
        self.assertTrue(result.models_available);self.assertFalse(result.engine_ready);self.assertFalse(result.owned)
        record=self.registry.get_model_reference(result.reference_id)
        self.assertEqual(record.origin,'external');self.assertEqual(record.directory,str(self.directory))
        for action in (adapter.install,adapter.remove):
            with self.assertRaises(PermissionError):action()
        self.assertEqual({p.name:p.read_bytes() for p in self.directory.iterdir()},before)
        self.assertFalse(self.registry.payloads.exists())

    def test_preexisting_default_location_is_not_implicitly_owned(self):
        self.seed();adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True)
        self.assertTrue(adapter.observe().models_available);self.assertFalse(adapter.can_install())
        with self.assertRaises(PermissionError):adapter.install(opener=self.opener)
        self.assertFalse((self.directory / OWNER_FILE).exists())

    def test_empty_managed_download_reuse_and_remove_preserve_unknown(self):
        adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True)
        self.assertTrue(adapter.install(opener=self.opener).models_available)
        self.assertTrue(adapter.owns_directory())
        adapter.install(opener=lambda *a,**k:self.fail('cached models must not download'))
        unknown=self.directory / '自備筆記.txt';unknown.write_text('保留')
        result=adapter.remove()
        self.assertFalse(result.models_available);self.assertTrue(unknown.exists())
        self.assertTrue((self.directory / OWNER_FILE).exists())

    def test_cancelled_managed_download_can_resume_without_partial_files(self):
        adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True);cancel=Event();cancel.set()
        with self.assertRaises(Cancelled):adapter.install(cancel,opener=self.opener)
        self.assertTrue(adapter.owns_directory());self.assertEqual(len(list(self.directory.iterdir())),1)
        self.assertTrue(adapter.install(opener=self.opener).models_available)

    def test_bad_download_is_not_adopted_or_marked_valid(self):
        adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True)
        with self.assertRaises(ValueError):adapter.install(opener=lambda *a,**k:io.BytesIO(b'bad'))
        self.assertFalse(adapter.observe().models_available)
        self.assertEqual(list(self.directory.glob('.model-*')),[])

    def test_tampered_owned_payload_is_never_overwritten_or_removed(self):
        adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True);adapter.install(opener=self.opener)
        target=self.directory / 'eng.traineddata';target.write_bytes(b'modified')
        self.assertFalse(adapter.observe().models_available)
        with self.assertRaises(ValueError):adapter.install(opener=self.opener)
        with self.assertRaises(ValueError):adapter.remove()
        self.assertEqual(target.read_bytes(),b'modified')

    def test_receipt_is_bound_to_path_and_manifest_not_directory_name(self):
        adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True);adapter.install(opener=self.opener)
        other=self.root / 'copy';shutil.copytree(self.directory,other)
        copied=LegacyModelsAdapter(other,self.registry,managed=True)
        self.assertFalse(copied.owns_directory())
        with self.assertRaises(PermissionError):copied.remove()
        receipt=self.directory / OWNER_FILE;receipt.write_text('{}')
        self.assertFalse(adapter.owns_directory())
        with self.assertRaises(PermissionError):adapter.remove()

    def test_forged_registry_origin_does_not_grant_ownership(self):
        self.seed();adapter=LegacyModelsAdapter(self.directory,self.registry,managed=True)
        result=adapter.observe()
        with sqlite3.connect(self.registry.database) as db:
            db.execute("UPDATE model_references SET origin='managed' WHERE reference_id=?",(result.reference_id,))
        self.assertFalse(adapter.owns_directory())
        with self.assertRaises(PermissionError):adapter.remove()

    def test_modified_external_reference_revokes_data_availability_after_reopen(self):
        self.seed();adapter=LegacyModelsAdapter(self.directory,self.registry);adapter.observe()
        (self.directory / 'eng.traineddata').unlink()
        reopened=LegacyModelsAdapter(self.directory,ComponentRegistry(self.registry.directory)).observe()
        self.assertFalse(reopened.models_available)
        self.assertEqual(dict(reopened.states)['eng.traineddata'],'missing')

    def test_missing_external_directory_is_not_created(self):
        result=LegacyModelsAdapter(self.directory,self.registry).observe()
        self.assertFalse(result.models_available);self.assertFalse(self.directory.exists())

    def test_linked_external_directory_is_not_followed_or_modified(self):
        self.seed();link=self.root / '連結'
        try:link.symlink_to(self.directory,target_is_directory=True)
        except OSError as exc:self.skipTest(str(exc))
        adapter=LegacyModelsAdapter(link,self.registry,managed=True)
        self.assertFalse(adapter.observe().models_available);self.assertFalse(adapter.can_install())
        with self.assertRaises(PermissionError):adapter.install(opener=self.opener)
        self.assertEqual((self.directory / 'eng.traineddata').read_bytes(),self.payload)

    def test_registry_v1_migration_preserves_original_component_rows(self):
        from test_components import descriptor
        spec=descriptor();self.registry.register(spec)
        with sqlite3.connect(self.registry.database) as db:
            before=db.execute('SELECT * FROM components').fetchall()
            db.execute('DROP TABLE model_references');db.execute('PRAGMA user_version=1')
        reopened=ComponentRegistry(self.registry.directory)
        self.assertEqual(reopened.get(*spec.key).spec,spec)
        with sqlite3.connect(reopened.database) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],2)
            self.assertEqual(db.execute('SELECT * FROM components').fetchall(),before)
        backup = next(self.registry.directory.glob('component-registry.pre-v1-*.sqlite3'))
        with sqlite3.connect(backup) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT * FROM components').fetchall(),before)

    def test_failed_registry_upgrade_rolls_back_original_rows_and_schema(self):
        from test_components import descriptor
        self.registry.register(descriptor())
        with sqlite3.connect(self.registry.database) as db:
            before=db.execute('SELECT * FROM components').fetchall()
            db.execute('DROP TABLE model_references');db.execute('PRAGMA user_version=1')
        original_connect=sqlite3.connect
        class FaultyConnection(sqlite3.Connection):
            def execute(self, sql, *args, **kwargs):
                if sql.startswith('CREATE TABLE model_references'):
                    raise sqlite3.OperationalError('simulated disk failure')
                return super().execute(sql,*args,**kwargs)
        def connect(*args,**kwargs):
            return original_connect(*args,**{**kwargs,'factory':FaultyConnection})
        with patch('desktop_app.components.registry.sqlite3.connect',side_effect=connect):
            with self.assertRaises(RegistryError):ComponentRegistry(self.registry.directory)
        with original_connect(self.registry.database) as db:
            self.assertEqual(db.execute('PRAGMA user_version').fetchone()[0],1)
            self.assertEqual(db.execute('SELECT * FROM components').fetchall(),before)
            self.assertEqual(db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall(),[('components',)])

    def test_corrupt_reference_is_rejected_without_resetting_registry(self):
        result=LegacyModelsAdapter(self.directory,self.registry).observe()
        with sqlite3.connect(self.registry.database) as db:db.execute("UPDATE model_references SET states_json='broken'")
        with self.assertRaises(RegistryError):self.registry.get_model_reference(result.reference_id)
        with sqlite3.connect(self.registry.database) as db:
            self.assertEqual(db.execute('SELECT states_json FROM model_references').fetchone()[0],'broken')


class OCRPathRegressionTests(MigrationDirectoryTests):
    def test_cli_preserves_saved_quality_paths_and_explicit_overrides(self):
        from desktop_app.cli import main
        path = self.root / 'settings.json'
        saved = Settings(quality='fast', ocr_executable='自備引擎', ocr_data_dir='自備模型',
                         ocr_backend='onnx_verify', cpu_threads=3)
        save_settings(saved, path)
        for options, quality in (([], Quality.FAST), (['--quality', 'precise'], Quality.PRECISE)):
            with patch('sys.argv', ['cli', 'input.txt', 'output.md', '--settings', str(path), *options]), \
                 patch('desktop_app.cli.Runner') as runner, patch('sys.stdout', new_callable=io.StringIO):
                runner.return_value.run.return_value = SimpleNamespace(state=State.COMPLETED, message='test')
                self.assertEqual(main(), 0)
                request = runner.return_value.run.call_args.args[0]
                self.assertEqual(request.quality, quality)
                self.assertEqual(request.ocr_executable, saved.ocr_executable)
                self.assertEqual(request.ocr_data_dir, saved.ocr_data_dir)
                self.assertEqual(request.ocr_backend, saved.ocr_backend)
                self.assertEqual(request.cpu_threads, 3)

    def test_explicit_missing_engine_does_not_fallback_to_path(self):
        from desktop_app.pdf_pipeline import _run_ocr
        with patch('desktop_app.pdf_pipeline.shutil.which',side_effect=AssertionError('must not fallback')):
            with self.assertRaises(FileNotFoundError):
                _run_ocr(None,lambda:None,lambda text:None,150,str(self.root / 'missing-tesseract'))

    @unittest.skipUnless(shutil.which('tesseract'),'Native OCR prerequisite required')
    def test_explicit_missing_data_directory_does_not_use_environment_models(self):
        from desktop_app.pdf_pipeline import _run_ocr
        with self.assertRaises((RuntimeError, OSError, __import__('subprocess').CalledProcessError)):
            _run_ocr(None,lambda:None,lambda text:None,150,shutil.which('tesseract'),str(self.root / 'missing-data'))

    @unittest.skipUnless(os.environ.get('TESSDATA_PREFIX'),'Verified pinned model directory required')
    def test_real_pinned_models_are_read_only_references_not_engine_readiness(self):
        directory=Path(os.environ['TESSDATA_PREFIX'])
        registry=ComponentRegistry(self.root / '登錄')
        result=LegacyModelsAdapter(directory,registry).observe()
        self.assertTrue(result.models_available);self.assertFalse(result.owned);self.assertFalse(result.engine_ready)
        self.assertEqual(len(result.states),3)

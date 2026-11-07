"""C08 使用真實簽章／ZIP／SQLite／Qt，合成健康資料不作 OCR 品質證據。"""
from dataclasses import replace
from datetime import timedelta
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from threading import Event
import time
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.capabilities import HealthResult
from desktop_app.components.catalog import TrustPolicy
from desktop_app.components.locks import file_lock
from desktop_app.components.management import ComponentManagement, TrustedSource
from test_component_downloads import NOW, Response, sign
from test_component_lifecycle import HOST, MODEL, bundle, health

os.environ.setdefault('QT_QPA_PLATFORM','offscreen')


class ManagementFixture:
    def prepare(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name); self.directory=self.root/'中文設定'
        self.spec,self.archive=bundle(self.root/'external')
        self.new,self.new_archive=bundle(self.root/'external',version='2.0.0')
        self.key=Ed25519PrivateKey.generate()
        self.policy=TrustPolicy(1,'test-catalog',1,{'test-key':self.key.public_key().public_bytes_raw()},frozenset(),('https://example.invalid',))
        self.source=TrustedSource(self.policy,'https://example.invalid/catalog')
        self.service=self.service_for()
        self.catalog=self.root/'catalog.json'; self.catalog.write_bytes(sign(self.key,[self.spec,self.new]))

    def service_for(self, **options):
        service=ComponentManagement(self.directory,source=self.source,host=HOST,
                                    health_checks={'fixture.health':health},**options)
        service.verifier.clock=lambda:NOW
        return service

    def load_catalog(self):
        result=self.service.run('catalog_file',path=self.catalog)
        self.assertEqual(result.state,'completed',result.message)
        return result

    def install(self, spec=None, archive=None):
        result=self.service.run('offline',(spec or self.spec).key,archive or self.archive)
        self.assertEqual(result.state,'completed',result.message)
        return result


class ManagementTests(ManagementFixture, unittest.TestCase):
    def setUp(self): self.prepare()

    def test_default_unconfigured_source_does_not_connect_or_change_settings(self):
        settings=self.root/'settings.json'; settings.write_bytes(b'original preferences')
        service=ComponentManagement(self.root/'unconfigured',host=HOST)
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('must not connect')):
            result=service.run('refresh')
            self.assertEqual(result.rows,()); self.assertIn('尚未提供',result.message)
            self.assertEqual(service.run('catalog_file',path=self.catalog).state,'failed')
        self.assertEqual(settings.read_bytes(),b'original preferences')

    def test_signed_catalog_saved_and_reloaded_without_health_or_network(self):
        result=self.load_catalog(); self.assertEqual(len(result.rows),2)
        self.assertTrue(all(row.approved and not row.owned for row in result.rows))
        again=self.service_for()
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('must not connect')):
            result=again.run('refresh')
        self.assertEqual(len(result.rows),2); self.assertFalse(any(row.active for row in result.rows))

    def test_invalid_signatures_and_oversize_or_linked_catalog_preserve_old(self):
        self.load_catalog(); original=self.service.catalog_path.read_bytes()
        for raw in (b'bad json',sign(Ed25519PrivateKey.generate(),[self.spec]),b' '*1048577):
            bad=self.root/'bad.json'; bad.write_bytes(raw)
            result=self.service.run('catalog_file',path=bad)
            self.assertEqual(result.state,'failed'); self.assertEqual(self.service.catalog_path.read_bytes(),original)
        link=self.root/'linked.json'; link.symlink_to(self.catalog)
        self.assertEqual(self.service.run('catalog_file',path=link).state,'failed')
        self.assertEqual(self.service.catalog_path.read_bytes(),original)
        if hasattr(os,'mkfifo'):
            fifo=self.root/'pipe.json'; os.mkfifo(fifo)
            self.assertEqual(self.service.run('catalog_file',path=fifo).state,'failed')

    def test_seen_revision_downgrade_is_rejected(self):
        self.catalog.write_bytes(sign(self.key,[self.spec],revision=2)); self.load_catalog()
        self.catalog.write_bytes(sign(self.key,[self.spec],revision=1))
        result=self.service.run('catalog_file',path=self.catalog)
        self.assertEqual(result.state,'failed'); self.assertIn('版本',result.message)

    def test_online_catalog_is_only_fetched_by_explicit_action(self):
        calls=[]
        def opener(request,timeout):
            calls.append((request.full_url,timeout)); return Response(self.catalog.read_bytes(),url=request.full_url)
        service=self.service_for(opener=opener)
        service.run('refresh'); self.assertEqual(calls,[])
        result=service.run('catalog_online')
        self.assertEqual(result.state,'completed',result.message); self.assertEqual(len(result.rows),2)
        self.assertEqual(calls,[('https://example.invalid/catalog',10)])

    def test_offline_transaction_and_license_plain_original(self):
        self.load_catalog(); result=self.install()
        row=next(row for row in result.rows if row.spec==self.spec)
        self.assertTrue(row.owned and row.active); self.assertEqual(row.state,'unchecked')
        result=self.service.run('license',self.spec.key)
        self.assertEqual(result.state,'completed'); self.assertEqual(result.document,'C06 synthetic test fixture license')

    def test_explicit_download_install_reports_progress_and_uses_cache(self):
        self.load_catalog(); calls=[]; progress=[]
        def opener(request,timeout):
            calls.append(request.full_url); return Response(self.archive.read_bytes(),url=request.full_url)
        self.service.opener=opener
        result=self.service.run('install',self.spec.key,progress=lambda current,total:progress.append((current,total)))
        self.assertEqual(result.state,'completed',result.message); self.assertTrue(progress)
        self.assertEqual(progress[-1],(self.spec.download_bytes,self.spec.download_bytes))
        self.assertEqual(self.service.run('install',self.spec.key).state,'completed'); self.assertEqual(len(calls),1)

    def test_repair_modified_payload_and_recheck_health(self):
        self.load_catalog(); self.install()
        payload=self.directory/'component-state/components'/self.spec.component_id/str(self.spec.version)/MODEL
        payload.write_bytes(b'changed')
        self.assertEqual(self.service.run('health',self.spec.key).state,'failed')
        result=self.service.run('repair',self.spec.key)
        self.assertEqual(result.state,'completed',result.message); self.assertEqual(json.loads(payload.read_bytes())['factor'],2)

    def test_health_of_inactive_version_does_not_switch_active_and_rollback_works(self):
        self.load_catalog(); self.install(); self.install(self.new,self.new_archive)
        result=self.service.run('health',self.spec.key)
        self.assertEqual(result.state,'completed',result.message)
        self.assertEqual([row.spec.key for row in result.rows if row.active],[self.new.key])
        result=self.service.run('rollback',self.new.key)
        self.assertEqual(result.state,'completed',result.message)
        self.assertEqual([row.spec.key for row in result.rows if row.active],[self.spec.key])
        result=self.service.run('activate',self.new.key)
        self.assertEqual([row.spec.key for row in result.rows if row.active],[self.new.key])

    def test_health_failure_leaves_current_active_unchanged(self):
        self.load_catalog(); self.install()
        self.service.health_checks['fixture.health']=lambda *args:HealthResult(False,'fixture unhealthy')
        result=self.service.run('offline',self.new.key,self.new_archive)
        self.assertEqual(result.state,'failed'); self.assertEqual([row.spec.key for row in result.rows if row.active],[self.spec.key])

    def test_withdrawn_catalog_disables_execution_but_owned_removal_allowed(self):
        self.load_catalog(); self.install()
        self.catalog.write_bytes(sign(self.key,[self.new],revision=2)); self.load_catalog()
        result=self.service.run('refresh'); row=next(row for row in result.rows if row.spec==self.spec)
        self.assertTrue(row.owned); self.assertFalse(row.approved)
        self.assertEqual(self.service.run('health',self.spec.key).state,'failed')
        self.assertEqual(self.service.run('remove',self.spec.key).state,'completed')
        self.assertFalse(any(row.owned for row in self.service.run('refresh').rows))

    def test_expired_catalog_retains_owned_rows_and_allows_safe_removal(self):
        self.load_catalog(); self.install(); self.service.verifier.clock=lambda:NOW+timedelta(days=2)
        result=self.service.run('refresh'); self.assertTrue(result.rows[0].owned)
        self.assertFalse(result.rows[0].approved)
        self.assertEqual(self.service.run('health',self.spec.key).state,'failed')
        self.assertEqual(self.service.run('remove',self.spec.key).state,'completed')

    def test_required_removal_and_unknown_operations_are_rejected(self):
        required,archive=bundle(self.root/'required',component_id='required-model',required=True)
        self.catalog.write_bytes(sign(self.key,[required])); self.load_catalog(); self.install(required,archive)
        self.assertEqual(self.service.run('remove',required.key).state,'failed')
        self.assertEqual(self.service.run('arbitrary-command',required.key).state,'failed')

    def test_pre_cancel_and_shared_worker_guard_preserve_active(self):
        self.load_catalog(); cancel=Event(); cancel.set()
        self.assertEqual(self.service.run('offline',self.spec.key,self.archive,cancel=cancel).state,'cancelled')
        self.install()
        with file_lock(self.directory/'component-state/.locks/worker-use.lock',exclusive=False):
            result=self.service.run('remove',self.spec.key)
        self.assertEqual(result.state,'failed'); self.assertTrue(any(row.active for row in result.rows))

    def test_other_window_lock_is_not_stolen(self):
        with file_lock(self.directory/'component-state/.locks/management.lock',exclusive=True):
            result=self.service.run('refresh')
        self.assertEqual(result.state,'failed'); self.assertIn('ComponentBusy',result.message)

    def test_license_tampering_is_not_displayed(self):
        self.load_catalog(); self.install()
        path=self.directory/'component-state/components'/self.spec.component_id/str(self.spec.version)/self.spec.license_path
        path.write_bytes(b'<script>modified</script>')
        result=self.service.run('license',self.spec.key)
        self.assertEqual(result.state,'failed'); self.assertIsNone(result.document)

    def test_unsupported_platform_or_health_binding_rejected_before_download(self):
        for changes in ({'platforms':('windows',)},{'health_check':'untrusted.script'}):
            spec=replace(self.spec,**changes); self.catalog.write_bytes(sign(self.key,[spec],revision=self.service.verifier._highest_revision+1)); self.load_catalog()
            with patch('desktop_app.components.management.DownloadService',side_effect=AssertionError('must not download')):
                result=self.service.run('install',spec.key)
            self.assertEqual(result.state,'failed'); self.assertNotIn('AssertionError',result.message)


@unittest.skipUnless(importlib.util.find_spec('PySide6'),'Install desktop dependencies')
class ManagementDialogTests(ManagementFixture, unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        self.prepare(); self.dialogs=[]
        self.addCleanup(self.close_dialogs)

    def close_dialogs(self):
        for dialog in self.dialogs:
            if dialog.busy(): dialog.cancel(); dialog.job.wait(15000)
            self.app.processEvents(); dialog.close()

    def wait(self, dialog):
        deadline=time.monotonic()+20
        while dialog.busy() and time.monotonic()<deadline:
            self.app.processEvents(); time.sleep(0.005)
        if dialog.busy(): dialog.cancel(); dialog.job.wait(15000); self.fail('Component UI exceeded bounded wait')
        self.app.processEvents()
        self.assertIsNotNone(dialog.last_result)
        return dialog.last_result

    def open_dialog(self,service=None):
        from desktop_app.component_dialog import ComponentDialog
        dialog=ComponentDialog(service or self.service); self.dialogs.append(dialog); self.wait(dialog)
        return dialog

    def select(self,dialog,key):
        from PySide6.QtCore import Qt
        for index in range(dialog.table.topLevelItemCount()):
            item=dialog.table.topLevelItem(index)
            if item.data(0,Qt.ItemDataRole.UserRole)==key: dialog.table.setCurrentItem(item); return
        self.fail('Expected component row missing')

    def test_unconfigured_dialog_no_network_and_actions_disabled(self):
        service=ComponentManagement(self.directory,host=HOST)
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('must not connect')):
            dialog=self.open_dialog(service)
        self.assertIn('尚未提供',dialog.status.text()); self.assertFalse(dialog.catalog_button.isEnabled())
        self.assertFalse(dialog.online_button.isEnabled()); self.assertFalse(dialog.buttons['install'].isEnabled())
        self.assertTrue(dialog.refresh_button.isEnabled())

    def test_capacity_license_version_plain_metadata_and_owned_controls(self):
        display='<img src="https://example.invalid/image">'
        self.spec=replace(self.spec,display_name=display)
        self.catalog.write_bytes(sign(self.key,[self.spec,self.new]))
        self.load_catalog(); dialog=self.open_dialog(); self.select(dialog,self.spec.key)
        self.assertIn('test-engine',dialog.details.toPlainText()); self.assertIn('RAM',dialog.details.toPlainText())
        self.assertIn('test-only',dialog.details.toPlainText()); self.assertIn('來源',dialog.details.toPlainText())
        self.assertIn(display,dialog.details.toPlainText())
        self.assertTrue(dialog.buttons['offline'].isEnabled()); self.assertFalse(dialog.buttons['remove'].isEnabled())

    def test_gui_offline_import_health_license_and_confirmed_remove(self):
        from PySide6.QtWidgets import QMessageBox
        self.load_catalog(); dialog=self.open_dialog(); self.select(dialog,self.spec.key)
        with patch('desktop_app.component_dialog.QFileDialog.getOpenFileName',return_value=(str(self.archive),'')):
            dialog.buttons['offline'].click()
        self.assertEqual(self.wait(dialog).state,'completed'); self.assertTrue(dialog.buttons['remove'].isEnabled())
        dialog.buttons['health'].click(); self.assertEqual(self.wait(dialog).state,'completed')
        dialog.buttons['license'].click(); self.wait(dialog)
        self.assertIn('synthetic test fixture license',dialog.details.toPlainText())
        with patch('desktop_app.component_dialog.QMessageBox.question',return_value=QMessageBox.StandardButton.No) as question:
            dialog.buttons['remove'].click()
        self.assertIn(self.spec.component_id,question.call_args.args[2])
        self.assertTrue(dialog.selected().owned)
        with patch('desktop_app.component_dialog.QMessageBox.question',return_value=QMessageBox.StandardButton.Yes): dialog.buttons['remove'].click()
        self.assertEqual(self.wait(dialog).state,'completed'); self.assertFalse(dialog.selected().owned)

    def test_cancel_escape_and_close_wait_for_background_cleanup(self):
        self.load_catalog(); dialog=self.open_dialog(); self.select(dialog,self.spec.key)
        entered=Event()
        def waiting(spec,directory,host):
            entered.set()
            while not dialog.job.cancel.wait(0.01): pass
            return HealthResult(True,'cancel fixture released')
        self.service.health_checks['fixture.health']=waiting
        dialog.start('offline',self.spec.key,self.archive)
        deadline=time.monotonic()+5
        while not entered.is_set() and time.monotonic()<deadline: self.app.processEvents(); time.sleep(0.005)
        self.assertTrue(entered.is_set()); self.assertFalse(dialog.buttons['install'].isEnabled())
        dialog.reject(); self.assertTrue(dialog.job.cancel.is_set())
        self.assertEqual(self.wait(dialog).state,'cancelled'); self.assertTrue(dialog.refresh_button.isEnabled())

    def test_failed_optional_operation_does_not_disable_main_text_conversion(self):
        from desktop_app.desktop import Window
        self.load_catalog(); dialog=self.open_dialog(); self.select(dialog,self.spec.key)
        dialog.start('offline',self.spec.key,self.root/'missing.zip'); self.assertEqual(self.wait(dialog).state,'failed')
        window=Window(settings_path=self.root/'main/settings.json'); self.addCleanup(window.close)
        source=self.root/'中文.txt'; source.write_text('基本文字轉換仍可使用')
        window.add_sources([source]); window.output.setText(str(self.root/'output')); window.reserve.setValue(0)
        window.start(); self.assertFalse(window.components_button.isEnabled())
        deadline=time.monotonic()+15
        while window.job.isRunning() and time.monotonic()<deadline: self.app.processEvents(); time.sleep(0.01)
        self.assertFalse(window.job.isRunning()); self.app.processEvents()
        self.assertEqual((self.root/'output/中文.txt.md').read_text(),source.read_text())
        self.assertTrue(window.components_button.isEnabled())

    def test_desktop_opens_dialog_with_current_resource_preferences(self):
        from desktop_app.desktop import Window
        calls=[]
        def factory(directory,settings): calls.append((directory,settings)); return self.service
        window=Window(settings_path=self.root/'main/settings.json',component_service_factory=factory)
        self.addCleanup(window.close); window.reserve.setValue(321)
        with patch('desktop_app.component_dialog.ComponentDialog.exec',return_value=0): window.components_button.click()
        dialog=window.component_dialog; self.dialogs.append(dialog); self.wait(dialog)
        self.assertEqual(calls[0][0],self.root/'main'); self.assertEqual(calls[0][1].reserve_mib,321)

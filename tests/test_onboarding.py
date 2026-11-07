"""C09 首次設定、偏好保護與真實 Qt／CPU 檢查；合成探針 fixture 不當作 OCR 證據。"""
from dataclasses import replace
import importlib.util
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Event, Timer
import time
import unittest
from unittest.mock import patch

from desktop_app.core import Cancelled
from desktop_app.onboarding.service import (EngineObservation, ONBOARDING_VERSION, SetupReport, SetupSession,
    native_command, probe_engine, recommend_ram)
from desktop_app.resources import MIB, Snapshot
from desktop_app.settings import Settings, load_settings, save_settings

AVAILABLE=Snapshot(8192*MIB,6144*MIB,64*MIB)


def fixture_probe(settings,directory,cancel,check):
    check()
    return EngineObservation(True,'/fixture/tesseract','/fixture/models','合成測試','fixture',('chi_tra','eng'),(),
                             'Fixture only, not native OCR')


class SetupServiceTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name); self.path=self.root/'中文/settings.json'

    def report(self,session): return session.inspect(read_snapshot=lambda:AVAILABLE,probe=fixture_probe)

    def test_ram_recommendations_small_normal_large_and_invalid(self):
        for total,expected in ((512,128),(4096,512),(8192,1024),(32768,2048)):
            advice=recommend_ram(Snapshot(total*MIB,total*MIB,0))
            self.assertEqual(advice.reserve_mib,expected); self.assertEqual(advice.automatic_budget_mib,total//4)
        for value in (Snapshot(0,0,0),Snapshot(1,2,0),Snapshot(1,-1,0)):
            with self.assertRaises(ValueError): recommend_ram(value)

    def test_new_session_is_read_only_until_explicit_completion(self):
        session=SetupSession(self.path); self.assertTrue(session.due)
        report=self.report(session); self.assertFalse(self.path.exists())
        session.complete(report,apply_ram=True,apply_engine=True)
        actual=load_settings(self.path)
        self.assertEqual(actual.onboarding_version,ONBOARDING_VERSION)
        self.assertEqual(actual.reserve_mib,1024); self.assertIsNone(actual.ram_budget_mib)
        self.assertEqual(actual.ocr_executable,'/fixture/tesseract')
        self.assertFalse(SetupSession(self.path).due)

    def test_existing_preferences_preserved_and_legacy_backup_exact(self):
        self.path.parent.mkdir(); raw=b'{"schema_version":5,"ram_budget_mib":768,"reserve_mib":512,"ocr_backend":"onnx_verify","ocr_executable":"C:/custom.exe","ocr_data_dir":"C:/models","cpu_threads":3}'
        self.path.write_bytes(raw); session=SetupSession(self.path); original=session.settings
        session.complete(self.report(session))
        self.assertEqual(load_settings(self.path),replace(original,onboarding_version=1))
        self.assertEqual(next(self.path.parent.glob('*.bak')).read_bytes(),raw)

    def test_apply_engine_never_replaces_explicit_paths_or_backend(self):
        settings=Settings(ocr_executable='missing-user-engine',ocr_data_dir='user-models',ocr_backend='onnx',device='gpu')
        save_settings(settings,self.path); session=SetupSession(self.path)
        result=session.complete(self.report(session),apply_engine=True)
        self.assertEqual(result,replace(settings,onboarding_version=1))

    def test_fingerprint_rejects_changes_during_probe_and_new_file_appearing(self):
        for existing in (False,True):
            with self.subTest(existing=existing):
                if self.path.exists():self.path.unlink()
                if existing:save_settings(Settings(),self.path)
                session=SetupSession(self.path); report=self.report(session)
                newer=Settings(reserve_mib=777); save_settings(newer,self.path); raw=self.path.read_bytes()
                with self.assertRaises(ValueError):session.complete(report,apply_ram=True)
                self.assertEqual(self.path.read_bytes(),raw)

    def test_stale_window_baseline_rejected_before_setup(self):
        save_settings(Settings(reserve_mib=999),self.path)
        with self.assertRaises(ValueError):SetupSession(self.path,expected_settings=Settings())

    def test_invalid_future_and_symlink_settings_never_reset(self):
        self.path.parent.mkdir()
        for raw in (b'bad json',b'{"schema_version":99}'):
            self.path.write_bytes(raw)
            with self.assertRaises(ValueError):SetupSession(self.path)
            self.assertEqual(self.path.read_bytes(),raw)
        self.path.unlink(); target=self.root/'other.json'; target.write_text('{"schema_version":6}')
        self.path.symlink_to(target)
        with self.assertRaises(ValueError):SetupSession(self.path)

    def test_missing_engine_still_allows_marking_flow_complete(self):
        session=SetupSession(self.path)
        report=session.inspect(read_snapshot=lambda:AVAILABLE,
            probe=lambda settings,directory,cancel,check:probe_engine(settings,directory,cancel,check,which=lambda name:None))
        self.assertFalse(report.engine.ready)
        session.complete(report,apply_engine=True)
        self.assertIsNone(load_settings(self.path).ocr_executable); self.assertFalse(SetupSession(self.path).due)

    def test_low_ram_does_not_start_native_probe(self):
        def forbidden(*args):raise AssertionError('must not start')
        report=SetupSession(self.path).inspect(read_snapshot=lambda:Snapshot(8192*MIB,0,0),probe=forbidden)
        self.assertFalse(report.engine.ready); self.assertNotIn('AssertionError',report.engine.message)

    def test_cancelled_probe_writes_no_settings(self):
        cancel=Event(); cancel.set()
        with self.assertRaises(Cancelled):SetupSession(self.path).inspect(cancel)
        self.assertFalse(self.path.exists())

    def test_explicit_missing_executable_does_not_fall_back(self):
        calls=[]
        report=probe_engine(Settings(ocr_executable='unavailable-custom'),self.root,Event(),which=lambda name:calls.append(name))
        self.assertFalse(report.ready); self.assertEqual(calls,['unavailable-custom'])

    def test_explicit_missing_models_do_not_fall_back(self):
        report=probe_engine(Settings(ocr_executable=sys.executable,ocr_data_dir=str(self.root/'missing')),self.root,Event())
        self.assertFalse(report.ready); self.assertIn('已指定',report.message)

    def test_model_reference_is_read_only_and_pinned_before_autoselection(self):
        folder=self.path.parent/'models/tesseract-managed'; folder.mkdir(parents=True)
        sentinel=folder/'eng.traineddata'; sentinel.write_bytes(b'user model')
        with patch.dict(os.environ,{'TESSDATA_PREFIX':''}), patch('desktop_app.onboarding.service.native_command',side_effect=['tesseract fixture','header\neng\n']):
            report=probe_engine(Settings(),self.path.parent,Event(),which=lambda name:sys.executable)
        self.assertFalse(report.ready); self.assertIsNone(report.data_dir); self.assertEqual(sentinel.read_bytes(),b'user model')

    def test_native_time_limit_output_bound_and_exit_failure(self):
        for command,timeout in (([sys.executable,'-I','-c','import time; time.sleep(2)'],0.1),
                                ([sys.executable,'-I','-c','print("x"*70000)'],2),
                                ([sys.executable,'-I','-c','raise SystemExit(2)'],2)):
            before=time.monotonic()
            with self.assertRaises(RuntimeError):native_command(command,Event(),timeout=timeout)
            self.assertLess(time.monotonic()-before,4)

    def test_running_native_cancel_reaps_child(self):
        cancel=Event(); children=[]; original=subprocess.Popen
        def launch(*args,**kwargs):
            child=original(*args,**kwargs); children.append(child); return child
        timer=Timer(0.1,cancel.set); timer.start()
        try:
            with patch('desktop_app.onboarding.service.subprocess.Popen',side_effect=launch),self.assertRaises(Cancelled):
                native_command([sys.executable,'-I','-c','import time; time.sleep(5)'],cancel)
        finally:timer.join()
        self.assertTrue(children); self.assertTrue(all(child.poll() is not None for child in children))


@unittest.skipUnless(shutil.which('tesseract') and importlib.util.find_spec('PIL'),'Install native Tesseract and Pillow prerequisites')
class NativeSetupTests(unittest.TestCase):
    def test_actual_cpu_bilingual_probe_offline(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('must not connect')):
                report=SetupSession(Path(temporary)/'settings.json').inspect()
        self.assertTrue(report.engine.ready,report.engine.message)
        self.assertIn('chi_tra',report.engine.languages); self.assertEqual(len(report.engine.samples),2)
        self.assertIn('WORKER HEALTH CHECK',report.engine.samples[0][1])
        self.assertIn('會議紀錄與資料轉換',''.join(report.engine.samples[1][1].split()))


@unittest.skipUnless(importlib.util.find_spec('PySide6'),'Install desktop dependencies')
class SetupDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])

    def setUp(self):
        temporary=tempfile.TemporaryDirectory(); self.addCleanup(temporary.cleanup)
        self.path=Path(temporary.name)/'settings.json'; self.dialogs=[]
        self.addCleanup(self.cleanup_dialogs)

    def cleanup_dialogs(self):
        for dialog in self.dialogs:
            if dialog.busy():dialog.reject(); dialog.job.wait(15000)
            self.app.processEvents(); dialog.close()

    def wait(self,dialog):
        deadline=time.monotonic()+15
        while dialog.busy() and time.monotonic()<deadline:self.app.processEvents(); time.sleep(0.005)
        if dialog.busy():dialog.reject(); dialog.job.wait(15000); self.fail('Setup exceeded bounded wait')
        self.app.processEvents()

    def open_fixture(self,session):
        from desktop_app.onboarding.dialog import SetupDialog
        report=session.inspect(read_snapshot=lambda:AVAILABLE,probe=fixture_probe)
        with patch.object(session,'inspect',return_value=report):
            dialog=SetupDialog(session); self.dialogs.append(dialog); self.wait(dialog)
        return dialog

    def test_new_defaults_ram_details_finish_and_no_repeat(self):
        dialog=self.open_fixture(SetupSession(self.path))
        self.assertTrue(dialog.ram.isChecked()); self.assertTrue(dialog.engine.isChecked())
        self.assertIn('25%',dialog.details.toPlainText()); self.assertIn('軟性預算',dialog.details.toPlainText())
        dialog.finish.click(); self.wait(dialog)
        self.assertTrue(dialog.did_save); self.assertFalse(SetupSession(self.path).due)

    def test_existing_defaults_preserve_preferences(self):
        saved=Settings(ram_budget_mib=888,ocr_backend='onnx_verify',reserve_mib=123)
        save_settings(saved,self.path); dialog=self.open_fixture(SetupSession(self.path))
        self.assertFalse(dialog.ram.isChecked()); self.assertFalse(dialog.engine.isChecked())
        dialog.finish.click(); self.wait(dialog)
        self.assertEqual(load_settings(self.path),replace(saved,onboarding_version=1))

    def test_later_and_close_cancel_without_marker(self):
        from desktop_app.onboarding.dialog import SetupDialog
        session=SetupSession(self.path); entered=Event()
        def waiting(cancel):entered.set(); cancel.wait(5); raise Cancelled('fixture')
        with patch.object(session,'inspect',side_effect=waiting):
            dialog=SetupDialog(session); self.dialogs.append(dialog)
            self.assertTrue(entered.wait(2)); self.assertFalse(dialog.finish.isEnabled())
            dialog.reject(); self.wait(dialog)
        self.assertFalse(self.path.exists()); self.assertTrue(dialog.pending_close)

    def test_failed_save_retains_dialog_and_external_preferences(self):
        dialog=self.open_fixture(SetupSession(self.path)); save_settings(Settings(reserve_mib=17),self.path)
        dialog.finish.click(); self.wait(dialog)
        self.assertFalse(dialog.did_save); self.assertIn('已變更',dialog.status.text())
        self.assertEqual(load_settings(self.path).reserve_mib,17)

    def test_completed_startup_does_not_reopen_or_run_probe(self):
        from desktop_app.desktop import Window
        save_settings(Settings(onboarding_version=1),self.path)
        window=Window(settings_path=self.path); self.addCleanup(window.close)
        with patch('desktop_app.onboarding.dialog.SetupDialog',side_effect=AssertionError('must not reopen')): window.offer_setup()
        self.assertIsNone(window.setup_dialog)

    def test_window_schedules_and_reopens_explicitly_with_saved_preferences(self):
        from desktop_app.desktop import Window
        window=Window(settings_path=self.path); self.addCleanup(window.close)
        window.reserve.setValue(333); window.save_preferences()
        with patch('desktop_app.onboarding.service.SetupSession.inspect',lambda session,cancel:session.inspect_fixture):
            # 以固定 fixture 回傳給同一視窗接線，真原生執行由獨立測試證明。
            from desktop_app.onboarding.service import SetupSession as Session
            Session.inspect_fixture=SetupReport(recommend_ram(AVAILABLE),fixture_probe(None,None,None,lambda:None),True)
            try:window.offer_setup(); dialog=window.setup_dialog; self.dialogs.append(dialog); self.wait(dialog)
            finally:del Session.inspect_fixture
        self.assertFalse(dialog.ram.isChecked()); dialog.finish.click(); self.wait(dialog)
        self.assertEqual(window.loaded_settings.onboarding_version,1); self.assertEqual(window.reserve.value(),333)

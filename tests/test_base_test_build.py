"""B1a 組裝／來源／上傳界線；本地合成 fixture 不代表真的 Windows 安裝驗收。"""
import copy
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import base_test_build as build


class BaseTestBuildTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.serial = 0

    def fixture(self):
        self.serial += 1
        root = self.root/str(self.serial)
        bundle, candidate, reports = root/'bundle', root/'candidate', root/'reports'
        def put(directory, name, data):
            path = directory/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(data)
            return path
        put(bundle, '_internal/desktop_app/data/build-profile.json', b'{"source_version":"0.19.1"}')
        native = put(bundle,'_internal/example.dll',b'SYNTHETIC native bytes, never executed')
        notice = put(bundle,'_internal/desktop_app/data/licenses/example/LICENSE.txt',b'SYNTHETIC original notice')
        for name in build.DISCLOSURES:
            data = b'{"schema_version":1,"accepted_gaps":{}}' if name.endswith('.json') else ('合成說明：'+name).encode()
            put(bundle,'_internal/desktop_app/data/licenses/'+name,data)
            put(candidate,'src/desktop_app/data/licenses/'+name,data)
        installer = put(root,'MarkItDownBase-Setup-0.19.1-windows-x64.exe',b'SYNTHETIC installer bytes, never executed')
        plan = dict(candidate_source=build.SOURCE,source_version='0.19.1',publish_allowed=False,
                    approval_policy=dict(source_commit='c'*40,flags=build.EXPECTED_FLAGS))
        review = dict(selection=dict(source_commit=build.SOURCE),candidate=dict(sha256='0'*64),classification=dict(files=[]),
             classification_input=dict(report=dict(native_files=[dict(file='example.dll',bundled_sha256=build.digest(native))])),
             packages=[dict(notices=[dict(path=notice.relative_to(bundle).as_posix(),sha256=build.digest(notice))])])
        reports.mkdir(parents=True)
        build.write(reports/'plan.json',plan)
        return dict(bundle=bundle,installer=installer,product=root/'product',reports=reports,plan=plan,review=review,candidate=candidate)

    def fake_api(self, *, expired=False, conclusion='success', path='.github/workflows/windows-base-validation.yml', digest=True):
        run=dict(id=123,status='completed',conclusion=conclusion,path=path,head_sha='d'*40)
        artifact=dict(id=456,name='windows-ocr-ci-inputs',expired=expired,expires_at='2099-01-01T00:00:00Z',
                      digest='sha256:'+'1'*64 if digest else None)
        def api(endpoint):
            if '/artifacts?' in endpoint:return dict(artifacts=[artifact])
            if '/runs?' in endpoint:return dict(workflow_runs=[run])
            if endpoint=='actions/runs/123':return run
            self.fail('Unexpected API call: '+endpoint)
        return api

    def test_current_policy_and_stage_guard_cannot_publish(self):
        result=build.policy(ROOT)
        self.assertEqual(result['flags'],build.EXPECTED_FLAGS)
        self.assertEqual(result['source_review']['path'],build.REVIEW)
        self.assertFalse(build.PUBLIC_UPLOAD_ENABLED)
        plan=build.make_plan(api=self.fake_api())
        self.assertEqual(plan['candidate_source'],build.SOURCE)
        self.assertEqual(plan['source_version'],'0.19.1')
        self.assertEqual(plan['retention_days'],30)
        self.assertFalse(plan['publish_allowed'])
        with self.assertRaisesRegex(ValueError,'B1b'):
            build.make_plan(publish=True,api=lambda _:self.fail('Public stage must fail before reading inputs'))

    def test_input_artifact_selection_refuses_expired_failed_or_wrong_workflow(self):
        result=build.select_inputs(api=self.fake_api())
        self.assertEqual(result['run_id'],123)
        for changes in (dict(expired=True),dict(conclusion='failure'),dict(path='.github/workflows/windows-build.yml'),dict(digest=False)):
            with self.subTest(changes=changes),self.assertRaises(ValueError):
                build.select_inputs(api=self.fake_api(**changes))
        with self.assertRaises(ValueError):
            build.select_inputs('../other-run',api=self.fake_api())
        with self.assertRaisesRegex(ValueError,'No unexpired'):
            build.select_inputs(api=self.fake_api(),now=datetime(2100,1,1,tzinfo=timezone.utc))

    def test_inputs_must_match_candidate_ocr_bytes_not_the_artifact_name(self):
        inputs,candidate=self.root/'inputs',self.root/'candidate'
        contract=candidate/'packaging/native/minimal-windows.json'
        contract.parent.mkdir(parents=True)
        contract.write_text('{}')
        records=[]
        for name in ('chi_tra','eng','jpn','kor'):
            path=inputs/'models'/(name+'.traineddata')
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(('SYNTHETIC '+name).encode())
            records.append(dict(path='_internal/desktop_app/data/native/tessdata/'+path.name,sha256=build.digest(path)))
        exe=inputs/'candidate/tesseract.exe'
        exe.parent.mkdir(parents=True)
        exe.write_bytes(b'SYNTHETIC native fixture')
        records.append(dict(path='_internal/desktop_app/data/native/bin/tesseract.exe',sha256=build.digest(exe)))
        build.write(inputs/'build-evidence.json',dict(candidate=dict(sha256=build.digest(exe)),source_contract_sha256=build.digest(contract)))
        review=dict(classification=dict(files=records))
        with mock.patch.object(build,'git_source',return_value=build.SOURCE):
            build.validate_inputs(inputs,candidate,review)
            (inputs/'models/jpn.traineddata').write_bytes(b'wrong model')
            with self.assertRaisesRegex(ValueError,'differ from the fixed candidate'):
                build.validate_inputs(inputs,candidate,review)
        with mock.patch.object(build,'git_source',return_value='0'*40),self.assertRaisesRegex(ValueError,'checkout differs'):
            build.validate_inputs(inputs,candidate,review)

    def test_generated_source_receipt_binds_current_inputs_without_reusing_old_run_hash(self):
        inputs,candidate,bundle=self.root/'inputs',self.root/'candidate',self.root/'bundle'
        inputs.mkdir()
        contract=candidate/'packaging/native/minimal-windows.json'
        contract.parent.mkdir(parents=True)
        contract.write_text('{}')
        build.write(inputs/'build-evidence.json',dict(windows_utf8_manifest={'synthetic':True}))
        source=bundle/build.NATIVE_SOURCE
        source.parent.mkdir(parents=True)
        expected=dict(kind='ci-rebuilt-windows-minimal',evidence_sha256=build.digest(inputs/'build-evidence.json'),
                      source_contract_sha256=build.digest(contract),upstream_version='5.5.3',windows_executed=False,
                      windows_utf8_manifest={'synthetic':True})
        build.write(source,expected)
        self.assertEqual(build.validate_generated_receipt(bundle,inputs,candidate),build.digest(source))
        build.write(source,dict(expected,evidence_sha256='0'*64))
        with self.assertRaisesRegex(ValueError,'not bound'):
            build.validate_generated_receipt(bundle,inputs,candidate)
        build.write(source,expected)
        (inputs/'build-evidence.json').write_text('{"windows_utf8_manifest":{"synthetic":false}}')
        with self.assertRaisesRegex(ValueError,'not bound'):
            build.validate_generated_receipt(bundle,inputs,candidate)

    def test_product_has_required_attachments_but_reports_never_contain_installer(self):
        fixture=self.fixture()
        result=build.assemble(**fixture)
        self.assertTrue(result['accepted'])
        self.assertFalse(result['installer_uploaded'])
        self.assertTrue(result['report_only'])
        self.assertEqual({p.name for p in fixture['reports'].iterdir()},build.REPORT_NAMES)
        self.assertTrue((fixture['product']/fixture['installer'].name).is_file())
        self.assertFalse(any(p.suffix.lower() in ('.exe','.dll','.zip') for p in fixture['reports'].rglob('*')))
        info=build.load(fixture['reports']/'BUILD-INFO.json')
        self.assertEqual(info['candidate_source'],build.SOURCE)
        self.assertEqual(info['workflow_source'],'c'*40)
        self.assertEqual(info['installer']['sha256'],build.digest(fixture['installer']))
        files=build.load(fixture['reports']/'LICENSE-FILES.json')['files']
        for row in files:self.assertEqual(build.digest(fixture['bundle']/row['path']),row['sha256'])
        for name in build.DISCLOSURES:
            self.assertEqual((fixture['reports']/name).read_bytes(),(fixture['product']/name).read_bytes())

    def test_modified_native_notices_disclosures_or_version_abort_assembly(self):
        changes=('_internal/example.dll','_internal/desktop_app/data/licenses/example/LICENSE.txt',
                 '_internal/desktop_app/data/licenses/known-gaps.json','_internal/desktop_app/data/build-profile.json')
        for relative in changes:
            with self.subTest(relative=relative):
                fixture=self.fixture()
                (fixture['bundle']/relative).write_bytes(b'{"source_version":"wrong"}' if relative.endswith('build-profile.json') else b'changed')
                with self.assertRaises(ValueError):build.assemble(**fixture)
        fixture=self.fixture()
        fixture['review']['selection']['source_commit']='0'*40
        with self.assertRaisesRegex(ValueError,'source differs'):build.assemble(**fixture)

    def test_report_and_product_paths_cannot_overlap_even_on_failure(self):
        for nested in ('same','product-in-reports','reports-in-product'):
            fixture=self.fixture()
            if nested=='same':fixture['product']=fixture['reports']/'new';fixture['reports']=fixture['product']
            elif nested=='product-in-reports':fixture['product']=fixture['reports']/'new'
            else:fixture['reports']=fixture['product']/'new'
            with self.subTest(nested=nested),self.assertRaisesRegex(ValueError,'disjoint'):
                build.assemble(**fixture)
        with self.assertRaisesRegex(ValueError,'Unsafe'):
            build.checked_file(self.root,'../outside')

    def test_copy_damage_is_not_relabelled_as_a_new_valid_manifest(self):
        fixture=self.fixture()
        original=shutil.copyfile
        def corrupt(source,target,*args,**kwargs):
            result=original(source,target,*args,**kwargs)
            if Path(target).suffix=='.exe':Path(target).write_bytes(b'copy damaged')
            return result
        with mock.patch.object(build.shutil,'copyfile',side_effect=corrupt),self.assertRaisesRegex(ValueError,'Copied attachment fingerprint'):
            build.assemble(**fixture)

    def test_public_report_parts_are_complete_bounded_and_contain_no_product_bytes(self):
        fixture=self.fixture()
        build.assemble(**fixture)
        (fixture['reports']/'README.md').write_bytes(b'# CRLF report\r\n\r\nExact Windows bytes\r\n')
        parts=build.public_parts(fixture['reports'])
        files=build.decode_parts(list(reversed(parts)))
        self.assertEqual(set(files),build.REPORT_NAMES)
        for name,text in files.items():self.assertEqual(text.encode('utf-8'),(fixture['reports']/name).read_bytes())
        cases=(parts[:-1],[dict(p,sha256='0'*64) for p in parts],
               [dict(p,part=len(parts)+1) if i==0 else p for i,p in enumerate(parts)])
        for case in cases:
            with self.subTest(case=case),self.assertRaises(ValueError):build.decode_parts(case)
        (fixture['reports']/'leaked.exe').write_bytes(b'SYNTHETIC binary')
        with self.assertRaisesRegex(ValueError,'Unsafe public report'):build.public_parts(fixture['reports'])

    def test_collect_checks_host_and_distinguishes_workflow_from_payload_source(self):
        with mock.patch.object(build.sys,'platform','linux'),self.assertRaisesRegex(ValueError,'hosted Windows'):
            build.collect(None,None,None,None,None,None)
        with mock.patch.object(build.sys,'platform','win32'),mock.patch.dict(build.os.environ,{'GITHUB_ACTIONS':'false'}),self.assertRaisesRegex(ValueError,'hosted Windows'):
            build.collect(None,None,None,None,None,None)
        root=self.root/'collect'
        reports=root/'build/reports'
        (reports/'installer').mkdir(parents=True)
        policy=dict(source_commit='a'*40)
        build.write(root/'plan.json',dict(check='base-test-build-plan',approval_policy=policy,publish_requested=False,source_version='0.19.1'))
        build.write(reports/'windows-build.json',dict(commit='a'*40,**{name:True for name in
                    ('build_verified','validation_accepted','installer_accepted','provenance_accepted','qt_replacement_accepted','overall_accepted')}))
        (root/'inputs').mkdir()
        (root/'inputs/build-evidence.json').write_text('{}')
        installer=root/'build/installer-work/setup/MarkItDownBase-Setup-0.19.1-windows-x64.exe'
        installer.parent.mkdir(parents=True)
        installer.write_bytes(b'SYNTHETIC installer, never executed')
        lifecycle=dict(accepted=True,windows_executed=True,source_version='0.19.1',installer_sha256=build.digest(installer),
                       install_verified=True,repair_verified=True,uninstall_verified=True)
        build.write(reports/'installer/installer-lifecycle.json',lifecycle)
        (reports/'acceptance').mkdir()
        build.write(reports/'acceptance/windows-acceptance.json',dict(accepted=True,windows_executed=True,checks_passed=5))
        provenance=dict(source_commit='a'*40,accepted=True,profile='base',source_version='0.19.1')
        build.write(reports/'bundle-provenance.json',provenance)
        with mock.patch.object(build.sys,'platform','win32'),mock.patch.dict(build.os.environ,{'GITHUB_ACTIONS':'true'}),\
             mock.patch.object(build,'policy',return_value=policy),mock.patch.object(build,'validate_inputs'),\
             mock.patch.object(build,'validate_generated_receipt',return_value='f'*64),\
             mock.patch.object(build,'assemble',side_effect=lambda *a,**kw:dict(accepted=True)):
            result=build.collect(root/'plan.json',root/'inputs',None,root/'build',None,reports,root=ROOT)
            self.assertTrue(result['windows_executed'])  # 只驗分支契約，此 fixture 不作實際 Windows 證據。
            build.write(reports/'bundle-provenance.json',dict(source_commit=build.SOURCE))
            with self.assertRaisesRegex(ValueError,'workflow source differs'):
                build.collect(root/'plan.json',root/'inputs',None,root/'build',None,reports,root=ROOT)
            build.write(reports/'bundle-provenance.json',provenance)
            build.write(reports/'installer/installer-lifecycle.json',dict(lifecycle,installer_sha256='0'*64))
            with self.assertRaisesRegex(ValueError,'Actual tested installer differs'):
                build.collect(root/'plan.json',root/'inputs',None,root/'build',None,reports,root=ROOT)

    def test_workflow_has_separate_trial_job_and_explicit_text_only_report_paths(self):
        text=(ROOT/'.github/workflows/windows-base-validation.yml').read_text()
        job=text.split('  b1-test-build:')[1]
        self.assertIn("github.event_name == 'workflow_dispatch' && inputs.prepare_test_build",job)
        self.assertIn("steps.plan.outputs.publish_allowed == 'true'",job)
        self.assertEqual(job.count('retention-days: 30'),2)
        report_upload=job.split('name: base-test-build-reports')[1].split('retention-days: 30')[0]
        self.assertNotIn('path: out/test-build-reports/',report_upload)
        for name in build.REPORT_NAMES:self.assertIn('out/test-build-reports/'+name,report_upload)
        self.assertNotIn('.exe',report_upload)
        self.assertNotIn('/actions/workflows/windows-build.yml/dispatches',text)
        self.assertIn('ref: ${{ steps.plan.outputs.candidate_source }}',job)
        self.assertIn('MARKITDOWN_CANDIDATE_SOURCE: '+build.SOURCE,job)
        self.assertIn("python-version: '3.12.10'",job)


if __name__=='__main__':
    unittest.main()

"""C05 驗收：真實 Ed25519／磁碟／SQLite，HTTP 反例採有界注入，不啟用元件。"""
import base64
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tempfile
from threading import Event
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.capabilities import CapabilityResolver, HostContext
from desktop_app.components.catalog import CatalogError, CatalogVerifier, TrustPolicy, canonical_json
from desktop_app.components.contracts import ComponentState, Version
from desktop_app.components.downloads import DownloadBusy, DownloadError, DownloadService
from desktop_app.components.network import ApprovedRedirects, fetch_catalog
from desktop_app.components.registry import ComponentRegistry, IntegrityError
from desktop_app.core import Cancelled
from test_components import descriptor

NOW = datetime(2026, 11, 6, tzinfo=timezone.utc)
URL = 'https://example.invalid/package'
DATA = b'fixed C05 payload\n' * 16000


def policy(key):
    return TrustPolicy(1, 'test-catalog', 1, {'test-key':key.public_key().public_bytes_raw()},
                       frozenset(), ('https://example.invalid',))


def sign(key, specs, **changes):
    payload = dict(schema_version=1, catalog_id='test-catalog', revision=1, trust_policy_version=1,
                   issued_at='2026-11-05T00:00:00Z', expires_at='2026-11-07T00:00:00Z',
                   components=[item.to_dict() for item in specs])
    payload.update(changes)
    return canonical_json(dict(payload=payload, signature=dict(key_id='test-key', algorithm='ed25519',
                          value=base64.b64encode(key.sign(canonical_json(payload))).decode())))


def package():
    return descriptor(source_url=URL, download_bytes=len(DATA), package_sha256=hashlib.sha256(DATA).hexdigest())


class Response(io.BytesIO):
    def __init__(self, data, *, status=200, headers=None, url=URL):
        super().__init__(data)
        self.status = status
        self.headers = {'ETag':'"c05-v1"', **(headers or {})}
        self.url = url

    def geturl(self):
        return self.url


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.key = Ed25519PrivateKey.generate()
        self.policy = policy(self.key)
        self.verifier = CatalogVerifier(self.policy, lambda:NOW)
        self.spec = package()
        self.raw = sign(self.key, [self.spec])

    def test_real_ed25519_catalog_validates_and_resolves_exact_component(self):
        catalog = self.verifier.load(self.raw)
        self.assertEqual(catalog.component(*self.spec.key), self.spec)
        self.assertEqual(self.verifier.load(catalog), catalog)
        with self.assertRaises(CatalogError):catalog.component('unknown', '1.0.0')

    def test_tampering_descriptor_does_not_pass_original_signature(self):
        value = json.loads(self.raw);value['payload']['components'][0]['source_url'] += '/changed'
        with self.assertRaises(CatalogError):self.verifier.load(canonical_json(value))

    def test_other_private_key_cannot_impersonate_trusted_key_id(self):
        with self.assertRaises(CatalogError):self.verifier.load(sign(Ed25519PrivateKey.generate(),[self.spec]))

    def test_unknown_revoked_and_rotated_keys(self):
        for updated in (replace(self.policy, keys={'another-key':self.key.public_key().public_bytes_raw()}),
                        replace(self.policy, revoked_keys=frozenset({'test-key'}))):
            with self.assertRaises(CatalogError):CatalogVerifier(updated,lambda:NOW).load(self.raw)
        new = Ed25519PrivateKey.generate()
        rotated = replace(self.policy, keys={**dict(self.policy.keys),'next-key':new.public_key().public_bytes_raw()})
        envelope = json.loads(sign(new,[self.spec]));envelope['signature']['key_id']='next-key'
        self.assertEqual(CatalogVerifier(rotated,lambda:NOW).load(canonical_json(envelope)).components,(self.spec,))

    def test_policy_and_catalog_identity_and_schema_must_match(self):
        for changes in ({'schema_version':2},{'schema_version':True},{'trust_policy_version':2},
                        {'catalog_id':'other'},{'revision':True},{'revision':0},{'unknown':1}):
            with self.subTest(changes=changes),self.assertRaises(CatalogError):
                self.verifier.load(sign(self.key,[self.spec],**changes))

    def test_expired_future_and_invalid_times_are_rejected(self):
        for changes in ({'expires_at':'2026-11-06T00:00:00Z'},{'issued_at':'2026-11-06T00:10:00Z'},
                        {'issued_at':'2026-11-09T00:00:00Z'},{'expires_at':'not-a-date'},
                        {'issued_at':'2026-11-05T00:00:00+00:00'}):
            with self.subTest(changes=changes),self.assertRaises(CatalogError):
                self.verifier.load(sign(self.key,[self.spec],**changes))

    def test_revision_high_water_and_minimum_reject_rollback(self):
        self.verifier.load(sign(self.key,[self.spec],revision=3))
        with self.assertRaises(CatalogError):self.verifier.load(self.raw)
        with self.assertRaises(CatalogError):CatalogVerifier(replace(self.policy,minimum_revision=2),lambda:NOW).load(self.raw)

    def test_same_signed_revision_cannot_change_contents(self):
        self.verifier.load(self.raw)
        changed=replace(self.spec,display_name='changed under same revision')
        with self.assertRaises(CatalogError):self.verifier.load(sign(self.key,[changed]))

    def test_duplicate_unknown_and_oversize_envelopes_rejected(self):
        for raw in (b'{"payload":{},"payload":{},"signature":{}}',b'{}',b'[]',b'broken',b'x'*(1024**2+1),b'['*2000):
            with self.subTest(size=len(raw)),self.assertRaises(CatalogError):self.verifier.load(raw)
        with self.assertRaises(CatalogError):self.verifier.load(sign(self.key,[self.spec,self.spec]))

    def test_sources_and_capacity_are_constrained_by_trust_policy(self):
        with self.assertRaises(CatalogError):self.verifier.load(sign(self.key,[replace(self.spec,source_url='https://other.invalid/file')]))
        small = replace(self.policy,max_download_bytes=100)
        with self.assertRaises(CatalogError):CatalogVerifier(small,lambda:NOW).load(self.raw)
        for url in ('http://example.invalid/a','https://user:password@example.invalid/a',
                    'https://example.invalid:8443/a','file:///etc/passwd','https://example.invalid/a#fragment'):
            with self.subTest(url=url),self.assertRaises(CatalogError):self.policy.check_url(url)

    def test_public_keys_are_immutable_and_network_cannot_add_trust_root(self):
        with self.assertRaises(TypeError):self.policy.keys['new']=b'a'*32
        envelope=json.loads(self.raw);envelope['payload']['keys']={'bad':'bad'}
        envelope['signature']['value']=base64.b64encode(self.key.sign(canonical_json(envelope['payload']))).decode()
        with self.assertRaises(CatalogError):self.verifier.load(canonical_json(envelope))

    def test_fetch_catalog_is_bounded_and_checks_response_source(self):
        loaded=fetch_catalog(URL,self.verifier,opener=lambda *a,**k:Response(self.raw))
        self.assertEqual(loaded.components,(self.spec,))
        for response in (Response(b'x'*(1024**2+1)),Response(self.raw,url='https://other.invalid/catalog'),
                         Response(self.raw,headers={'Content-Encoding':'gzip'})):
            with self.assertRaises(CatalogError):fetch_catalog(URL,self.verifier,opener=lambda *a,**k:response)

    def test_redirect_policy_blocks_before_network_request(self):
        handler=ApprovedRedirects(self.policy)
        for url in ('http://example.invalid/a','https://other.invalid/a','file:///tmp/payload'):
            with self.assertRaises(CatalogError):handler.redirect_request(urllib.request.Request(URL),None,302,'Found',{},url)
        request=handler.redirect_request(urllib.request.Request(URL),None,302,'Found',{},URL+'/next')
        self.assertEqual(request.full_url,URL+'/next')

    def test_approved_cross_origin_redirect_clears_resume_headers(self):
        trusted=replace(self.policy,allowed_origins=(*self.policy.allowed_origins,'https://cdn.example.invalid'))
        handler=ApprovedRedirects(trusted)
        original=urllib.request.Request(URL,headers={'Range':'bytes=100-','If-Range':'"old"'})
        request=handler.redirect_request(original,None,302,'Found',{},'https://cdn.example.invalid/file')
        self.assertIsNone(request.get_header('Range'));self.assertIsNone(request.get_header('If-range'))


class DownloadTests(unittest.TestCase):
    def setUp(self):
        directory=tempfile.TemporaryDirectory();self.addCleanup(directory.cleanup)
        self.root=Path(directory.name)/'中文元件';self.root.mkdir()
        self.key=Ed25519PrivateKey.generate();self.verifier=CatalogVerifier(policy(self.key),lambda:NOW)
        self.spec=package();self.catalog=self.verifier.load(sign(self.key,[self.spec]))
        self.registry=ComponentRegistry(self.root/'registry')
        self.requests=[]

    def response(self,request,timeout):
        self.requests.append(dict(request.header_items()))
        self.assertEqual(timeout,10)
        return Response(DATA,headers={'Content-Length':str(len(DATA))})

    def service(self,opener=None,**kwargs):
        return DownloadService(self.root/'cache',self.verifier,self.registry,opener=opener or self.response,
                               reserve_bytes=0,**kwargs)

    def download(self,service,**kwargs):
        return service.download(self.catalog,*self.spec.key,wait=lambda seconds:False,**kwargs)

    def partial(self,service,content=DATA[:4000],etag='"c05-v1"'):
        final,part,meta,_=service._paths(self.spec);part.write_bytes(content)
        service._metadata(self.spec,meta,etag)
        return final,part,meta

    def test_download_to_verified_cache_and_registry_never_ready(self):
        result=self.download(self.service())
        self.assertEqual(result.path.read_bytes(),DATA);self.assertEqual(result.source,'network')
        self.assertEqual(self.registry.get(*self.spec.key).state,ComponentState.VERIFIED)
        host=HostContext('linux','x86_64',Version.parse('0.3.0'),Version.parse('1.0.0'))
        self.assertFalse(CapabilityResolver(self.registry,[self.spec],host,{}).resolve('ocr.text.zh-hant').available)
        self.assertFalse(self.registry.payloads.exists())

    def test_valid_cache_reuse_needs_no_network(self):
        first=self.download(self.service())
        result=self.download(self.service(lambda *a,**k:self.fail('must reuse verified cache')))
        self.assertEqual(result.source,'cache');self.assertEqual(result.path,first.path)

    def test_corrupt_final_cache_is_preserved_and_refused(self):
        service=self.service();final,*_=service._paths(self.spec);final.write_bytes(b'user modified')
        with self.assertRaises(IntegrityError):self.download(service)
        self.assertEqual(final.read_bytes(),b'user modified');self.assertEqual(self.requests,[])

    def test_cancel_and_resume_with_strong_etag_range(self):
        cancel=Event();service=self.service()
        def progress(received,total):cancel.set()
        with self.assertRaises(Cancelled):self.download(service,cancel=cancel,progress=progress)
        final,part,meta,_=service._paths(self.spec);offset=part.stat().st_size
        self.assertGreater(offset,0);self.assertFalse(final.exists())
        def resumed(request,timeout):
            self.assertEqual(request.get_header('Range'),f'bytes={offset}-')
            self.assertEqual(request.get_header('If-range'),'"c05-v1"')
            return Response(DATA[offset:],status=206,headers={
                'Content-Range':f'bytes {offset}-{len(DATA)-1}/{len(DATA)}',
                'Content-Length':str(len(DATA)-offset)})
        service.opener=resumed;result=self.download(service)
        self.assertEqual(result.resumed_from,offset);self.assertEqual(result.path.read_bytes(),DATA)
        self.assertFalse(part.exists());self.assertFalse(meta.exists())

    def test_missing_or_weak_etag_restarts_without_range(self):
        for validator in (None,'W/"weak"','invalid'):
            with self.subTest(validator=validator):
                service=self.service();self.partial(service,etag=validator)
                def fresh(request,timeout):
                    self.assertIsNone(request.get_header('Range'))
                    return Response(DATA)
                service.opener=fresh;result=self.download(service)
                self.assertEqual(result.resumed_from,0);result.path.unlink()

    def test_ignored_range_200_replaces_fragment_without_duplication(self):
        service=self.service();self.partial(service)
        result=self.download(service)
        self.assertEqual(result.path.read_bytes(),DATA);self.assertEqual(result.resumed_from,0)

    def test_invalid_range_or_changed_etag_discards_fragment_then_restarts(self):
        for headers in ({'Content-Range':'bytes 0-9/10'},
                        {'Content-Range':f'bytes 4000-{len(DATA)-1}/{len(DATA)}','ETag':'"new"'}):
            service=self.service();self.partial(service);calls=[]
            def answer(request,timeout):
                calls.append(request)
                return Response(DATA[4000:],status=206,headers=headers) if len(calls)==1 else Response(DATA)
            service.opener=answer;result=self.download(service)
            self.assertEqual(len(calls),2);self.assertIsNone(calls[-1].get_header('Range'))
            self.assertEqual(result.path.read_bytes(),DATA);result.path.unlink()

    def test_range_416_discards_stale_fragment_and_restarts(self):
        service=self.service();self.partial(service);calls=[]
        def answer(request,timeout):
            calls.append(request)
            if len(calls)==1:raise urllib.error.HTTPError(URL,416,'range',{},None)
            self.assertIsNone(request.get_header('Range'));return Response(DATA)
        service.opener=answer
        self.assertEqual(self.download(service).path.read_bytes(),DATA)

    def test_partial_cache_with_complete_bytes_can_finish_without_network(self):
        service=self.service(lambda *a,**k:self.fail('complete fragment only needs hash'))
        self.partial(service,DATA)
        result=self.download(service)
        self.assertEqual(result.source,'partial-cache');self.assertEqual(result.attempts,0)

    def test_short_response_resumes_within_retry_budget(self):
        calls=[]
        def answer(request,timeout):
            calls.append(request)
            if len(calls)==1:return Response(DATA[:5000])
            self.assertEqual(request.get_header('Range'),'bytes=5000-')
            return Response(DATA[5000:],status=206,headers={'Content-Range':f'bytes 5000-{len(DATA)-1}/{len(DATA)}'})
        result=self.download(self.service(answer))
        self.assertEqual(result.path.read_bytes(),DATA);self.assertEqual(result.attempts,2)

    def test_retry_limit_and_nonretryable_http_errors(self):
        for code,expected in ((503,3),(429,3),(404,1),(403,1)):
            with self.subTest(code=code):
                calls=[]
                def fail(request,timeout):
                    calls.append(request);raise urllib.error.HTTPError(URL,code,'test',{},None)
                with self.assertRaises(DownloadError):self.download(self.service(fail))
                self.assertEqual(len(calls),expected)

    def test_timeout_is_retried_but_cancel_and_checkpoint_are_not(self):
        calls=[]
        def fail(*a,**k):calls.append(1);raise TimeoutError('test')
        with self.assertRaises(DownloadError):self.download(self.service(fail))
        self.assertEqual(len(calls),3)
        calls.clear();cancel=Event();cancel.set()
        with self.assertRaises(Cancelled):self.download(self.service(fail),cancel=cancel)
        self.assertEqual(calls,[])
        def checkpoint():raise RuntimeError('resource pause rejected')
        with self.assertRaises(RuntimeError):self.download(self.service(fail),checkpoint=checkpoint)
        self.assertEqual(calls,[])

    def test_cancelling_backoff_stops_before_next_network_attempt(self):
        calls=[]
        def fail(*a,**k):calls.append(1);raise TimeoutError('test')
        service=self.service(fail)
        with self.assertRaises(Cancelled):service.download(self.catalog,*self.spec.key,wait=lambda seconds:True)
        self.assertEqual(len(calls),1)
        self.assertFalse(service._paths(self.spec)[-1].exists())

    def test_disk_write_error_is_not_retried_and_lock_is_released(self):
        service=self.service()
        with patch('desktop_app.components.downloads.os.fsync',side_effect=OSError('disk full')):
            with self.assertRaises(OSError):self.download(service)
        self.assertEqual(len(self.requests),1)
        self.assertFalse(service._paths(self.spec)[0].exists())
        self.assertFalse(service._paths(self.spec)[-1].exists())
        self.assertEqual(list(service.directory.glob('.resume-*')),[])

    def test_hash_mismatch_is_not_published_or_registered(self):
        service=self.service(lambda *a,**k:Response(b'x'*len(DATA)))
        with self.assertRaises(IntegrityError):self.download(service)
        final,part,meta,_=service._paths(self.spec)
        self.assertFalse(final.exists());self.assertFalse(part.exists());self.assertFalse(meta.exists())
        self.assertIsNone(self.registry.get(*self.spec.key))

    def test_oversize_and_bad_content_length_are_bounded_and_rejected(self):
        for response in (lambda:Response(DATA+b'x'),lambda:Response(DATA,headers={'Content-Length':'99999999999999'})):
            calls=[]
            def answer(*a,**k):calls.append(1);return response()
            with self.assertRaises(DownloadError):self.download(self.service(answer))
            self.assertEqual(len(calls),3)
        self.assertFalse(self.service()._paths(self.spec)[0].exists())

    def test_encoded_or_unapproved_response_is_rejected(self):
        for response in (Response(DATA,headers={'Content-Encoding':'gzip'}),Response(DATA,url='https://other.invalid/payload')):
            with self.assertRaises((DownloadError,CatalogError)):
                self.download(self.service(lambda *a,**k:response))

    def test_same_package_lock_rejects_concurrent_work_and_preserves_other_files(self):
        service=self.service();other=service.directory/'user-notes.txt';other.write_text('keep')
        with service._lock(self.spec):
            with self.assertRaises(DownloadBusy):self.download(service)
        self.assertEqual(other.read_text(),'keep')
        self.assertEqual(self.download(service).path.read_bytes(),DATA)

    def test_insufficient_disk_space_stops_before_network(self):
        service=self.service()
        with patch('desktop_app.components.downloads.shutil.disk_usage',return_value=SimpleNamespace(free=1)):
            with self.assertRaises(DownloadError):self.download(service)
        self.assertEqual(self.requests,[])

    def test_symlink_cache_files_and_linked_roots_are_rejected(self):
        service=self.service();external=self.root/'external';external.write_bytes(b'private')
        final,*_=service._paths(self.spec)
        try:final.symlink_to(external)
        except OSError as exc:self.skipTest(str(exc))
        with self.assertRaises(IntegrityError):self.download(service)
        self.assertEqual(external.read_bytes(),b'private')
        link=self.root/'link';link.symlink_to(service.directory,target_is_directory=True)
        with self.assertRaises(IntegrityError):DownloadService(link,self.verifier)

    def test_tampered_resume_metadata_restarts_without_trusting_url_or_offsets(self):
        service=self.service();_,_,meta=self.partial(service)
        meta.write_text('{"url":"https://other.invalid/private","offset":999999}')
        self.assertEqual(self.download(service).path.read_bytes(),DATA)
        self.assertNotIn('Range',self.requests[0])

    def test_offline_import_validates_and_preserves_external_source(self):
        source=self.root/'外部套件.zip';source.write_bytes(DATA)
        service=self.service(lambda *a,**k:self.fail('offline import must not use network'))
        result=service.import_offline(self.catalog,*self.spec.key,source)
        self.assertEqual(result.source,'offline');self.assertEqual(source.read_bytes(),DATA)
        self.assertEqual(result.path.read_bytes(),DATA)
        self.assertEqual(self.registry.get(*self.spec.key).state,ComponentState.VERIFIED)

    def test_offline_corrupt_oversize_or_linked_source_never_changes_source(self):
        service=self.service();source=self.root/'bad';source.write_bytes(DATA+b'x')
        with self.assertRaises(IntegrityError):service.import_offline(self.catalog,*self.spec.key,source)
        self.assertEqual(source.read_bytes(),DATA+b'x')
        source.write_bytes(b'x'*len(DATA))
        with self.assertRaises(IntegrityError):service.import_offline(self.catalog,*self.spec.key,source)
        self.assertFalse(service._paths(self.spec)[0].exists())
        source.write_bytes(DATA);linked=self.root/'linked-source'
        try:linked.symlink_to(source)
        except OSError as exc:self.skipTest(str(exc))
        with self.assertRaises(IntegrityError):service.import_offline(self.catalog,*self.spec.key,linked)
        self.assertEqual(source.read_bytes(),DATA)

    def test_expired_catalog_cannot_reuse_cached_or_offline_package(self):
        service=self.service();result=self.download(service)
        self.verifier.clock=lambda:datetime(2026,11,8,tzinfo=timezone.utc)
        with self.assertRaises(CatalogError):self.download(service)
        with self.assertRaises(CatalogError):service.import_offline(self.catalog,*self.spec.key,result.path)

    def test_expired_or_revoked_catalog_during_transfer_is_not_published(self):
        for revoke in (False,True):
            with self.subTest(revoke=revoke):
                self.verifier=CatalogVerifier(policy(self.key),lambda:NOW)
                service=self.service()
                def progress(received,total):
                    if revoke:self.verifier.policy=replace(self.verifier.policy,revoked_keys=frozenset({'test-key'}))
                    else:self.verifier.clock=lambda:datetime(2026,11,8,tzinfo=timezone.utc)
                with self.assertRaises(CatalogError):self.download(service,progress=progress)
                self.assertFalse(service._paths(self.spec)[0].exists())
                self.assertIsNone(self.registry.get(*self.spec.key))
                # 下一個子案例獨立驗證傳輸中的撤銷，不能重用已完整的片段。
                service._discard(service._paths(self.spec)[1],service._paths(self.spec)[2])

    def test_forged_verified_catalog_is_reverified_before_any_network(self):
        forged=replace(self.catalog,components=(replace(self.spec,source_url='https://other.invalid/evil'),))
        result=self.download(self.service())
        # 被替換的物件欄位不影響結果：服務重驗原始簽署封套，永不下載偽造 URL。
        result2=self.service().download(forged,*self.spec.key)
        self.assertEqual(result2.path,result.path)
        self.assertEqual(len(self.requests),1)

    def test_invalid_retry_configuration_is_rejected(self):
        for count in (0,6,True):
            with self.assertRaises(ValueError):self.service(attempts=count)

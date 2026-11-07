"""C07 真正 frozen 元件驗收：控制端不得安裝 OCR runtime，金鑰只存在記憶體。"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
import hashlib
from importlib import metadata, resources, util
import json
import os
from pathlib import Path
import platform
import tempfile
from threading import Event
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from desktop_app.capabilities import HostContext
from desktop_app.component_workers.binding import CPUWorkerBinding
from desktop_app.components.catalog import CatalogVerifier, TrustPolicy, canonical_json
from desktop_app.components.contracts import ComponentSpec, Version
from desktop_app.components.downloads import DownloadService
from desktop_app.components.lifecycle import ComponentManager
from desktop_app.components.registry import ComponentRegistry
from desktop_app.core import State
from desktop_app.resources import MIB, Policy


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def environment():
    """只列套件版本及可用性，不讀環境機密或使用者資料。"""
    return dict(packages={item.metadata['Name']: item.version for item in metadata.distributions()},
                native_available={name: util.find_spec(name) is not None
                                  for name in ('onnxruntime', 'rapidocr_onnxruntime', 'numpy', 'PIL', 'PySide6')})


def acceptance(package_directory, report_path):
    before = environment()
    require(not any(before['native_available'].values()), '控制端不得預先安裝原生 OCR／Qt 套件。')
    spec = ComponentSpec.from_dict(json.loads((package_directory/'component.json').read_bytes()))
    now = datetime.now(timezone.utc)
    stamp = lambda value: value.strftime('%Y-%m-%dT%H:%M:%SZ')
    key = Ed25519PrivateKey.generate()
    policy = TrustPolicy(1, 'c07-development', 1, {'ephemeral': key.public_key().public_bytes_raw()},
                         frozenset(), ('https://example.invalid',))
    payload = dict(schema_version=1, catalog_id='c07-development', revision=1, trust_policy_version=1,
                   issued_at=stamp(now-timedelta(minutes=1)), expires_at=stamp(now+timedelta(hours=1)),
                   components=[spec.to_dict()])
    envelope = canonical_json(dict(payload=payload, signature=dict(algorithm='ed25519', key_id='ephemeral',
                              value=base64.b64encode(key.sign(canonical_json(payload))).decode())))
    verifier = CatalogVerifier(policy)
    events = []
    health_observations = []
    with tempfile.TemporaryDirectory(prefix='markitdown-c07-acceptance-') as temporary:
        root = Path(temporary)/'中文受管環境'
        registry = ComponentRegistry(root/'state')
        binding = CPUWorkerBinding(root/'state/.locks/worker-use.lock', Policy(budget=2048*MIB, reserve=0))
        def actual_health(component, directory, host):
            result = binding.health(component, directory, host)
            health_observations.append(dict(staging=directory.is_relative_to(root/'state/lifecycle-staging'),
                                            passed=result.passed, message=result.detail))
            return result
        host = HostContext(platform.system().lower(), 'x86_64', Version.parse(metadata.version('markitdown-desktop')),
                           Version.parse('1.0.0'))
        manager = ComponentManager(registry, verifier, host, {'onnx.cpu.health': actual_health}, reserve_bytes=0)
        download = DownloadService(root/'cache', verifier, registry, reserve_bytes=0)
        cached = download.import_offline(envelope, *spec.key, package_directory/'onnx-cpu-ocr-development.zip')
        # PATH 留空，仍沿用 proxy／CA；實際 CPU 推論只能使用獨立包內 runtime。
        with patch.dict(os.environ, {'PATH': ''}):
            installed = manager.install(envelope, *spec.key, cached.path)
            require(installed.state == 'ready', '實際元件安裝失敗。')
            source = Path(resources.files('desktop_app').joinpath('data', 'worker-health.png'))
            destination = root/'English CPU.md'
            result = binding.run_managed(manager, envelope, source, destination,
                                         notify=lambda state, message: events.append(dict(state=state.value, message=message)))
            require(result.state == State.COMPLETED, result.message)
            require(result.pid != os.getpid() and result.report['runtime']['frozen'], '未使用真正獨立 frozen worker。')
            require(result.report['providers'] == ['CPUExecutionProvider']*3, '實際 provider 不是 CPU。')
            expected = json.loads(Path(resources.files('desktop_app').joinpath('data', 'worker-health.json')).read_bytes())['expected']
            require(expected in ' '.join(result.report['text'].split()), '英文辨識未達固定功能目標。')
            bad = root/'invalid.png'; bad.write_bytes(b'invalid image')
            bad_destination = root/'invalid.md'
            failed = binding.run_managed(manager, envelope, bad, bad_destination)
            require(failed.state == State.FAILED and not bad_destination.exists(), '無效影像未隔離。')
            next_result = binding.run_managed(manager, envelope, source, root/'after failure.md')
            require(next_result.state == State.COMPLETED, '前次引擎失敗污染後續工作。')
            cancel = Event()
            cancelled = binding.run_managed(manager, envelope, source, root/'cancelled.md', cancel=cancel,
                          notify=lambda state, message: cancel.set() if message.endswith('loading') else None)
            require(cancelled.state == State.CANCELLED and not (root/'cancelled.md').exists(), '原生程序取消／輸出保護失敗。')
            low = CPUWorkerBinding(manager.worker_guard_path, Policy(budget=MIB, reserve=0))
            runner = low.runner(spec, registry.installation_path(spec)); runner.resource_wait = 0.1
            insufficient = runner.run(operation='health')
            require(insufficient.state == State.FAILED and insufficient.pid is None, 'RAM 不足時仍啟動引擎。')
        original_manifest = registry.installation_path(spec)/'_internal/worker-assets/installed-manifest.json'
        native_manifest = registry.installation_path(spec)/'_internal/worker-assets/native/manifest.json'
        originals = json.loads(original_manifest.read_bytes()); natives = json.loads(native_manifest.read_bytes())
        result_report = result.report
        output = destination.read_bytes()
        manager.remove(*spec.key)
        require(not registry.installation_path(spec).exists(), '閒置元件移除未完成。')
    after = environment()
    require(before == after, '安裝或推論改動主控制端 Python 套件。')
    require(all(item['passed'] for item in health_observations) and len(health_observations) >= 2,
            '沒有 staging 與正式位置的實際 OCR 健康檢查。')
    require(any(item['staging'] for item in health_observations) and any(not item['staging'] for item in health_observations),
            '健康檢查位置不完整。')
    report_path.parent.mkdir(parents=True, exist_ok=True)
    (report_path.parent/'frozen-english-output.md').write_bytes(output)
    (report_path.parent/'frozen-worker-result.json').write_text(json.dumps(result_report, ensure_ascii=False, indent=2)+'\n')
    report = dict(recorded_at=now.isoformat(), source_version=metadata.version('markitdown-desktop'), accepted=True,
                  platform=platform.platform(), controller=before, controller_unchanged=before == after,
                  path_empty_during_install_health_and_inference=True, ephemeral_test_key_not_saved=True,
                  package_sha256=spec.package_sha256, package_bytes=spec.download_bytes,
                  unpacked_bytes=spec.unpacked_bytes, files=len(spec.files), health_checks=health_observations,
                  actual_worker_pid=result.pid, actual_providers=result_report['providers'], runtime=result_report['runtime'],
                  checks=['signed offline import', 'staging real CPU health', 'final real CPU health',
                          'managed real OCR lease', 'invalid PNG failure isolated', 'subsequent real OCR succeeds',
                          'cancel native worker without output', 'RAM rejection before spawn',
                          'remove idle real bundle', 'controller package environment unchanged'],
                  checks_passed=10, events=events, output_sha256=hashlib.sha256(output).hexdigest(),
                  installed_notice_packages=len(originals['packages']), installed_notice_files=len(originals['files']),
                  native_binary_records=len(natives['files']), native_copyright_packages=len(natives['native_copyrights']),
                  windows_executed=False, gpu_executed=False, traditional_chinese_quality_passed=False,
                  production_release=False)
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(accepted=True, checks=10, frozen=True, controller_native_packages=False), ensure_ascii=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--package-directory', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    acceptance(args.package_directory, args.report)

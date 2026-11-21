"""B3-3：用同一受管元件逐一驗證 GEOS 替換與損壞還原。"""
import hashlib
import json
from pathlib import Path
import shutil

from desktop_app.component_workers.geos_replacement import DIRECTORY, ERROR, LABEL, NAMES, STATUS
from desktop_app.components.lifecycle import LifecycleError
from desktop_app.components.registry import IntegrityError
from desktop_app.conversion import convert_document
from desktop_app.core import Request, State


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_replacements(manager, binding, envelope, spec, source, root, replacements, baseline):
    if baseline.state != State.COMPLETED or 'geos_replacement' in baseline.report['runtime']:
        raise AssertionError('Clean managed worker did not start normally')
    installed = manager.registry.installation_path(spec)
    managed = tuple(installed/'_internal/shapely.libs'/name for name in NAMES)
    bundled_sha = {path.name: sha(path) for path in managed}
    original = managed[0].read_bytes()
    try:
        managed[0].write_bytes(original + b'B3-3 integrity test')
        try:
            with manager.lease(envelope, spec.component_id):
                raise AssertionError('An overwritten managed GEOS passed the lease')
        except IntegrityError:
            pass
        plain = root/'basic.txt'
        output = root/'basic.md'
        plain.write_text('basic conversion', encoding='utf-8')
        convert_document(Request(plain, output), lambda: None)
        if output.read_text(encoding='utf-8') != 'basic conversion':
            raise AssertionError('Managed tampering affected basic conversion')
    finally:
        managed[0].write_bytes(original)

    directory = root/DIRECTORY
    directory.mkdir()
    try:
        expected = []
        for name in NAMES:
            target = directory/name
            shutil.copyfile(replacements/name, target)
            digest = sha(target)
            if digest == bundled_sha[name]:
                raise AssertionError('Replacement must differ from managed bytes')
            expected.append(dict(path=str(target), sha256=digest))
        health = binding.health(spec, installed, manager.host)
        if not health.passed or LABEL not in health.detail or any(
            file['path'] not in health.detail or file['sha256'] not in health.detail for file in expected
        ):
            raise AssertionError('Replacement health metadata missing')
        output = root/'replacement.md'
        replaced = binding.run_managed(manager, envelope, source, output)
        actual = (replaced.report or {}).get('runtime', {}).get('geos_replacement')
        if (replaced.state != State.COMPLETED or actual != dict(status=STATUS, files=expected)
                or 'WORKER HEALTH CHECK 12345' not in ' '.join(replaced.report['text'].split())):
            raise AssertionError('Real replacement OCR or module binding did not match: '+replaced.message)
        markdown = output.read_text(encoding='utf-8')
        if LABEL not in markdown or any(
            json.dumps(file['path'], ensure_ascii=False) not in markdown or file['sha256'] not in markdown
            for file in expected
        ):
            raise AssertionError('Replacement path and fingerprint missing from OCR output')
        (directory/NAMES[1]).write_bytes(b'not a DLL')
        failed = binding.health(spec, installed, manager.host)
        if failed.passed or ERROR not in failed.detail:
            raise AssertionError('Damaged replacement did not fail explicitly')
        try:
            binding.run_managed(manager, envelope, source, root/'damaged.md')
        except LifecycleError as exc:
            if ERROR not in str(exc):
                raise
        else:
            raise AssertionError('Damaged replacement did not fail the managed lease')
        if (root/'damaged.md').exists():
            raise AssertionError('Damaged GEOS published OCR output')
    finally:
        shutil.rmtree(directory)

    recovered = binding.run_managed(manager, envelope, source, root/'recovered.md')
    if (recovered.state != State.COMPLETED or 'geos_replacement' in recovered.report['runtime']
            or any(sha(path) != bundled_sha[path.name] for path in managed)):
        raise AssertionError('Removing the replacement did not restore managed OCR')
    return dict(clean_managed_ocr=True, tamper_rejected=True, basic_conversion=True,
                replacement_ocr=True, replacement_geometry=True, damaged_rejected=True,
                removal_restores_managed=True, managed_sha256=bundled_sha, replacement=actual)

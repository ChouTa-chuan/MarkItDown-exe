"""Windows CPU 選配與精簡控制端：沿用既有 hash／wheel METADATA，不重新解析版本。"""
import argparse
import json
from pathlib import Path
import tomllib

from packaging_profiles import load_metadata, closure, marker_environment, sha
from license_inventory import verify

ROOT = Path(__file__).resolve().parents[1]
ROOTS = {
    'build': ['rapidocr-onnxruntime==1.4.4', 'pyinstaller', 'setuptools'],
    'controller': ['setuptools'],
}
FORBIDDEN = {'pyside6', 'pyside6-essentials', 'shiboken6', 'markitdown', 'torch',
             'onnxruntime-gpu', 'reportlab', 'python-docx', 'pandas', 'magika'}


def expected_files(root=ROOT):
    parent, metadata = load_metadata(root, 'windows')
    inventory = verify(root/'packaging/requirements-windows.txt', root/'src/desktop_app/data/licenses/windows')
    licensed = {item['name']: item for item in inventory['packages']}
    environment = marker_environment('windows', '3.12.14')
    project = tomllib.loads((root/'pyproject.toml').read_text())['project']
    outputs = {}; profiles = {}
    for scope, tools in ROOTS.items():
        # 控制端必須滿足實際應用程式的基本相依與版號範圍；新增核心相依不能被舊清單漏掉。
        roots = [*project['dependencies'], *tools]
        names, edges = closure(roots, metadata, environment)
        forbidden = FORBIDDEN | ({'numpy', 'onnxruntime', 'rapidocr-onnxruntime', 'opencv-python', 'pillow'}
                                  if scope == 'controller' else set())
        if set(names) & forbidden: raise ValueError('CPU profile mixed unrelated runtime: '+scope)
        lines = ['# Windows CPython 3.12 CPU worker '+scope+'; fixed parent hashes and original wheel METADATA.',
                 '# python scripts/cpu_worker_profiles.py --generate; not native execution / release acceptance.']
        notices = {}
        for name in names:
            pin = parent[name]; lines.append(name+'=='+pin['version']+' \\')
            lines.extend('    --hash=sha256:'+value+(' \\' if i<len(pin['hashes'])-1 else '')
                         for i,value in enumerate(pin['hashes']))
            record = licensed[name]
            for path in [name+'/METADATA', *record['wheel_notice_files'],
                         *(item['path'] for item in record['supplemental_sources'])]:
                notices[path] = inventory['files'][path]
        path = 'packaging/profiles/cpu-windows-'+scope+'.txt'; raw = ('\n'.join(lines)+'\n').encode()
        outputs[path] = raw
        profiles[scope] = dict(lock=path, sha256=sha(raw), roots=roots, packages=names,
                               dependency_edges=edges, windows_notice_files=notices)
    report = dict(schema_version=1, id='cpu-worker-windows',
        source_version=project['version'],
        parent_sha256=sha((root/'packaging/requirements-windows.txt').read_bytes()), profiles=profiles,
        windows_executed=False, gpu_executed=False, release_ready=False,
        scope='Fixed Python dependency closure and existing original Windows notices; native binaries require actual build validation')
    outputs['packaging/profiles/cpu-windows-closure.json'] = (json.dumps(report,ensure_ascii=False,indent=2)+'\n').encode()
    return outputs, report


def verify_profiles(root=ROOT):
    outputs, report = expected_files(root)
    for path, raw in outputs.items():
        if (root/path).read_bytes()!=raw: raise ValueError('CPU profile output changed or expired: '+path)
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--generate',action='store_true')
    args=parser.parse_args();outputs,report=expected_files()
    if args.generate:
        for path,raw in outputs.items():(ROOT/path).write_bytes(raw)
    verify_profiles()
    print(json.dumps({scope:len(value['packages']) for scope,value in report['profiles'].items()}))

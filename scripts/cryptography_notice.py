"""A9b：綁定 cryptography 實際連結的 OpenSSL 與上游原文；不核准再散布。

讀的是 cryptography 的 OpenSSL API，不使用 CPython ssl、PE 字串或外層套件版本推測。
原文沿既有 supplemental_sources 複製，本模組負責版本、來源與隨包內容的二次檢核。
"""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'packaging/cryptography/openssl.json'
NOTICE = 'licenses/supplemental/cryptography.txt'
REPORT = 'licenses/cryptography-openssl.json'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root=ROOT):
    p = json.loads((root/PROFILE).read_text(encoding='utf-8'))
    require(p['schema_version'] == 1 and p['distribution'] == 'cryptography', 'Invalid cryptography notice profile')
    require(p['openssl_tag'] == 'openssl-'+p['expected_openssl_version'], 'OpenSSL version and official tag differ')
    source = root/p['notice']['path']
    require(source.is_file() and not source.is_symlink() and sha(source) == p['notice']['sha256'], 'OpenSSL original missing or changed')
    raw = source.read_bytes()
    require(hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest() == p['notice']['upstream_git_blob'], 'OpenSSL source Git blob differs')
    ref_path = root/p['official_ref']['path']
    require(sha(ref_path) == p['official_ref']['sha256'], 'OpenSSL official ref changed')
    ref = json.loads(ref_path.read_text(encoding='utf-8'))
    obj = ref['ref']['object']
    require(ref['ref']['ref'] == 'refs/tags/'+p['openssl_tag'], 'OpenSSL tag differs')
    for tag in ref['tags']:
        require(obj['type'] == 'tag' and obj['sha'] == tag['sha'], 'OpenSSL tag chain differs')
        obj = tag['object']
    require(obj['type'] == 'commit' and obj['sha'] == ref['commit'] == p['openssl_commit'], 'OpenSSL commit differs')
    return p


def observe():
    from cryptography.hazmat.backends.openssl.backend import backend
    from cryptography.hazmat.bindings import _rust
    binary = Path(_rust.__file__).resolve()
    dist = metadata.distribution('cryptography')
    require(binary.is_relative_to(Path(dist.locate_file('cryptography')).resolve()), 'OpenSSL API loaded outside cryptography distribution')
    number = backend.openssl_version_number()
    version = '.'.join(str(v) for v in ((number >> 28) & 15, (number >> 20) & 255, (number >> 4) & 255))
    text = backend.openssl_version_text()
    require(re.match(r'^OpenSSL '+re.escape(version)+r'(?:\s|$)', text), 'OpenSSL text/numeric API disagreement')
    return dict(platform=sys.platform,distribution_version=dist.version,version=version,version_text=text,
                version_number=number,binary=binary.name,binary_sha256=sha(binary),
                api='cryptography.hazmat.backends.openssl.backend: openssl_version_text / openssl_version_number')


def validate_observation(observed, profile):
    require(observed['distribution_version'] == profile['distribution_version']
            and observed['version'] == profile['expected_openssl_version'], 'Actual cryptography/OpenSSL version differs from original')
    number = observed['version_number']
    require(type(number) is int and '.'.join(str(v) for v in ((number >> 28)&15,(number >> 20)&255,(number >> 4)&255)) == observed['version'], 'OpenSSL numeric version differs')
    require(re.match(r'^OpenSSL '+re.escape(observed['version'])+r'(?:\s|$)',observed['version_text']), 'OpenSSL text version differs')
    require(observed['platform'] in ('win32','linux') and re.fullmatch('[0-9a-f]{64}',observed['binary_sha256']), 'Invalid runtime observation')


def verify(assets, packages, *, root=ROOT):
    p = load(root)
    rows = [r for r in packages if r['name'] == 'cryptography']
    require(len(rows) == 1 and rows[0]['version'] == p['distribution_version'], 'Missing actual cryptography package')
    refs = [r for r in rows[0]['supplemental_sources'] if r['path'] == NOTICE]
    require(len(refs) == 1 and refs[0]['sha256'] == p['notice']['sha256'], 'Missing OpenSSL supplemental binding')
    for row in packages:
        if row['name'] != 'cryptography':
            require(all(ref.get('path') != NOTICE for ref in row.get('supplemental_sources',[])), 'OpenSSL original bound to wrong package')
    path = assets/NOTICE
    require(path.is_file() and not path.is_symlink() and sha(path) == p['notice']['sha256'], 'Bundled OpenSSL original missing or changed')
    report = json.loads((assets/REPORT).read_text(encoding='utf-8'))
    require(report['check'] == 'cryptography-openssl' and report['profile_sha256'] == sha(root/PROFILE)
            and report['notice_sha256'] == p['notice']['sha256'] and report['redistribution_approved'] is False, 'Invalid bundled OpenSSL report')
    validate_observation(report['observed'],p)
    return report


def stage(root, assets, packages, observation=None):
    p = load(root)
    observed = observe() if observation is None else observation
    validate_observation(observed,p)
    report = dict(check='cryptography-openssl',schema_version=1,observed=observed,
                  profile_sha256=sha(root/PROFILE),notice_sha256=p['notice']['sha256'],openssl_tag=p['openssl_tag'],
                  openssl_commit=p['openssl_commit'],redistribution_approved=False)
    (assets/REPORT).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    return verify(assets,packages,root=root)


def publish(report):
    if os.environ.get('GITHUB_ACTIONS') == 'true':
        text = json.dumps(report,separators=(',',':'))
        require(len(text.encode()) < 3800,'OpenSSL observation exceeds annotation budget')
        print('::notice title=cryptography OpenSSL observation::'+text.replace('%','%25'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    p = load()
    observed = observe()
    validate_observation(observed,p)
    report = dict(check='cryptography-openssl',schema_version=1,observed=observed,profile_sha256=sha(ROOT/PROFILE),
                  notice_sha256=p['notice']['sha256'],openssl_tag=p['openssl_tag'],openssl_commit=p['openssl_commit'],redistribution_approved=False)
    require(not args.output.exists(), 'Output must be new')
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    publish(report)

"""離線交叉建置最小 Windows OCR 候選；不執行 PE、不安裝到主程式，也不核准發行。"""
import argparse
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tarfile

from desktop_app.components.registry import _chain, IntegrityError
from desktop_app.diagnostics import write_report
from desktop_app.native_assets import NativeAssetError, file_hash, inspect_pe, is_system_dll

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / 'packaging/native/minimal-windows.json'
NOTICES = ROOT / 'packaging/native/minimal-notices'
SOURCE_IDS = {'zlib', 'libpng', 'leptonica', 'tesseract'}
REQUIRED_NOTICES = {'tesseract-LICENSE.txt', 'leptonica-LICENSE.txt', 'libpng-LICENSE.txt',
                    'zlib-LICENSE.txt', 'toolchain-LLVM-LICENSE.TXT', 'libcxx-LICENSE.TXT',
                    'libcxxabi-LICENSE.TXT', 'libunwind-LICENSE.TXT', 'compiler-rt-LICENSE.TXT',
                    'toolchain-COPYING.MinGW-w64-runtime.txt', 'toolchain-COPYING.winpthreads.txt'}
MAX_MEMBERS = 12000
MAX_UNPACKED = 768 * 1024**2


def validate_contract(contract):
    """待驗候選不能經由資料旗標變成已完成的基本包或發行核准。"""
    if (contract.get('schema_version') != 1 or contract.get('recipe_version') != 1
            or contract.get('id') != 'tesseract-minimal-windows-amd64'
            or contract.get('target') != 'x86_64-w64-mingw32'):
        raise NativeAssetError('最小原生來源契約不符。')
    for flag in ('windows_executed', 'native_ocr_bundled', 'release_ready', 'redistribution_approved'):
        if contract.get(flag) is not False:
            raise NativeAssetError('來源契約不能宣稱執行、內含或發行核准。')
    sources = contract['source_archives']
    if len(sources) != 4 or {entry['id'] for entry in sources} != SOURCE_IDS:
        raise NativeAssetError('最小候選必須固定四項直接建置來源。')
    names = set()
    for entry in [*sources, contract['toolchain_archive'], *contract['notices']]:
        name = entry['file']
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.+-]{0,180}', name) or name.casefold() in names:
            raise NativeAssetError('來源檔名無效或重複。')
        names.add(name.casefold())
        if (not re.fullmatch('[0-9a-f]{64}', entry['sha256'])
                or type(entry['bytes']) is not int or not 0 < entry['bytes'] <= 128 * 1024**2):
            raise NativeAssetError('來源必須有固定大小與 SHA-256。')
        if 'archive_root' in entry and not re.fullmatch(r'[A-Za-z0-9_.+-]+', entry['archive_root']):
            raise NativeAssetError('封存根目錄無效。')
    if not REQUIRED_NOTICES <= {entry['file'] for entry in contract['notices']}:
        raise NativeAssetError('缺少原始授權／建置來源文字。')
    return contract


def verify_record(path, record):
    digest, size = file_hash(path)
    if (digest, size) != (record['sha256'], record['bytes']):
        raise NativeAssetError('固定來源完整性不符：' + record['file'])


def extract_archive(path, directory, archive_root):
    """對可信 hash 的封存檔仍設解包界限；只在全新私有目錄套用 data filter。"""
    directory = Path(directory)
    try:
        _chain(directory)
    except IntegrityError as exc:
        raise NativeAssetError('解包目錄不可含連結。') from exc
    if directory.exists():
        raise NativeAssetError('解包目錄必須尚未存在。')
    with tarfile.open(path) as archive:
        # 逐項讀取可在達上限時停止，避免先建立無界 member 清單。
        members = []
        total = 0
        for member in archive:
            parts = PurePosixPath(member.name).parts
            total += member.size
            if (not parts or parts[0] != archive_root or '..' in parts or '\\' in member.name
                    or member.size < 0 or total > MAX_UNPACKED or len(members) >= MAX_MEMBERS
                    or not (member.isfile() or member.isdir() or member.issym() or member.islnk())):
                raise NativeAssetError('封存路徑、類型或容量超出限制。')
            members.append(member)
        if not members:
            raise NativeAssetError('來源封存檔為空。')
        directory.mkdir()
        try:
            archive.extractall(directory, members=members, filter='data')
        except (tarfile.TarError, OSError) as exc:
            raise NativeAssetError('封存連結或內容未通過安全解包。') from exc
    return directory / archive_root


def recipes(prefix, link_map):
    """PNG 為既有逐頁 OCR 的固定輸入；其他外部編碼器、網路與訓練工具不引入。"""
    zlib = ['-DZLIB_LIBRARY=' + str(prefix / 'lib/libzs.a'),
            '-DZLIB_INCLUDE_DIR=' + str(prefix / 'include')]
    return {
        'zlib': ['-DZLIB_BUILD_SHARED=OFF', '-DZLIB_BUILD_STATIC=ON', '-DZLIB_BUILD_TESTING=OFF'],
        'libpng': [*zlib, '-DPNG_SHARED=OFF', '-DPNG_STATIC=ON', '-DPNG_TESTS=OFF',
                   '-DPNG_TOOLS=OFF', '-DPNG_DEBUG=OFF', '-DPNG_HARDWARE_OPTIMIZATIONS=OFF'],
        'leptonica': [*zlib, '-DBUILD_SHARED_LIBS=OFF', '-DBUILD_PROG=OFF', '-DSW_BUILD=OFF',
                      '-DSTRICT_CONF=ON', '-DENABLE_ZLIB=ON', '-DENABLE_PNG=ON',
                      *['-DENABLE_' + name + '=OFF' for name in ('GIF', 'JPEG', 'TIFF', 'WEBP', 'OPENJPEG')]],
        'tesseract': [
            # libc++ 新版不再間接提供 string／cstdlib；以標準標頭前置選項處理，不改上游檔案。
            '-DCMAKE_CXX_FLAGS=-include string -include cstdlib',
            # 此值由 Leptonica 的 ENABLE_TIFF=OFF 推得；不是執行 Windows 探針的結果。
            '-DLEPT_TIFF_RESULT=1', '-DBUILD_SHARED_LIBS=OFF', '-DBUILD_TRAINING_TOOLS=OFF',
            '-DBUILD_TESTS=OFF', '-DOPENMP_BUILD=OFF', '-DGRAPHICS_DISABLED=ON',
            '-DDISABLED_LEGACY_ENGINE=ON', '-DENABLE_NATIVE=OFF', '-DENABLE_LTO=OFF',
            '-DENABLE_CCACHE=OFF', '-DENABLE_PRECOMPILED_HEADERS=OFF', '-DINSTALL_CONFIGS=OFF',
            '-DDISABLE_TIFF=ON', '-DDISABLE_ARCHIVE=ON', '-DDISABLE_CURL=ON',
            '-DUSE_SYSTEM_ICU=OFF', '-DCMAKE_DISABLE_FIND_PACKAGE_PkgConfig=TRUE',
            '-DCMAKE_EXE_LINKER_FLAGS_RELEASE=-Wl,-Map,' + str(link_map) + ' -Wl,-verbose']}


def toolchain_text(tools, prefix):
    values = [('CMAKE_SYSTEM_NAME', 'Windows'), ('CMAKE_SYSTEM_PROCESSOR', 'AMD64'),
              ('CMAKE_C_COMPILER', tools / 'bin/x86_64-w64-mingw32-clang'),
              ('CMAKE_CXX_COMPILER', tools / 'bin/x86_64-w64-mingw32-clang++'),
              ('CMAKE_RC_COMPILER', tools / 'bin/x86_64-w64-mingw32-windres'),
              ('CMAKE_AR', tools / 'bin/llvm-ar'), ('CMAKE_RANLIB', tools / 'bin/llvm-ranlib'),
              ('CMAKE_STRIP', tools / 'bin/llvm-strip'),
              ('CMAKE_FIND_ROOT_PATH', str(prefix) + ';' + str(tools / 'x86_64-w64-mingw32')),
              ('CMAKE_FIND_ROOT_PATH_MODE_PROGRAM', 'NEVER'),
              ('CMAKE_FIND_ROOT_PATH_MODE_LIBRARY', 'ONLY'),
              ('CMAKE_FIND_ROOT_PATH_MODE_INCLUDE', 'ONLY'),
              ('CMAKE_FIND_ROOT_PATH_MODE_PACKAGE', 'ONLY'),
              ('CMAKE_EXE_LINKER_FLAGS', '-static -Wl,--no-insert-timestamp')]
    # 主機工具的路徑可能有空格；拒絕能改寫 CMake 字串／清單的特殊字元。
    for _, value in values:
        if any(c in str(value) for c in ('"', '\n', '\r', '$')):
            raise NativeAssetError('建置路徑含不支援的 CMake 字元。')
    return ''.join('set(' + key + ' "' + str(value) + '")\n' for key, value in values)


def inspect_candidate(path):
    digest, size = file_hash(path)
    data = Path(path).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise NativeAssetError('PE 解析前候選檔已變動。')
    pe = inspect_pe(data)
    dependencies = sorted(set(pe['imports'] + pe['delay_imports']))
    if pe['is_dll'] or any(not is_system_dll(name) for name in dependencies):
        raise NativeAssetError('最小入口不得是 DLL 或依賴未內含的第三方 DLL。')
    return dict(file='tesseract.exe', sha256=digest, bytes=size, **pe,
                third_party_dlls=[], windows_system_imports=dependencies)


def verify_configuration(work):
    """驗實際生成的標頭，避免僅靠傳入 OFF 旗標就宣稱外部能力已關閉。"""
    work = Path(work)
    paths = [work / 'build-leptonica/src/config_auto.h', work / 'build-tesseract/config_auto.h']
    texts = [path.read_text() for path in paths]
    definitions = [dict(re.findall(r'^#define\s+(\w+)\s+(\S+)', text, re.M)) for text in texts]
    lept, tess = definitions
    if any(lept.get(name) != '1' for name in ('HAVE_LIBPNG', 'HAVE_LIBZ')):
        raise NativeAssetError('最小候選缺少 PNG／zlib。')
    if any(name in lept for name in ('HAVE_LIBGIF', 'HAVE_LIBJP2K', 'HAVE_LIBJPEG', 'HAVE_LIBTIFF',
                                      'HAVE_LIBWEBP', 'HAVE_LIBWEBP_ANIM', 'HAVE_FMEMOPEN', 'HAVE_OPEN_MEMSTREAM')):
        raise NativeAssetError('Leptonica 混入其他編碼器或主機探針結果。')
    if any(name in tess for name in ('HAVE_LIBARCHIVE', 'HAVE_LIBCURL')):
        raise NativeAssetError('Tesseract 不應引入網路或封存相依。')
    if any(tess.get(name) != 'ON' for name in ('GRAPHICS_DISABLED', 'DISABLED_LEGACY_ENGINE')):
        raise NativeAssetError('最小 Tesseract 必須停用 ScrollView 與 legacy engine。')
    return [dict(file=str(path.relative_to(work)), sha256=file_hash(path)[0], definitions=value)
            for path, value in zip(paths, definitions)]


def verify_link_inputs(log, work, tools, leptonica_version):
    """從真實 linker verbose 紀錄追蹤靜態庫；map 的 member 名稱不足以證明原 archive。"""
    work, tools = Path(work).resolve(), Path(tools).resolve()
    declared = {
        (work / 'build-tesseract/libtesseract55.a').resolve(): 'tesseract',
        (work / ('prefix/lib/libleptonica-' + leptonica_version + '.dll')).resolve(): 'leptonica',
        (work / 'prefix/lib/libpng.a').resolve(): 'libpng',
        (work / 'prefix/lib/libzs.a').resolve(): 'zlib'}
    records = {}
    members = []
    for value in re.findall(r'^ld\.lld: Reading (.+)$', log, re.M):
        member = re.fullmatch(r'([^()]+\.(?:a|dll))\(([^()]+)\)', value)
        if member:
            members.append((Path(member[1]).name, member[2]))
            continue
        path = Path(value)
        if not path.is_absolute():
            path = work / 'build-tesseract' / path
        lexical = path
        path = path.resolve(strict=True)
        origin = declared.get(path)
        if path.is_relative_to(tools):
            origin = 'toolchain-runtime-or-system-import'
        elif path.is_relative_to(work / 'build-tesseract/CMakeFiles/tesseract.dir'):
            origin = 'tesseract'
        if origin is None:
            raise NativeAssetError('linker 引用未知來源：' + str(path))
        digest, size = file_hash(path)
        # libpng.a 是安裝器產生的本地別名；保留 linker 實際拼寫來對應後續 member。
        name = (str(lexical.relative_to(work)) if lexical.is_relative_to(work)
                else 'toolchain/' + str(lexical.relative_to(tools)))
        records[name] = dict(origin=origin, sha256=digest, bytes=size)
    origins = {entry['origin'] for entry in records.values()}
    if origins != SOURCE_IDS | {'toolchain-runtime-or-system-import'}:
        raise NativeAssetError('linker 紀錄未涵蓋全部固定來源。')
    for archive, member in members:
        matches = [name for name in records if Path(name).name == archive]
        if len(matches) != 1:
            raise NativeAssetError('linker member 無法對應唯一原始 archive：' + archive)
        records[matches[0]].setdefault('linked_members', []).append(member)
    return [dict(file=name, **record) for name, record in sorted(records.items())]


def build(inputs, work, cmake, ninja, jobs=2):
    if type(jobs) is not int or not 1 <= jobs <= 4:
        raise NativeAssetError('建置並行數須在 1–4 之間。')
    contract = validate_contract(json.loads(CONTRACT.read_text()))
    work = Path(work).absolute()
    try:
        _chain(work)
    except IntegrityError as exc:
        raise NativeAssetError('建置目錄不可含連結。') from exc
    if work.exists():
        raise NativeAssetError('建置目錄必須使用新路徑；失敗紀錄不覆寫。')
    if any(c in str(work) for c in (';', '"', '\n', '\r', '$', ',')):
        raise NativeAssetError('建置路徑含不支援的字元。')
    for record in [*contract['source_archives'], contract['toolchain_archive']]:
        verify_record(Path(inputs) / record['file'], record)
    for record in contract['notices']:
        verify_record(NOTICES / record['file'], record)
    cmake, ninja = Path(cmake).absolute(), Path(ninja).absolute()
    for executable, expected in [(cmake, 'cmake version ' + contract['required_cmake']),
                                 (ninja, contract['required_ninja'])]:
        result = subprocess.run([str(executable), '--version'], capture_output=True, text=True,
                                check=True, timeout=20)
        if result.stdout.splitlines()[0].strip() != expected:
            raise NativeAssetError('請使用契約固定的 CMake／Ninja；這些為明確指定的可信主機工具。')
    work.mkdir()
    sources = {}
    for record in [*contract['source_archives'], contract['toolchain_archive']]:
        # 在新目錄重新核對快照，避免驗完外部路徑後才讀到替換檔。
        snapshot = work / record['file']
        shutil.copyfile(Path(inputs) / record['file'], snapshot)
        verify_record(snapshot, record)
        sources[record['id']] = extract_archive(snapshot, work / ('source-' + record['id']), record['archive_root'])
    tools = sources.pop('toolchain')
    # 上游 CMake 使用 Windows 大小寫 Ws2_32；Linux 上的 import archive 名為小寫。
    # 只複製相同位元組的 import library 別名，不下載 DLL，也不修改上游原始碼。
    original = tools / 'x86_64-w64-mingw32/lib/libws2_32.a'
    alias = original.with_name('libWs2_32.a')
    if alias.exists():
        raise NativeAssetError('未預期的 Winsock import archive 別名。')
    shutil.copyfile(original, alias)
    alias_digest, alias_size = file_hash(alias)
    if (alias_digest, alias_size) != file_hash(original):
        raise NativeAssetError('Winsock 大小寫別名與固定來源不同。')
    prefix = work / 'prefix'
    chain = work / 'toolchain.cmake'
    chain.write_text(toolchain_text(tools, prefix))
    environment = {**os.environ, 'SOURCE_DATE_EPOCH': str(contract['source_date_epoch'])}
    # 取消指向主機 include／lib 的隱含輸入；Windows 目標只從隔離 prefix／工具鏈尋找。
    for name in ('CPATH', 'C_INCLUDE_PATH', 'CPLUS_INCLUDE_PATH', 'LIBRARY_PATH',
                 'CFLAGS', 'CXXFLAGS', 'LDFLAGS', 'CMAKE_PREFIX_PATH', 'PKG_CONFIG_PATH', 'PKG_CONFIG_LIBDIR'):
        environment.pop(name, None)
    commands = []

    def call(label, argv):
        commands.append(dict(label=label, argv=[str(arg) for arg in argv]))
        (work / 'commands.json').write_text(json.dumps(commands, ensure_ascii=False, indent=2) + '\n')
        with (work / (label + '.log')).open('wb') as log:
            subprocess.run(argv, cwd=work, env=environment, stdout=log, stderr=subprocess.STDOUT,
                           check=True, timeout=1200)

    for name, flags in recipes(prefix, work / 'tesseract-link.map').items():
        directory = work / ('build-' + name)
        call(name + '-configure', [str(cmake), '-S', str(sources[name]), '-B', str(directory),
             '-G', 'Ninja', '-DCMAKE_MAKE_PROGRAM=' + str(ninja), '-DCMAKE_TOOLCHAIN_FILE=' + str(chain),
             '-DCMAKE_BUILD_TYPE=Release', '-DCMAKE_INSTALL_PREFIX=' + str(prefix),
             '-DCMAKE_INSTALL_LIBDIR=lib', '-DCMAKE_PREFIX_PATH=' + str(prefix), *flags])
        call(name + '-build', [str(cmake), '--build', str(directory), '--parallel', str(jobs)])
        call(name + '-install', [str(cmake), '--install', str(directory)])
    configuration = verify_configuration(work)
    lept = next(entry for entry in contract['source_archives'] if entry['id'] == 'leptonica')
    link_inputs = verify_link_inputs((work / 'tesseract-build.log').read_text(), work, tools, lept['tag'])
    candidate = work / 'candidate'
    candidate.mkdir()
    entry = candidate / 'tesseract.exe'
    shutil.copyfile(work / 'build-tesseract/bin/tesseract.exe', entry)
    call('strip', [str(tools / 'bin/llvm-strip'), str(entry)])
    for record in contract['notices']:
        target = candidate / 'notices' / record['file']
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(NOTICES / record['file'], target)
        verify_record(target, record)
    report = dict(check='C03-minimal-source', source_version=metadata.version('markitdown-desktop'),
                  recorded_at=datetime.now(timezone.utc).isoformat(), cross_build_complete=True,
                  candidate=inspect_candidate(entry), source_archives=contract['source_archives'],
                  toolchain_archive=contract['toolchain_archive'], notices=contract['notices'],
                  toolchain_import_alias=dict(original=str(original.relative_to(tools)),
                                              alias=str(alias.relative_to(tools)),
                                              sha256=alias_digest, bytes=alias_size),
                  configuration=configuration,
                  link_inputs=link_inputs, link_map_sha256=file_hash(work / 'tesseract-link.map')[0],
                  source_contract_sha256=file_hash(CONTRACT)[0],
                  source_evidence_prepared=True, windows_executed=False, gpu_executed=False,
                  authenticode_verified=False, dynamic_loading_verified=False,
                  native_ocr_bundled=False, full_c03_complete=False, redistribution_approved=False,
                  release_ready=False, scope='Linux cross build and static/source evidence only; no Windows OCR or application bundle acceptance')
    (candidate / 'provenance.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inputs', type=Path, required=True)
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--cmake', type=Path, required=True, help='可信主機 CMake 3.31.6')
    parser.add_argument('--ninja', type=Path, required=True, help='可信主機 Ninja 1.11.1')
    parser.add_argument('--jobs', type=int, default=2)
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if args.report.exists() or args.report.is_symlink():
        parser.error('報告已存在；請選新檔名。')
    try:
        report = build(args.inputs, args.work, args.cmake, args.ninja, args.jobs)
        write_report(report, args.report)
        print('Cross build complete; third-party DLLs: 0; Windows execution and redistribution remain unapproved')
        return 0
    except (ValueError, OSError, KeyError, tarfile.TarError, subprocess.SubprocessError) as exc:
        write_report(dict(check='C03-minimal-source', cross_build_complete=False, release_ready=False,
                          native_ocr_bundled=False, windows_executed=False, full_c03_complete=False,
                          error=f'{type(exc).__name__}: {exc}'), args.report)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())

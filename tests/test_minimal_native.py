"""離線最小候選的來源、解包與 PE 邊界；合成資料不當成 Windows OCR 驗收。"""
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_minimal_native as native
from test_native_assets import pe_fixture


class MinimalNativeTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.contract = json.loads(native.CONTRACT.read_text())

    def archive(self, names=('source/file.txt',), *, kind=None, size=5):
        path = self.root / 'source.tar'
        with tarfile.open(path, 'w') as archive:
            for name in names:
                item = tarfile.TarInfo(name)
                if kind == 'symlink':
                    item.type = tarfile.SYMTYPE
                    item.linkname = '../../escaped'
                elif kind == 'device':
                    item.type = tarfile.CHRTYPE
                else:
                    item.size = size
                archive.addfile(item, io.BytesIO(b'x' * size) if item.isfile() else None)
        return path

    def configuration(self):
        lept = self.root / 'build-leptonica/src/config_auto.h'
        lept.parent.mkdir(parents=True)
        lept.write_text('#define HAVE_LIBPNG 1\n#define HAVE_LIBZ 1\n/* #undef HAVE_LIBTIFF */\n')
        tess = self.root / 'build-tesseract/config_auto.h'
        tess.parent.mkdir()
        tess.write_text('#define GRAPHICS_DISABLED ON\n#define DISABLED_LEGACY_ENGINE ON\n')
        return lept, tess

    def test_fixed_contract_does_not_approve_windows_or_release(self):
        result = native.validate_contract(self.contract)
        self.assertEqual({entry['id'] for entry in result['source_archives']}, native.SOURCE_IDS)
        self.assertFalse(result['windows_executed'])
        self.assertFalse(result['redistribution_approved'])

    def test_forged_data_flags_are_rejected(self):
        for flag in ('windows_executed', 'native_ocr_bundled', 'release_ready', 'redistribution_approved'):
            with self.subTest(flag=flag):
                contract = deepcopy(self.contract)
                contract[flag] = True
                with self.assertRaises(native.NativeAssetError):
                    native.validate_contract(contract)

    def test_missing_component_or_runtime_notice_is_rejected(self):
        for field in ('source_archives', 'notices'):
            contract = deepcopy(self.contract)
            contract[field] = []
            with self.assertRaises(native.NativeAssetError):
                native.validate_contract(contract)

    def test_real_original_notices_match_all_fixed_hashes(self):
        for entry in self.contract['notices']:
            native.verify_record(native.NOTICES / entry['file'], entry)

    def test_altered_file_and_link_cannot_match_fixed_record(self):
        path = self.root / 'notice.txt'
        path.write_bytes(b'original')
        record = dict(file='notice.txt', sha256=hashlib.sha256(b'original').hexdigest(), bytes=8)
        native.verify_record(path, record)
        path.write_bytes(b'changed!')
        with self.assertRaises(native.NativeAssetError):
            native.verify_record(path, record)
        link = self.root / 'link.txt'
        link.symlink_to(path)
        with self.assertRaises(native.NativeAssetError):
            native.verify_record(link, record)

    def test_regular_archive_extracts_inside_new_directory(self):
        result = native.extract_archive(self.archive(), self.root / 'extract', 'source')
        self.assertEqual((result / 'file.txt').read_bytes(), b'xxxxx')

    def test_wrong_archive_root_is_rejected(self):
        with self.assertRaises(native.NativeAssetError):
            native.extract_archive(self.archive(['other/file.txt']), self.root / 'extract', 'source')

    def test_archive_parent_and_absolute_paths_are_rejected(self):
        for name in ('source/../../escaped', '/source/escaped', 'source\\escaped'):
            with self.subTest(name=name), self.assertRaises(native.NativeAssetError):
                native.extract_archive(self.archive([name]), self.root / 'extract', 'source')
        self.assertFalse((self.root / 'escaped').exists())

    def test_escape_symlink_is_rejected(self):
        with self.assertRaises(native.NativeAssetError):
            native.extract_archive(self.archive(kind='symlink'), self.root / 'extract', 'source')

    def test_archive_special_device_is_rejected(self):
        with self.assertRaises(native.NativeAssetError):
            native.extract_archive(self.archive(kind='device'), self.root / 'extract', 'source')

    def test_archive_byte_and_member_limits_are_enforced(self):
        path = self.archive(['source/first', 'source/second'])
        for limit, value in [('MAX_UNPACKED', 4), ('MAX_MEMBERS', 1)]:
            with patch.object(native, limit, value), self.assertRaises(native.NativeAssetError):
                native.extract_archive(path, self.root / 'extract', 'source')

    def test_existing_archive_destination_preserves_user_file(self):
        directory = self.root / 'extract'
        directory.mkdir()
        marker = directory / 'user.txt'
        marker.write_text('keep')
        with self.assertRaises(native.NativeAssetError):
            native.extract_archive(self.archive(), directory, 'source')
        self.assertEqual(marker.read_text(), 'keep')

    def test_candidate_accepts_only_static_system_import_classification(self):
        entry = self.root / 'tesseract.exe'
        entry.write_bytes(pe_fixture(['KERNEL32.dll', 'api-ms-win-crt-runtime-l1-1-0.dll']))
        result = native.inspect_candidate(entry)
        self.assertEqual(result['third_party_dlls'], [])
        self.assertEqual(result['machine'], 'AMD64')

    def test_candidate_cannot_hide_third_party_delay_import(self):
        entry = self.root / 'tesseract.exe'
        entry.write_bytes(pe_fixture(['kernel32.dll'], delayed=['libpng16.dll']))
        with self.assertRaises(native.NativeAssetError):
            native.inspect_candidate(entry)

    def test_candidate_must_be_exe_not_dll(self):
        entry = self.root / 'tesseract.exe'
        entry.write_bytes(pe_fixture(dll=True))
        with self.assertRaises(native.NativeAssetError):
            native.inspect_candidate(entry)

    def test_generated_headers_prove_png_and_disabled_capabilities(self):
        self.configuration()
        result = native.verify_configuration(self.root)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['definitions']['HAVE_LIBPNG'], '1')

    def test_missing_png_is_rejected_even_with_valid_pe(self):
        lept, _ = self.configuration()
        lept.write_text('#define HAVE_LIBZ 1\n')
        with self.assertRaises(native.NativeAssetError):
            native.verify_configuration(self.root)

    def test_host_probe_and_extra_codecs_or_network_are_rejected(self):
        lept, tess = self.configuration()
        for target, name in [(lept, 'HAVE_OPEN_MEMSTREAM'), (lept, 'HAVE_LIBTIFF'), (tess, 'HAVE_LIBCURL')]:
            original = target.read_text()
            target.write_text(original + '#define ' + name + ' 1\n')
            with self.subTest(name=name), self.assertRaises(native.NativeAssetError):
                native.verify_configuration(self.root)
            target.write_text(original)

    def test_existing_work_is_rejected_before_invoking_tools(self):
        marker = self.root / 'user.txt'
        marker.write_text('keep')
        with patch.object(native.subprocess, 'run') as run, self.assertRaises(native.NativeAssetError):
            native.build(self.root, self.root, 'not-used', 'not-used')
        run.assert_not_called()
        self.assertEqual(marker.read_text(), 'keep')

    def test_invalid_jobs_are_rejected_before_any_io(self):
        for jobs in (0, 5, True, '2'):
            with self.subTest(jobs=jobs), self.assertRaises(native.NativeAssetError):
                native.build('not-used', 'not-used', 'not-used', 'not-used', jobs)

    def link_fixture(self):
        files = ['build-tesseract/libtesseract55.a', 'prefix/lib/libleptonica-1.87.0.dll',
                 'prefix/lib/libpng.a', 'prefix/lib/libzs.a', 'tools/lib/runtime.a']
        lines = []
        for name in files:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b'synthetic archive marker, never linked or executed')
            lines.append('ld.lld: Reading ' + str(path))
        return '\n'.join(lines)

    def test_linker_origins_cover_four_sources_and_toolchain(self):
        log = self.link_fixture() + '\nld.lld: Reading libtesseract55.a(baseapi.cpp.obj)\nld.lld: Reading libpng.a(png.c.obj)'
        alias = self.root / 'prefix/lib/libpng.a'
        original = alias.with_name('libpng16.a')
        alias.rename(original)
        alias.symlink_to(original.name)
        records = native.verify_link_inputs(log, self.root, self.root / 'tools', '1.87.0')
        self.assertEqual(len(records), 5)
        self.assertEqual({entry['origin'] for entry in records},
                         native.SOURCE_IDS | {'toolchain-runtime-or-system-import'})
        self.assertEqual(next(entry for entry in records if entry['origin'] == 'tesseract')['linked_members'],
                         ['baseapi.cpp.obj'])

    def test_linker_missing_source_and_unknown_host_library_are_rejected(self):
        log = self.link_fixture()
        with self.assertRaises(native.NativeAssetError):
            native.verify_link_inputs('\n'.join(log.splitlines()[:-1]), self.root, self.root / 'tools', '1.87.0')
        unknown = self.root / 'unapproved.a'
        unknown.write_bytes(b'host artifact')
        with self.assertRaises(native.NativeAssetError):
            native.verify_link_inputs(log + '\nld.lld: Reading ' + str(unknown),
                                      self.root, self.root / 'tools', '1.87.0')
        with self.assertRaises(native.NativeAssetError):
            native.verify_link_inputs(log + '\nld.lld: Reading unlisted.a(member.o)',
                                      self.root, self.root / 'tools', '1.87.0')


if __name__ == '__main__':
    unittest.main()

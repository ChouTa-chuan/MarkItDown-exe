"""有界 PE／固定來源與發布門檻；合成 PE 只驗靜態解析，不冒充 Windows 執行。"""
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from desktop_app.native_assets import inspect_pe,inspect_windows_assets,require_bundle_permission,NativeAssetError,file_hash


def pe_fixture(imports=(),*,dll=False,delayed=()):
    data=bytearray(0x1000);data[:2]=b'MZ';struct.pack_into('<I',data,0x3c,0x80);data[0x80:0x84]=b'PE\0\0'
    struct.pack_into('<HHIIIHH',data,0x84,0x8664,1,0,0,0,0xf0,0x2022 if dll else 0x22)
    opt=0x98;struct.pack_into('<H',data,opt,0x20b);struct.pack_into('<Q',data,opt+24,0x140000000)
    struct.pack_into('<I',data,opt+60,0x200);struct.pack_into('<I',data,opt+108,16)
    struct.pack_into('<8sIIIIIIHHI',data,opt+0xf0,b'.rdata\0\0',0xe00,0x1000,0xe00,0x200,0,0,0,0,0x40000040)
    if imports:
        struct.pack_into('<II',data,opt+112+8,0x1000,(len(imports)+1)*20)
        for index,name in enumerate(imports):
            name_offset=0x600+index*260;raw=name.encode()+b'\0';data[name_offset:name_offset+len(raw)]=raw
            struct.pack_into('<IIIII',data,0x200+index*20,0x1300,0,0,name_offset+0xe00,0x1300)
    if delayed:
        struct.pack_into('<II',data,opt+112+13*8,0x1100,(len(delayed)+1)*32)
        for index,name in enumerate(delayed):
            name_offset=0xa00+index*260;raw=name.encode()+b'\0';data[name_offset:name_offset+len(raw)]=raw
            struct.pack_into('<IIIIIIII',data,0x300+index*32,1,name_offset+0xe00,0,0,0,0,0,0)
    return bytes(data)


class PEInspectionTests(unittest.TestCase):
    def test_normal_and_delayed_imports_include_mingw_cpp_name(self):
        report=inspect_pe(pe_fixture(['KERNEL32.dll','libstdc++-6.dll'],delayed=['USER32.dll']))
        self.assertEqual(report['imports'],['kernel32.dll','libstdc++-6.dll'])
        self.assertEqual(report['delay_imports'],['user32.dll']);self.assertFalse(report['is_dll'])

    def test_dll_flag_and_no_import_data_dll(self):
        self.assertTrue(inspect_pe(pe_fixture(dll=True))['is_dll'])

    def test_x86_and_arm_are_rejected(self):
        for machine in [0x14c,0xaa64]:
            data=bytearray(pe_fixture());struct.pack_into('<H',data,0x84,machine)
            with self.assertRaisesRegex(NativeAssetError,'AMD64'):inspect_pe(data)

    def test_bad_signature_and_truncated_header_rejected(self):
        for data in [b'',b'MZ',b'ELF'+bytes(256),pe_fixture()[:200]]:
            with self.assertRaises(NativeAssetError):inspect_pe(data)

    def test_bad_rva_cannot_read_unrelated_file_bytes(self):
        data=bytearray(pe_fixture(['kernel32.dll']));struct.pack_into('<I',data,0x20c,0xf0000000)
        with self.assertRaisesRegex(NativeAssetError,'RVA'):inspect_pe(data)

    def test_invalid_name_and_path_are_rejected(self):
        for name in ['../outside.dll','C:/outside.dll','bad name.dll']:
            with self.assertRaises(NativeAssetError):inspect_pe(pe_fixture([name]))

    def test_unterminated_descriptor_is_rejected(self):
        data=bytearray(pe_fixture(['kernel32.dll']));struct.pack_into('<I',data,0x98+112+8+4,20)
        with self.assertRaisesRegex(NativeAssetError,'終止'):inspect_pe(data)

    def test_invalid_delay_attribute_is_rejected(self):
        data=bytearray(pe_fixture(delayed=['user32.dll']));struct.pack_into('<I',data,0x300,0)
        with self.assertRaisesRegex(NativeAssetError,'延遲匯入'):inspect_pe(data)

    def test_section_beyond_file_and_ambiguous_mapping_rejected(self):
        data=bytearray(pe_fixture());struct.pack_into('<I',data,0x188+16,0xfffffff)
        with self.assertRaises(NativeAssetError):inspect_pe(data)
        data=bytearray(pe_fixture(['kernel32.dll']));struct.pack_into('<H',data,0x86,2)
        data[0x1b0:0x1d8]=data[0x188:0x1b0]
        with self.assertRaisesRegex(NativeAssetError,'RVA'):inspect_pe(data)


class NativePinTests(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup);self.root=Path(temporary.name)
        self.installer=self.root/'setup.exe';self.installer.write_bytes(b'synthetic archive, never executed')
        self.directory=self.root/'payload';self.directory.mkdir();(self.directory/'doc').mkdir()
        (self.directory/'doc/LICENSE').write_text('Synthetic notice for Tesseract only')
        (self.directory/'tesseract.exe').write_bytes(pe_fixture(['KERNEL32.dll','engine.dll']))
        (self.directory/'engine.dll').write_bytes(pe_fixture(['USER32.dll','tesseract-helper.dll'],dll=True))
        (self.directory/'tesseract-helper.dll').write_bytes(pe_fixture(['engine.dll'],dll=True))
        self.pin=dict(schema_version=1,id='tesseract-windows-x64',version='fixture',entrypoint='tesseract.exe',
            installer=self.record(self.installer),runtime_files={p.name:self.record(p) for p in sorted(self.directory.glob('*.*'))},
            notice_files={'doc/LICENSE':self.record(self.directory/'doc/LICENSE')},
            license_evidence={'tesseract.exe':'doc/LICENSE'},redistribution_approved=False)

    def record(self,path):
        return dict(sha256=hashlib.sha256(path.read_bytes()).hexdigest(),bytes=path.stat().st_size)

    def inspect(self):return inspect_windows_assets(self.installer,self.directory,self.pin)

    def test_dependency_cycles_resolve_without_executing_and_gaps_remain(self):
        report=self.inspect();self.assertEqual(len(report['reachable_files']),3)
        self.assertEqual(report['missing_license_evidence'],['engine.dll','tesseract-helper.dll'])
        self.assertFalse(report['windows_executed']);self.assertFalse(report['bundle_allowed'])

    def test_modified_installer_rejected(self):
        self.installer.write_bytes(b'changed')
        with self.assertRaisesRegex(NativeAssetError,'安裝來源'):self.inspect()

    def test_modified_runtime_rejected(self):
        (self.directory/'engine.dll').write_bytes(b'changed')
        with self.assertRaisesRegex(NativeAssetError,'完整性'):self.inspect()

    def test_missing_local_dependency_cannot_use_path_fallback(self):
        del self.pin['runtime_files']['engine.dll']
        with self.assertRaisesRegex(NativeAssetError,'相依 DLL'):self.inspect()

    def test_notice_tampering_rejected(self):
        (self.directory/'doc/LICENSE').write_text('changed')
        with self.assertRaisesRegex(NativeAssetError,'原始授權'):self.inspect()

    def test_case_collisions_and_symlinks_rejected(self):
        self.pin['runtime_files']['ENGINE.DLL']=self.pin['runtime_files']['engine.dll']
        with self.assertRaisesRegex(NativeAssetError,'大小寫衝突'):self.inspect()
        del self.pin['runtime_files']['ENGINE.DLL']
        target=self.directory/'engine.dll';saved=target.read_bytes();target.unlink()
        other=self.root/'other';other.write_bytes(saved);target.symlink_to(other)
        with self.assertRaises(ValueError):self.inspect()

    def test_dll_type_and_declared_entry_are_checked(self):
        path=self.directory/'engine.dll';path.write_bytes(pe_fixture());self.pin['runtime_files']['engine.dll']=self.record(path)
        with self.assertRaisesRegex(NativeAssetError,'類型'):self.inspect()

    def test_data_flags_cannot_approve_unreviewed_package(self):
        with self.assertRaisesRegex(NativeAssetError,'尚未核准'):require_bundle_permission(dict(bundle_allowed=True,redistribution_approved=True))
        self.pin['redistribution_approved']=True
        with self.assertRaisesRegex(NativeAssetError,'契約'):self.inspect()

    def test_fixed_notice_reference_must_exist(self):
        self.pin['license_evidence']['engine.dll']='not-listed'
        with self.assertRaisesRegex(NativeAssetError,'證據引用'):self.inspect()

    def test_file_byte_limit_is_enforced(self):
        with self.assertRaises(NativeAssetError):file_hash(self.installer,1)

    def test_real_pin_stays_unapproved_and_has_expected_entry(self):
        pin=json.loads((Path(__file__).parents[1]/'packaging/native/tesseract-windows.json').read_text())
        self.assertEqual(pin['installer']['sha256'],'bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4')
        self.assertEqual(len(pin['runtime_files']),56);self.assertFalse(pin['redistribution_approved'])

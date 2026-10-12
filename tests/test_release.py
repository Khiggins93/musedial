import hashlib,json,shutil,struct,subprocess,sys,tempfile,unittest,zlib
from unittest.mock import patch
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from halloween_format import validate_assets,partition_image,layout
from flash import validate_release,validate_backup,read_backup,SEGMENTS

class Resources(unittest.TestCase):
    def test_committed_resource(self):
        data=(ROOT/'assets/halloween.bin').read_bytes();meta=validate_assets(data)
        self.assertEqual(meta['sha256'],json.loads((ROOT/'dependencies.lock.json').read_text())['assets_sha256'])
    def test_corruption_and_truncation(self):
        data=(ROOT/'assets/halloween.bin').read_bytes()
        for bad in (data[:47],data[:-1],data[:-1]+bytes([data[-1]^1])):
            with self.assertRaises(ValueError):validate_assets(bad)
    def test_bounds_even_with_valid_crc(self):
        data=bytearray((ROOT/'assets/halloween.bin').read_bytes());struct.pack_into('<I',data,52,0xffffffff);struct.pack_into('<I',data,44,zlib.crc32(data[48:]))
        with self.assertRaises(ValueError):validate_assets(data)
    def test_exact_partition_layouts(self):
        self.assertEqual(layout(partition_image(True)),'halloween')
        with self.assertRaises(ValueError):layout(partition_image(True)[:-1])

class Release(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)
        self.data={'bootloader.bin':b'\xe9boot','partitions.bin':partition_image(True),'boot_app0.bin':b'\xff'*8192,'application.bin':b'\xe9app','halloween.bin':(ROOT/'assets/halloween.bin').read_bytes()}
        self.m={'version':'test','board':'M5Stack Dial','chip':'esp32s3','flash_bytes':8388608,'files':[]}
        for name,data in self.data.items():
            (self.path/name).write_bytes(data)
            self.m['files'].append({'name':name,'offset':SEGMENTS[name][0],'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):(self.path/'manifest.json').write_text(json.dumps(self.m))
    def test_valid(self):validate_release(self.path)
    def test_modified_bytes(self):
        (self.path/'application.bin').write_bytes(b'bad')
        with self.assertRaises(ValueError):validate_release(self.path)
    def test_arbitrary_offset(self):
        self.m['files'][0]['offset']=0x9000;self.save()
        with self.assertRaises(ValueError):validate_release(self.path)
    def test_traversal_or_duplicate_segment(self):
        for name in ('../outside.bin','application.bin'):
            self.m['files'][0]['name']=name;self.save()
            with self.assertRaises(ValueError):validate_release(self.path)
    def test_wrong_board(self):
        self.m['flash_bytes']=4194304;self.save()
        with self.assertRaises(ValueError):validate_release(self.path)
    def test_wrong_device_backup(self):
        (self.path/'flash.bin').write_bytes(b'\xff'*8388608)
        (self.path/'backup.json').write_text(json.dumps({'mac':'test-device-a','chip':'esp32s3','bytes':8388608,'sha256':hashlib.sha256(b'\xff'*8388608).hexdigest()}))
        with self.assertRaises(ValueError):validate_backup(self.path,'test-device-b')
        validate_backup(self.path,'test-device-a')
        (self.path/'flash.bin').write_bytes(b'bad')
        with self.assertRaises(ValueError):validate_backup(self.path,'test-device-a')

class Input(unittest.TestCase):
    @unittest.skipUnless(shutil.which('g++'),'Host C++ compiler unavailable; device selftests remain required')
    def test_boundaries_and_wrap(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/('inputs.exe' if sys.platform=='win32' else 'inputs')
            subprocess.run(['g++','-std=c++11','-I',str(ROOT/'firmware/MuseDial'),str(ROOT/'tests/input_test.cpp'),'-o',str(exe)],check=True)
            subprocess.run([str(exe)],check=True)
    def test_palette_and_sdk_removal(self):
        source=(ROOT/'firmware/MuseDial/MuseDial.ino').read_text()
        self.assertIn('0xa77dff,0x5cb8ff,0xe07bff,0x6ff0bf,0x7c72d0,0xa77dff,0xa77dff,0x5cb8ff,0x7c72d0',source)
        self.assertNotIn('muse_pixel',source)
        self.assertFalse((ROOT/'firmware/MuseDial/muse_pixel.c').exists())

class BackupRead(unittest.TestCase):
    class Stub:
        def __init__(self,fail=False):self.fail=fail;self.closed=False;self._port=self
        def close(self):self.closed=True
        def read_flash(self,offset,size):
            if self.fail:raise RuntimeError('Simulated USB interruption')
            return b'\xff'*size
        def flash_md5sum(self,offset,size):return hashlib.md5(b'\xff'*size).hexdigest()
    def test_retry_preserves_verified_bytes(self):
        old=self.Stub(True);new=self.Stub()
        with patch('flash.connect',return_value=(new,'test-device')),patch('flash.time.sleep'):
            data=read_backup(old,'test-device','test-port')
        self.assertEqual(len(data),8388608);self.assertTrue(old.closed and new.closed)
    def test_reconnect_rejects_another_device(self):
        old=self.Stub(True);new=self.Stub()
        with patch('flash.connect',return_value=(new,'other-device')),patch('flash.time.sleep'):
            with self.assertRaises(ValueError):read_backup(old,'test-device','test-port')
        self.assertTrue(old.closed and new.closed)
if __name__=='__main__':unittest.main()

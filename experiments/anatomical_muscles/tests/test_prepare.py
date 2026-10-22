import hashlib
from pathlib import Path
import tempfile
import unittest
from experiments.anatomical_muscles.prepare import copy_experiment

class PreparationTests(unittest.TestCase):
    def test_copy_is_exact_and_source_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'original.blend'; dst=Path(d)/'test.blend'
            src.write_bytes(b'BLENDER-test-fixture')
            sha=hashlib.sha256(src.read_bytes()).hexdigest()
            report=copy_experiment(src,dst,sha)
            self.assertEqual(src.read_bytes(),dst.read_bytes())
            self.assertEqual(report['source_sha256'],sha)
            self.assertFalse(report['blender_executed'])
    def test_wrong_hash_and_alias_and_existing_destination_refused(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'original.blend'; dst=Path(d)/'test.blend'
            src.write_bytes(b'BLENDER-test-fixture')
            sha=hashlib.sha256(src.read_bytes()).hexdigest()
            with self.assertRaises(ValueError): copy_experiment(src,dst,'0'*64)
            self.assertFalse(dst.exists())
            with self.assertRaises(ValueError): copy_experiment(src,src,sha)
            dst.symlink_to(src)
            with self.assertRaises(ValueError): copy_experiment(src,dst,sha)
            dst.unlink(); dst.write_bytes(b'keep')
            with self.assertRaises(FileExistsError): copy_experiment(src,dst,sha)
            self.assertEqual(dst.read_bytes(),b'keep')
    def test_zstd_compressed_blender_copy(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/"compressed.blend"; dst=Path(d)/"test.blend"
            src.write_bytes(bytes.fromhex("28b52ffd")+b"synthetic")
            sha=hashlib.sha256(src.read_bytes()).hexdigest()
            copy_experiment(src,dst,sha)
            self.assertEqual(dst.read_bytes(),src.read_bytes())

    def test_lfs_pointer_refused(self):
        with tempfile.TemporaryDirectory() as d:
            src=Path(d)/'pointer.blend'; src.write_bytes(b'version https://git-lfs.github.com/spec/v1')
            with self.assertRaises(ValueError): copy_experiment(src,Path(d)/'test.blend',hashlib.sha256(src.read_bytes()).hexdigest())

if __name__=='__main__': unittest.main()

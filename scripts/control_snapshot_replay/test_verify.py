"""Synthetic byte-integrity guards; not native anatomy/render validation."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

PATH = Path(__file__).with_name('verify.py')


class SnapshotReplayVerificationTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PATH.exists(), 'snapshot replay verifier missing')
        spec = importlib.util.spec_from_file_location('verify_snapshots', PATH)
        self.mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.mod)
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.manifest = {'source_sha256': self.mod.W8_SHA,
                         'status': 'ACTUAL_BLENDER_RENDER_OF_FROZEN_EVALUATED_GEOMETRY_NOT_REPAIR',
                         'original_blend_opened_by_renderer': False, 'saved_blend': False,
                         'anatomical_approval': False, 'samples': []}
        for sample in (0, 6):
            rows = []
            for condition in self.mod.CONDITIONS:
                name = f'sample{sample:02d}__{condition}.npz'
                data = name.encode() # invented bytes, not claimed to be native NPZs
                (self.root/name).write_bytes(data)
                rows.append({'condition': condition, 'snapshot_npz_sha256': hashlib.sha256(data).hexdigest()})
            self.manifest['samples'].append({'sample': sample, 'conditions': rows})

    def run_verify(self, expected=None):
        raw = json.dumps(self.manifest).encode()
        return self.mod.verify(raw, self.root, expected or hashlib.sha256(raw).hexdigest())

    def test_exact_eight_snapshot_hashes_preserve_unapproved_status(self):
        result = self.run_verify()
        self.assertEqual(len(result['verified_files']), 8)
        self.assertFalse(result['anatomical_approval'])
        self.assertFalse(result['native_npz_geometry_revalidated'])

    def test_unpinned_manifest_rejected(self):
        with self.assertRaisesRegex(ValueError, 'manifest hash'):
            self.run_verify('0'*64)

    def test_modified_or_missing_snapshot_rejected(self):
        file = self.root/'sample00__observed.npz'
        file.write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'snapshot hash'):
            self.run_verify()
        file.unlink()
        with self.assertRaisesRegex(ValueError, 'snapshot inventory'):
            self.run_verify()

    def test_extra_snapshot_rejected(self):
        (self.root/'other.npz').write_bytes(b'other')
        with self.assertRaisesRegex(ValueError, 'snapshot inventory'):
            self.run_verify()

    def test_promoted_or_wrong_model_provenance_rejected(self):
        for key,value in (('anatomical_approval', True),('source_sha256', 'other'),('saved_blend',True)):
            with self.subTest(key=key):
                old=self.manifest[key];self.manifest[key]=value
                with self.assertRaisesRegex(ValueError,'provenance'):
                    self.run_verify()
                self.manifest[key]=old

    def test_duplicate_or_missing_condition_rejected(self):
        self.manifest['samples'][0]['conditions'][1] = self.manifest['samples'][0]['conditions'][0].copy()
        with self.assertRaisesRegex(ValueError, 'conditions'):
            self.run_verify()

    def test_wrong_sample_set_rejected(self):
        self.manifest['samples'][1]['sample']=0
        with self.assertRaisesRegex(ValueError, 'samples'):
            self.run_verify()


if __name__ == '__main__':
    unittest.main()

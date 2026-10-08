"""Rib-sternum coupled inspiration: solver behaviour and the a003/c003 Blender runs (implementation integrity only)."""
import hashlib, json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import rib_sternum_coupling as rs  # noqa: E402

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'
RECS = {'a003': ANAT / 'character_fit_r95_a003.json',
        'c003': ANAT / 'audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json'}
RUNS = ANAT / 'audit/runs'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class Solver(unittest.TestCase):
    rec = json.loads(RECS['a003'].read_text())

    def test_amplitude_is_sourced_test_amplitude(self):
        self.assertEqual(rs.amplitude(), 4.6)

    def test_zero_amplitude_is_identity(self):
        T, m = rs.coupled_pose(self.rec, 0.0)
        for k, (R, off) in T.items():
            self.assertTrue(np.allclose(R, np.eye(3), atol=1e-9) and np.allclose(off, 0, atol=1e-6), k)
        self.assertLess(m['cartilage_change_max_mm'], 1e-6)

    def test_coupling_reduces_cartilage_deformation_and_direction_emerges(self):
        _, m = rs.coupled_pose(self.rec, rs.amplitude())
        self.assertLess(m['cartilage_change_max_mm'], m['cartilage_change_max_if_sternum_fixed_mm'] / 3)
        self.assertGreater(m['sternum_dz_mm'], 0); self.assertLess(m['sternum_dy_mm'], 0)   # rises and moves anteriorly
        _, me = rs.coupled_pose(self.rec, -rs.amplitude())                                  # expiration reverses it
        self.assertLess(me['sternum_dz_mm'], 0)

    def test_anterior_ends_rise_and_heads_fixed(self):
        T, _ = rs.coupled_pose(self.rec, rs.amplitude())
        for s in ('left', 'right'):
            for n in range(1, 11):
                b = self.rec['bones'][f'rib_{n:02d}_{s}']
                head1 = rs.apply(T[f'rib_{n:02d}_{s}'], rs.mm(b['head_m'])); tail1 = rs.apply(T[f'rib_{n:02d}_{s}'], rs.mm(b['tail_m']))
                self.assertLess(np.linalg.norm(head1 - rs.mm(b['head_m'])), 1e-6)
                self.assertGreater(tail1[2], rs.mm(b['tail_m'])[2], (n, s))


class Runs(unittest.TestCase):
    def test_reports(self):
        for name, rec in RECS.items():
            r = json.loads((RUNS / f'rib_sternum_coupling_{name}_001/rib_sternum_report.json').read_text())
            self.assertEqual(r['integrity_status'], 'PASS', name)
            self.assertEqual(r['provenance']['record_sha256'], sha(rec))
            self.assertEqual(r['provenance']['source_sha256_before'], r['provenance']['source_sha256_after'])
            res = r['results']
            self.assertLess(res['max_bone_end_error_m'], 1e-5); self.assertLess(res['max_costovertebral_drift_m'], 1e-6)
            self.assertLess(res['max_mirror_displacement_error_m'], 1e-5)
            self.assertTrue(res['sternum_direction_at_peak']['superior'] and res['sternum_direction_at_peak']['anterior'])
            self.assertTrue(all(abs(p['sternum_x_mm']) < 1e-3 for p in r['sternum_path']))

    def test_clips_manifest(self):
        man = json.loads((RUNS / 'rib_sternum_coupling_c003_001/clips/manifest.json').read_text())
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)
        self.assertIn('rib-sternum', man['note'])


if __name__ == '__main__':
    unittest.main()

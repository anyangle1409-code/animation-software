"""Dynamic bone-axis crossing scan over the committed isolated runs (a003 run 014, c003 run 001)."""
import hashlib, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import movement_collision_scan as m  # noqa: E402

O = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/movement_collision_scan'
RUNS = ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/runs'


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


class SegmentDistance(unittest.TestCase):
    def test_known_geometry(self):
        P = np.array([[0, 1, 0.0], [5, 5, 5.0], [0, 0, 2.0]]); Q = np.array([[0, -1, 0.0], [6, 6, 6.0], [0, 0, 3.0]])
        d = m.seg_dist_many(np.array([-1, 0, 0.0]), np.array([1, 0, 0.0]), P, Q)
        self.assertAlmostEqual(d[0], 0.0); self.assertAlmostEqual(d[2], 2.0)
        self.assertAlmostEqual(d[1], np.linalg.norm([4, 5, 5]))


class Scans(unittest.TestCase):
    def test_reproduce_and_findings(self):
        for name, rec, smp in (('c003_isolated_001', 'ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c003_ansur_coupled/candidate_record.json',
                                RUNS / 'isolated_bone_only_c003_shoulder_thorax_001/isolated_samples.json'),
                               ('a003_isolated_014', 'ORIGINAL_V1_WORK/anatomy/character_fit_r95_a003.json', RUNS / 'isolated_bone_only_014/isolated_samples.json')):
            S = json.loads((O / f'{name}.json').read_text())
            r = m.scan(json.loads((ROOT / rec).read_text()), json.loads(smp.read_text()), S['stride'])
            for k in ('new_axis_crossings', 'tests_with_new_crossings', 'crossing_profiles'):
                self.assertEqual(json.loads(json.dumps(r[k])), S[k], (name, k))
            self.assertEqual(S['tests_scanned'], 135)
            self.assertEqual(S['tests_with_new_crossings'], ['hip_abduction_adduction_left', 'hip_abduction_adduction_right'])
            self.assertEqual({tuple(c['bones']) for c in S['new_axis_crossings']}, {('tibia_left', 'tibia_right')})
            p = S['crossing_profiles']['hip_abduction_adduction_left|tibia_left|tibia_right']['first_frame_below_bound']
            self.assertAlmostEqual(p['commanded']['adduction'], 13.45, delta=0.01)

    def test_clip_manifest(self):
        man = json.loads((O / 'clips/manifest.json').read_text())
        for rel, h in man['files_sha256'].items():
            self.assertEqual(sha(ROOT / rel), h, rel)


if __name__ == '__main__':
    unittest.main()

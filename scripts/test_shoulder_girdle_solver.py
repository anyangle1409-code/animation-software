import json, math, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import shoulder_girdle_solver as m  # noqa: E402
from report_compare import report_differences  # noqa: E402

STORED = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/canonical_shoulder_girdle_solution_182_v1.json').read_text())


class ShoulderSolver(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(STORED, json.loads(json.dumps(m.build()))), [])

    def test_not_frozen(self):
        self.assertEqual(STORED['status'], 'PROVISIONAL_SOLUTION_NOT_SELECTED_NOT_FROZEN')
        self.assertIs(STORED['freeze_ready'], False)
        self.assertIn('OPEN', STORED['vertical_relation_check']['reading'])

    def test_rotation_senses(self):
        R = m.scapula_rotation(30, 10, 10)
        self.assertAlmostEqual(np.linalg.det(R), 1.0)
        self.assertGreater((R @ [0, 0, 1])[0], 0)                 # internal rotation: lateral axis forward
        Rx = m.scapula_rotation(0, 10, 0); self.assertGreater((Rx @ [0, 0, 1])[1], 0)   # upward rotation raises lateral axis
        Rz = m.scapula_rotation(0, 0, 10); self.assertGreater((Rz @ [0, 1, 0])[0], 0)   # anterior tilt: superior axis forward

    def test_unreconciled_tension_and_reconciled_fit(self):
        v = STORED['variants']['source_scale']
        self.assertGreater(v['checks']['AC_to_lateral_distal_acromion_mm'], 34 + 3 * 8)        # direct placement cannot close
        r = v['reconciled']
        self.assertLess(max(abs(z) for z in r['residual_z'].values()), 1.5)
        self.assertLess(abs(r['clavicle_joint_centre_length_mm'] - 152.9), 9.3)
        ag = r['checks']['AC_to_GH_mm']
        self.assertTrue(min(ag.values()) <= r['checks']['AC_to_GH_seth_model_mm'] <= max(ag.values()))

    def test_bilateral_mirror_and_sides(self):
        for key, w in STORED['variants']['source_scale']['world_mm'].items():
            for lm in ('SC', 'AC', 'AA', 'TS', 'AI'):
                l, r = np.array(w['left'][lm]), np.array(w['right'][lm])
                self.assertGreater(l[0], 0); self.assertLess(r[0], 0)
                self.assertTrue(np.allclose(l, r * [-1, 1, 1], atol=0.02), (key, lm))

    def test_a003_shoulder_defects_recorded(self):
        a = STORED['a003_comparison_mm']; r = STORED['variants']['source_scale']['reconciled']
        self.assertGreater(a['clavicle_SC_AC'] - r['clavicle_joint_centre_length_mm'], 60)
        self.assertGreater(a['AA_TS'], 200)


if __name__ == '__main__':
    unittest.main()

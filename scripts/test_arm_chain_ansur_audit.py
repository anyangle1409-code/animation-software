"""Arm-chain ANSUR audit: reproducible, recomputed from the raw CSV, no target selected, recorded tensions pinned."""
import json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit')); sys.path.insert(0, str(ROOT / 'scripts'))
import arm_chain_ansur_audit as m  # noqa: E402
from report_compare import report_differences  # noqa: E402

A = json.loads((ROOT / 'ORIGINAL_V1_WORK/anatomy/audit/arm_chain_ansur_audit_v1.json').read_text())


class ArmChain(unittest.TestCase):
    def test_reproduces(self):
        self.assertEqual(report_differences(A, json.loads(json.dumps(m.build()))), [])

    def test_ansur_values(self):
        a = A['ansur_at_182_mm']
        self.assertEqual(a['_n'], 4082)
        self.assertEqual((a['acromial_height']['mean'], a['radiale_stylion']['mean'], a['acromion_radiale']['mean']), (1497.7, 278.1, 348.2))

    def test_c003_shoulder_on_target_and_recorded_arm_tension(self):
        c = A['candidates']['c003']
        self.assertAlmostEqual(c['acromion_z_mm'], 1497.7, delta=0.05)
        self.assertLess(c['acromion_radiale_z'], -1.5)                 # upper-arm drop short: recorded, not hidden
        self.assertLess(c['radiale_stylion_z'], -3)                    # a003 forearm shortness unchanged
        self.assertEqual(A['candidates']['a003']['radiale_stylion_z'], c['radiale_stylion_z'])
        self.assertEqual(A['status'], 'AUDIT_ONLY_NO_TARGET_SELECTED')

    def test_no_head_acromion_collision(self):
        for k in ('c001', 'c003'):
            cl = A['candidates'][k]['landmark_clearance_from_24mm_head_sphere_mm']
            self.assertTrue(all(cl[f'LM{i}'] > 15 for i in (25, 26, 27)), k)
            self.assertTrue(all(cl[f'LM{i}'] >= -0.1 for i in (15, 16, 17, 18, 19)), k)


if __name__ == '__main__':
    unittest.main()

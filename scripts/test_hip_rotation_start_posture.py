#!/usr/bin/env python3
"""L7 start-posture analysis: beta=0 reproduces the interaction scan; a small contralateral abduction separates the feet."""
import json, unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/'
                'hip_rotation_start_posture_c004_v1.json').read_text())


class HipRotation(unittest.TestCase):
    def test_beta0_reproduces_interaction_scan(self):
        for t, c in D['beta0_consistency_with_interaction_scan'].items():
            if c['interaction_scan_min_mm'] is not None:
                self.assertAlmostEqual(c['beta0_mm'], c['interaction_scan_min_mm'], places=1, msg=t)

    def test_l7_closes_at_rest_and_clears_with_abduction(self):
        for sd in ('left', 'right'):
            row = D['per_test'][f'hip_rotation_at_0_flexion_{sd}']
            self.assertLess(row['0']['min_axis_mm'], 5)
            self.assertGreater(row['5']['min_axis_mm'], 25)
        self.assertLessEqual(max(v for k, v in D['smallest_contralateral_abduction_deg_for_axis_distance'].items() if k.endswith('ge25mm')), 5)

    def test_bilateral(self):
        a, b = D['per_test']['hip_rotation_at_0_flexion_left'], D['per_test']['hip_rotation_at_0_flexion_right']
        for k in a:
            self.assertLess(abs(a[k]['min_axis_mm'] - b[k]['min_axis_mm']), 5.0, k)    # c004 mirror within 0.29 mm; sweep sampling stride 2


if __name__ == '__main__':
    unittest.main()

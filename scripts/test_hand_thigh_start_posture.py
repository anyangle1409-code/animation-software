#!/usr/bin/env python3
"""H6 start-posture analysis: alpha=0 reproduces the interaction scan; a modest GH start abduction clears every sweep."""
import json, unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/'
                'hand_thigh_start_posture_c004_v1.json').read_text())


class HandThigh(unittest.TestCase):
    def test_alpha0_reproduces_interaction_scan(self):
        for t, c in D['alpha0_consistency_with_interaction_scan'].items():
            if c['interaction_scan_min_mm'] is not None:
                self.assertAlmostEqual(c['alpha0_mm'], c['interaction_scan_min_mm'], places=1, msg=t)

    def test_h6_tests_close_at_rest(self):
        for t in ('forearm_rotation_at_elbow_0_left', 'elbow_flexion_at_pronation_60_left', 'wrist_flexion_left'):
            self.assertLess(D['per_test'][t]['0']['min_axis_mm'], 10)

    def test_start_abduction_clears_all(self):
        s = D['smallest_start_abduction_deg_for_axis_distance']
        self.assertLessEqual(max(v for k, v in s.items() if k.endswith('_ge25mm')), 10)
        for t, row in D['per_test'].items():
            self.assertGreater(row['10']['min_axis_mm'], 25, t)

    def test_bilateral(self):
        for t, row in D['per_test'].items():
            if t.endswith('_left'):
                r = D['per_test'][t[:-5] + '_right']
                for a in row:
                    self.assertAlmostEqual(row[a]['min_axis_mm'], r[a]['min_axis_mm'], places=1)


if __name__ == '__main__':
    unittest.main()

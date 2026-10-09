#!/usr/bin/env python3
"""Committed c004 follower verification: followers match their couplings; the recorded gaps stay recorded."""
import json, unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/'
                'follower_verification_c004_v1.json').read_text())
R = D['results']


class Followers(unittest.TestCase):
    def test_patella_follows_sourced_ratio(self):
        self.assertEqual(D['patellar_flexion_ratio'], 0.66)
        for sd in ('left', 'right'):
            self.assertLess(R['knee'][sd]['max_abs_follower_error_deg'], 1e-3)
            self.assertGreater(R['knee'][sd]['min_patella_femur_axis_mm'], 1.0)

    def test_patellar_ligament_gap_recorded(self):
        for sd in ('left', 'right'):
            k = R['knee'][sd]
            self.assertLess(k['ligament_change_with_follower_mm'][1], k['ligament_change_plain_flexion_no_follower_mm'][1])
            self.assertGreater(k['ligament_change_with_follower_mm'][1], 5.0)      # rotation-only follower: translation unsourced
        self.assertTrue(any('translation path' in u for u in D['unresolved']))

    def test_girdle_rhythm_and_continuity(self):
        for sd in ('left', 'right'):
            g = R['shoulder_girdle'][sd]
            self.assertTrue(all(v < 1e-3 for v in g['max_abs_error_vs_rhythm_deg'].values()), g)
            self.assertLess(g['max_SC_head_displacement_mm'], 1e-3)
            self.assertLess(g['max_AC_closure_mm'], 1e-2)
            lo, hi = g['gh_to_ac_distance_range_mm']; self.assertLess(hi - lo, 1e-2)
            self.assertGreater(min(g['min_axis_clearance_mm'].values()), 1.0)

    def test_clavicle_elevation_gap_recorded(self):
        for sd in ('left', 'right'):
            self.assertLess(abs(R['shoulder_girdle'][sd]['clavicle_elevation_change_deg_at_max']), 0.5)
        self.assertTrue(any('Clavicle elevation' in u for u in D['unresolved']))

    def test_bilateral_symmetry(self):
        for test, d in R['bilateral_symmetry_max_abs_diff'].items():
            for k, v in d.items():
                self.assertLess(v, 1e-6 if k.endswith('_m') else 1e-2, (test, k))      # metres / degrees


if __name__ == '__main__':
    unittest.main()

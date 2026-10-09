#!/usr/bin/env python3
"""Follower source matrix: conflicts stay recorded; only the patella experiment is proposed, nothing adopted."""
import json, unittest
from pathlib import Path

D = json.loads((Path(__file__).resolve().parents[1] / 'ORIGINAL_V1_WORK/anatomy/audit/claude_anatomical_development_20261009/'
                'follower_source_matrix_v1.json').read_text())


class SourceMatrix(unittest.TestCase):
    def test_patella_rotation_conflict_recorded(self):
        c = D['conflicts']['patella_rotation']
        self.assertEqual(c['sourced_ratio'], 0.66)
        self.assertTrue(all(r > 0.66 for r in c['rajagopal_ratio_at_60_90_120']))

    def test_myolegs_not_independent(self):
        m = next(x for x in D['matrix']['patella'] if 'myolegs' in x['source'])
        self.assertLess(m['max_abs_diff_vs_rajagopal_translation1_spline_mm'], 1.0)

    def test_clavicle_unresolved_no_relation(self):
        self.assertEqual(D['proposals']['E-CLAV-1']['status'], 'NO_RELATION_PROPOSED_UNRESOLVED')
        self.assertGreater(D['conflicts']['clavicle_elevation']['mobl_at_HT_90_168'][1], 10.0)

    def test_patella_proposal_is_experiment_only(self):
        p = D['proposals']['E-PAT-1']
        self.assertEqual(p['status'], 'PROPOSED_FUTURE_EXPERIMENT_NOT_ADOPTED')
        self.assertEqual(set(p['arms']), {'A_rotation_rajagopal', 'B_rotation_sourced_0.66'})


if __name__ == '__main__':
    unittest.main()

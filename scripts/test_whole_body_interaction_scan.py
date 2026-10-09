"""Whole-body interaction scan: committed c004/a003 lists pinned; detector proven by mutation; articulating partners excluded."""
import copy, json, sys, unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import whole_body_interaction_scan as w  # noqa: E402

A = ROOT / 'ORIGINAL_V1_WORK/anatomy'
O = A / 'audit/claude_independent_review_20261009'
REC = json.loads((A / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json').read_text())
S = json.loads((A / 'audit/runs/isolated_bone_only_c004_arm_inputs_001/isolated_samples.json').read_text())


class Committed(unittest.TestCase):
    def test_lists(self):
        c, a = (json.loads((O / f'whole_body_interaction_{k}.json').read_text()) for k in ('c004', 'a003'))
        tc = {x['test'] for x in c['tests_with_cross_region_approach_below_10mm']}
        ta = {x['test'] for x in a['tests_with_cross_region_approach_below_10mm']}
        self.assertIn('wrist_flexion_left', tc); self.assertNotIn('wrist_flexion_left', ta)          # exposed by narrower shoulders
        self.assertEqual(sorted(x['test'] for x in c['graded_crossings_below_1mm']), ['hip_abduction_adduction_left', 'hip_abduction_adduction_right'])
        self.assertFalse(any(set(x['bones']) == {'hip_bone_left', 'hip_bone_right'} for x in c['pairs']))


class Mutation(unittest.TestCase):
    def test_injected_contact_listed(self):
        rec = copy.deepcopy(REC); f = np.asarray(rec['bones']['femur_left']['head_m']) * 0.5 + np.asarray(rec['bones']['femur_left']['tail_m']) * 0.5
        b = rec['bones']['digit3_distal_phalanx_left']; off = f + [0.004, 0, 0] - np.asarray(b['head_m'])
        for e in ('head_m', 'tail_m'):
            b[e] = (np.asarray(b[e]) + off).tolist()
        r = w.scan(rec, {'wrist_flexion_left': S['wrist_flexion_left'][:3]}, stride=1)
        self.assertTrue(any(set(x['bones']) == {'digit3_distal_phalanx_left', 'femur_left'} and x['min_axis_mm'] < 5 for x in r['pairs']))


if __name__ == '__main__':
    unittest.main()

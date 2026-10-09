#!/usr/bin/env python3
"""Tests for the T001 isolated experimental coupled trunk rebuild (not a candidate)."""
import json, math, sys, unittest
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'anatomy_fit'))
import build_experiment_t001_coupled_trunk as t1  # noqa: E402
import compare_isolated_runs as cmp  # noqa: E402

ANAT = HERE.parent / 'ORIGINAL_V1_WORK/anatomy'
EXP = ANAT / 'audit/experiments/t001_coupled_trunk'
MOVED = set(t1.CHAIN) | {f'rib_{n:02d}_{s}' for n in range(1, 13) for s in ('left', 'right')}


class T001(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads((EXP / 'experiment_record.json').read_text())
        cls.base = json.loads(t1.BASE.read_text())

    def test_rebuild_is_deterministic(self):
        new = t1.build('CL_hasegawa')
        for k in self.rec['bones']:
            for e in ('head_m', 'tail_m'):
                self.assertTrue(np.allclose(new['bones'][k][e], self.rec['bones'][k][e], atol=1e-9), k)
        self.assertEqual(new['candidate']['solution'], self.rec['candidate']['solution'])

    def test_only_spine_and_ribs_move(self):
        changed = {k for k in self.base['bones'] if self.base['bones'][k] != self.rec['bones'][k]}
        self.assertTrue(changed <= MOVED, changed - MOVED)
        for k in ('sacrum', 'c2', 'c1', 'sternum', 'clavicle_left', 'scapula_right', 'humerus_left', 'hyoid', 'femur_left'):
            self.assertEqual(self.base['bones'][k], self.rec['bones'][k], k)

    def test_closure_and_priors(self):
        s = self.rec['candidate']['solution']
        gap = math.dist(self.rec['bones']['c3']['tail_m'], self.base['bones']['c2']['head_m']) * 1000      # chain closes on the fixed C2
        self.assertAlmostEqual(gap, self.rec['candidate']['disc_gaps_mm']['C2/C3'], places=2)
        for k, z in s['z_scores'].items():
            self.assertLess(abs(z), 1.0, k)
        self.assertTrue(1.6 < s['implied_source_cohort_stature_m'] < 2.0)

    def test_disc_gaps_positive_and_rib_lengths_kept(self):
        for k, g in self.rec['candidate']['disc_gaps_mm'].items():
            self.assertGreater(g, 2.0, k)
        for n in range(1, 13):
            for sd in ('left', 'right'):
                k = f'rib_{n:02d}_{sd}'
                L0 = math.dist(self.base['bones'][k]['head_m'], self.base['bones'][k]['tail_m'])
                L1 = math.dist(self.rec['bones'][k]['head_m'], self.rec['bones'][k]['tail_m'])
                self.assertAlmostEqual(L0, L1, places=9)

    def test_outcomes(self):
        o = json.loads((EXP / 'checks/outcome_audit.json').read_text())['records']
        c = o['ORIGINAL_V1_WORK/anatomy/audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json']
        t = o['ORIGINAL_V1_WORK/anatomy/audit/experiments/t001_coupled_trunk/experiment_record.json']
        self.assertLess(abs(t['T12_L1_mid_z_minus_pelvis_prediction_mm']), 10)
        self.assertGreater(abs(c['T12_L1_mid_z_minus_pelvis_prediction_mm']), 30)
        self.assertTrue(t['disc_centre_gaps_mm']['all_positive'])
        self.assertTrue(t['IJ_vs_T2_T3_bodies']['inside'])
        for r, v in t['rib_head_minus_articular_level_z_mm'].items():
            self.assertLess(abs(v - c['rib_head_minus_articular_level_z_mm'][r]), 1.5, r)

    def test_movement_changes_confined_to_trunk(self):
        d = json.loads((EXP / 'checks/run_comparison_vs_c004.json').read_text())
        for t in d['groups']['MATERIALLY_CHANGED']:
            self.assertTrue(t.startswith(('thoracic', 'rib_', 'cervical', 'lumbar')), t)

    def test_comparator_gimbal_and_wrap(self):
        a = [{'plane_of_elevation': 10.0, 'elevation': 1e-6, 'isb_yxy_raw': [40.0, 1e-6, 60.0], 'x': 179.9999}]
        b = [{'plane_of_elevation': 150.0, 'elevation': 1e-6, 'isb_yxy_raw': [0.0, 0.0, 0.0], 'x': -179.9999}]
        la, lb = dict(cmp.leaves(cmp.canon(a))), dict(cmp.leaves(cmp.canon(b)))
        self.assertEqual(la['[0]/plane_of_elevation'], lb['[0]/plane_of_elevation'])
        self.assertEqual(la['[0]/isb_yxy_raw[0]'], lb['[0]/isb_yxy_raw[0]'])


if __name__ == '__main__':
    unittest.main()

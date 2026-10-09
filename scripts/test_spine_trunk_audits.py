#!/usr/bin/env python3
"""Tests for the spine length discriminator, P002 feasibility, rejected P003 re-partition and trunk closure audit."""
import json, math, sys, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'anatomy_fit'))
import spine_column_length_discriminator as sd  # noqa: E402
import build_proposal_p003_spine_discs as p3  # noqa: E402
import trunk_vertical_closure_audit as tv  # noqa: E402

ANAT = HERE.parent / 'ORIGINAL_V1_WORK/anatomy'
OUT = ANAT / 'audit/claude_anatomical_development_20261009'
P003 = ANAT / 'audit/proposals/p003_spine_disc_repartition_rejected/proposal_record.json'


class Discriminator(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = json.loads((OUT / 'spine_column_length_discriminator_v1.json').read_text())

    def test_ansur_regression_matches_committed_thorax_review(self):
        r = sd.ansur_at('cervicaleheight')
        self.assertEqual(r['n'], 4082)
        self.assertAlmostEqual(r['prediction_mm'], 1575.2, places=1)       # canonical_thorax_frame_182_review_v1.json
        self.assertAlmostEqual(sd.ansur_at('suprasternaleheight')['prediction_mm'], 1494.5, places=1)

    def test_source_A_needs_implausible_cohort_B_does_not(self):
        v = self.d['variants']
        for k, x in v.items():
            if '|A_anatomical_2011|' in k:
                self.assertLess(x['implied_source_cohort_stature_m'], 1.55, k)
                self.assertFalse(x['ANSUR_inside_envelope'], k)
            if k.startswith('MRI_edge_mean|B_CT_2016'):
                self.assertGreater(x['implied_source_cohort_stature_m'], 1.65, k)

    def test_envelope_monotone_and_bounded_by_arc(self):
        stack, geom = sd.load('stack'), sd.load('geom')
        tb, td = sd.thoracic_heights('B_CT_2016', stack, geom)
        env = sd.thoracic_envelope(tb, td, -15.5, 43.7)
        self.assertLessEqual(env['rise_min_mm'], env['rise_max_mm'])
        self.assertLessEqual(env['rise_max_mm'], env['arc_mm'] + 1e-9)
        for seq in (env['min_sequence_deg'], env['max_sequence_deg']):
            self.assertTrue(all(b >= a - 1e-9 for a, b in zip(seq, seq[1:])), 'tilt sequence must be monotone')
            self.assertAlmostEqual(seq[0], -15.5); self.assertAlmostEqual(seq[-1], -15.5 + 43.7)

    def test_tip_rotation_is_rigid(self):
        off = {'along_axis_superior': -27.0, 'posterior': 52.0}
        for phi in (-20, 0, 15, 30):
            y, z = sd.tip_world((0, 0), phi, off)
            self.assertAlmostEqual(math.hypot(y, z), math.hypot(27.0, 52.0), places=9)


class P003Rejected(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = json.loads(P003.read_text())
        cls.base = json.loads(p3.BASE.read_text())

    def test_rebuild_is_deterministic(self):
        self.assertEqual(p3.build(), self.rec)

    def test_only_spine_chain_bones_changed_and_arc_conserved(self):
        changed = {k for k in self.base['bones'] if self.base['bones'][k] != self.rec['bones'][k]}
        self.assertEqual(changed, set(p3.CHAIN))
        for k in ('sacrum', 'c2', 'c1', 'rib_12_left', 'sternum', 'clavicle_left'):
            self.assertEqual(self.base['bones'][k], self.rec['bones'][k])
        c = self.rec['candidate']
        self.assertAlmostEqual(sum(r['scaled_height_mm'] for r in c['bodies']) + sum(r['scaled_height_mm'] for r in c['discs'].values()),
                               c['c004_arc_l5head_to_c2head_mm'], places=1)

    def test_every_disc_gap_positive(self):
        B = self.rec['bones']
        chain = p3.CHAIN + ['c2']
        for lo, up in zip(chain, chain[1:]):
            axis = [b - a for a, b in zip(B[lo]['head_m'], B[lo]['tail_m'])]
            step = [b - a for a, b in zip(B[lo]['tail_m'], B[up]['head_m'])]
            along = sum(x * y for x, y in zip(axis, step)) / math.hypot(*axis)
            self.assertGreater(along, 0.002, f'{lo}->{up}')

    def test_rejected_by_rib_level_rule(self):
        r = tv.rib_test(self.rec)
        self.assertEqual(r['verdict'], 'REJECTED_RIB_LEVEL_ACCEPTANCE')
        self.assertGreater(r['max_abs_rib_head_offset_from_articular_level_mm']['p003'], 30)


class Closure(unittest.TestCase):
    def test_committed_residual_signs(self):
        d = json.loads((OUT / 'trunk_vertical_closure_c004_v1.json').read_text())['residuals_mm']
        self.assertGreater(d['lumbar_length'], 30)          # c004 lumbar curve longer than sourced bodies + discs
        for k in ('T12_L1_height', 'IJ_height', 'rib10_height'):
            self.assertGreater(d[k], 15, k)                  # lower trunk too high on three independent checks
        self.assertLess(abs(d['thoracic_length']), 15)


class KneeHipGrip(unittest.TestCase):
    def test_patella_static_vs_follower(self):
        d = json.loads((OUT / 'patellar_tracking_c004_v1.json').read_text())['summary']
        self.assertGreater(d['static_patella_ligament_change_max_percent'], 50)
        self.assertLess(d['follower_ligament_change_max_percent'], 15)
        self.assertLess(d['rajagopal_own_ligament_change_percent'], 15)

    def test_hip_adduction_needs_contralateral_abduction(self):
        d = json.loads((OUT / 'hip_adduction_start_posture_c004_v1.json').read_text())
        self.assertLess(d['grid']['add20_contra_abd0']['min_axis_distance_mm'], 5)
        self.assertGreater(d['grid']['add20_contra_abd15']['min_axis_distance_mm'], 25)

    def test_segment_distance_function(self):
        import numpy as np
        import hip_adduction_start_posture as hp
        a, b = np.array([0., 0, 0]), np.array([1., 0, 0])
        self.assertAlmostEqual(hp.seg_dist(a, b, np.array([0.5, 0, 1.]), np.array([0.5, 0, 2.])), 1.0)
        self.assertAlmostEqual(hp.seg_dist(a, b, np.array([0.5, -1., 0]), np.array([0.5, 1., 0])), 0.0)

    def test_grip_chord_geometry(self):
        import grip_wrap_capacity as g
        L = [0.045, 0.027, 0.019]
        ang, wrap = g.needed(10.0, L)                    # huge radius -> nearly straight
        self.assertTrue(all(a < 0.3 for a in ang))
        R = g.min_radius(L, [86, 97.2, 81.6])
        ang, _ = g.needed(R, L)
        self.assertAlmostEqual(max(a / b for a, b in zip(ang, [86, 97.2, 81.6])), 1.0, places=6)


if __name__ == '__main__':
    unittest.main()

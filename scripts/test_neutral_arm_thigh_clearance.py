"""Numeric axis-to-axis clearance diagnostics for resting P005 arm pose."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import neutral_arm_thigh_clearance as ac
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5


class SegmentDistance(unittest.TestCase):
    def test_segments_cross(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [1, 0, 0], [.5, -1, 0], [.5, 1, 0]), 0, places=10)

    def test_segments_skew(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [1, 0, 0], [.5, -1, 1], [.5, 1, 1]), 1, places=10)

    def test_parallel_segments(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]), 1, places=10)

    def test_endpoints_beyond_each_other(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [1, 0, 0], [2, 0, 0], [3, 0, 0]), 1, places=10)

    def test_parallel_overlapping_segments(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [2, 0, 0], [1, 0, 0], [3, 0, 0]), 0, places=10)

    def test_degenerate_first_segment(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [0, 0, 0], [1, -1, 0], [1, 1, 0]), 1, places=10)

    def test_degenerate_second_segment(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [1, -1, 0], [1, 1, 0], [0, 0, 0], [0, 0, 0]), 1, places=10)

    def test_both_degenerate_segments(self):
        self.assertAlmostEqual(ac.segment_distance_m(
            [0, 0, 0], [0, 0, 0], [0, 3, 4], [0, 3, 4]), 5, places=10)


class RealSkeletonClearance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.baseline, cls.p003)
        cls.p005 = p5.build(cls.baseline, cls.p004)

    def test_real_body_returns_finite_distances(self):
        r = ac.audit(self.baseline, self.p005)
        self.assertTrue(math.isfinite(r['baseline_min_axis_separation_mm']))
        self.assertTrue(math.isfinite(r['candidate_min_axis_separation_mm']))
        self.assertGreaterEqual(r['baseline_min_axis_separation_mm'], 0)
        self.assertGreaterEqual(r['candidate_min_axis_separation_mm'], 0)

    def test_no_anatomical_surface_collision_claim(self):
        r = ac.audit(self.baseline, self.p005)
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertFalse(r['anatomical_surface_collision_verified'])
        self.assertFalse(r['dynamic_motion_verified'])
        self.assertFalse(r['clinical_clearance_threshold_established'])

    def test_unmodified_control_has_zero_clearance_change(self):
        r = ac.audit(self.baseline, self.baseline)
        self.assertAlmostEqual(r['largest_clearance_decrease']['distance_change_mm'], 0)
        self.assertFalse(r['clearance_change_over_engineering_10mm_review_guard'])

    def test_hand_sticks_and_both_thighs_checked(self):
        r = ac.measure(self.p005)
        names = {(x['arm_bone'], x['femur']) for x in r['pairs']}
        for side in ('left', 'right'):
            for thigh in ('left', 'right'):
                self.assertIn((f'ulna_{side}', f'femur_{thigh}'), names)
                self.assertIn((f'metacarpal_2_{side}', f'femur_{thigh}'), names)
        self.assertEqual(len(names), len(r['pairs']))

    def test_inputs_unchanged_and_deterministic(self):
        prior = json.dumps([self.baseline, self.p005], sort_keys=True)
        self.assertEqual(ac.audit(self.baseline, self.p005),
                         ac.audit(self.baseline, self.p005))
        self.assertEqual(prior, json.dumps([self.baseline, self.p005], sort_keys=True))

    def test_missing_femur_fails_closed(self):
        bad = copy.deepcopy(self.p005)
        bad['bones'].pop('femur_left')
        with self.assertRaisesRegex(ValueError, 'bone inventory changed'):
            ac.audit(self.baseline, bad)

    def test_artificial_large_arm_shift_is_detected(self):
        # Real P005 may improve or worsen control spacing. This deliberately
        # moves an ulna straight into the femur stick to test measurement,
        # not to claim physiological surface collision.
        bad = copy.deepcopy(self.baseline)
        bid = 'ulna_left'
        original = bad['bones'][bid]
        femur = bad['bones']['femur_left']
        mid_arm = [(a+b)/2 for a,b in zip(original['head_m'], original['tail_m'])]
        mid_femur = [(a+b)/2 for a,b in zip(femur['head_m'], femur['tail_m'])]
        shift = [x-y for x,y in zip(mid_femur, mid_arm)]
        for end in ('head_m', 'tail_m'):
            original[end] = [v+s for v,s in zip(original[end], shift)]
        result = ac.audit(self.baseline, bad)
        self.assertEqual(result['candidate_min_axis_separation_mm'], 0)
        self.assertTrue(result['clearance_change_over_engineering_10mm_review_guard'])


if __name__ == '__main__':
    unittest.main()

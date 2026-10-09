"""P006: distinguish least-squares sternum translation from anatomical closure."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5
import p006_sternocostal_translation_feasibility as p6


class AnalyticTranslationProof(unittest.TestCase):
    def test_two_corridors_20mm_apart_impossible_under_5mm_guard(self):
        r = p6.analyse_displacements(
            {'a': [-0.01, 0, 0], 'b': [0.01, 0, 0]}, [0, 0, 0])
        self.assertAlmostEqual(r['maximum_pairwise_rib_displacement_difference_mm'], 20)
        self.assertAlmostEqual(r['unavoidable_max_residual_lower_bound_for_translation_mm'], 10)
        self.assertTrue(r['single_translation_cannot_pass_every_corridor_guard'])
        self.assertFalse(r['sternum_rotation_evaluated'])

    def test_identical_displacements_have_zero_lower_bound(self):
        r = p6.analyse_displacements(
            {'a': [0, 0, -.02], 'b': [0, 0, -.02], 'c': [0, 0, -.02]}, [0, 0, -.02])
        self.assertAlmostEqual(r['actual_worst_vector_change_mm'], 0)
        self.assertAlmostEqual(r['ls_worst_vector_change_mm'], 0)
        self.assertFalse(r['single_translation_cannot_pass_every_corridor_guard'])

    def test_optimal_mean_better_than_arbitrary_translation_in_l2(self):
        d = {'a': [0, 0, 0], 'b': [0.006, 0.005, 0], 'c': [0.022, -.01, 0]}
        r = p6.analyse_displacements(d, [0.10, 0, 0])
        self.assertLess(r['sum_of_squared_vector_changes_ls_mm2'],
                        r['sum_of_squared_vector_changes_actual_mm2'])
        self.assertFalse(r['anatomical_target_selected'])

    def test_3d_triangle_inequality_lower_bound(self):
        d = {'a': [0, 0, 0], 'b': [0, .01, 0], 'c': [.02, 0, 0]}
        r = p6.analyse_displacements(d, [.006, .003, 0])
        self.assertAlmostEqual(
            r['unavoidable_max_residual_lower_bound_for_translation_mm'],
            math.sqrt(0.02**2 + 0.01**2)*500, places=5)
        self.assertLessEqual(r['unavoidable_max_residual_lower_bound_for_translation_mm'],
                             r['actual_worst_vector_change_mm'] + 1e-4)

    def test_insufficient_corridors_rejected(self):
        with self.assertRaisesRegex(ValueError, 'two or more'):
            p6.analyse_displacements({'a': [0, 0, 0]}, [0, 0, 0])

    def test_nonfinite_vector_rejected(self):
        with self.assertRaisesRegex(ValueError, 'invalid displacement'):
            p6.analyse_displacements({'a': [0, 0, 0], 'b': [0, float('nan'), 0]}, [0, 0, 0])

    def test_invalid_guard_rejected(self):
        with self.assertRaisesRegex(ValueError, 'positive finite'):
            p6.analyse_displacements({'a': [0, 0, 0], 'b': [0, .02, 0]}, [0, 0, 0], guard_mm=-1)


class RealSternumTranslationProof(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.base, cls.p003)
        cls.p005 = p5.build(cls.base, cls.p004)

    def test_identity_record_requires_no_translation(self):
        r = p6.audit(self.base, self.base)
        self.assertEqual(r['number_of_corridors'], 14)
        self.assertAlmostEqual(r['actual_worst_vector_change_mm'], 0)
        self.assertFalse(r['canonical_promotion_allowed'])

    def test_p004_p005_require_same_sternum_translation_solution(self):
        a, b = p6.audit(self.base, self.p004), p6.audit(self.base, self.p005)
        self.assertEqual(a, b)
        self.assertEqual(a['number_of_corridors'], 14)
        self.assertFalse(a['anatomical_target_selected'])

    def test_ls_solution_cannot_have_higher_sum_squared_than_p004(self):
        r = p6.audit(self.base, self.p004)
        self.assertLessEqual(r['sum_of_squared_vector_changes_ls_mm2'],
                             r['sum_of_squared_vector_changes_actual_mm2'] + .0001)

    def test_current_actual_worst_cannot_undercut_lower_bound(self):
        r = p6.audit(self.base, self.p005)
        self.assertLessEqual(r['unavoidable_max_residual_lower_bound_for_translation_mm'],
                             r['actual_worst_vector_change_mm'] + 1e-4)

    def test_rejects_nonrigid_sternal_movement(self):
        bad = copy.deepcopy(self.p004)
        bad['bones']['sternum']['tail_m'][2] += .01
        with self.assertRaisesRegex(ValueError, 'not a rigid pure translation'):
            p6.audit(self.base, bad)

    def test_rejects_marker_not_following_sternum(self):
        bad = copy.deepcopy(self.p005)
        bad['joint_markers']['sternocostal_01_left']['centre_m'][2] += .01
        with self.assertRaisesRegex(ValueError, 'not translated with sternum'):
            p6.audit(self.base, bad)

    def test_rejects_rib_not_rigidly_moved(self):
        bad = copy.deepcopy(self.p004)
        bad['bones']['rib_04_right']['tail_m'][0] += .01
        with self.assertRaisesRegex(ValueError, 'not translated rigidly'):
            p6.audit(self.base, bad)

    def test_rejects_incorrect_marker_owner(self):
        bad = copy.deepcopy(self.p005)
        bad['joint_markers']['sternocostal_04_right']['frame_bone'] = 'rib_04_right'
        with self.assertRaisesRegex(ValueError, 'does not belong to sternum'):
            p6.audit(self.base, bad)

    def test_rejects_bone_inventory_edit(self):
        bad = copy.deepcopy(self.p005)
        del bad['bones']['rib_04_right']
        with self.assertRaisesRegex(ValueError, 'bone inventory changed'):
            p6.audit(self.base, bad)

    def test_deterministic_and_input_immutable(self):
        before = json.dumps([self.base, self.p005], sort_keys=True)
        self.assertEqual(p6.audit(self.base, self.p005), p6.audit(self.base, self.p005))
        self.assertEqual(before, json.dumps([self.base, self.p005], sort_keys=True))


if __name__ == '__main__':
    unittest.main()

"""Mutation tests for independently computed 3D rib and sternal marker closure."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import rib_3d_coupling_audit as a
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5


class Rib3DCouplingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.baseline, cls.p003)
        cls.p005 = p5.build(cls.baseline, cls.p004)

    def test_baseline_against_itself_has_zero_3d_regressions(self):
        result = a.audit(self.baseline, self.baseline)
        self.assertEqual(result['status'], 'NO_RELATIVE_VECTOR_REGRESSION_ANATOMY_UNVERIFIED')
        self.assertEqual(result['blockers'], [])
        self.assertFalse(result['canonical_promotion_allowed'])

    def test_exact_participants_and_corridors(self):
        result = a.audit(self.baseline, self.p005)
        self.assertEqual(result['ribs_checked'], 24)
        self.assertEqual(result['rib_joint_markers_checked'], 48)
        self.assertEqual(result['sternocostal_corridors_checked'], 14)
        self.assertFalse(result['contact_surfaces_verified'])
        self.assertFalse(result['costal_cartilage_modelled'])

    def test_p003_rejected_rib_3d_displacement_not_just_z(self):
        r = a.audit(self.baseline, self.p003)
        self.assertIn('RIB_VERTEBRAL_ANCHOR_3D_VECTOR_CHANGED', r['blockers'])
        self.assertGreater(max(r['rib_level_3d_vector_delta_mm'].values()), 20)

    def test_p004_restores_all_3d_rib_attachment_relative_vectors(self):
        r = a.audit(self.baseline, self.p004)
        self.assertEqual(r['rib_level_review_over_5mm'], {})
        self.assertLess(max(r['rib_level_3d_vector_delta_mm'].values()), 1e-4)

    def test_p004_joint_markers_follow_ribs_without_new_drift(self):
        r = a.audit(self.baseline, self.p004)
        self.assertEqual(r['joint_marker_review_over_5mm'], {})
        self.assertLess(max(r['costovertebral_costotransverse_marker_vector_delta_mm'].values()), 1e-4)

    def test_p005_has_identical_rib_checks_as_p004(self):
        r4 = a.audit(self.baseline, self.p004)
        r5 = a.audit(self.baseline, self.p005)
        for key in ('rib_level_3d_vector_delta_mm',
                    'costovertebral_costotransverse_marker_vector_delta_mm',
                    'sternocostal_control_corridor', 'rib_length_change_mm'):
            self.assertEqual(r4[key], r5[key])

    def test_adversarial_depth_shift_undetected_by_z_guard_is_rejected(self):
        mutated = copy.deepcopy(self.p005)
        rib = mutated['bones']['rib_03_left']
        # Same Z throughout; deliberately move 20mm posterior (Y)
        # while retaining rib segment length.
        for end in ('head_m', 'tail_m'):
            rib[end][1] += .02
        result = a.audit(self.baseline, mutated)
        self.assertIn('RIB_VERTEBRAL_ANCHOR_3D_VECTOR_CHANGED', result['blockers'])
        self.assertIn('RIB_COSTOVERTEBRAL_TRANSVERSE_MARKER_DRIFT', result['blockers'])
        self.assertGreater(result['rib_level_3d_vector_delta_mm']['rib_03_left'], 19.99)

    def test_marker_drift_rejected_without_moving_any_bone(self):
        mutated = copy.deepcopy(self.p005)
        mutated['joint_markers']['costotransverse_04_right']['centre_m'][0] -= .015
        r = a.audit(self.baseline, mutated)
        self.assertIn('RIB_COSTOVERTEBRAL_TRANSVERSE_MARKER_DRIFT', r['blockers'])
        self.assertGreater(r['costovertebral_costotransverse_marker_vector_delta_mm'][
            'costotransverse:rib_04_right'], 14)

    def test_sternocostal_proxy_detects_silent_sternal_marker_drift(self):
        mutated = copy.deepcopy(self.baseline)
        mutated['joint_markers']['sternocostal_02_left']['centre_m'][1] += 0.020
        r = a.audit(self.baseline, mutated)
        self.assertIn('STERNOCOSTAL_CORRIDOR_VECTOR_CHANGED', r['blockers'])
        self.assertGreater(r['sternocostal_control_corridor']['rib_02_left']['vector_change_mm'], 19)

    def test_rib_control_length_change_detected(self):
        mutated = copy.deepcopy(self.baseline)
        mutated['bones']['rib_09_right']['tail_m'][2] += .015
        r = a.audit(self.baseline, mutated)
        self.assertIn('RIB_CONTROL_LENGTH_CHANGED', r['blockers'])

    def test_invalid_costovertebral_frame_rejected(self):
        mutated = copy.deepcopy(self.p005)
        mutated['joint_markers']['costovertebral_01_left']['frame_bone'] = 'sternum'
        with self.assertRaisesRegex(ValueError, 'incorrect costovertebral'):
            a.audit(self.baseline, mutated)

    def test_invalid_sternocostal_frame_rejected(self):
        mutated = copy.deepcopy(self.p005)
        mutated['joint_markers']['sternocostal_04_left']['frame_bone'] = 'rib_04_left'
        with self.assertRaisesRegex(ValueError, 'does not reference sternum'):
            a.audit(self.baseline, mutated)

    def test_nan_marker_coordinate_rejected(self):
        mutated = copy.deepcopy(self.p005)
        mutated['joint_markers']['costovertebral_02_left']['centre_m'][1] = float('nan')
        with self.assertRaisesRegex(ValueError, 'invalid costovertebral'):
            a.audit(self.baseline, mutated)

    def test_removed_rib_marker_fails_closed(self):
        mutated = copy.deepcopy(self.p005)
        del mutated['joint_markers']['costotransverse_11_left']
        with self.assertRaisesRegex(ValueError, 'joint marker inventory differs'):
            a.audit(self.baseline, mutated)

    def test_changed_bone_inventory_fails_closed(self):
        mutated = copy.deepcopy(self.p005)
        del mutated['bones']['rib_09_left']
        with self.assertRaisesRegex(ValueError, 'bone inventory differs'):
            a.audit(self.baseline, mutated)

    def test_inputs_not_modified_determinism(self):
        base = json.dumps(self.baseline, sort_keys=True)
        proposal = json.dumps(self.p005, sort_keys=True)
        self.assertEqual(a.audit(self.baseline, self.p005), a.audit(self.baseline, self.p005))
        self.assertEqual(base, json.dumps(self.baseline, sort_keys=True))
        self.assertEqual(proposal, json.dumps(self.p005, sort_keys=True))


if __name__ == '__main__':
    unittest.main()

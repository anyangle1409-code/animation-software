"""Diagnostic P005 shoulder-chain closure and marker ownership regressions."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'anatomy_fit'))
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5
import coupled_trunk_preflight as cp
import coupled_shoulder_contact_audit as contact


class P005Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.base, cls.p003)
        cls.p005 = p5.build(cls.base, cls.p004)

    def test_never_canonical(self):
        self.assertFalse(self.p005['candidate']['canonical_promotion_allowed'])
        self.assertFalse(self.p005['candidate']['freeze_ready'])
        self.assertIn('DIAGNOSTIC', self.p005['candidate']['status'])

    def test_206_bones_and_427_marker_ids_remain(self):
        self.assertEqual(set(self.base['bones']), set(self.p005['bones']))
        self.assertEqual(set(self.base['joint_markers']), set(self.p005['joint_markers']))
        self.assertEqual(len(self.p005['bones']), 206)
        self.assertEqual(len(self.p005['joint_markers']), 427)

    def test_clavicle_descendants_really_include_hands_and_arms(self):
        moved = set(self.p005['candidate']['translated_bone_ids'])
        for side in ('left', 'right'):
            for bone in ('clavicle', 'scapula', 'humerus', 'radius', 'ulna',
                         'metacarpal_1', 'metacarpal_2', 'digit2_proximal_phalanx'):
                self.assertIn(f'{bone}_{side}', moved)

    def test_entire_shoulder_subtree_receives_identical_translation(self):
        shift = self.p005['candidate']['translation_m']
        for bone in self.p005['candidate']['translated_bone_ids']:
            for end in ('head_m', 'tail_m'):
                expected = p4._add(self.p004['bones'][bone][end], shift)
                actual = self.p005['bones'][bone][end]
                for a, b in zip(actual, expected):
                    self.assertAlmostEqual(a, b, places=12, msg=bone)

    def test_ribs_sternum_and_spine_still_match_p004(self):
        for bone in cp.SPINE + cp.RIBS + ['sternum', 'sacrum']:
            self.assertEqual(self.p005['bones'][bone], self.p004['bones'][bone], msg=bone)

    def test_strict_sc_reattachment_guard_clears_but_not_anatomical(self):
        old = cp.examine(self.base, self.p004)
        new = cp.examine(self.base, self.p005)
        self.assertIn('STERNUM_SC_RELATIVE_OFFSET_CHANGED_GT_5MM', old['blockers'])
        self.assertNotIn('STERNUM_SC_RELATIVE_OFFSET_CHANGED_GT_5MM', new['blockers'])
        for value in new['sternoclavicular_reference_delta_mm'].values():
            self.assertLess(value, 1e-4)
        self.assertEqual(new['status'], 'NO_MECHANICAL_BLOCKER_ANATOMY_UNVERIFIED')
        self.assertFalse(new['safe_for_canonical_promotion'])

    def test_relative_ac_gh_control_markers_still_unchanged(self):
        for joint in ('acromioclavicular', 'glenohumeral'):
            for side in ('left', 'right'):
                key = f'{joint}_{side}'
                self.assertIn(key, self.p005['joint_markers'])
                self.assertEqual(self.p005['joint_markers'][key]['frame_bone'],
                                 self.base['joint_markers'][key]['frame_bone'])
        result = contact.audit(self.base, self.p005)
        self.assertEqual(result['rig_control_closure'], 'RELATIVE_CONTROL_VECTORS_PRESERVED')
        self.assertFalse(result['anatomical_joint_surface_verified'])
        self.assertFalse(result['scapulothoracic_surface_verified'])
        self.assertEqual(result['changes_over_engineering_5mm_guard'], {})

    def test_p004_sc_failure_is_detected_by_independent_audit(self):
        r = contact.audit(self.base, self.p004)
        self.assertEqual(r['rig_control_closure'], 'FAILED')
        self.assertEqual(len(r['changes_over_engineering_5mm_guard']), 2)
        for k in r['changes_over_engineering_5mm_guard']:
            self.assertIn('sternoclavicular_', k)

    def test_every_translated_marker_follows_its_recorded_bone(self):
        delta = self.p005['candidate']['translation_m']
        shifted = set(self.p005['candidate']['translated_bone_ids'])
        for name, marker in self.p004['joint_markers'].items():
            old = marker['centre_m']
            new = self.p005['joint_markers'][name]['centre_m']
            desired = p4._add(old, delta) if marker.get('frame_bone') in shifted else old
            for a, b in zip(new, desired):
                self.assertAlmostEqual(a, b, places=12, msg=name)

    def test_marker_frames_unmodified_by_rigid_translation(self):
        for key in self.base['joint_markers']:
            self.assertEqual(self.p005['joint_markers'][key]['frame_axes_columns_XYZ'],
                             self.p004['joint_markers'][key]['frame_axes_columns_XYZ'])

    def test_all_translated_bone_lengths_preserved(self):
        for bid in self.p005['candidate']['translated_bone_ids']:
            a, b = self.p004['bones'][bid], self.p005['bones'][bid]
            self.assertAlmostEqual(math.dist(a['head_m'], a['tail_m']),
                                   math.dist(b['head_m'], b['tail_m']), places=12)

    def test_scapulothoracic_proxy_is_numeric_but_not_surface_proof(self):
        r = contact.audit(self.base, self.p005)
        for side in ('left', 'right'):
            v = r['scapulothoracic_rib_chord_proxy'][side]
            self.assertTrue(math.isfinite(v['proxy_distance_change_mm']))
            self.assertGreater(v['baseline_marker_to_rib_chord_mm'], 0)
        self.assertFalse(r['canonical_promotion_allowed'])

    def test_both_input_objects_unmodified(self):
        p4_before = json.dumps(self.p004, sort_keys=True)
        base_before = json.dumps(self.base, sort_keys=True)
        self.assertEqual(self.p005, p5.build(self.base, self.p004))
        self.assertEqual(p4_before, json.dumps(self.p004, sort_keys=True))
        self.assertEqual(base_before, json.dumps(self.base, sort_keys=True))

    def test_invalid_p004_is_rejected(self):
        altered = copy.deepcopy(self.p004)
        altered['candidate']['id'] = 'TRUST_ME_CANONICAL'
        with self.assertRaisesRegex(ValueError, 'requires isolated P004'):
            p5.build(self.base, altered)

    def test_no_sternum_move_is_rejected(self):
        altered = copy.deepcopy(self.p004)
        altered['bones']['sternum'] = copy.deepcopy(self.base['bones']['sternum'])
        with self.assertRaisesRegex(ValueError, 'no substantive'):
            p5.build(self.base, altered)

    def test_inventory_change_rejected(self):
        altered = copy.deepcopy(self.p004)
        altered['bones'].pop('ulna_left')
        with self.assertRaisesRegex(ValueError, 'bone or joint identities differ'):
            p5.build(self.base, altered)

    def test_joint_inventory_change_rejected_by_contact_audit(self):
        altered = copy.deepcopy(self.p005)
        altered['joint_markers'].pop('acromioclavicular_left')
        with self.assertRaisesRegex(ValueError, 'bone/joint inventory changed'):
            contact.audit(self.base, altered)


if __name__ == '__main__':
    unittest.main()

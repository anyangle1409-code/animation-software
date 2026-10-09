"""P004: independent regression for coupled diagnostic ribs/sternum geometry."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import coupled_trunk_preflight as cp
import replay_p004_coupled_thorax as p4

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'


class P004Rehearsal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.candidate = p4.build(cls.base, cls.p003)

    def test_strictly_noncanonical(self):
        d = self.candidate['candidate']
        self.assertFalse(d['canonical_promotion_allowed'])
        self.assertFalse(d['freeze_ready'])
        self.assertIn('DIAGNOSTIC', d['status'])

    def test_every_spine_bone_exactly_matches_prior_source_p003(self):
        for name in cp.SPINE:
            self.assertEqual(self.candidate['bones'][name], self.p003['bones'][name])

    def test_sacrum_and_nontrunk_bones_are_identical_to_p003(self):
        changed = {
            b for b in self.candidate['bones']
            if self.candidate['bones'][b] != self.p003['bones'][b]
        }
        self.assertEqual(changed, set(cp.RIBS) | {'sternum'})
        self.assertEqual(self.candidate['bones']['sacrum'], self.base['bones']['sacrum'])

    def test_3d_rib_head_to_level_vector_is_preserved_exactly(self):
        for i in range(1, 13):
            old = p4.vertebral_anchor(self.base['bones'], i)
            new = p4.vertebral_anchor(self.candidate['bones'], i)
            for side in ('left', 'right'):
                bid = f'rib_{i:02d}_{side}'
                old_offset = p4._sub(self.base['bones'][bid]['head_m'], old)
                new_offset = p4._sub(self.candidate['bones'][bid]['head_m'], new)
                for a, b in zip(old_offset, new_offset):
                    self.assertAlmostEqual(a, b, places=10, msg=bid)

    def test_all_rib_lengths_are_exactly_preserved(self):
        for bid in cp.RIBS:
            def length(b):
                return math.dist(b['head_m'], b['tail_m'])
            self.assertAlmostEqual(length(self.base['bones'][bid]),
                                   length(self.candidate['bones'][bid]), places=12)

    def test_sternal_length_is_exactly_preserved(self):
        def length(b):
            return math.dist(b['head_m'], b['tail_m'])
        self.assertAlmostEqual(length(self.base['bones']['sternum']),
                               length(self.candidate['bones']['sternum']), places=12)

    def test_every_rib_carried_marker_moves_with_its_rib(self):
        for name, marker in self.base['joint_markers'].items():
            bone = marker.get('frame_bone')
            if bone in cp.RIBS:
                rib = self.candidate['bones'][bone]
                original_rib = self.base['bones'][bone]
                delta = p4._sub(rib['head_m'], original_rib['head_m'])
                # P003 did not adjust costovertebral/transpose rib markers.
                point = p4._add(marker['centre_m'], delta)
                for actual, expected in zip(self.candidate['joint_markers'][name]['centre_m'], point):
                    self.assertAlmostEqual(actual, expected, places=10, msg=name)

    def test_sternum_carried_markers_move_with_sternum(self):
        delta = p4._sub(self.candidate['bones']['sternum']['head_m'],
                        self.base['bones']['sternum']['head_m'])
        for name, m in self.base['joint_markers'].items():
            if m.get('frame_bone') == 'sternum':
                expected = p4._add(m['centre_m'], delta)
                actual = self.candidate['joint_markers'][name]['centre_m']
                for a, b in zip(actual, expected):
                    self.assertAlmostEqual(a, b, places=10, msg=name)

    def test_p004_replays_close_old_p003_rib_vertical_regression(self):
        p3 = cp.examine(self.base, self.p003)
        p4 = cp.examine(self.base, self.candidate)
        self.assertIn('RIB_ARTICULAR_LEVEL_Z_REGRESSION', p3['blockers'])
        self.assertNotIn('RIB_ARTICULAR_LEVEL_Z_REGRESSION', p4['blockers'])
        self.assertNotIn('RIBS_NOT_COUPLED_TO_THORAX', p4['blockers'])
        self.assertNotIn('STERNUM_NOT_COUPLED_TO_THORAX', p4['blockers'])
        self.assertTrue(p4['shoulder_anchor_follow_up_required'])
        self.assertFalse(p4['safe_for_canonical_promotion'])

    def test_every_c004_p003_bone_id_and_marker_id_is_preserved(self):
        self.assertEqual(set(self.base['bones']), set(self.candidate['bones']))
        self.assertEqual(set(self.base['joint_markers']), set(self.candidate['joint_markers']))
        self.assertEqual(len(self.candidate['bones']), 206)
        self.assertEqual(len(self.candidate['joint_markers']), 427)

    def test_all_clavicle_shoulder_positions_unchanged_and_followup_open(self):
        for b in ('clavicle_left', 'clavicle_right', 'scapula_left', 'scapula_right'):
            self.assertEqual(self.candidate['bones'][b], self.base['bones'][b])
        self.assertGreater(self.candidate['candidate']['unresolved_clavicle_followup_shift_mm'], 0)
        self.assertTrue(any('SC/AC/GH' in s for s in self.candidate['candidate']['preflight_limitations']))

    def test_inputs_unmodified_and_deterministic(self):
        base_json = json.dumps(self.base, sort_keys=True)
        p003_json = json.dumps(self.p003, sort_keys=True)
        self.assertEqual(p4.build(self.base, self.p003), self.candidate)
        self.assertEqual(base_json, json.dumps(self.base, sort_keys=True))
        self.assertEqual(p003_json, json.dumps(self.p003, sort_keys=True))


if __name__ == '__main__':
    unittest.main()

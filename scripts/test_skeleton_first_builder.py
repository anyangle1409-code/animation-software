"""Construction contract tests; replay data is never independent anatomy."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts/anatomy_fit'))
import skeleton_first_builder as b

ANAT = ROOT / 'ORIGINAL_V1_WORK/anatomy'


class SkeletonFirstBuilderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a = json.loads((ANAT / 'character_fit_r95_a003.json').read_text())
        cls.c = json.loads((ANAT / 'audit/candidates/shoulder_thorax_c004_arm_inputs/candidate_record.json').read_text())

    def contract(self):
        return b.replay_contract(self.a, 'a003')

    def test_replays_both_records_exactly(self):
        records = [('a003', self.a)] + [(p.parent.name, json.loads(p.read_text()))
            for p in sorted((ANAT / 'audit/candidates').glob('*/candidate_record.json'))]
        self.assertEqual(len(records), 5)  # preserved a003 and c001–c004
        for label, rec in records:
            with self.subTest(record=label):
                out = b.construct(b.replay_contract(rec, label))
                self.assertEqual(out['record']['bones'], rec['bones'])
                self.assertEqual(out['record']['joint_markers'], rec['joint_markers'])
                self.assertEqual(len(out['record']['bones']), 206)
                self.assertEqual(len(out['record']['joint_markers']), 427)
                self.assertFalse(out['promotion_allowed'])

    def test_replay_never_claims_evidence_or_promotion(self):
        out = b.construct(self.contract())
        self.assertFalse(out['promotion_allowed'])
        self.assertFalse(out['anatomical_acceptance'])
        self.assertFalse(out['evidence']['claims_complete'])
        self.assertEqual(out['coordinate_origin'], 'legacy_audit_replay')
        self.assertIn('spinal_disc_centre_gap_positive', [x['id'] for x in out['validation']['checks'] if x['status'] == 'FAIL'])

    def test_input_and_output_do_not_alias(self):
        c = self.contract(); old = copy.deepcopy(c)
        out = b.construct(c)
        self.assertEqual(c, old)
        out['record']['bones']['radius_left']['tail_m'][0] += 1
        self.assertEqual(c, old)

    def test_skin_outside_does_not_move_coordinates(self):
        rec = b.construct(self.contract())['record']; old = copy.deepcopy(rec)
        report = b.skin_diagnostic(rec, lambda p: -1.0)
        self.assertEqual(report['points'], 412)
        self.assertEqual(report['outside'], 412)
        self.assertEqual(rec, old)
        self.assertFalse(report['skeleton_relocation_allowed'])

    def test_skin_callback_receives_immutable_points(self):
        rec = b.construct(self.contract())['record']
        def mutate(p):
            p[0] = 4
            return 1
        with self.assertRaises(TypeError):
            b.skin_diagnostic(rec, mutate)

    def test_nonfinite_skin_result_rejected(self):
        with self.assertRaisesRegex(ValueError, 'finite clearance'):
            b.skin_diagnostic(self.a, lambda p: float('nan'))

    def test_wrong_units_or_basis_rejected(self):
        for key, value in [('units', 'mm'), ('world_basis', 'left=-X')]:
            c = self.contract(); c[key] = value
            with self.assertRaisesRegex(ValueError, key):
                b.construct(c)

    def test_mesh_origin_rejected(self):
        c = self.contract(); c['coordinate_origin'] = 'mesh_containment'
        with self.assertRaisesRegex(ValueError, 'coordinate_origin'):
            b.construct(c)

    def test_nonfinite_bone_rejected(self):
        c = self.contract(); c['record']['bones']['radius_left']['head_m'][0] = float('inf')
        with self.assertRaisesRegex(ValueError, 'finite'):
            b.construct(c)

    def test_invalid_frame_is_a_failure(self):
        c = self.contract(); c['record']['joint_markers']['glenohumeral_left']['frame_axes_columns_XYZ'][0][0] += 0.2
        out = b.construct(c)
        self.assertIn('joint_frames_proper', [x['id'] for x in out['validation']['checks'] if x['status'] == 'FAIL'])

    def test_nonfinite_frame_rejected_before_output(self):
        c = self.contract()
        c['record']['joint_markers']['glenohumeral_left']['frame_axes_columns_XYZ'][0][0] = float('nan')
        with self.assertRaisesRegex(ValueError, 'finite frame'):
            b.construct(c)

    def test_joint_constraint_rejects_nonparticipant_endpoint(self):
        c = self.contract()
        centre = c['record']['joint_markers']['digit2_mcp_left']['centre_m']
        c['record']['bones']['femur_left']['tail_m'] = list(centre)
        c['joint_constraints'] = [{'joint': 'digit2_mcp_left', 'endpoints': [['femur_left', 'tail_m']],
                                  'tolerance_m': 1e-6, 'basis': 'numerical rounding only'}]
        with self.assertRaisesRegex(ValueError, 'participant'):
            b.construct(c)

    def test_proportion_constraint_fails_without_moving_bone(self):
        c = self.contract(); c['length_constraints'] = [{'bone': 'radius_left', 'range_mm': [10, 20],
            'measurement_definition': 'TEST ONLY head_m to tail_m', 'source_ids': ['SYNTHETIC_TEST']}]
        out = b.construct(c)
        self.assertEqual(out['constraints']['status'], 'FAIL')
        self.assertEqual(out['record']['bones'], self.a['bones'])

    def test_joint_constraint_detects_detachment(self):
        c = self.contract(); c['joint_constraints'] = [{'joint': 'digit2_mcp_left',
            'endpoints': [['metacarpal_2_left', 'tail_m'], ['digit2_proximal_phalanx_left', 'head_m']],
            'tolerance_m': 1e-6, 'basis': 'numerical rounding only'}]
        c['record']['bones']['digit2_proximal_phalanx_left']['head_m'][0] += 0.001
        out = b.construct(c)
        self.assertEqual(out['constraints']['status'], 'FAIL')

    def test_invalid_constraint_references_rejected(self):
        c = self.contract(); c['length_constraints'] = [{'bone': 'missing', 'range_mm': [1, 2],
            'measurement_definition': 'test', 'source_ids': ['SYNTHETIC_TEST']}]
        with self.assertRaisesRegex(ValueError, 'constraint'):
            b.construct(c)

    def test_independent_mode_cannot_relabel_replay(self):
        c = self.contract(); c['coordinate_origin'] = 'independent_anatomy'
        out = b.construct(c)
        self.assertFalse(out['evidence']['claims_complete'])
        self.assertFalse(out['promotion_allowed'])

    def test_strict_mode_rejects_failed_or_unverified_geometry(self):
        with self.assertRaisesRegex(ValueError, 'not validated'):
            b.construct(self.contract(), strict=True)

    def test_target_profile_never_uniformly_scales_bones(self):
        c = self.contract(); c['target_profile']['sex'] = 'female'; c['target_profile']['stature_m'] = 1.65
        out = b.construct(c)
        self.assertEqual(out['record']['bones'], self.a['bones'])
        self.assertFalse(out['anatomical_acceptance'])


if __name__ == '__main__':
    unittest.main()

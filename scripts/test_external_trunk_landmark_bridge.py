"""Primary-source proxy landmark comparisons: never apply means as coordinates."""
import copy
import json
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / 'anatomy_fit'))
import external_trunk_landmark_bridge as audit_module
import replay_p004_coupled_thorax as p4
import replay_p005_shoulder_chain as p5

REGISTRY = (HERE.parent / 'ORIGINAL_V1_WORK/anatomy/audit'
            / 'external_trunk_landmark_source_registry_20261009.json')


class RealSourceComparisons(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(REGISTRY.read_text())
        cls.base = json.loads(p4.C004.read_text())
        cls.p003 = json.loads(p4.P003.read_text())
        cls.p004 = p4.build(cls.base, cls.p003)
        cls.p005 = p5.build(cls.base, cls.p004)

    def test_sources_pinned_exact_and_never_targets(self):
        r = audit_module.audit(self.base, self.source)
        self.assertEqual(r['source_ids'], ['S1_HIP_IMAI_2019', 'TID_BAKER_2021'])
        self.assertFalse(r['canonical_promotion_allowed'])
        self.assertFalse(r['candidate_or_mesh_updated'])
        self.assertEqual(len(r['blocking_gates']), 6)
        for row in self.source['source_landmarks']:
            self.assertFalse(row['model_proxy']['equivalence_verified'])

    def test_model_c004_upper_chest_proxy_is_88_point_7_mm(self):
        r = audit_module.audit(self.base, self.source)['comparisons']['TID_BAKER_2021']
        self.assertAlmostEqual(r['model_proxy_T1_superior_to_sternum_head_mm'], 88.743, places=2)
        self.assertFalse(r['within_observed_study_minmax_context'])
        self.assertFalse(r['source_landmark_equivalence_verified'])
        self.assertFalse(r['sternum_to_spine_AP_depth_measured'])

    def test_table_abstract_discrepancy_explicit(self):
        r = audit_module.audit(self.base, self.source)['comparisons']['TID_BAKER_2021']
        self.assertAlmostEqual(r['study_table1_mean_mm'], 65.9)
        self.assertAlmostEqual(r['study_abstract_mean_mm'], 66.1)
        self.assertAlmostEqual(r['study_mean_discrepancy_mm'], 0.2)
        self.assertEqual(r['study_observed_range_mm'], [52,83])

    def test_p003_t1_to_sternum_control_proxy_changes_not_anatomical_fit(self):
        r = audit_module.audit(self.p003, self.source)['comparisons']['TID_BAKER_2021']
        self.assertAlmostEqual(r['model_proxy_T1_superior_to_sternum_head_mm'], 73.182, places=2)
        self.assertTrue(r['within_observed_study_minmax_context'])
        self.assertTrue(r['not_a_patient_anatomical_fit'])

    def test_p004_p005_proxy_identical_because_sternum_and_t1_same(self):
        r4 = audit_module.audit(self.p004, self.source)
        r5 = audit_module.audit(self.p005, self.source)
        self.assertEqual(r4['comparisons']['TID_BAKER_2021'],
                         r5['comparisons']['TID_BAKER_2021'])
        self.assertFalse(r5['canonical_promotion_allowed'])

    def test_current_pelvis_y_z_are_raw_world_not_app(self):
        p = audit_module.audit(self.base, self.source)['comparisons']['S1_HIP_IMAI_2019']
        self.assertAlmostEqual(p['model_S1_minus_hip_axis_world_y_mm'], 59.268, places=2)
        self.assertAlmostEqual(p['model_S1_minus_hip_axis_world_z_mm'], 116.346, places=2)
        self.assertGreater(p['model_sagittal_yz_length_mm'], 130)
        self.assertFalse(p['model_world_to_study_APP_transform_verified'])
        self.assertFalse(p['model_endplate_and_hip_landmark_identity_verified'])
        self.assertTrue(p['not_allowed_to_apply_source_numbers_as_coordinates'])

    def test_pelvis_does_not_change_in_p003_p004_p005(self):
        expected = audit_module.audit(self.base, self.source)['comparisons']['S1_HIP_IMAI_2019']
        for candidate in (self.p003, self.p004, self.p005):
            actual = audit_module.audit(candidate, self.source)['comparisons']['S1_HIP_IMAI_2019']
            self.assertEqual(expected, actual)

    def test_study_2sd_not_mislabeled_as_1sd(self):
        x = audit_module.audit(self.base, self.source)
        self.assertTrue(x['comparisons']['S1_HIP_IMAI_2019']['study_spreads_are_2SD'])
        self.assertEqual(self.source['source_landmarks'][1]['measurement']['male_dyp_pm_2sd_mm'], 21.2)

    def test_input_immutable(self):
        before = json.dumps([self.base,self.source], sort_keys=True)
        audit_module.audit(self.base,self.source)
        self.assertEqual(before, json.dumps([self.base,self.source], sort_keys=True))

    def test_changing_world_frame_rejected(self):
        bad = copy.deepcopy(self.base)
        bad['conventions']['world'] = 'LEFT plus Y'
        with self.assertRaisesRegex(ValueError, 'world coordinate convention changed'):
            audit_module.audit(bad, self.source)

    def test_corrupt_control_point_rejected(self):
        bad = copy.deepcopy(self.base)
        bad['bones']['sacrum']['tail_m'][1] = float('nan')
        with self.assertRaisesRegex(ValueError, 'nonfinite'):
            audit_module.audit(bad, self.source)

    def test_source_metric_tampering_rejected(self):
        bad = copy.deepcopy(self.source)
        bad['source_landmarks'][0]['measurement']['table1_mean_mm'] = 65.0
        with self.assertRaisesRegex(ValueError, 'source has been modified'):
            audit_module.audit(self.base, bad)

    def test_ap_spread_tampering_rejected(self):
        bad = copy.deepcopy(self.source)
        bad['source_landmarks'][1]['measurement']['male_dyp_pm_2sd_mm'] = 10.6
        with self.assertRaisesRegex(ValueError, 'TWO SD'):
            audit_module.audit(self.base, bad)

    def test_source_promotable_flag_rejected(self):
        bad = copy.deepcopy(self.source)
        bad['canonical_promotion_allowed'] = True
        with self.assertRaisesRegex(ValueError, 'promotable'):
            audit_module.audit(self.base, bad)

    def test_bad_proxy_equivalence_flag_rejected(self):
        bad = copy.deepcopy(self.source)
        bad['source_landmarks'][0]['model_proxy']['equivalence_verified'] = True
        with self.assertRaisesRegex(ValueError, 'not approved'):
            audit_module.audit(self.base, bad)

    def test_bad_source_inventory_rejected(self):
        bad = copy.deepcopy(self.source)
        bad['source_landmarks'].pop()
        with self.assertRaisesRegex(ValueError, 'source inventory'):
            audit_module.audit(self.base, bad)

    def test_unknown_bone_inventory_rejected(self):
        bad = copy.deepcopy(self.base)
        del bad['bones']['sternum']
        with self.assertRaisesRegex(ValueError, 'missing anatomical controls'):
            audit_module.audit(bad, self.source)


if __name__ == '__main__':
    unittest.main()

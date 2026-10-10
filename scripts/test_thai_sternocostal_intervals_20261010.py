"""Adversarial original male costal-notch centre interval QA; no anatomy targets."""
import copy
import json
import unittest
from anatomy_fit.audit_thai_sternocostal_intervals import SOURCE,OLD,validate


class ThaiSternalFacetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.src=json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.old=json.loads(OLD.read_text(encoding="utf-8"))

    def audit(self,src=None,old=None):
        return validate(src if src is not None else copy.deepcopy(self.src),
                        old if old is not None else copy.deepcopy(self.old))

    def test_three_direct_source_facet_intervals(self):
        result=self.audit()
        self.assertEqual(result["source_study_means_center2_to3_3to4_4to5_mm"],
                         [29.3,25.2,19.56])
        self.assertEqual(result["successive_mean_interval_decreases_mm"],[4.1,5.64])
        self.assertEqual(result["final_to_initial_mean_interval_ratio"],0.6676)
        self.assertTrue(result["remaining_notch_levels_unresolved"])

    def test_model_legacy_sternum_uniform_spacing_is_diagnostic(self):
        result=self.audit()
        self.assertEqual(result["a003_vertical_level_spacing_2to3_3to4_4to5_diagnostic_only_mm"],
                         [35.2,31.9,31.0])
        self.assertFalse(result["true_3d_facet_centres_captured"])
        self.assertFalse(result["absolute_spatial_transforms_or_joint_centres_selected"])

    def test_cannot_promote_numerical_intervals(self):
        result=self.audit()
        self.assertFalse(result["canonical_geometry_changed"])
        self.assertFalse(result["cp1_gate6_passed"])
        self.assertFalse(result["source_noncommercial_visual_reuse_cleared"])

    def test_outside_source_training_stature(self):
        result=self.audit()
        self.assertTrue(result["target_182cm_outside_training_stature_range"])

    def test_sample_count_training_vs_heldout(self):
        d=copy.deepcopy(self.src)
        d["source"]["training_male"]=114
        with self.assertRaisesRegex(ValueError,"donor counts"):
            self.audit(d)

    def test_source_license_noncommercial_guard(self):
        d=copy.deepcopy(self.src)
        d["source"]["license_reported"]="CC BY 4.0 unrestricted"
        with self.assertRaisesRegex(ValueError,"licence"):
            self.audit(d)

    def test_stature_not_extrapolated(self):
        d=copy.deepcopy(self.src)
        d["source"]["target_stature_is_inside_study_training_range"]=True
        with self.assertRaisesRegex(ValueError,"target-stature"):
            self.audit(d)

    def test_side_specific_joints_not_claimed(self):
        d=copy.deepcopy(self.src)
        d["source"]["side_specific_measurements_published"]=True
        with self.assertRaisesRegex(ValueError,"source-sides"):
            self.audit(d)

    def test_unsupported_more_notch_data_guard(self):
        d=copy.deepcopy(self.src)
        d["endpoint_definitions"]["other_intervals_not_provided"]=False
        with self.assertRaisesRegex(ValueError,"overinterpreted"):
            self.audit(d)

    def test_source_mean_mutation_refused(self):
        d=copy.deepcopy(self.src)
        d["male_training_table_2"]["intercostal_center_distance_3_to_4_mm"]["mean"]=31.0
        with self.assertRaisesRegex(ValueError,"Table 2"):
            self.audit(d)

    def test_wrong_endpoint_definition_refused(self):
        d=copy.deepcopy(self.src)
        d["endpoint_definitions"]["ICL23"]="2nd thoracic vertebra to rib head"
        with self.assertRaisesRegex(ValueError,"semantically altered"):
            self.audit(d)

    def test_no_relative_geometry_acceptance(self):
        d=copy.deepcopy(self.src)
        d["acceptance"]["canonical_rib_contacts_selected"]=True
        with self.assertRaisesRegex(ValueError,"Cannot promote"):
            self.audit(d)

    def test_no_unverified_182cm_registration(self):
        d=copy.deepcopy(self.src)
        d["acceptance"]["normative_182cm_calibration_passed"]=True
        with self.assertRaisesRegex(ValueError,"Cannot promote"):
            self.audit(d)

    def test_old_baseline_preserved(self):
        d=copy.deepcopy(self.old)
        d["a003"]["sternocostal_depth_mm"]["3"]=29.3
        with self.assertRaisesRegex(ValueError,"baseline changed"):
            self.audit(old=d)


if __name__=="__main__":
    unittest.main()

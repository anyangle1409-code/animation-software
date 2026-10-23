"""Fail-closed tests for human reference data; NEVER certify an anatomical rig."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / "human_rom_reference.py"
SPEC = importlib.util.spec_from_file_location("human_rom_reference", MODULE)
reference = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(reference)


class HumanRangeReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = reference.load_reference()

    def test_adult_table_and_full_body_test_coverage(self):
        summary = reference.readiness(self.data)
        self.assertTrue(summary["source_backed_reference_ready"])
        self.assertEqual(summary["cdc_group_statistics_count"], 44)
        self.assertGreaterEqual(summary["named_joint_coordinates"], 40)
        self.assertGreaterEqual(summary["conceptual_pose_tests"], 19)
        self.assertEqual(summary["native_coordinate_calibration"], "NOT_GRANTED")
        self.assertEqual(summary["realistic_human_motion_approval"], "NOT_GRANTED")
        self.assertEqual(summary["hard_joint_limits_approved"], 0)

    def test_verbatim_cdc_adult_reference_examples(self):
        comparison = reference.compare_population_mean(
            self.data, "elbow_flexion", "male", "20_44", 144.6)
        self.assertEqual(comparison["group_mean_deg"], 144.6)
        self.assertEqual(comparison["confidence_interval_for_group_mean_deg"], [143.6, 145.6])
        self.assertEqual(comparison["difference_from_group_mean_deg"], 0)
        self.assertFalse(comparison["safety_limit_test"])
        self.assertIsNone(comparison["individual_possible_range"])
        other = reference.compare_population_mean(
            self.data, "shoulder_flexion", "female", "20_44", 172)
        self.assertEqual(other["group_mean_deg"], 172.0)
        older = reference.compare_population_mean(
            self.data, "elbow_extension", "male", "45_69", -0.7)
        self.assertEqual(older["confidence_interval_for_group_mean_deg"], [-1.5, 0.1])

    def test_above_and_below_mean_never_means_invalid_pose(self):
        lower = reference.compare_population_mean(
            self.data, "hip_flexion", "male", "20_44", 5)
        upper = reference.compare_population_mean(
            self.data, "hip_flexion", "male", "20_44", 180)
        self.assertLess(lower["difference_from_group_mean_deg"], 0)
        self.assertGreater(upper["difference_from_group_mean_deg"], 0)
        for observed in (lower, upper):
            self.assertEqual(observed["result"], "DESCRIPTIVE_COMPARISON_ONLY_NOT_EXERCISE_APPROVAL")
            self.assertFalse(observed["safety_limit_test"])

    def test_reject_nonfinite_angle(self):
        for angle in (float("nan"), float("inf"), float("-inf"), True, "95"):
            with self.subTest(angle=angle), self.assertRaises(ValueError):
                reference.compare_population_mean(
                    self.data, "elbow_flexion", "male", "20_44", angle)

    def test_reject_unknown_joint_reference(self):
        with self.assertRaisesRegex(ValueError, "unknown motion"):
            reference.compare_population_mean(self.data, "unknown_joint", "male", "20_44", 10)

    def test_group_ci_cannot_be_promoted_into_limit(self):
        modified = copy.deepcopy(self.data)
        modified["clinical_confidence_interval_is_an_individual_limit"] = True
        self.assertTrue(any("CI for mean" in e for e in reference.validate(modified)))
        modified = copy.deepcopy(self.data)
        modified["rom_mean_is_a_hard_limit"] = True
        self.assertTrue(any("hard limit" in e for e in reference.validate(modified)))

    def test_reject_fake_native_coordinate_approval(self):
        modified = copy.deepcopy(self.data)
        modified["coordinate_catalog"][0]["approval"] = "APPROVED"
        self.assertTrue(any("unverified rig axis/side" in e for e in reference.validate(modified)))
        modified = copy.deepcopy(self.data)
        modified["coordinate_catalog"][0]["rig_axis_binding"] = "elbow_wrong_axis"
        self.assertTrue(any("unverified rig axis/side" in e for e in reference.validate(modified)))

    def test_never_turn_clinical_average_into_hard_blender_constraint(self):
        modified = copy.deepcopy(self.data)
        modified["coordinate_catalog"][0]["hard_upper_limit_deg"] = 172.0
        self.assertTrue(any("hard joint limits" in e for e in reference.validate(modified)))

    def test_reject_confidence_intervals_that_are_missing_or_unphysical(self):
        modified = copy.deepcopy(self.data)
        modified["population_statistics"]["measurements"][0]["ci95_for_population_mean_deg"] = [200, 5]
        self.assertTrue(any("confidence interval" in e for e in reference.validate(modified)))
        modified = copy.deepcopy(self.data)
        modified["population_statistics"]["measurements"][0]["mean_deg"] = float("nan")
        self.assertTrue(any("nonfinite" in e for e in reference.validate(modified)))

    def test_group_source_and_coverage_fail_closed(self):
        modified = copy.deepcopy(self.data)
        modified["population_statistics"]["measurements"].pop()
        self.assertTrue(any("incomplete adult" in e for e in reference.validate(modified)))
        modified = copy.deepcopy(self.data)
        modified["population_statistics"]["measurements"][0]["source_id"] = "missing-paper"
        self.assertTrue(any("CDC reference source mismatch" in e for e in reference.validate(modified)))

    def test_shoulder_complex_not_identical_to_glenohumeral_component(self):
        by_id = {c["id"]: c for c in self.data["coordinate_catalog"]}
        self.assertEqual(by_id["hgpt.coordinate.shoulder_complex_flexion"]["cdc_reference_key"],
                         "shoulder_flexion")
        self.assertIsNone(by_id["hgpt.coordinate.glenohumeral_flexion"]["cdc_reference_key"])
        altered = copy.deepcopy(self.data)
        next(c for c in altered["coordinate_catalog"]
             if c["id"] == "hgpt.coordinate.glenohumeral_flexion")["cdc_reference_key"] = "shoulder_flexion"
        self.assertTrue(any("confuse CDC shoulder complex" in e for e in reference.validate(altered)))

    def test_unexecuted_pose_tests_never_pass(self):
        altered = copy.deepcopy(self.data)
        altered["motion_test_program"][0]["native_acceptance"] = "PASS"
        self.assertTrue(any("executed Blender validation" in e for e in reference.validate(altered)))
        altered = copy.deepcopy(self.data)
        altered["motion_test_program"][0]["blender_pose_recipe"] = "fake pose"
        self.assertTrue(any("executed Blender validation" in e for e in reference.validate(altered)))

    def test_full_body_and_compound_tests_present(self):
        tests = {t["id"] for t in self.data["motion_test_program"]}
        for name in ("shoulder_flexion", "elbow_flexion_supinated", "forearm_rotation",
                     "hip_flexion_extension", "knee_flexion_extension",
                     "ankle_dorsi_plantarflexion", "foot_roll_toe_off",
                     "compound_overhead_press", "compound_squat", "compound_dumbbell_curl"):
            self.assertIn("hgpt.motion_test." + name, tests)

    def test_secondary_aaos_and_spine_studies_are_separate(self):
        context = self.data["secondary_reference_context"]
        self.assertEqual(context["safety_approval"], "NOT_GRANTED")
        nominal = {r["movement"]: r for r in context["aaos_illustrative_goniometry"]}
        spine = {r["movement"]: r for r in context["young_adult_spine_means"]}
        self.assertEqual(nominal["wrist_flexion"]["nominal_deg"], 80)
        self.assertEqual(nominal["shoulder_complex_abduction"]["nominal_deg"], 180)
        self.assertFalse(nominal["shoulder_complex_abduction"]["hard_limit"])
        self.assertEqual(spine["cervical_flexion"]["mean_deg"], 57.7)
        self.assertEqual(spine["cervical_flexion"]["sd_deg"], 8.2)
        self.assertEqual(spine["lumbar_rotation_left"]["mean_deg"], 38.6)
        self.assertNotEqual(spine["cervical_flexion"]["source_id"],
                            self.data["population_statistics"]["population_source"])

    def test_reject_bad_secondary_limit_and_missing_spine_record(self):
        altered = copy.deepcopy(self.data)
        altered["secondary_reference_context"]["aaos_illustrative_goniometry"][0]["hard_limit"] = True
        self.assertTrue(any("source/limit guard" in e for e in reference.validate(altered)))
        altered = copy.deepcopy(self.data)
        altered["secondary_reference_context"]["young_adult_spine_means"][0]["sd_deg"] = float("nan")
        self.assertTrue(any("invalid SD/mean" in e for e in reference.validate(altered)))
        altered = copy.deepcopy(self.data)
        altered["secondary_reference_context"]["young_adult_spine_means"].pop()
        self.assertTrue(any("incomplete source-specific" in e for e in reference.validate(altered)))

    def test_deferred_highlighting_not_implemented(self):
        self.assertEqual(self.data["future_display"]["muscle_highlighting"], "DEFERRED_BY_OWNER")
        altered = copy.deepcopy(self.data)
        altered["future_display"]["muscle_highlighting"] = "READY"
        self.assertTrue(any("highlight appearance" in e for e in reference.validate(altered)))

    def test_no_blender_dependency_or_model_save(self):
        code = MODULE.read_text(encoding="utf-8")
        self.assertNotIn("import bpy", code)
        self.assertNotIn("save_as_mainfile", code)
        self.assertNotIn("bpy.ops", code)


if __name__ == "__main__":
    unittest.main()

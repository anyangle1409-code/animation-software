"""Tests for declaration-scoped shoulder-yoke weight analysis."""
import unittest

import original_v1_shoulder_yoke_weights as weights


class ShoulderYokeWeightTests(unittest.TestCase):
    def test_non_deform_groups_are_excluded_before_normalisation(self):
        row = {"upperarm_l": 0.4, "clavicle_l": 0.6, "HGPT_UNDER_SHORTS": 1.0}
        self.assertEqual(
            weights.normalise_deform_row(row, {"upperarm_l", "clavicle_l"}),
            {"clavicle_l": 0.6, "upperarm_l": 0.4},
        )

    def test_cross_side_and_excessive_dominance_are_reported(self):
        row = {"upperarm_l": 0.94, "clavicle_l": 0.04, "upperarm_r": 0.02}
        result = weights.classify_vertex(row, "l")
        self.assertEqual(result["cross_side_bones"], ["upperarm_r"])
        self.assertEqual(result["dominant_bone"], "upperarm_l")
        self.assertTrue(result["excessive_single_bone_dominance"])

    def test_missing_shared_influence_requires_two_meaningful_bones(self):
        single = weights.classify_vertex({"upperarm_l": 0.97, "clavicle_l": 0.03}, "l")
        shared = weights.classify_vertex({"upperarm_l": 0.7, "clavicle_l": 0.2, "scapula_l": 0.1}, "l")
        self.assertTrue(single["missing_shared_influence"])
        self.assertFalse(shared["missing_shared_influence"])

    def test_mirror_comparison_swaps_lateral_bone_names(self):
        left = {"upperarm_l": 0.6, "clavicle_l": 0.25, "spine_03": 0.15}
        right = {"upperarm_r": 0.58, "clavicle_r": 0.27, "spine_03": 0.15}
        result = weights.compare_mirror_rows(left, right)
        self.assertAlmostEqual(result["l1_error"], 0.04)
        self.assertEqual(result["largest_difference"]["bone"], "upperarm_l")

    def test_edge_gradient_uses_union_of_deform_bones(self):
        a = {"upperarm_l": 0.75, "clavicle_l": 0.25}
        b = {"upperarm_l": 0.25, "scapula_l": 0.75}
        self.assertAlmostEqual(weights.edge_l1(a, b), 1.5)


if __name__ == "__main__":
    unittest.main()

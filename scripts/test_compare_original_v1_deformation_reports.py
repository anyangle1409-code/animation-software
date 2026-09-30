from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare_original_v1_deformation_reports.py")
SPEC = importlib.util.spec_from_file_location("deformation_compare", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


TOLS = {
    "volume_deviation_from_1_rise": 0.005,
    "edge_ratio_p01_drop": 0.02,
    "edge_ratio_p99_rise": 0.05,
    "region_min_ratio_drop": 0.02,
    "region_max_ratio_rise": 0.1,
    "self_intersecting_face_pairs_rise": 5,
    "lowest_z_drop_m": 0.001,
    "grip_penetration_rise_mm": 0.25,
    "grip_contact_fraction_drop": 0.01,
}


def pose(name="press_top", **overrides):
    data = {
        "pose": name,
        "volume_ratio": 1.0,
        "edge_ratio_p01": 0.7,
        "edge_ratio_p99": 1.4,
        "self_intersecting_face_pairs": 20,
        "lowest_z": 0.0,
        "by_region": {
            "shoulder": {
                "min_ratio": 0.6,
                "max_ratio": 1.8,
            }
        },
    }
    data.update(overrides)
    return data


class DeformationComparatorTests(unittest.TestCase):
    def test_no_pose_regression_when_failures_drop(self):
        self.assertEqual(
            mod.compare_counts({"press_top": 5, "curl_peak": 4}, {"press_top": 3, "curl_peak": 4}, "pose"),
            [],
        )

    def test_pose_regression_is_reported(self):
        regressions = mod.compare_counts({"press_top": 5}, {"press_top": 6}, "pose")
        self.assertEqual(len(regressions), 1)
        self.assertEqual(regressions[0]["reason"], "failed_check_count_increased")

    def test_missing_baseline_pose_is_regression(self):
        regressions = mod.compare_counts({"pushup_bottom": 1}, {}, "pose")
        self.assertEqual(len(regressions), 1)
        self.assertEqual(regressions[0]["reason"], "missing_from_candidate")

    def test_new_pose_does_not_hide_existing_pose_regression(self):
        regressions = mod.compare_counts(
            {"press_top": 5, "curl_peak": 4},
            {"press_top": 6, "curl_peak": 1, "new_pose": 0},
            "pose",
        )
        self.assertEqual(len(regressions), 1)
        self.assertEqual(regressions[0]["name"], "press_top")

    def test_severity_regression_detected_even_if_failure_count_can_stay_same(self):
        base = [pose()]
        cand = [pose(by_region={"shoulder": {"min_ratio": 0.59, "max_ratio": 4.0}})]
        regressions, improvements = mod.compare_pose_severity(base, cand, TOLS)
        self.assertTrue(any(r["metric"] == "region_max_ratio" for r in regressions))
        self.assertFalse(any(i["metric"] == "region_max_ratio" for i in improvements))

    def test_small_numerical_drift_is_tolerated(self):
        base = [pose()]
        cand = [
            pose(
                volume_ratio=1.004,
                edge_ratio_p01=0.685,
                edge_ratio_p99=1.445,
                self_intersecting_face_pairs=24,
                lowest_z=-0.0008,
                by_region={"shoulder": {"min_ratio": 0.585, "max_ratio": 1.89}},
            )
        ]
        regressions, _ = mod.compare_pose_severity(base, cand, TOLS)
        self.assertEqual(regressions, [])

    def test_material_pose_improvement_is_recorded(self):
        base = [pose(by_region={"shoulder": {"min_ratio": 0.2, "max_ratio": 8.0}})]
        cand = [pose(by_region={"shoulder": {"min_ratio": 0.4, "max_ratio": 5.0}})]
        regressions, improvements = mod.compare_pose_severity(base, cand, TOLS)
        self.assertEqual(regressions, [])
        metrics = {i["metric"] for i in improvements}
        self.assertIn("region_min_ratio", metrics)
        self.assertIn("region_max_ratio", metrics)

    def test_self_intersection_increase_beyond_tolerance_is_regression(self):
        base = [pose(self_intersecting_face_pairs=100)]
        cand = [pose(self_intersecting_face_pairs=106)]
        regressions, _ = mod.compare_pose_severity(base, cand, TOLS)
        self.assertTrue(any(r["metric"] == "self_intersecting_face_pairs" for r in regressions))

    def test_grip_penetration_severity_regression(self):
        base = [{
            "pose": "curl_handle",
            "grip_l": {"max_penetration_mm": 2.0, "contact_vertices_within_2mm": 100, "finger_vertices": 1000},
        }]
        cand = [{
            "pose": "curl_handle",
            "grip_l": {"max_penetration_mm": 2.4, "contact_vertices_within_2mm": 100, "finger_vertices": 1000},
        }]
        regressions, _ = mod.compare_grip_severity(base, cand, TOLS)
        self.assertTrue(any(r["metric"] == "grip_penetration_mm" for r in regressions))

    def test_grip_contact_compares_fraction_not_raw_vertex_count(self):
        base = [{
            "pose": "curl_handle",
            "grip_l": {"max_penetration_mm": 1.0, "contact_vertices_within_2mm": 100, "finger_vertices": 1000},
        }]
        cand = [{
            "pose": "curl_handle",
            "grip_l": {"max_penetration_mm": 1.0, "contact_vertices_within_2mm": 150, "finger_vertices": 2000},
        }]
        regressions, _ = mod.compare_grip_severity(base, cand, TOLS)
        self.assertTrue(any(r["metric"] == "grip_contact_fraction" for r in regressions))


if __name__ == "__main__":
    unittest.main()

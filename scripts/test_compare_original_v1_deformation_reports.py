from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("compare_original_v1_deformation_reports.py")
SPEC = importlib.util.spec_from_file_location("deformation_compare", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


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


if __name__ == "__main__":
    unittest.main()

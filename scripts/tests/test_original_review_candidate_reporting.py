import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from original_review_candidate_checks import acceptance

class ReviewReportingTests(unittest.TestCase):
    def check(self, **overrides):
        args = dict(invariants={"bones": True}, front_exit=0, front_log="Ran 2 tests\nOK\n",
                    press_rows=[{"ht": 166.0, "volume_pct": 1.6, "pairs": 0, "collapse": 0}],
                    regressions=[], guard_report={"violations": [], "sample_count": 82, "paths": ["press", "benchmark_press"]})
        args.update(overrides)
        for row in args["press_rows"]:
            row.setdefault("pairs", 0)
            row.setdefault("collapse", 0)
        return acceptance(**args)["passed"]

    def test_successful_measurements_remain_pending_visual_review(self):
        self.assertTrue(self.check())

    def test_process_failure_after_ok_is_rejected(self):
        self.assertFalse(self.check(front_exit=139))

    def test_existing_lockout_volume_limit_is_preserved(self):
        self.assertFalse(self.check(press_rows=[{"ht": 166.0, "volume_pct": 2.6}]))

    def test_exact_volume_boundary_is_rejected(self):
        self.assertFalse(self.check(press_rows=[{"ht": 166.0, "volume_pct": -2.5}]))

    def test_residual_original_guard_failure_is_rejected(self):
        self.assertFalse(self.check(guard_report={"violations": [{"t": 0.6, "pairs": 1}], "sample_count": 82, "paths": ["press", "benchmark_press"]}))

    def test_missing_guard_measurement_is_rejected(self):
        self.assertFalse(self.check(guard_report=None))

    def test_nonfinite_lockout_volume_is_rejected(self):
        self.assertFalse(self.check(press_rows=[{"ht": 166.0, "volume_pct": float("nan")}]))

    def test_original_zero_collision_rule_above_95_is_preserved(self):
        self.assertFalse(self.check(press_rows=[{"ht": 166.0, "volume_pct": 1.6, "pairs": 1, "collapse": 0}]))

if __name__ == "__main__":
    unittest.main()


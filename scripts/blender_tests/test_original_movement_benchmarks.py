import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "anatomy_fit"))

import build_original_movement_benchmarks_blender as m1


class OriginalMovementBenchmarkNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m1.run(None)

    def test_three_benchmarks_with_all_frames(self):
        self.assertEqual(sorted(self.report["benchmarks"]), ["bent_over_row", "shoulder_press", "squat"])
        for b in self.report["benchmarks"].values():
            self.assertEqual(len(b["frames"]), m1.FRAMES)

    def test_first_frame_is_rest_and_unapproved(self):
        self.assertFalse(self.report["approved"])
        for name in ("squat", "bent_over_row"):
            f0 = self.report["benchmarks"][name]["frames"][0]
            self.assertEqual(f0["self_intersecting_pairs"], 0, name)
            self.assertEqual(f0["body_volume_change_pct"], 0.0, name)

    def test_feet_stay_on_the_floor(self):
        for name, b in self.report["benchmarks"].items():
            for f in b["frames"]:
                self.assertLess(abs(f["lowest_point_z_mm"]), 1.0, (name, f["t"]))

    def test_peak_angles_respect_cdc_except_recorded_ankle(self):
        for name, b in self.report["benchmarks"].items():
            for f in b["frames"]:
                self.assertTrue(set(f["exceeds_cdc_passive_mean"]) <= {"ankle_dorsiflexion"}, (name, f["exceeds_cdc_passive_mean"]))

    def test_metrics_are_finite(self):
        for b in self.report["benchmarks"].values():
            for f in b["frames"]:
                for k in ("area_ratio_min", "area_ratio_max", "body_volume_change_pct"):
                    self.assertTrue(math.isfinite(f[k]))


if __name__ == "__main__":
    unittest.main(argv=[__file__])

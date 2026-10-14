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

    def test_nine_benchmarks_with_all_frames(self):
        self.assertEqual(sorted(self.report["benchmarks"]),
                         ["bent_over_row", "calf_raise", "grip", "lunge", "shoulder_press", "single_leg_stance", "squat",
                          "trunk_rotation", "walk_stride"])
        for b in self.report["benchmarks"].values():
            self.assertEqual(len(b["frames"]), m1.FRAMES)

    def test_first_frame_is_rest_and_unapproved(self):
        self.assertFalse(self.report["approved"])
        for name in ("squat", "bent_over_row", "calf_raise"):               # no arm carriage: exact rest
            f0 = self.report["benchmarks"][name]["frames"][0]
            self.assertEqual(f0["self_intersecting_pairs"], 0, name)
            self.assertEqual(f0["body_volume_change_pct"], 0.0, name)
        for name in ("lunge", "trunk_rotation", "single_leg_stance"):      # H1: standing with the 4 deg arm carriage
            f0 = self.report["benchmarks"][name]["frames"][0]
            self.assertEqual(f0["self_intersecting_pairs"], 0, name)
            self.assertLess(abs(f0["body_volume_change_pct"]), 0.5, name)

    def test_no_hand_thigh_contact_with_arm_carriage(self):
        for name in ("walk_stride", "lunge", "trunk_rotation", "single_leg_stance"):
            for f in self.report["benchmarks"][name]["frames"]:
                for a, b, n in f["self_intersection_classes_top"]:
                    hand = any(x.split("_")[0] in ("thumb", "index", "middle", "ring", "pinky", "hand", "metacarpal") for x in (a, b))
                    thigh = any(x.startswith("thigh") for x in (a, b))
                    self.assertFalse(hand and thigh, (name, f["t"], a, b, n))

    def test_feet_stay_on_the_floor(self):
        for name, b in self.report["benchmarks"].items():
            for f in b["frames"]:
                self.assertLess(abs(f["lowest_point_z_mm"]), 1.0, (name, f["t"]))

    def test_peak_angles_respect_cdc_except_recorded_ankle(self):
        for name, b in self.report["benchmarks"].items():
            for f in b["frames"]:
                self.assertTrue(set(f["exceeds_cdc_passive_mean"]) <= {"ankle_dorsiflexion"}, (name, f["exceeds_cdc_passive_mean"]))

    def test_walk_cycle_closes_and_is_left_right_symmetric(self):
        frames = self.report["benchmarks"]["walk_stride"]["frames"]
        self.assertEqual(frames[0]["self_intersecting_pairs"], frames[-1]["self_intersecting_pairs"])
        half = len(frames) // 2
        for a, b in zip(frames[:half], frames[half:]):          # second half = first half with sides swapped
            self.assertEqual(a["self_intersecting_pairs"], b["self_intersecting_pairs"], (a["t"], b["t"]))

    def test_grip_closes_toward_the_palm_on_both_hands_mirror_symmetrically(self):
        frames = self.report["benchmarks"]["grip"]["frames"]
        a0, a1 = frames[0]["angles_deg"], frames[-1]["angles_deg"]
        for s in ("l", "r"):
            self.assertLess(a1[f"fingertip_to_wrist_mm_{s}"], 0.5 * a0[f"fingertip_to_wrist_mm_{s}"], s)
        for f in frames:
            # a wrong per-side flexion sign (the rig's digit axes are not mirrored) shows up here as centimetres
            self.assertLess(f["angles_deg"]["digit_tip_mirror_error_mm"], 0.5, f["t"])
        self.assertEqual(frames[-1]["collapse_lt_0_1"], 0)

    def test_calf_raise_lifts_the_heels_monotonically_within_cdc_plantarflexion(self):
        frames = self.report["benchmarks"]["calf_raise"]["frames"]
        rise = [f["angles_deg"]["heel_rise_mm"] for f in frames]
        self.assertEqual(rise, sorted(rise))
        self.assertGreater(rise[-1], 50.0)
        self.assertLess(frames[-1]["angles_deg"]["ankle_plantarflexion"], self.report["cdc_passive_means_deg"]["ankle_plantarflexion"])

    def test_metrics_are_finite(self):
        for b in self.report["benchmarks"].values():
            for f in b["frames"]:
                for k in ("area_ratio_min", "area_ratio_max", "body_volume_change_pct"):
                    self.assertTrue(math.isfinite(f[k]))


if __name__ == "__main__":
    unittest.main(argv=[__file__])

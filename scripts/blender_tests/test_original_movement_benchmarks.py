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

    def test_thirteen_benchmarks_with_all_frames(self):
        self.assertEqual(sorted(self.report["benchmarks"]),
                         ["bent_over_row", "calf_raise", "deadlift", "forearm_rotation", "grip", "lunge", "push_up",
                          "shoulder_press", "single_leg_stance", "squat", "trunk_rotation", "walk_stride", "wrist_circuit"])
        for b in self.report["benchmarks"].values():
            self.assertEqual(len(b["frames"]), m1.FRAMES)

    def test_first_frame_is_rest_and_unapproved(self):
        self.assertFalse(self.report["approved"])
        for name in ("squat", "bent_over_row", "calf_raise"):   # no arm carriage at t = 0 (squat ramps in from 0): exact rest
            f0 = self.report["benchmarks"][name]["frames"][0]
            self.assertEqual(f0["self_intersecting_pairs"], 0, name)
            self.assertEqual(f0["body_volume_change_pct"], 0.0, name)
        # H1: standing with the 4 deg arm carriage; the deadlift too since 15 Oct 2026 (grip just outside the legs from the
        # start: without it the hanging hands met the thighs, 44-116 hand-thigh intersections per frame on R13)
        for name in ("lunge", "trunk_rotation", "single_leg_stance", "deadlift"):
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
                allowed = {"ankle_dorsiflexion"} | {"push_up": {"wrist_extension"}, "deadlift": {"hip_flexion"}}.get(name, set())  # recorded findings
                self.assertTrue(set(f["exceeds_cdc_passive_mean"]) <= allowed, (name, f["exceeds_cdc_passive_mean"]))

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

    def test_forearm_rotation_reaches_atlas_range_without_candy_wrapper(self):
        frames = self.report["benchmarks"]["forearm_rotation"]["frames"]
        lim = self.report["cdc_passive_means_deg"]
        self.assertAlmostEqual(max(f["angles_deg"]["forearm_pronation"] for f in frames), lim["forearm_pronation"], places=1)
        self.assertAlmostEqual(max(f["angles_deg"]["forearm_supination"] for f in frames), lim["forearm_supination"], places=1)
        for f in frames:
            for s in ("l", "r"):
                self.assertGreater(f["angles_deg"][f"forearm_min_slice_radius_ratio_{s}"], 0.85, (f["t"], s))
            self.assertEqual(f["collapse_lt_0_1"], 0, f["t"])

    def test_wrist_circuit_visits_each_atlas_peak(self):
        frames = self.report["benchmarks"]["wrist_circuit"]["frames"]
        lim = self.report["cdc_passive_means_deg"]
        for k in ("wrist_flexion", "wrist_extension", "wrist_radial_deviation", "wrist_ulnar_deviation"):
            self.assertAlmostEqual(max(f["angles_deg"][k] for f in frames), lim[k], places=1)
        for f in frames:
            self.assertEqual(f["collapse_lt_0_1"], 0, f["t"])

    def test_deadlift_start_meets_bar_invariants(self):
        end = self.report["benchmarks"]["deadlift"]["frames"][-1]["angles_deg"]
        lim = m1.DEADLIFT_LIMITS
        self.assertLessEqual(abs(end["bar_offset_from_midfoot_mm"]), lim["bar_offset_abs_mm"])
        self.assertTrue(lim["bar_height_mm"][0] <= end["bar_height_mm"] <= lim["bar_height_mm"][1], end["bar_height_mm"])
        self.assertTrue(lim["ankle_dorsiflexion"][0] <= end["ankle_dorsiflexion"] <= lim["ankle_dorsiflexion"][1])
        start = self.report["benchmarks"]["deadlift"]["frames"][0]
        self.assertEqual(start["self_intersecting_pairs"], 0)

    def test_push_up_contacts_solved_and_trunk_clear_of_floor(self):
        frames = self.report["benchmarks"]["push_up"]["frames"]
        for f in frames:
            a = f["angles_deg"]
            self.assertLess(abs(a["palm_floor_error_mm"]), 0.5, f["t"])
            self.assertLess(abs(a["hand_position_error_mm"]), 0.5, f["t"])
            self.assertGreater(a["trunk_floor_clearance_mm"], 0.0, f["t"])
            self.assertLess(abs(f["lowest_point_z_mm"]), 1.0, f["t"])
        self.assertAlmostEqual(frames[-1]["angles_deg"]["elbow_flexion"], m1.PUSHUP["elbow_bottom"], places=3)

    def test_push_up_thumb_lies_beside_the_index_without_web_intersection(self):
        # 15 Oct 2026: the 40 deg CMC extension alone pressed the thumb metacarpal into the index metacarpal (thumb-web
        # self-intersections on every frame); PUSHUP["thumb_axial"] turns the thumb metacarpal so it lies flat beside it
        self.assertEqual(m1.PUSHUP["thumb_axial"], 10.0)
        for f in self.report["benchmarks"]["push_up"]["frames"]:
            for a, b, n in f["self_intersection_classes_top"]:
                self.assertFalse(a.startswith("thumb_01") or b.startswith("thumb_01"), (f["t"], a, b, n))
            self.assertLess(abs(f["lowest_point_z_mm"]), 1.0, f["t"])

    def test_squat_and_deadlift_hands_clear_of_thighs(self):
        hand = ("thumb", "index", "middle", "ring", "pinky", "hand", "metacarpal")
        for name in ("squat", "deadlift"):
            for f in self.report["benchmarks"][name]["frames"]:
                for a, b, n in f["self_intersection_classes_top"]:
                    self.assertFalse((a.split("_")[0] in hand) != (b.split("_")[0] in hand), (name, f["t"], a, b, n))

    def test_metrics_are_finite(self):
        for b in self.report["benchmarks"].values():
            for f in b["frames"]:
                for k in ("area_ratio_min", "area_ratio_max", "body_volume_change_pct"):
                    self.assertTrue(math.isfinite(f[k]))


if __name__ == "__main__":
    unittest.main(argv=[__file__])

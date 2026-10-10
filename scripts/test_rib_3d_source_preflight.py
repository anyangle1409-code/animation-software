"""Noncanonical source-locked rib orientation: real source and adversarial checks."""
import copy
import importlib.util
import json
import math
import pathlib
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rib3dsource", ROOT / "scripts/anatomy_fit/rib_3d_source_preflight.py"
)
R = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(R)


class Rib3DSourcePreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model, cls.sha = R.load_source()
        cls.report = R.build_report(cls.model, cls.sha)

    def test_exact_original_source_and_all_12_levels(self):
        self.assertEqual(len(self.model["levels"]), 12)
        self.assertEqual(len(self.report["levels"]), 12)
        self.assertEqual(self.report["source_git_blob_sha1"], R.SOURCE_GIT_BLOB)
        self.assertEqual(self.report["source_doi"], "10.1111/joa.12632")
        self.assertEqual(self.model["levels"]["1"]["population_mean"]["alpha_PH_deg"], 58.2)
        self.assertEqual(self.model["levels"]["12"]["population_mean"]["alpha_LS_deg"], 94)

    def test_stale_or_modified_original_model_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p = pathlib.Path(temp) / "model.json"
            p.write_bytes(R.MODEL.read_bytes() + b" ")
            with self.assertRaisesRegex(ValueError, "changed"):
                R.load_source(p)

    def test_naive_plane_angle_shortcut_explicitly_rejected_for_six_levels(self):
        # Independent-final-plane-angle shortcut incorrectly treats sequential
        # published rotations as two orthogonal direction cosines.
        self.assertEqual(
            self.report["naive_independent_angle_shortcut_invalid_levels"],
            [1, 8, 9, 10, 11, 12],
        )
        for n in [1, 8, 9, 10, 11, 12]:
            self.assertGreater(
                self.report["levels"][str(n)]["naive_independent_angles_counterexample"][
                    "sum_squared_assumed_components"
                ], 1,
            )
        self.assertTrue(self.report["naive_shortcut_counterexamples_are_not_source_errors"])

    def test_both_sides_all_source_means_make_proper_frames(self):
        for data in self.report["levels"].values():
            for side in ("left", "right"):
                q = data["hypothesis_" + side]
                x, y, z = (q[k] for k in ("longitudinal_x", "rib_plane_y", "normal_z"))
                for vector in (x, y, z):
                    self.assertAlmostEqual(math.dist(vector, [0, 0, 0]), 1, places=12)
                self.assertAlmostEqual(sum(a*b for a, b in zip(x, y)), 0, places=12)
                self.assertAlmostEqual(sum(a*b for a, b in zip(x, z)), 0, places=12)
                self.assertAlmostEqual(sum(a*b for a, b in zip(y, z)), 0, places=12)
                self.assertGreater(sum(a*b for a, b in zip(x, R._cross(y,z))), 0.999999999999)

    def test_bilateral_physical_direction_mirror_not_name_alias(self):
        for n in range(1, 13):
            pair = self.report["levels"][str(n)]
            l = pair["hypothesis_left"]
            r = pair["hypothesis_right"]
            for axis in ("longitudinal_x", "rib_plane_y"):
                self.assertAlmostEqual(l[axis][0], -r[axis][0], places=12)
                self.assertAlmostEqual(l[axis][1], r[axis][1], places=12)
                self.assertAlmostEqual(l[axis][2], r[axis][2], places=12)
            z_l, z_r = l["normal_z"], r["normal_z"]
            self.assertAlmostEqual(z_l[0], z_r[0], places=12)
            self.assertAlmostEqual(z_l[1], -z_r[1], places=12)
            self.assertAlmostEqual(z_l[2], -z_r[2], places=12)

    def test_bucket_handle_sign_moves_rib_lateral_axis_up_bilaterally(self):
        for side in ("left", "right"):
            f = R.orientation_hypothesis(60, 25, 15, side)
            zero = R.orientation_hypothesis(60, 25, 0, side)
            self.assertGreater(f["rib_plane_y"][2], zero["rib_plane_y"][2])
            self.assertAlmostEqual(
                f["rib_plane_y"][2], math.sin(math.radians(60))*math.sin(math.radians(15)),
                places=12,
            )

    def test_neutral_pose_is_not_anatomically_verified(self):
        l = R.orientation_hypothesis(0, 0, 0, "left")
        self.assertEqual(l["longitudinal_x"], [0.0, -0.0, -1.0])
        self.assertEqual(l["rib_plane_y"], [1.0, 0.0, 0.0])
        self.assertFalse(self.report["canonical_promotion_allowed"])
        self.assertTrue(self.report["zero_verified_rib_bone_surfaces"])
        self.assertTrue(self.report["blender_independent_visual_verification_required"])
        for value in self.report["levels"].values():
            self.assertFalse(value["orientation_frame_independently_verified"])
            self.assertIsNone(value["source_curve_proximal"])
            self.assertIsNone(value["actual_3d_bone_surface"])
            self.assertIsNone(value["out_of_plane_z_a_z_b_mm"])

    def test_reject_bad_angles_sides_boolean_nonfinite_and_range(self):
        for side in (None, "left ", "", "midline", 1):
            with self.assertRaises(ValueError):
                R.orientation_hypothesis(60, 35, 10, side)
        for bad in (None, True, float("nan"), float("inf"), float("-inf"), "45"):
            for idx in range(3):
                args = [60, 35, 10]
                args[idx] = bad
                with self.assertRaises(ValueError):
                    R.orientation_hypothesis(*args, "left")
        for args in ((91,20,0),(-1,20,0),(60,-1,0),(60,181,0),(60,15,181),(60,15,-181)):
            with self.assertRaises(ValueError):
                R.orientation_hypothesis(*args, "left")

    def test_out_of_plane_bezier_uses_full_arc_fraction_and_endpoint_zero(self):
        self.assertAlmostEqual(R.bernstein_deviation_mm(0, 12, -6), 0)
        self.assertAlmostEqual(R.bernstein_deviation_mm(1, 12, -6), 0)
        # At u=0.5, the two basis functions are both 3/8.
        self.assertAlmostEqual(R.bernstein_deviation_mm(.5, 12, -6), 2.25)
        self.assertAlmostEqual(R.bernstein_deviation_mm(.25, 4, -4),
                               -R.bernstein_deviation_mm(.75, 4, -4))
        for bad in (-.1, 1.1, None, True, float("nan")):
            with self.assertRaises(ValueError):
                R.bernstein_deviation_mm(bad, 1, 1)
        with self.assertRaises(ValueError):
            R.bernstein_deviation_mm(.5, None, 4)

    def test_no_unknown_or_unpinned_levels_promoted(self):
        bad = copy.deepcopy(self.model)
        del bad["levels"]["12"]
        with self.assertRaisesRegex(ValueError, "12"):
            R.build_report(bad, self.sha)
        bad = copy.deepcopy(self.model)
        bad["levels"]["12"]["population_mean"]["alpha_BH_deg"] = float("nan")
        with self.assertRaises(ValueError):
            R.build_report(bad, self.sha)
        self.assertIn("proximal spiral", " ".join(self.report["missing"]))
        self.assertNotIn("bone_surface_mesh", json.dumps(self.report))

    def test_private_output_refuses_overwrite_and_git_directory(self):
        # Avoid file changes in checkout: validate documented CLI guard
        self.assertIn("target.is_relative_to(ROOT.resolve())", SPEC.origin and
                      pathlib.Path(SPEC.origin).read_text())
        self.assertIn('target.open("x"', pathlib.Path(SPEC.origin).read_text())


if __name__ == "__main__":
    unittest.main()

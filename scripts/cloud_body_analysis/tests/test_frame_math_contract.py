"""Numerical synthetic frame checks, never anatomy approval."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "frame_math_contract.py"
spec = importlib.util.spec_from_file_location("frame_math_contract", SOURCE)
fm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fm)


class FrameMathContractTests(unittest.TestCase):
    def setUp(self):
        self.frame = fm.triad((0, 0, 0), (0, 0, 1), (1, 0, 0))

    def test_right_handed_orthonormal(self):
        self.assertAlmostEqual(self.frame["determinant"], 1)
        self.assertEqual(self.frame["axes"], ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)))

    def test_translation_invariant(self):
        other = fm.triad((1, 2, 3), (1, 2, 4), (2, 2, 3))
        self.assertAlmostEqual(fm.rotation_angle_degrees(self.frame, other), 0, places=6)

    def test_synthetic_quarter_turn(self):
        other = fm.triad((0, 0, 0), (0, 0, 1), (0, 1, 0))
        self.assertAlmostEqual(fm.rotation_angle_degrees(self.frame, other), 90, places=6)

    def test_synthetic_half_turn(self):
        other = fm.triad((0, 0, 0), (0, 0, 1), (-1, 0, 0))
        self.assertAlmostEqual(fm.rotation_angle_degrees(self.frame, other), 180, places=6)

    def test_collinear_rejected(self):
        with self.assertRaisesRegex(ValueError, "collinear"):
            fm.triad((0, 0, 0), (0, 0, 1), (0, 0, 2))

    def test_near_collinear_rejected(self):
        with self.assertRaisesRegex(ValueError, "collinear"):
            fm.triad((0, 0, 0), (0, 0, 1), (0.001, 0, 1))

    def test_duplicate_landmark_rejected(self):
        with self.assertRaisesRegex(ValueError, "zero-length"):
            fm.triad((0, 0, 0), (0, 0, 0), (1, 0, 0))

    def test_nonfinite_and_bool_rejected(self):
        for bad in (float('nan'), float('inf'), True, "1"):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                fm.triad((0, 0, bad), (0, 0, 1), (1, 0, 0))

    def test_bad_point_shape_rejected(self):
        with self.assertRaisesRegex(ValueError, "exactly three"):
            fm.triad((0, 0), (0, 0, 1), (1, 0, 0))

    def test_left_handed_reflection_rejected(self):
        reflected = dict(self.frame, axes=((1., 0., 0.), (0., -1., 0.), (0., 0., 1.)))
        with self.assertRaisesRegex(ValueError, "right-handed"):
            fm.rotation_angle_degrees(self.frame, reflected)

    def test_mirrored_points_reconstruct_proper_frame(self):
        mirrored = fm.triad((0, 0, 0), (0, 0, 1), (-1, 0, 0))
        self.assertAlmostEqual(mirrored["determinant"], 1)
        self.assertEqual(mirrored["frame_type"], "GENERIC_TRIAD_NOT_ISB")

    def test_path_return_is_not_validation(self):
        rotated = fm.triad((0, 0, 0), (0, 0, 1), (0, 1, 0))
        result = fm.describe_path([self.frame, rotated, self.frame])
        self.assertEqual(result["sample_count"], 3)
        self.assertAlmostEqual(result["return_to_initial_degrees_unsigned"], 0)
        self.assertIn("NOT_ANATOMICAL", result["status"])

    def test_short_path_rejected(self):
        with self.assertRaisesRegex(ValueError, "at least two"):
            fm.describe_path([self.frame])

    def test_synthetic_report_never_approves(self):
        report = fm.synthetic_report()
        self.assertEqual(len(report["regions"]), 4)
        self.assertEqual(report["native_model_landmarks_used"], 0)
        self.assertEqual(report["generic_motion_tests_executed"], 0)
        for key in ("isb_frames_approved", "anatomical_sides_approved", "skin_deformation_approved",
                    "muscle_attachments_approved", "clinical_rom_limits_applied", "muscle_highlighting_implemented"):
            self.assertIs(report[key], False)

    def test_no_blender_or_model_mutation_calls(self):
        source = SOURCE.read_text()
        self.assertNotIn("import bpy", source)
        self.assertNotIn("save_as_mainfile", source)
        self.assertNotIn(".blend", source)


if __name__ == "__main__":
    unittest.main()

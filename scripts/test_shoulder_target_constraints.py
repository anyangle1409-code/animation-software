import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from anatomy_fit.shoulder_target_constraints import (
    ac_breadth_bounds_from_outer_and_3d_distance,
    a003_outer_breadth_failure,
    bilateral_ac_breadth_from_transverse_offset,
    endpoint_chord_is_anatomically_possible,
    minimum_bilateral_sc_breadth_for_lateral_only_chord,
    required_transverse_acromion_to_ac_offset,
)


class ShoulderTargetConstraintTests(unittest.TestCase):
    def test_transverse_offset_conversion_is_pure_geometry(self):
        self.assertAlmostEqual(
            bilateral_ac_breadth_from_transverse_offset(420.0, 30.0),
            360.0,
            places=9,
        )

    def test_3d_distance_yields_bounds_not_equality(self):
        # Synthetic values: a 3-D distance is only an upper bound on its
        # transverse component, so the upper AC-breadth ceiling is the outer
        # breadth itself, not outer-2*d.
        lo, ceiling = ac_breadth_bounds_from_outer_and_3d_distance(
            (400.0, 440.0),
            (20.0, 40.0),
        )
        self.assertAlmostEqual(lo, 320.0, places=9)
        self.assertAlmostEqual(ceiling, 440.0, places=9)

    def test_required_transverse_offset(self):
        self.assertAlmostEqual(
            required_transverse_acromion_to_ac_offset(420.0, 340.0),
            40.0,
            places=9,
        )

    def test_a003_outer_breadth_failure_does_not_need_ac_offset_source(self):
        self.assertTrue(a003_outer_breadth_failure(481.3938993665297, 425.15656060295987))
        self.assertFalse(a003_outer_breadth_failure(350.0, 425.15656060295987))

    def test_chord_cannot_exceed_curved_length(self):
        self.assertTrue(
            endpoint_chord_is_anatomically_possible(
                (25.0, 0.0, 1500.0),
                (175.0, 20.0, 1495.0),
                166.8,
            )
        )
        self.assertFalse(
            endpoint_chord_is_anatomically_possible(
                (25.0, 0.0, 1500.0),
                (225.0, 40.0, 1490.0),
                166.8,
            )
        )

    def test_lateral_only_sc_breadth_is_lower_bound(self):
        self.assertAlmostEqual(
            minimum_bilateral_sc_breadth_for_lateral_only_chord(360.0, 150.0),
            60.0,
            places=9,
        )

    def test_bad_inputs_rejected(self):
        with self.assertRaises(ValueError):
            bilateral_ac_breadth_from_transverse_offset(50.0, 30.0)
        with self.assertRaises(ValueError):
            ac_breadth_bounds_from_outer_and_3d_distance((10.0, 5.0), (1.0, 2.0))
        with self.assertRaises(ValueError):
            required_transverse_acromion_to_ac_offset(100.0, 110.0)


if __name__ == "__main__":
    unittest.main()

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from anatomy_fit.shoulder_target_constraints import (
    ac_breadth_bounds_from_outer_and_3d_distance,
    bilateral_ac_breadth_from_transverse_offset,
    chord_length_mm,
    endpoint_chord_is_anatomically_possible,
    evaluate_mean_outer_scaffold,
    minimum_bilateral_sc_breadth_for_lateral_only_chord,
    required_transverse_acromion_to_ac_offset,
)


class ShoulderTargetConstraintTests(unittest.TestCase):
    def test_transverse_offset_conversion(self):
        self.assertAlmostEqual(
            bilateral_ac_breadth_from_transverse_offset(425.15656060295987, 34.0),
            357.15656060295987,
            places=9,
        )

    def test_3d_distance_yields_bounds_not_equality(self):
        lo, ceiling = ac_breadth_bounds_from_outer_and_3d_distance(
            (408.9265234968994, 441.38659770902035),
            (26.0, 42.0),
        )
        self.assertAlmostEqual(lo, 324.9265234968994, places=9)
        self.assertAlmostEqual(ceiling, 441.38659770902035, places=9)

    def test_required_transverse_offset(self):
        self.assertAlmostEqual(
            required_transverse_acromion_to_ac_offset(
                425.15656060295987,
                342.86404303708286,
            ),
            41.1462587829385,
            places=9,
        )

    def test_a003_biacromial_logic_is_impossible_as_normal_target(self):
        # Current a003 bi-AC breadth is already wider than the mean outer
        # biacromial breadth. AC must be medial to lateral acromion.
        self.assertGreater(481.3938993665297, 425.15656060295987)

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
        ac = 357.15656060295987
        self.assertAlmostEqual(
            minimum_bilateral_sc_breadth_for_lateral_only_chord(ac, 154.8),
            47.55656060295989,
            places=9,
        )

    def test_mean_outer_scaffold_keeps_strict_ceiling(self):
        x = evaluate_mean_outer_scaffold()
        self.assertAlmostEqual(
            x["bilateral_ac_breadth_lower_bound_if_3d_distance_is_34mm"],
            357.15656060295987,
            places=9,
        )
        self.assertEqual(
            x["bilateral_ac_breadth_upper_ceiling"],
            425.15656060295987,
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

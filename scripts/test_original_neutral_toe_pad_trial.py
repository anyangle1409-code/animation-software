import math
import unittest
from original_neutral_toe_pad_trial import expand_plantar


class NeutralToePadTrialTests(unittest.TestCase):
    def test_suspended_plantar_point_reaches_floor(self):
        self.assertAlmostEqual(expand_plantar(.009, .009), 0)

    def test_upper_envelope_is_preserved(self):
        self.assertEqual(expand_plantar(.030, .009), .030)
        self.assertEqual(expand_plantar(.022, .009), .022)

    def test_vertical_order_is_preserved(self):
        values=[expand_plantar(z, .009) for z in (.009,.012,.015,.018,.022)]
        self.assertTrue(all(a<b for a,b in zip(values,values[1:])))
        self.assertLess(values[2], .015)

    def test_grounded_regions_and_zero_blend_stay_fixed(self):
        self.assertEqual(expand_plantar(.01, 0), .01)
        self.assertEqual(expand_plantar(.015, .009, blend=0), .015)

    def test_invalid_envelopes_are_refused(self):
        for z,bottom,anchor,blend in [(math.nan,.009,.022,1),(.01,.022,.022,1),(.01,.009,.022,2)]:
            with self.subTest(values=(z,bottom,anchor,blend)):
                with self.assertRaises(ValueError):
                    expand_plantar(z,bottom,anchor,blend)


if __name__=='__main__':
    unittest.main()

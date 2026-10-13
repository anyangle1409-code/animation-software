import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "anatomy_fit"))

import functional_coupled_corrective as contract


class CoupledCorrectiveContractTests(unittest.TestCase):
    def test_keys_are_inactive_at_and_below_ninety(self):
        for e in (0, 45, 89.999, 90):
            self.assertTrue(all(w == 0.0 for w in contract.key_weights(e).values()), e)

    def test_each_key_is_exact_at_its_pose(self):
        for k in contract.KEY_POSES_DEG:
            w = contract.key_weights(k)
            self.assertEqual(w[contract.key_label(k)], 1.0)
            self.assertAlmostEqual(sum(w.values()), 1.0, places=12)

    def test_partition_of_unity_continuity_and_two_neighbour_support(self):
        prev = None
        for i in range(int(contract.KEY_POSES_DEG[0]) * 10, 1601):
            e = i / 10.0
            w = contract.key_weights(e)
            self.assertAlmostEqual(sum(w.values()), 1.0, places=9)
            self.assertLessEqual(sum(1 for v in w.values() if v > 0), 2)
            if prev is not None:
                self.assertLess(max(abs(w[k] - prev[k]) for k in w), 0.011)
            prev = w

    def test_ramp_from_ninety_to_first_key(self):
        first = contract.key_label(contract.KEY_POSES_DEG[0])
        self.assertAlmostEqual(contract.key_weights(95)[first], 0.5)

    def test_rejects_invalid_elevation(self):
        for bad in (True, -1, 160.5, math.nan, math.inf, "120"):
            with self.assertRaises(ValueError):
                contract.key_weights(bad)

    def test_zone_falloff_and_taubin_guards(self):
        self.assertEqual(contract.zone_falloff(0, 4), 1.0)
        self.assertEqual(contract.zone_falloff(5, 4), 0.0)
        vals = [contract.zone_falloff(d, 4) for d in range(6)]
        self.assertTrue(all(b <= a for a, b in zip(vals, vals[1:])))
        for bad in ((-1, 4), (1, 0), (True, 4)):
            with self.assertRaises(ValueError):
                contract.zone_falloff(*bad)
        self.assertEqual(contract.taubin_coefficients(), (0.5, -0.53))
        with self.assertRaises(ValueError):
            contract.taubin_coefficients(0.5, -0.4)

    def test_targets_report_every_unmet_guard(self):
        ok = {"collapse_faces_ratio_lt_0_1": 0, "self_intersecting_face_pairs_in_region": 0,
              "body_volume_change_pct": -1.9}
        self.assertEqual(contract.meets_targets(ok, 3.0), [])
        bad = dict(ok, collapse_faces_ratio_lt_0_1=1, self_intersecting_face_pairs_in_region=5,
                   body_volume_change_pct=2.5)
        self.assertEqual(contract.meets_targets(bad, 1.0), ["collapse", "self_intersection", "volume", "rib_clearance"])


if __name__ == "__main__":
    unittest.main()

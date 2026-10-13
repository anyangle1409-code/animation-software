import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "anatomy_fit"))

import functional_original_coupled_motion as motion


class FunctionalOriginalCoupledMotionTests(unittest.TestCase):
    def test_required_evidence_samples_have_absolute_ht_targets(self):
        samples = motion.sample_profiles((0, 90, 160))
        self.assertEqual([sample["ht_elevation_deg"] for sample in samples], [0.0, 90.0, 160.0])
        self.assertTrue(all(sample["plane_deg"] == 40.0 for sample in samples))
        self.assertTrue(all(sample["approval"] is False for sample in samples))

    def test_coupled_components_are_zero_at_rest_and_increase_nonuniformly(self):
        rest, middle, top = motion.sample_profiles((0, 90, 160))
        components = motion.COUPLED_COMPONENTS
        self.assertTrue(all(rest[name] == 0.0 for name in components))
        self.assertTrue(all(0.0 < middle[name] < top[name] for name in components))
        self.assertNotAlmostEqual(
            middle["scapula_upward_rotation_deg"] / top["scapula_upward_rotation_deg"],
            90.0 / 160.0,
        )

    def test_reference_bounded_components_do_not_overclaim_reported_averages(self):
        at_120 = motion.pose_profile(120)
        self.assertLessEqual(at_120["clavicle_posterior_rotation_deg"], 31.0)
        self.assertLessEqual(at_120["scapula_posterior_tilt_deg"], 19.0)
        self.assertEqual(at_120["reference_ceiling_deg"], 120.0)
        self.assertFalse(at_120["human_motion_accepted"])

    def test_profile_rejects_bool_nonfinite_and_out_of_range(self):
        for invalid in (True, -0.1, 160.1, math.nan, math.inf, "90"):
            with self.subTest(invalid=invalid):
                with self.assertRaisesRegex(ValueError, "finite HT elevation 0..160"):
                    motion.pose_profile(invalid)

    def test_profile_is_finite_and_explicitly_authored_not_a_cohort_fit(self):
        for angle in range(0, 161, 5):
            sample = motion.pose_profile(angle)
            numeric = [value for value in sample.values() if isinstance(value, float)]
            self.assertTrue(all(math.isfinite(value) for value in numeric))
            self.assertEqual(sample["coupling_scope"], "project-authored directional hypothesis")
            self.assertFalse(sample["cohort_trajectory_fit"])


if __name__ == "__main__":
    unittest.main()

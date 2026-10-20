"""R54 capture screen: synthetic identity, exact ablation algebra and hard guards."""
import pathlib
import sys
import unittest
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
from screen_original_review_r54_s5_s7 import combine, max_dense_motion_excess_mm, locate_subset


class ScreenMath(unittest.TestCase):
    def setUp(self):
        frame = np.arange(161, dtype=np.float64)
        self.base = np.zeros((161, 2, 3), dtype=np.float64)
        self.base[:, :, 0] = frame[:, None]*0.0001
        self.d5 = np.zeros_like(self.base)
        self.d7 = np.zeros_like(self.base)
        self.d5[:, 0, 0] = 0.001
        self.d7[:, 1, 1] = 0.002

    def test_original_key_pair_exactly_replays_source(self):
        self.assertTrue(np.array_equal(combine(self.base, self.d5, self.d7, 1, 1), self.base))

    def test_full_mute_reproduces_both_independent_ablation_vectors(self):
        both = combine(self.base, self.d5, self.d7, 0, 0)
        np.testing.assert_allclose(both, self.base + self.d5 + self.d7, atol=0, rtol=0)
        np.testing.assert_allclose(combine(self.base, self.d5, self.d7, 0, 1), self.base + self.d5)
        np.testing.assert_allclose(combine(self.base, self.d5, self.d7, 1, 0), self.base + self.d7)

    def test_scaling_changes_delta_linearly_not_poses(self):
        np.testing.assert_allclose(combine(self.base, self.d5, self.d7, 0.9, 1.1),
                                   self.base + 0.1*self.d5 - 0.1*self.d7, atol=1e-15)
        frozen = self.base.copy()
        combine(self.base, self.d5, self.d7, 0.95, 1.05)
        np.testing.assert_array_equal(self.base, frozen)

    def test_second_difference_uses_dense_frame_normalization(self):
        perturbation = self.base.copy()
        perturbation[80, 0, 1] = 0.001
        # A single 1mm spatial jump has a 2mm second difference;
        # the existing coarse-grid-equivalent factor is 16.
        self.assertAlmostEqual(max_dense_motion_excess_mm(perturbation, self.base), 32.0)

    def test_one_frame_clip_cannot_silently_pass(self):
        with self.assertRaises(ValueError):
            combine(self.base[:1], self.d5[:1], self.d7[:1], 1, 1)
        with self.assertRaises(ValueError):
            max_dense_motion_excess_mm(self.base[:1], self.base[:1])

    def test_nonfinite_and_bad_coefficient_rejected(self):
        for coefficient in (-0.01, float("nan"), float("inf"), 2.01):
            with self.assertRaises(ValueError):
                combine(self.base, self.d5, self.d7, coefficient, 1)
        with self.assertRaises(ValueError):
            combine(self.base, self.d5[:5], self.d7, 1, 1)

    def test_subset_identity_never_spills_to_unrelated_vertices(self):
        np.testing.assert_array_equal(locate_subset(np.array([3, 5, 8, 12]), np.array([5, 12])),
                                      [1, 3])
        for subset in ([1], [5, 13], [12, 5]):
            with self.assertRaises(ValueError):
                locate_subset(np.array([3, 5, 8, 12]), np.array(subset))


if __name__ == "__main__":
    unittest.main()

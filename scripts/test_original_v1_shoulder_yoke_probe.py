"""Safety tests for the r96 weights-only shoulder-yoke probe."""
from __future__ import annotations

import unittest

import numpy as np

import original_v1_shoulder_yoke_probe as probe


class ShoulderYokeProbeTests(unittest.TestCase):
    def test_subzone_is_mirror_closed_and_excludes_forbidden_existing_weights(self):
        rows = [
            {"upperarm_l": 0.8, "clavicle_l": 0.2},
            {"upperarm_l": 0.4, "clavicle_l": 0.6},
            {"upperarm_l": 0.8, "forearm_tw0_l": 0.2},
            {"upperarm_r": 0.8, "clavicle_r": 0.2},
            {"upperarm_r": 0.4, "clavicle_r": 0.6},
            {"upperarm_r": 0.8, "forearm_tw0_r": 0.2},
        ]
        result = probe.select_safe_mirror_subzone(
            left_ids=[0, 1, 2],
            right_ids=[3, 4, 5],
            rows=rows,
            regions=["shoulder"] * 6,
            permitted_regions={"shoulder"},
            permitted_bones={"upperarm_l", "clavicle_l", "upperarm_r", "clavicle_r"},
            edges=[(0, 1), (1, 2), (3, 4), (4, 5)],
            gradient_threshold=0.5,
            dilation_rings=1,
        )
        self.assertEqual(result["left_vertex_ids"], [0, 1])
        self.assertEqual(result["right_vertex_ids"], [3, 4])
        self.assertEqual(result["excluded_forbidden_pair_count"], 1)

    def test_subzone_requires_a_measured_gradient_seed(self):
        rows = [
            {"upperarm_l": 0.6, "clavicle_l": 0.4},
            {"upperarm_l": 0.55, "clavicle_l": 0.45},
            {"upperarm_r": 0.6, "clavicle_r": 0.4},
            {"upperarm_r": 0.55, "clavicle_r": 0.45},
        ]
        result = probe.select_safe_mirror_subzone(
            [0, 1], [2, 3], rows, ["shoulder"] * 4, {"shoulder"},
            {"upperarm_l", "clavicle_l", "upperarm_r", "clavicle_r"},
            [(0, 1), (2, 3)], gradient_threshold=0.2, dilation_rings=1,
        )
        self.assertEqual(result["left_vertex_ids"], [])
        self.assertEqual(result["seed_pair_count"], 0)

    def test_diffusion_changes_only_zone_and_permitted_columns(self):
        weights = np.array([
            [0.8, 0.2, 0.0],
            [0.2, 0.8, 0.0],
            [0.1, 0.4, 0.5],
        ], dtype=float)
        changed = probe.diffuse_permitted_weights(
            weights, edges=np.array([[0, 1], [1, 2]]), zone_ids=[1],
            permitted_indices=[0, 1], iterations=1, lam=0.5,
        )
        np.testing.assert_allclose(changed[[0, 2]], weights[[0, 2]])
        self.assertEqual(changed[1, 2], weights[1, 2])
        self.assertAlmostEqual(float(changed[1].sum()), 1.0)
        self.assertGreater(changed[1, 0], weights[1, 0])

    def test_mirror_symmetry_swaps_lateral_columns(self):
        weights = np.array([
            [0.9, 0.1, 0.0, 0.0],
            [0.0, 0.0, 0.7, 0.3],
        ], dtype=float)
        sym = probe.symmetrise_pairs(
            weights, left_ids=[0], right_ids=[1], swap_indices=[2, 3, 0, 1]
        )
        np.testing.assert_allclose(sym[0], [0.8, 0.2, 0.0, 0.0])
        np.testing.assert_allclose(sym[1], [0.0, 0.0, 0.8, 0.2])

    def test_influence_limit_keeps_largest_weights_and_normalises(self):
        weights = np.array([
            [0.40, 0.30, 0.20, 0.06, 0.04],
            [0.10, 0.20, 0.30, 0.15, 0.25],
        ], dtype=float)
        limited = probe.limit_influences(weights, zone_ids=[0], maximum=4)
        np.testing.assert_allclose(limited[1], weights[1])
        self.assertEqual(int((limited[0] > 1e-8).sum()), 4)
        self.assertEqual(limited[0, 4], 0.0)
        self.assertAlmostEqual(float(limited[0].sum()), 1.0)


if __name__ == "__main__":
    unittest.main()

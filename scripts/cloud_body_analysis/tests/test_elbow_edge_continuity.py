"""Synthetic mesh-edge guards; no native or anatomical validation."""
import ast
import sys
import unittest
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import elbow_edge_continuity as e


class EdgeContinuityTests(unittest.TestCase):
    def setUp(self):
        # 2x4 strip has interior edges and no anatomical meaning.
        self.tri = np.array([[0, 1, 4], [1, 5, 4], [1, 2, 5],
                             [2, 6, 5], [2, 3, 6], [3, 7, 6]], dtype=int)
        self.rest = np.array([[x, y, 0.] for y in (0., 1.) for x in range(4)], dtype=float)

    def test_unique_edges_no_double_count(self):
        tri = []
        for y in range(3):
            for x in range(3):
                a = y * 4 + x
                tri.extend(((a, a + 1, a + 4), (a + 1, a + 5, a + 4)))
        edges = e.region_edges(np.array(tri), np.arange(16), 16)
        self.assertEqual(len(edges), 33)
        self.assertEqual(len(edges), len(np.unique(edges, axis=0)))

    def test_translation_and_rotation_invariance(self):
        edges = np.array([[0, 1], [1, 2], [4, 5]])
        t = 0.6
        rotation = np.array([[np.cos(t), -np.sin(t), 0],
                             [np.sin(t), np.cos(t), 0], [0, 0, 1]])
        ratios = e.edge_ratios(self.rest, self.rest @ rotation.T + [4, -2, 1], edges)
        np.testing.assert_allclose(ratios, 1, atol=1e-12)

    def test_uniform_scale_ratio(self):
        edges = np.array([[0, 1], [1, 2], [4, 5]])
        np.testing.assert_allclose(e.edge_ratios(self.rest, 1.3*self.rest, edges), 1.3)

    def test_local_edge_change_not_absolute_pose_displacement(self):
        edges = np.array([[0, 1], [1, 2], [4, 5]])
        pose = self.rest.copy()
        pose[1, 0] = 1.5
        r = e.edge_ratios(self.rest, pose, edges)
        self.assertAlmostEqual(r[0], 1.5)
        self.assertAlmostEqual(r[1], 0.5)
        self.assertAlmostEqual(r[2], 1.)

    def test_percentiles_and_baseline(self):
        d = e.describe(np.array([1., 1.2, 1.5, 2.]), np.array([1., 1., 1., 1.]))
        self.assertEqual(d["max"], 2.)
        self.assertGreater(d["p95_abs_ratio_change_from_pose_sample0"], .9)

    def test_bad_vertex_ids_rejected(self):
        for ids in ([0, 0, 1], [-1, 0], [0, 20], []):
            with self.assertRaises(ValueError):
                e.region_edges(self.tri, np.asarray(ids, dtype=int), 8)

    def test_bad_triangles_and_sparse_band_rejected(self):
        with self.assertRaises(ValueError):
            e.region_edges(np.array([[0, 1, 99]]), np.arange(8), 8)
        with self.assertRaises(ValueError):
            e.region_edges(self.tri, np.array([0, 1]), 8)

    def test_zero_rest_edge_rejected(self):
        with self.assertRaises(ValueError):
            e.edge_ratios(np.zeros((2, 3)), np.zeros((2, 3)), np.array([[0, 1]]))

    def test_nonfinite_or_wrong_shape_rejected(self):
        with self.assertRaises(ValueError):
            e.edge_ratios(self.rest, np.full_like(self.rest, np.nan), np.array([[0, 1]]))
        with self.assertRaises(ValueError):
            e.describe(np.array([1., np.inf]))
        with self.assertRaises(ValueError):
            e.describe(np.array([1., 2.]), np.array([1.]))

    def test_no_blender_model_mutation_and_no_anatomy_promotion(self):
        tree = ast.parse((ROOT / "elbow_edge_continuity.py").read_text())
        imports = [n for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse(any(x.name == "bpy" for n in imports for x in n.names))
        self.assertFalse(any(isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                             and n.func.attr in ("save_mainfile", "save_as_mainfile") for n in ast.walk(tree)))
        self.assertIn("ANATOMY AND SKIN NOT APPROVED", e.markdown({"suffixes_NOT_anatomical_sides": {}}))


if __name__ == "__main__":
    unittest.main()

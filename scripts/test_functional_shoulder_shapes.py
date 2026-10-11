import importlib.util
import math
import unittest
from pathlib import Path

MODULE = Path(__file__).parent / 'anatomy_fit' / 'functional_shoulder_shapes.py'


class ShapeTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(MODULE.exists(), 'new source-aware shape builder is missing')
        spec = importlib.util.spec_from_file_location('shapes', MODULE)
        self.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.m)

    def test_clavicle_preserves_joint_centres_and_has_opposite_bends(self):
        p = self.m.clavicle_points((.025, 0, 1.5), (.175, 0, 1.5))
        self.assertEqual(p[0], (.025, 0, 1.5))
        self.assertEqual(p[-1], (.175, 0, 1.5))
        self.assertLess(p[10][1], 0)
        self.assertGreater(p[30][1], 0)
        self.assertGreater(sum(math.dist(a, b) for a, b in zip(p, p[1:])), .15)

    def test_anatomical_laterality_mirrors_x_not_anterior(self):
        a = self.m.clavicle_points((.025, .02, 1.5), (.175, .06, 1.49))
        b = self.m.clavicle_points((-.025, .02, 1.5), (-.175, .06, 1.49))
        for p, q in zip(a, b):
            self.assertEqual(q, (-p[0], p[1], p[2]))

    def test_bad_and_collapsed_inputs_refused(self):
        for p, q in [((0, 0, 0), (0, 0, 0)), ((0, 0, math.nan), (1, 0, 0)),
                     ((0, 0), (1, 0, 0))]:
            with self.assertRaises(ValueError):
                self.m.clavicle_points(p, q)

    def test_blade_keeps_perimeter_and_closed_thickness(self):
        vertices, faces = self.m.blade_mesh([(0, 0, 0), (1, 0, 0), (0, 0, 1)])
        self.assertEqual(len(vertices), 8)
        edges = {}
        for face in faces:
            for a, b in zip(face, face[1:] + face[:1]):
                key = tuple(sorted((a, b)))
                edges[key] = edges.get(key, 0) + 1
        self.assertTrue(all(n == 2 for n in edges.values()))
        self.assertEqual(vertices[0], (0, -.002, 0))
        self.assertEqual(vertices[4], (0, .002, 0))

    def test_collinear_blade_refused(self):
        with self.assertRaises(ValueError):
            self.m.blade_mesh([(0, 0, 0), (1, 0, 0), (2, 0, 0)])

    def test_degenerate_bow_tie_fan_refused(self):
        with self.assertRaises(ValueError):
            self.m.blade_mesh([(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)])

    def test_huge_integer_is_rejected_as_invalid_coordinate(self):
        try:
            with self.assertRaises(ValueError):
                self.m.clavicle_points((10**400, 0, 0), (1, 0, 0))
        except OverflowError:
            self.fail('numeric corruption must be refused with ValueError, not overflow')


if __name__ == '__main__':
    unittest.main()

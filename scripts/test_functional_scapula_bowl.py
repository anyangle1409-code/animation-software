"""Behaviour guards for an authored concave costal guide, not anatomy acceptance."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'anatomy_fit'))
import functional_shoulder_shapes as shapes


class BowlTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(hasattr(shapes, 'scapula_bowl_mesh'), 'curved blade builder missing')
        self.p = [(0, 0, 0), (.12, 0, 0), (0, 0, .18)]

    def test_costal_centre_recedes_posteriorly_without_moving_border(self):
        # A flat fan or anterior bulge must fail these hand-derived values.
        v, _ = shapes.scapula_bowl_mesh(self.p, .008)
        size = len(v) // 2
        centre = tuple((v[0][k] + v[size][k]) / 2 for k in range(3))
        for x, want in zip(centre, (.04, .008, .06)):
            self.assertAlmostEqual(x, want)
        for i, p in enumerate(self.p):
            mid = tuple((v[size-3+i][k] + v[2*size-3+i][k]) / 2 for k in range(3))
            self.assertEqual(mid, p)

    def test_closed_shell_has_opposite_oriented_edge_uses(self):
        # Missing rim caps or reversed surface winding must fail.
        _, faces = shapes.scapula_bowl_mesh(self.p, .008)
        edges = {}
        for face in faces:
            for a, b in zip(face, face[1:] + face[:1]):
                edges.setdefault(tuple(sorted((a,b))), []).append((a,b))
        for uses in edges.values():
            self.assertEqual(len(uses), 2)
            self.assertEqual(uses[0], uses[1][::-1])

    def test_x_mirror_keeps_costal_concavity_posterior(self):
        a, _ = shapes.scapula_bowl_mesh(self.p, .008)
        b, _ = shapes.scapula_bowl_mesh([(-x,y,z) for x,y,z in self.p], .008)
        for p, q in zip(a,b):
            self.assertEqual(q, (-p[0],p[1],p[2]))

    def test_invalid_depth_and_ambiguous_costal_orientation_refused(self):
        for depth in (True, -.001, .021, float('nan'), float('inf'), '8mm'):
            with self.assertRaises(ValueError):
                shapes.scapula_bowl_mesh(self.p, depth)
        with self.assertRaises(ValueError):
            shapes.scapula_bowl_mesh([(0,0,0),(1,0,0),(0,1,0)], .008)


if __name__ == '__main__':
    unittest.main()

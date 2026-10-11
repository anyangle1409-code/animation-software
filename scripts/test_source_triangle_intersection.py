"""Hand-derived triangle fixtures; not anatomy or complete mesh evidence."""
import importlib.util
import itertools
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))


class TriangleIntersectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.intersect = None
        if importlib.util.find_spec('source_triangle_intersection'):
            import source_triangle_intersection
            cls.intersect = staticmethod(source_triangle_intersection.intersection)

    def check(self, a, b, want):
        self.assertTrue(callable(self.intersect), 'Missing closed-triangle intersection')
        result = self.intersect(a, b)
        self.assertIs(result['closed_triangles_intersect'], want)
        for key in ('anatomical_contact_accepted', 'physical_units_verified',
                    'whole_surface_clearance_verified'):
            self.assertIs(result[key], False)
        return result

    def test_crossing_faces_with_no_coincident_vertices(self):
        self.check([(0,0,0),(2,0,0),(0,2,0)],
                   [(.5,.5,-1),(.5,.5,1),(1,.5,1)], True)

    def test_parallel_planes_and_tiny_positive_gap_are_separate(self):
        a = [(0,0,0),(2,0,0),(0,2,0)]
        for gap in (1, 1e-200, 5e-324):
            with self.subTest(gap=gap):
                self.check(a, [(0,0,gap),(2,0,gap),(0,2,gap)], False)

    def test_coplanar_disjoint_with_overlapping_axis_aligned_boxes(self):
        # A occupies x+y<=2; B occupies x+y>=3 despite overlapping X/Y boxes.
        self.check([(0,0,0),(2,0,0),(0,2,0)],
                   [(2,2,0),(1,2,0),(2,1,0)], False)

    def test_coplanar_overlap_and_containment(self):
        a = [(0,0,0),(2,0,0),(0,2,0)]
        for b in ([(-1,1,0),(1,1,0),(1,-1,0)],
                  [(.1,.1,0),(.2,.1,0),(.1,.2,0)], a):
            self.check(a, b, True)

    def test_closed_vertex_edge_and_face_contacts(self):
        a = [(0,0,0),(2,0,0),(0,2,0)]
        for b in ([(2,0,0),(3,0,0),(2,1,0)],
                  [(0,0,0),(2,0,0),(1,-1,0)],
                  [(.5,.5,0),(.5,.5,1),(1,.5,1)]):
            self.check(a, b, True)

    def test_nonparallel_planes_can_still_be_disjoint(self):
        self.check([(0,0,0),(2,0,0),(0,2,0)],
                   [(3,3,-1),(3,3,1),(4,3,0)], False)

    def test_permutation_and_argument_order_invariance(self):
        a = [(0,0,0),(2,0,0),(0,2,0)]
        for b, want in (([(.5,.5,-1),(.5,.5,1),(1,.5,1)], True),
                        ([(2,2,0),(1,2,0),(2,1,0)], False)):
            for aa in itertools.permutations(a):
                for bb in itertools.permutations(b):
                    self.check(aa, bb, want)
                    self.check(bb, aa, want)

    def test_axis_rotation_and_large_translation(self):
        # Rotate (x,y,z)->(z,x,y), then translate by (1000,2000,3000).
        self.check([(1000,2000,3000),(1000,2002,3000),(1000,2000,3002)],
                   [(999,2000.5,3000.5),(1001,2000.5,3000.5),
                    (1001,2001,3000.5)], True)

    def test_exact_tiny_triangle_does_not_underflow_to_degenerate(self):
        t = [(0,0,0),(1e-200,0,0),(0,1e-200,0)]
        self.check(t, t, True)

    def test_degenerate_triangles_refused(self):
        self.assertTrue(callable(self.intersect), 'Missing closed-triangle intersection')
        for t in ([(0,0,0)]*3, [(0,0,0),(1,1,1),(2,2,2)]):
            with self.assertRaises(ValueError):
                self.intersect(t, [(0,0,0),(1,0,0),(0,1,0)])

    def test_invalid_coordinates_and_shapes_refused(self):
        self.assertTrue(callable(self.intersect), 'Missing closed-triangle intersection')
        good = [(0,0,0),(1,0,0),(0,1,0)]
        for t in (None, good[:2], [(0,0)]*3,
                  *[[(v,0,0),(1,0,0),(0,1,0)]
                    for v in (True, '1', float('nan'), float('inf'), 1000001)]):
            with self.subTest(t=t), self.assertRaises(ValueError):
                self.intersect(t, good)


if __name__ == '__main__':
    unittest.main()

"""Hand-derived closed-triangle witnesses, not anatomical clearance tests."""
import importlib.util
import itertools
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))


class TriangleWitnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if importlib.util.find_spec('source_triangle_witness') is None:
            cls.project = None
            return
        import source_triangle_witness
        cls.project = staticmethod(source_triangle_witness.closest_point)

    def check(self, p, tri, want, distance):
        self.assertTrue(callable(self.project), 'Missing triangle-interior witness implementation')
        r = self.project(p, tri)
        for a, b in zip(r['point_source_units'], want):
            self.assertAlmostEqual(a, b, places=10)
        self.assertAlmostEqual(r['distance_source_units'], distance, places=10)
        self.assertAlmostEqual(sum(r['barycentric']), 1)
        self.assertTrue(all(0 <= x <= 1 for x in r['barycentric']))
        self.assertFalse(r['physical_units_verified'])
        self.assertFalse(r['anatomical_contact_accepted'])
        self.assertFalse(r['whole_surface_clearance_verified'])
        return r

    def test_triangle_interior_beats_every_vertex(self):
        r = self.check((.5, .5, 3), [(0,0,0),(2,0,0),(0,2,0)], (.5,.5,0), 3)
        self.assertEqual(r['barycentric'], [.5,.25,.25])
        self.assertLess(r['distance_source_units'], math.sqrt(9.5))

    def test_each_edge_and_vertex_voronoi_region(self):
        tri = [(0,0,0),(2,0,0),(0,2,0)]
        for p, want, d in [((1,-1,0),(1,0,0),1),
                            ((-1,1,0),(0,1,0),1),
                            ((2,2,0),(1,1,0),math.sqrt(2)),
                            ((-1,-1,0),(0,0,0),math.sqrt(2)),
                            ((3,-1,0),(2,0,0),math.sqrt(2)),
                            ((-1,3,0),(0,2,0),math.sqrt(2))]:
            with self.subTest(p=p): self.check(p, tri, want, d)

    def test_winding_and_all_corner_orders_preserve_projection(self):
        for tri in itertools.permutations([(0,0,0),(2,0,0),(0,2,0)]):
            self.check((.5,.5,-3), tri, (.5,.5,0), 3)

    def test_translation_and_axis_rotation(self):
        # In local Y/Z coordinates (1,2), the hypotenuse is y+z=2.
        self.check((11,21,32), [(10,20,30),(10,22,30),(10,20,32)], (10,20.5,31.5),math.sqrt(1.5))

    def test_on_surface_edge_and_vertex_have_zero_unsigned_distance(self):
        for p in [(0,0,0),(1,0,0),(.5,.5,0)]:
            self.check(p, [(0,0,0),(2,0,0),(0,2,0)], p, 0)

    def test_scale_is_source_units_not_mm_or_patient_registration(self):
        self.check((5,5,30), [(0,0,0),(20,0,0),(0,20,0)], (5,5,0),30)

    def test_slender_triangle_keeps_interior(self):
        self.check((.5,2e-7,1), [(0,0,0),(2,0,0),(0,1e-6,0)], (.5,2e-7,0),1)

    def test_degenerate_triangle_refused_not_called_surface(self):
        for tri in [[(0,0,0)]*3,[(0,0,0),(1,1,1),(2,2,2)]]:
            with self.assertRaises(ValueError): self.project((0,0,1),tri)

    def test_invalid_nonfinite_boolean_and_oversized_coordinates_refused(self):
        for value in [float('nan'),float('inf'),True,'1',1e100]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.project((value,0,0),[(0,0,0),(2,0,0),(0,2,0)])

    def test_malformed_triangle_and_point_refused(self):
        for p,tri in [((1,2),[(0,0,0)]*3),((0,0,0),[(0,0,0)]*2),
                      ((0,0,0),[(0,0,0),(1,0,0),(0,1,float('nan'))])]:
            with self.assertRaises(ValueError): self.project(p,tri)

    def test_subnormal_area_is_refused_before_plane_projection(self):
        with self.assertRaises(ValueError):
            self.project((1e-81,1e-81,4e-81),
                         [(0,0,0),(4e-81,0,0),(0,4e-81,0)])

    def test_tiny_positive_edge_distance_does_not_underflow_to_contact(self):
        r = self.project((.5,-1e-200,0),[(0,0,0),(2,0,0),(0,2,0)])
        self.assertEqual(r['point_source_units'],[.5,0.,0.])
        self.assertEqual(r['distance_source_units'],1e-200)


if __name__ == '__main__':
    unittest.main()

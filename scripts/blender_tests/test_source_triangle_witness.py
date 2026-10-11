"""Independent native BVH check of synthetic witnesses, no patient bytes."""
from pathlib import Path
import sys
import unittest
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'anatomy_fit'))
from source_triangle_witness import closest_point


class NativeWitnessTests(unittest.TestCase):
    def test_native_bvh_matches_interior_edges_vertices_and_both_sides(self):
        # Synthetic signed-X mirrored frames are mathematical tests only,
        # not anatomical laterality or bilateral patient evidence.
        base = [(0,0,0),(2,0,0),(0,2,0)]
        points = [(.5,.5,3),(1,-1,0),(-1,1,0),(2,2,0),
                  (-1,-1,0),(3,-1,0),(-1,3,0),(.5,.5,-3)]
        for sign in (-1,1):
            tri = [(sign*x,y,z) for x,y,z in base]
            tree = BVHTree.FromPolygons(tri,[(0,1,2)],all_triangles=True,epsilon=0)
            for x,y,z in points:
                p = (sign*x,y,z)
                native,normal,index,distance = tree.find_nearest(Vector(p))
                r = closest_point(p,tri)
                self.assertEqual(index,0)
                self.assertAlmostEqual(distance,r['distance_source_units'],places=6)
                for a,b in zip(native,r['point_source_units']):
                    self.assertAlmostEqual(a,b,places=6)
                self.assertFalse(r['whole_surface_clearance_verified'])


suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeWitnessTests)
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    raise SystemExit(1)

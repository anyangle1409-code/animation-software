"""Native synthetic crossing checks; no patient surfaces or anatomy claims."""
from pathlib import Path
import sys
import unittest

import bpy
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'anatomy_fit'))
from source_triangle_intersection import intersection


class NativeTriangleIntersection(unittest.TestCase):
    def test_native_crossing_and_separated_triangles(self):
        # Independent native BVH on simple representable noncoplanar fixtures.
        # BVH boundary/coplanar/epsilon behavior is not used as exact authority.
        a = [(0,0,0),(2,0,0),(0,2,0)]
        for b, want in (([(.5,.5,-1),(.5,.5,1),(1,.5,1)], True),
                        ([(0,0,1),(2,0,1),(0,2,1)], False),
                        ([(3,3,-1),(3,3,1),(4,3,0)], False)):
            meshes = []
            try:
                for vertices in (a,b):
                    mesh = bpy.data.meshes.new('synthetic-triangle-only')
                    meshes.append(mesh)
                    mesh.from_pydata(vertices, [], [(0,1,2)])
                    mesh.update()
                coords = [[tuple(v.co) for v in mesh.vertices] for mesh in meshes]
                self.assertEqual(coords, [a,b])
                trees = [BVHTree.FromPolygons(v, [(0,1,2)], all_triangles=True,
                                              epsilon=0) for v in coords]
                self.assertEqual(bool(trees[0].overlap(trees[1])), want)
                result = intersection(*coords)
                self.assertIs(result['closed_triangles_intersect'], want)
                self.assertIs(result['whole_surface_clearance_verified'], False)
                self.assertIs(result['anatomical_contact_accepted'], False)
            finally:
                for mesh in meshes:
                    bpy.data.meshes.remove(mesh)


if __name__ == '__main__':
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeTriangleIntersection)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise RuntimeError('Native synthetic intersection checks failed')

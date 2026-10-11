"""Native common-frame source-list identities, synthetic geometry only."""
from pathlib import Path
import sys
import unittest
import bpy

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'anatomy_fit'))
from source_triangle_broadphase import candidate_pairs
from source_triangle_intersection import intersection


class NativeCandidateIdentity(unittest.TestCase):
    def test_common_frame_retains_original_face_ids_and_vertices(self):
        a = [[(4,0,0),(5,0,0),(4,1,0)],[(0,0,0),(2,0,0),(0,2,0)]]
        b = [[(.5,.5,-1),(.5,.5,1),(1,.5,1)],[(8,0,0),(9,0,0),(8,1,0)]]
        for offset in (0,1000):
            inputs = [[[(x+offset,y+offset,z+offset) for x,y,z in t] for t in ts]
                      for ts in (a,b)]
            meshes = []
            try:
                readback = []
                for ts in inputs:
                    mesh = bpy.data.meshes.new('synthetic-original-face-identities')
                    meshes.append(mesh)
                    vertices = [v for t in ts for v in t]
                    mesh.from_pydata(vertices,[],[(3*i,3*i+1,3*i+2) for i in range(len(ts))])
                    mesh.update()
                    self.assertEqual([tuple(v.co) for v in mesh.vertices],vertices)
                    self.assertEqual(len(mesh.polygons),len(ts))
                    readback.append([[tuple(mesh.vertices[k].co) for k in p.vertices]
                                     for p in mesh.polygons])
                self.assertEqual(readback,inputs)
                r = candidate_pairs(*readback)
                self.assertEqual(r['triangle_index_pairs'],[[1,0]])
                self.assertTrue(intersection(readback[0][1],readback[1][0])['closed_triangles_intersect'])
                self.assertFalse(r['whole_surface_clearance_verified'])
                self.assertFalse(r['anatomical_contact_accepted'])
            finally:
                for mesh in meshes: bpy.data.meshes.remove(mesh)


suite = unittest.defaultTestLoader.loadTestsFromTestCase(NativeCandidateIdentity)
if not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful():
    raise RuntimeError('Native original face identity checks failed')

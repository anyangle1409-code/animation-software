"""Mutation tests reproducing the independent Claude PR #12 review concerns."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import bone_surface_contract as contract
import bone_surface_correspondence as correspondence
import bone_surface_topology as topology

from test_bone_surface_contract import ASSET, SKELETON, ARTICULATIONS


class GeometryCorrespondenceTests(unittest.TestCase):
    def test_valid_baseline_passes_and_remains_unapproved(self):
        actual = contract.validate(copy.deepcopy(ASSET), SKELETON, ARTICULATIONS)
        self.assertFalse(actual['canonical_promotion_allowed'])
        self.assertFalse(actual['spatial']['bone_identity_verified'])

    def test_five_metre_remote_geometry_is_rejected(self):
        a = copy.deepcopy(ASSET)
        a['vertices_m'] = [[v[0] + 5., v[1], v[2]] for v in a['vertices_m']]
        with self.assertRaisesRegex(ValueError, 'spatially detached'):
            contract.validate(a, SKELETON, ARTICULATIONS)

    def test_micro_femur_is_rejected(self):
        a = {'bone_id': 'femur_left'}
        bone = {'head_m': [0.08, 0, 1.1], 'tail_m': [0.08, 0, 0.7]}
        micro = [[0.08, 0, 1.1], [0.0805, 0, 1.1],
                 [0.08, 0.0005, 1.1], [0.08, 0, 1.0995]]
        with self.assertRaisesRegex(ValueError, 'implausibly small'):
            correspondence.check(a, bone, micro)

    def test_wrong_side_femur_is_rejected_independently_of_anchor(self):
        a = {'bone_id': 'femur_left'}
        bone = {'head_m': [0.06, 0, 1.1], 'tail_m': [0.06, 0, 0.7]}
        # Centroid on the RIGHT, but close enough to the bone line for the
        # separate coarse proximity tolerance not to short-circuit this test.
        v = [[-0.03, 0, 1.1], [-0.05, 0, 1.1],
             [-0.03, 0.02, 1.1], [-0.03, 0, 0.7]]
        with self.assertRaisesRegex(ValueError, 'opposite anatomical side'):
            correspondence.check(a, bone, v)

    def test_left_femur_correctly_sided_passes(self):
        a = {'bone_id': 'femur_left'}
        bone = {'head_m': [0.06, 0, 1.1], 'tail_m': [0.06, 0, 0.7]}
        v = [[0.06, 0, 1.1], [0.08, 0, 1.1],
             [0.06, 0.02, 1.1], [0.06, 0, 0.7]]
        x = correspondence.check(a, bone, v)
        self.assertTrue(x['side_checked'])
        self.assertFalse(x['anatomical_landmarks_verified'])

    def test_right_femur_correctly_sided_passes(self):
        a = {'bone_id': 'femur_right'}
        bone = {'head_m': [-0.06, 0, 1.1], 'tail_m': [-0.06, 0, 0.7]}
        v = [[-0.06, 0, 1.1], [-0.08, 0, 1.1],
             [-0.06, 0.02, 1.1], [-0.06, 0, 0.7]]
        self.assertTrue(correspondence.check(a, bone, v)['side_checked'])

    def test_invalid_basis_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unsupported world basis'):
            correspondence.check({'bone_id': 'femur_left'},
                {'head_m': [0, 0, 0], 'tail_m': [0, 0, 1]},
                [[0, 0, 0], [0, 0, 1]], basis='SOME_OTHER_BASIS')

    def test_oversized_geometry_rejected(self):
        with self.assertRaisesRegex(ValueError, 'implausibly large'):
            correspondence.check({'bone_id': 'humerus_left'},
                {'head_m': [0, 0, 0], 'tail_m': [0, 0, 1]},
                [[0, 0, 0], [0, 0, 1], [10, 0, 0]])

    def test_unknown_surface_type_rejected_before_mesh_processing(self):
        a = copy.deepcopy(ASSET)
        a['surface_type'] = 'not_a_real_surface_type'
        a['triangles'] = []
        with self.assertRaisesRegex(ValueError, 'unsupported surface type'):
            contract.validate(a, SKELETON, ARTICULATIONS)

    def test_spatial_inputs_never_modified(self):
        a = {'bone_id': 'femur_left'}
        b = {'head_m': [0.06, 0, 1.1], 'tail_m': [0.06, 0, 0.7]}
        v = [[0.06, 0, 1.1], [0.08, 0, 1.1],
             [0.06, 0.02, 1.1], [0.06, 0, 0.7]]
        prior = copy.deepcopy((a, b, v))
        correspondence.check(a, b, v)
        self.assertEqual((a, b, v), prior)


def pinched_connected_shell():
    # Three quads of ring vertices with two apex fans. The two end apices
    # are identified as one topological vertex. The resulting surface has
    # two disconnected *fans at one vertex* but an otherwise connected
    # edge-manifold triangle graph.
    import math
    rings = []
    for z in (2., 0., -2.):
        rings.extend([[math.cos(2*math.pi*i/4), math.sin(2*math.pi*i/4), z]
                      for i in range(4)])
    apex = 12
    verts = rings + [[0, 0, 3]]
    faces = []
    for i in range(4):
        j = (i + 1) % 4
        faces.append([apex, j, i])
        for k in (0, 4):
            faces.append([k+i, k+j, k+4+i])
            faces.append([k+j, k+4+j, k+4+i])
        faces.append([apex, 8+i, 8+j])
    return verts, faces


class PinchedVertexTests(unittest.TestCase):
    def test_connected_edge_manifold_but_pinched_vertex_is_rejected(self):
        verts, faces = pinched_connected_shell()
        with self.assertRaisesRegex(ValueError, 'pinched/non-manifold vertex'):
            topology.inspect(verts, faces, True)

    def test_separated_open_triangles_do_not_require_a_single_shell(self):
        vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0],
                    [2, 0, 0], [3, 0, 0], [2, 1, 0]]
        triangles = [[0, 1, 2], [3, 4, 5]]
        x = topology.inspect(vertices, triangles, False)
        self.assertEqual(x['edge_connected_components'], 2)

    def test_vertex_only_gluing_in_open_patch_is_rejected(self):
        vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0],
                    [-1, 0, 0], [0, -1, 0]]
        triangles = [[0, 1, 2], [0, 3, 4]]
        with self.assertRaisesRegex(ValueError, 'pinched/non-manifold vertex'):
            topology.inspect(vertices, triangles, False)


if __name__ == '__main__':
    unittest.main()

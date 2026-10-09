"""No-Blender mutation tests for bone mesh orientation and topology."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import bone_surface_topology as topo
import bone_surface_contract as contract

V = [[0., 0., 0.], [1., 0., 0.], [0., 1., 0.], [0., 0., 1.]]
F = [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]]


def inspect(verts=V, faces=F, closed=True):
    return topo.inspect(copy.deepcopy(verts), copy.deepcopy(faces), closed)


class TopologyChecks(unittest.TestCase):
    def test_closed_tetra_is_single_oriented_shell(self):
        r = inspect()
        self.assertEqual(r['edge_connected_components'], 1)
        self.assertEqual(r['boundary_edges'], 0)
        self.assertEqual(r['unused_vertices'], 0)
        self.assertAlmostEqual(r['signed_enclosed_volume_m3'], 1 / 6)
        self.assertFalse(r['anatomical_shape_verified'])
        self.assertFalse(r['self_intersection_checked'])

    def test_reverse_all_faces_rejected(self):
        with self.assertRaisesRegex(ValueError, 'nonpositive signed'):
            inspect(faces=[list(reversed(f)) for f in F])

    def test_single_flipped_face_rejected(self):
        ff = copy.deepcopy(F)
        ff[2].reverse()
        with self.assertRaisesRegex(ValueError, 'inconsistent face winding'):
            inspect(faces=ff)

    def test_duplicate_face_rejected_even_when_reversed(self):
        with self.assertRaisesRegex(ValueError, 'duplicate triangle'):
            inspect(faces=F + [list(reversed(F[0]))])

    def test_missing_closed_face_rejected(self):
        with self.assertRaisesRegex(ValueError, 'boundary edges'):
            inspect(faces=F[:-1])

    def test_two_disconnected_closed_shells_rejected(self):
        W = V + [[x + 3, y, z] for x, y, z in V]
        G = F + [[x + 4 for x in f] for f in F]
        with self.assertRaisesRegex(ValueError, 'disconnected shells'):
            inspect(verts=W, faces=G)

    def test_two_shells_touching_only_at_one_vertex_still_disconnected(self):
        # Sharing a point does not establish an edge-connected manifold.
        W = V + [[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]]
        G = F + [[x + 4 for x in f] for f in F]
        with self.assertRaisesRegex(ValueError, 'disconnected shells'):
            inspect(verts=W, faces=G)

    def test_more_than_two_faces_per_edge_rejected(self):
        W = V + [[1, 1, 1]]
        G = F + [[0, 1, 4]]
        with self.assertRaisesRegex(ValueError, 'non-manifold edge'):
            inspect(verts=W, faces=G)

    def test_unused_closed_vertex_rejected(self):
        with self.assertRaisesRegex(ValueError, 'unreferenced vertices'):
            inspect(verts=V + [[2, 2, 2]])

    def test_open_patch_can_have_boundary_and_unused_vertex(self):
        r = inspect(faces=[[0, 1, 2]], closed=False)
        self.assertEqual(r['boundary_edges'], 3)
        self.assertEqual(r['unused_vertices'], 1)
        self.assertIsNone(r['signed_enclosed_volume_m3'])

    def test_open_patch_with_two_consistent_triangles(self):
        r = inspect(faces=[[0, 1, 2], [1, 0, 3]], closed=False)
        self.assertEqual(r['edge_connected_components'], 1)
        self.assertEqual(r['boundary_edges'], 4)

    def test_open_patch_with_wrong_shared_winding_rejected(self):
        with self.assertRaisesRegex(ValueError, 'inconsistent face winding'):
            inspect(faces=[[0, 1, 2], [0, 1, 3]], closed=False)

    def test_caller_inputs_unchanged(self):
        verts, faces = copy.deepcopy(V), copy.deepcopy(F)
        topo.inspect(verts, faces, True)
        self.assertEqual(verts, V)
        self.assertEqual(faces, F)

    def test_existing_contract_uses_topology_checks(self):
        asset = {
            'schema_version': 1, 'status': 'AUDIT_ONLY', 'units': 'm',
            'bone_id': 'humerus_left', 'surface_type': 'closed_bone',
            'world_from_local': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
            'rig_anchors_local_m': {'head': [0, 0, 0], 'tail': [0, 0, 1]},
            'vertices_m': copy.deepcopy(V), 'triangles': [list(reversed(f)) for f in F],
            'articular_patches': [], 'attachment_landmarks': []}
        skel = {'bones': {'humerus_left': {'head_m': [0, 0, 0], 'tail_m': [0, 0, 1]}}}
        joints = {'articulations': [], 'additional_structures': {}}
        with self.assertRaisesRegex(ValueError, 'nonpositive signed'):
            contract.validate(asset, skel, joints)

    def test_open_component_count_is_diagnostic_not_acceptance(self):
        W = V + [[x + 3, y, z] for x, y, z in V]
        G = [F[0], [x + 4 for x in F[1]]]
        r = inspect(verts=W, faces=G, closed=False)
        self.assertEqual(r['edge_connected_components'], 2)
        self.assertFalse(r['anatomical_shape_verified'])


if __name__ == '__main__':
    unittest.main()

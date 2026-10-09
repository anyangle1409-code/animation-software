"""Minimal no-Blender tests of the bone geometry validation contract."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'anatomy_fit'))
import bone_surface_contract as g

SKELETON = {'bones': {'humerus_left': {'head_m': [0., 0., 0.], 'tail_m': [0., 0., 1.]},
                      'humerus_right': {'head_m': [0., 0., 0.], 'tail_m': [0., 0., 1.]}}}
ARTICULATIONS = {'articulations': [{'id': 'elbow_left', 'participants': ['humerus_left', 'ulna_left', 'radius_left']}],
                 'additional_structures': {}}
ASSET = {'schema_version': 1, 'status': 'AUDIT_ONLY', 'units': 'm',
         'bone_id': 'humerus_left', 'surface_type': 'closed_bone',
         'world_from_local': [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]],
         'rig_anchors_local_m': {'head': [0, 0, 0], 'tail': [0, 0, 1]},
         'vertices_m': [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]],
         'triangles': [[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]],
         'articular_patches': [{'id': 'distal', 'joint_id': 'elbow_left', 'triangle_indices': [0]}],
         'attachment_landmarks': [{'id': 'sample', 'point_local_m': [0, 0, 0]}]}


class SurfaceContractTests(unittest.TestCase):
    def check(self, changes=None):
        a = copy.deepcopy(ASSET)
        if changes:
            changes(a)
        return g.validate(a, SKELETON, ARTICULATIONS)

    def test_valid_closed_fixture_never_promotes(self):
        result = self.check()
        self.assertFalse(result['canonical_promotion_allowed'])
        self.assertEqual(result['status'], 'GEOMETRY_CONSISTENT_ANATOMY_UNVERIFIED')
        self.assertEqual(result['mesh']['boundary_edges'], 0)
        self.assertEqual(result['articular_patches_checked'], 1)

    def test_original_input_records_untouched(self):
        before = json.dumps([SKELETON, ARTICULATIONS, ASSET], sort_keys=True)
        self.check()
        after = json.dumps([SKELETON, ARTICULATIONS, ASSET], sort_keys=True)
        self.assertEqual(before, after)

    def test_rejects_units(self):
        with self.assertRaisesRegex(ValueError, 'metre'):
            self.check(lambda a: a.update(units='mm'))

    def test_rejects_bad_rig_alignment(self):
        with self.assertRaisesRegex(ValueError, 'anchor differs'):
            self.check(lambda a: a['rig_anchors_local_m']['tail'].__setitem__(2, 1.01))

    def test_rejects_reflections(self):
        with self.assertRaisesRegex(ValueError, 'mirrored'):
            self.check(lambda a: a['world_from_local'][0].__setitem__(0, -1))

    def test_rejects_scale(self):
        with self.assertRaisesRegex(ValueError, 'scaled'):
            self.check(lambda a: a['world_from_local'][0].__setitem__(0, 1.01))

    def test_rejects_nonfinite_vertex(self):
        with self.assertRaisesRegex(ValueError, 'finite'):
            self.check(lambda a: a['vertices_m'][0].__setitem__(0, float('nan')))

    def test_rejects_missing_mesh_face(self):
        with self.assertRaisesRegex(ValueError, 'edge-manifold'):
            self.check(lambda a: a['triangles'].pop())

    def test_rejects_nonparticipant_joint(self):
        with self.assertRaisesRegex(ValueError, 'not an articulation participant'):
            self.check(lambda a: a.update(bone_id='humerus_right'))

    def test_rejects_out_of_range_patch_face(self):
        with self.assertRaisesRegex(ValueError, 'invalid triangle'):
            self.check(lambda a: a['articular_patches'][0].update(triangle_indices=[9]))

    def test_rejects_duplicate_landmark(self):
        with self.assertRaisesRegex(ValueError, 'duplicate attachment'):
            self.check(lambda a: a['attachment_landmarks'].append(dict(a['attachment_landmarks'][0])))

    def test_open_diagnostic_patch_is_supported(self):
        result = self.check(lambda a: a.update(surface_type='open_review_patch', triangles=[[0, 1, 2]]))
        self.assertEqual(result['mesh']['boundary_edges'], 3)
        self.assertFalse(result['canonical_promotion_allowed'])

    def test_rejects_fake_acceptance(self):
        with self.assertRaisesRegex(ValueError, 'AUDIT_ONLY'):
            self.check(lambda a: a.update(status='ACCEPTED'))


if __name__ == '__main__':
    unittest.main()

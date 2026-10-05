import unittest

import numpy as np

import original_v1_shoulder_yoke_rest_length as rest_length


class ShoulderYokeRestLengthTests(unittest.TestCase):
    def valid_declaration(self):
        return {
            "declared_before_edit": True,
            "target_revision": "r96",
            "parent": {
                "sha256": rest_length.TOPOLOGY_PARENT_SHA256,
                "lineage_parent_r95_sha256": rest_length.R95_SHA256,
            },
            "mirror_pairs": [[10, 20], [11, 21]],
            "new_support_vertex_ids": [10, 11, 20, 21],
            "probe_strengths_m": [0.004, 0.008, 0.012],
            "maximum_displacement_m": 0.012,
            "shape_key_policy": "same_offset_all_keys",
            "preserve": ["original_vertices", "weights", "topology", "rig"],
            "stop_conditions": ["critical_or_high_defect", "material_regression"],
            "production_approved": False,
        }

    def test_offset_field_is_mirror_symmetric_tapered_and_bounded(self):
        rest = np.array(
            [
                [-0.08, -0.10, 1.41],
                [-0.18, -0.02, 1.41],
                [-0.29, 0.08, 1.41],
                [0.08, -0.10, 1.41],
                [0.18, -0.02, 1.41],
                [0.29, 0.08, 1.41],
            ],
            dtype=float,
        )
        normals = np.array(
            [
                [-1.0, -0.1, 0.2],
                [-0.8, -0.4, 0.1],
                [-1.0, 0.2, -0.1],
                [1.0, -0.1, 0.2],
                [0.8, -0.4, 0.1],
                [1.0, 0.2, -0.1],
            ],
            dtype=float,
        )
        offsets = rest_length.build_mirrored_normal_offsets(
            rest, normals, [(0, 3), (1, 4), (2, 5)], strength=0.012
        )

        self.assertTrue(np.array_equal(offsets[[0, 2, 3, 5]], np.zeros((4, 3))))
        self.assertAlmostEqual(float(np.linalg.norm(offsets[1])), 0.012)
        self.assertTrue(np.allclose(offsets[4], offsets[1] * [-1.0, 1.0, 1.0]))
        self.assertLessEqual(float(np.linalg.norm(offsets, axis=1).max()), 0.012)

    def test_offset_field_rejects_non_mirrored_pair_geometry(self):
        rest = np.array([[-0.18, 0.0, 1.41], [0.19, 0.0, 1.41]], dtype=float)
        normals = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
        with self.assertRaisesRegex(ValueError, "rest-space mirror"):
            rest_length.build_mirrored_normal_offsets(rest, normals, [(0, 1)], strength=0.004)

    def test_strength_must_stay_inside_declared_family(self):
        rest = np.array([[-0.18, 0.0, 1.41], [0.18, 0.0, 1.41]], dtype=float)
        normals = np.array([[-1.0, 0.0, 0.0], [1.0, 0.0, 0.0]], dtype=float)
        with self.assertRaisesRegex(ValueError, "declared maximum"):
            rest_length.build_mirrored_normal_offsets(rest, normals, [(0, 1)], strength=0.013)

    def test_rest_length_declaration_is_fail_closed(self):
        self.assertEqual(rest_length.validate_rest_length_declaration(self.valid_declaration()), [])
        declaration = self.valid_declaration()
        declaration["mirror_pairs"][0][0] = 99
        self.assertIn("mirror pair IDs must exactly cover new support vertices", rest_length.validate_rest_length_declaration(declaration))
        declaration = self.valid_declaration()
        declaration["probe_strengths_m"][-1] = 0.013
        self.assertIn("probe strengths exceed the displacement bound", rest_length.validate_rest_length_declaration(declaration))


if __name__ == "__main__":
    unittest.main()

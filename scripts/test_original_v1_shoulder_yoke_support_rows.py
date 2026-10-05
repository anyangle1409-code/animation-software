import copy
import unittest

import original_v1_shoulder_yoke_support_rows as support_rows


class ShoulderYokeSupportRowsTests(unittest.TestCase):
    def fixture(self):
        return {
            "schema_version": 1,
            "declared_before_edit": True,
            "target_revision": "r96",
            "parent_sha256": support_rows.R96_TOPOLOGY_SHA256,
            "ancestor_r95_sha256": support_rows.R95_SHA256,
            "localization_evidence_sha256": "a" * 64,
            "operation": "three_closed_quad_support_rows",
            "ring_seed_edge_pairs": [[1, 2], [3, 4], [5, 6]],
            "ring_edge_ids": [[10, 11], [20, 21], [30, 31]],
            "existing_endpoint_vertex_ids": [1, 2, 3, 4, 5, 6],
            "expected_new_vertices": 6,
            "existing_r96_new_vertices": 120,
            "cumulative_new_vertices_from_r95": 126,
            "maximum_cumulative_new_vertices": 480,
            "maximum_cumulative_new_faces": 960,
            "maximum_new_vertex_influences": 4,
            "preserve_original_vertex_ids": True,
            "preserve_original_positions": True,
            "preserve_shape_key_original_points": True,
            "preserve_quads": True,
            "mirror_symmetric": True,
            "correctives_disabled_during_gate": True,
            "production_approved": False,
        }

    def test_valid_three_row_declaration_passes(self):
        self.assertEqual(support_rows.validate_support_rows_declaration(self.fixture()), [])

    def test_exact_topology_parent_and_r95_ancestor_are_required(self):
        row = self.fixture()
        row["parent_sha256"] = "0" * 64
        row["ancestor_r95_sha256"] = "1" * 64
        errors = support_rows.validate_support_rows_declaration(row)
        self.assertTrue(any("parent" in error for error in errors), errors)
        self.assertTrue(any("ancestor" in error for error in errors), errors)

    def test_exactly_three_disjoint_closed_rows_are_required(self):
        row = self.fixture()
        row["ring_edge_ids"] = [[10, 11], [11, 12]]
        errors = support_rows.validate_support_rows_declaration(row)
        self.assertTrue(any("three" in error for error in errors), errors)
        self.assertTrue(any("disjoint" in error for error in errors), errors)

    def test_cumulative_scope_cannot_exceed_original_ceiling(self):
        row = self.fixture()
        row["cumulative_new_vertices_from_r95"] = 481
        self.assertTrue(any("cumulative" in error for error in support_rows.validate_support_rows_declaration(row)))

    def test_preservation_and_gate_invariants_cannot_be_relaxed(self):
        row = self.fixture()
        for key in (
            "preserve_original_vertex_ids",
            "preserve_original_positions",
            "preserve_shape_key_original_points",
            "preserve_quads",
            "mirror_symmetric",
            "correctives_disabled_during_gate",
        ):
            broken = copy.deepcopy(row)
            broken[key] = False
            self.assertTrue(support_rows.validate_support_rows_declaration(broken), key)


if __name__ == "__main__":
    unittest.main()

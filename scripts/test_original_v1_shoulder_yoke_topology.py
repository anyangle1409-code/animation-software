"""Fail-closed tests for the r96 shoulder support-ring declaration."""
from __future__ import annotations

import copy
import unittest

import original_v1_shoulder_yoke_topology as topology


class ShoulderYokeTopologyTests(unittest.TestCase):
    def fixture(self):
        return {
            "schema_version": 1,
            "declared_before_edit": True,
            "target_revision": "r96",
            "parent_sha256": topology.R95_SHA256,
            "maximum_declaration_sha256": "a" * 64,
            "operation": "single_closed_quad_support_ring",
            "ring_edge_ids": [5, 8, 13],
            "existing_endpoint_vertex_ids": [1, 2, 3, 4, 5, 6],
            "centerline_bridge_vertex_ids": [2, 5],
            "expected_new_vertices": 3,
            "maximum_new_vertices": 480,
            "maximum_new_faces": 960,
            "maximum_new_vertex_influences": 4,
            "preserve_original_vertex_ids": True,
            "preserve_original_positions": True,
            "preserve_shape_key_original_points": True,
            "preserve_quads": True,
            "mirror_symmetric": True,
            "production_approved": False,
        }

    def test_valid_declaration_passes(self):
        self.assertEqual(topology.validate_topology_declaration(self.fixture()), [])

    def test_exact_parent_and_pre_edit_state_are_required(self):
        row = self.fixture()
        row["parent_sha256"] = "0" * 64
        row["declared_before_edit"] = False
        errors = topology.validate_topology_declaration(row)
        self.assertTrue(any("parent" in error for error in errors), errors)
        self.assertTrue(any("before edit" in error for error in errors), errors)

    def test_ring_ids_must_be_unique_and_counts_bounded(self):
        row = self.fixture()
        row["ring_edge_ids"] = [5, 5]
        row["expected_new_vertices"] = 481
        errors = topology.validate_topology_declaration(row)
        self.assertTrue(any("edge IDs" in error for error in errors), errors)
        self.assertTrue(any("new vertices" in error for error in errors), errors)

    def test_new_vertex_influence_limit_is_four(self):
        row = self.fixture()
        row["maximum_new_vertex_influences"] = 5
        self.assertTrue(any("influences" in error for error in topology.validate_topology_declaration(row)))

    def test_centerline_bridge_must_be_subset_of_endpoints(self):
        row = self.fixture()
        row["centerline_bridge_vertex_ids"].append(99)
        errors = topology.validate_topology_declaration(row)
        self.assertTrue(any("centerline" in error for error in errors), errors)

    def test_preservation_invariants_cannot_be_relaxed(self):
        row = self.fixture()
        for key in (
            "preserve_original_vertex_ids", "preserve_original_positions",
            "preserve_shape_key_original_points", "preserve_quads", "mirror_symmetric",
        ):
            broken = copy.deepcopy(row)
            broken[key] = False
            self.assertTrue(topology.validate_topology_declaration(broken), key)


if __name__ == "__main__":
    unittest.main()

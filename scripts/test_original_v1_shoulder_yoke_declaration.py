"""Safety tests for the r96 shoulder-yoke repair declaration."""
from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

import original_v1_shoulder_yoke_declaration as declaration


R95_SHA = "8a39a22d3fec36f82c1cd53f6d0a976748a8cf97de14d81e62b5789178403bdd"


class ShoulderYokeDeclarationTests(unittest.TestCase):
    def fixture(self, root: Path) -> dict:
        evidence = root / "evidence.json"
        evidence.write_text("{}\n", encoding="utf-8")
        return {
            "schema_version": 1,
            "declared_before_edit": True,
            "target_revision": "r96",
            "parent": {
                "revision": "r95",
                "candidate_path": "ORIGINAL_V1_WORK/candidates/HomeGymPT_Male_ORIGINAL_v1_O4_CANDIDATE_r95.blend",
                "sha256": R95_SHA,
            },
            "issue_ids": ["WB-AX-001", "WB-PEC-002"],
            "evidence_paths": ["evidence.json"],
            "zone": {
                "left_vertex_ids": [10, 11],
                "right_vertex_ids": [110, 111],
                "mirror_pairs": [[10, 110], [11, 111]],
                "maximum_existing_vertex_count": 4,
                "permitted_regions": ["shoulder", "torso", "arm"],
            },
            "permitted_bones": ["clavicle_l", "clavicle_r", "scapula_l", "scapula_r", "upperarm_l", "upperarm_r", "spine_02", "spine_03"],
            "topology_intent": {
                "operation": "local_support_loops",
                "maximum_new_vertices": 480,
                "maximum_new_faces": 480,
                "preserve_original_vertex_ids": True,
                "preserve_quads": True,
                "preserve_outward_normals": True,
            },
            "weight_intent": {
                "scope": "declared_zone_only",
                "maximum_influences": 4,
                "normalized": True,
                "mirror_symmetric": True,
            },
            "protected_zones": ["neck_boundary", "pelvis_boundary", "hands", "feet", "head", "clothing", "frozen_correctives"],
            "stop_conditions": ["parent_identity_mismatch", "out_of_scope_edit", "critical_or_high_defect", "material_regression"],
        }

    def validate(self, mutate=None):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            data = self.fixture(root)
            if mutate:
                mutate(data)
            return declaration.validate_declaration(data, root)

    def test_valid_exact_parent_mirror_closed_declaration_passes(self):
        self.assertEqual(self.validate(), [])

    def test_exact_r95_parent_identity_is_required(self):
        errors = self.validate(lambda data: data["parent"].update(sha256="0" * 64))
        self.assertTrue(any("exact r95 parent" in error for error in errors), errors)

    def test_zone_must_be_unique_disjoint_and_pair_complete(self):
        def mutate(data):
            data["zone"]["left_vertex_ids"] = [10, 10]
            data["zone"]["mirror_pairs"] = [[10, 110]]
        errors = self.validate(mutate)
        self.assertTrue(any("unique" in error for error in errors), errors)
        self.assertTrue(any("mirror" in error for error in errors), errors)

    def test_issue_and_existing_evidence_links_are_required(self):
        def mutate(data):
            data["issue_ids"] = []
            data["evidence_paths"] = ["missing.json"]
        errors = self.validate(mutate)
        self.assertTrue(any("issue" in error for error in errors), errors)
        self.assertTrue(any("evidence" in error for error in errors), errors)

    def test_permitted_bones_are_existing_shoulder_yoke_bones_only(self):
        errors = self.validate(lambda data: data["permitted_bones"].append("thigh_l"))
        self.assertTrue(any("permitted bones" in error for error in errors), errors)

    def test_topology_and_weight_scope_are_finite_and_fail_closed(self):
        def mutate(data):
            data["topology_intent"]["maximum_new_vertices"] = 0
            data["weight_intent"]["scope"] = "whole_mesh"
        errors = self.validate(mutate)
        self.assertTrue(any("maximum topology scope" in error for error in errors), errors)
        self.assertTrue(any("declared zone" in error for error in errors), errors)

    def test_all_protected_zones_and_stop_conditions_are_required(self):
        def mutate(data):
            data["protected_zones"].remove("neck_boundary")
            data["stop_conditions"].remove("material_regression")
        errors = self.validate(mutate)
        self.assertTrue(any("protected zones" in error for error in errors), errors)
        self.assertTrue(any("stop conditions" in error for error in errors), errors)


if __name__ == "__main__":
    unittest.main()

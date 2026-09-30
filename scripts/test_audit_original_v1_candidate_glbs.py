from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("audit_original_v1_candidate_glbs.py")
SPEC = importlib.util.spec_from_file_location("candidate_glb_audit", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)

ROOT = Path(__file__).resolve().parents[1]


class CandidateGlbAuditTests(unittest.TestCase):
    def test_committed_candidate_glbs_are_structurally_self_contained(self):
        result = mod.audit_candidate_set(
            ROOT / "ORIGINAL_V1_WORK/candidates/CANDIDATE_GLB_EXPORT.json",
            ROOT / "ORIGINAL_V1_WORK/hgpt_canonical_v4_original.json",
        )
        self.assertTrue(result["pass"], result)
        by_variant = {item["variant"]: item for item in result["variants"]}

        self.assertEqual(by_variant["bare"]["expected_bone_count"], 63)
        self.assertEqual(by_variant["bare"]["image_count"], 0)
        self.assertEqual(by_variant["bare"]["texture_count"], 0)
        self.assertEqual(by_variant["bare"]["animation_count"], 0)
        self.assertEqual(by_variant["bare"]["mesh_node_count"], 1)

        self.assertEqual(by_variant["dressed"]["expected_bone_count"], 63)
        self.assertEqual(by_variant["dressed"]["image_count"], 0)
        self.assertEqual(by_variant["dressed"]["texture_count"], 0)
        self.assertEqual(by_variant["dressed"]["animation_count"], 0)
        self.assertEqual(by_variant["dressed"]["mesh_node_count"], 2)


if __name__ == "__main__":
    unittest.main()

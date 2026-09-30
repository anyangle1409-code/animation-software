from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("verify_original_v1_candidate_status.py")
SPEC = importlib.util.spec_from_file_location("candidate_status_verify", SCRIPT)
assert SPEC and SPEC.loader
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class CandidateStatusTests(unittest.TestCase):
    def test_current_candidate_status_matches_repository_evidence(self):
        result = mod.verify_status()
        self.assertTrue(result["pass"], result)
        self.assertEqual(result["overall_status"], "candidate_not_production")
        self.assertFalse(result["production_approved"])
        self.assertEqual(result["development_failures"], 54)
        self.assertEqual(result["production_failures"], 133)
        self.assertEqual(result["next_repair_priority"], 1)
        self.assertEqual(result["unmapped_failures"], 0)
        self.assertTrue(result["candidate_glb_structural_pass"])


if __name__ == "__main__":
    unittest.main()

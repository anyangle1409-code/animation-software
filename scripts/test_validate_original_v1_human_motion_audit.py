"""Tests for the ORIGINAL v1 whole-body human-motion realism audit contract."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

MODULE_PATH = Path(__file__).with_name("validate_original_v1_human_motion_audit.py")
SPEC = importlib.util.spec_from_file_location("human_motion_audit", MODULE_PATH)
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class HumanMotionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = audit.validate_plan(audit.read_json(audit.PLAN_PATH))

    def fixture(self):
        sha = "a" * 64
        refs = [{
            "id": "REF-001",
            "source_kind": "real_human_video",
            "title": "fixture human movement",
            "locator": "https://example.invalid/reference",
            "observations": ["fixture observation"],
        }]
        coverage = []
        for region in self.plan["regions"]:
            coverage.append({
                "region": region["id"],
                "candidate_sha256": sha,
                "states": list(self.plan["required_states"]),
                "movement_families": list(region["movement_families"]),
                "capture_ids": [f"{region['id']}_fixture"],
            })
        sweep = []
        for side in self.plan["axilla_chest_sweep"]["sides"]:
            for deg in self.plan["axilla_chest_sweep"]["arm_elevation_degrees"]:
                sweep.append({
                    "candidate_sha256": sha,
                    "side": side,
                    "elevation_degrees": deg,
                    "direction": "outbound",
                    "capture_id": f"{side}_{deg}",
                })
            sweep.append({
                "candidate_sha256": sha,
                "side": side,
                "elevation_degrees": 90,
                "direction": "return",
                "capture_id": f"{side}_return_90",
            })
        return {
            "schema_version": 1,
            "status": "AUDIT_IN_PROGRESS",
            "production_approved": False,
            "candidate_revision": "r96",
            "candidate_sha256": sha,
            "source_branch": "fixture",
            "reference_observations": refs,
            "coverage": coverage,
            "axilla_chest_sweep": sweep,
            "defects": [],
            "summary": {
                "engineering_verification": "IN_PROGRESS",
                "owner_review": "pending",
                "critical_open": 0,
                "high_open": 0,
                "medium_open": 0,
                "low_open": 0,
            },
        }

    def test_plan_has_explicit_chest_and_posterior_axilla_regions(self):
        ids = {row["id"] for row in self.plan["regions"]}
        self.assertIn("chest_anterior_axilla", ids)
        self.assertIn("back_posterior_axilla", ids)

    def test_plan_requires_intermediate_motion(self):
        self.assertIn("intermediate_transition", self.plan["required_states"])
        overhead = next(x for x in self.plan["movement_families"] if x["id"] == "overhead_push")
        self.assertTrue({"25%", "50%", "75%"}.issubset(set(overhead["samples"])))

    def test_plan_requires_bilateral_multi_angle_axilla_sweep(self):
        sweep = self.plan["axilla_chest_sweep"]
        self.assertEqual(sweep["sides"], ["left", "right"])
        self.assertEqual(sweep["arm_elevation_degrees"], [0, 45, 90, 120, 150, 170])
        self.assertTrue(sweep["include_return_transition"])

    def test_complete_fixture_passes_exit(self):
        result = audit.validate_ledger(self.plan, self.fixture(), require_exit=True)
        self.assertEqual(result["regions_with_evidence"], result["total_regions"])
        self.assertEqual(result["open_by_severity"]["HIGH"], 0)

    def test_missing_axilla_checkpoint_blocks_exit(self):
        ledger = self.fixture()
        ledger["axilla_chest_sweep"] = ledger["axilla_chest_sweep"][1:]
        with self.assertRaisesRegex(ValueError, "axilla/chest sweep incomplete"):
            audit.validate_ledger(self.plan, ledger, require_exit=True)

    def test_open_high_defect_blocks_exit(self):
        ledger = self.fixture()
        ledger["defects"].append({
            "defect_id": "HM-001",
            "candidate_revision": "r96",
            "candidate_sha256": ledger["candidate_sha256"],
            "region": "chest_anterior_axilla",
            "side": "left",
            "movement_family": "overhead_push",
            "sample": "50%",
            "capture_id": "left_90",
            "severity": "HIGH",
            "observed_defect": "deep artificial axillary tunnel",
            "expected_human_behaviour": "fold changes continuously with arm elevation",
            "reference_observations": ["REF-001"],
            "suspected_cause_hypothesis": "local skin/corrective behaviour",
            "before_evidence": ["fixture.png"],
            "status": "OPEN",
            "owner_review": "pending",
        })
        with self.assertRaisesRegex(ValueError, "open critical/high"):
            audit.validate_ledger(self.plan, ledger, require_exit=True)

    def test_fixed_defect_requires_after_and_regression_evidence(self):
        ledger = self.fixture()
        defect = {
            "defect_id": "HM-002",
            "candidate_revision": "r96",
            "candidate_sha256": ledger["candidate_sha256"],
            "region": "chest_anterior_axilla",
            "side": "left",
            "movement_family": "overhead_push",
            "sample": "50%",
            "capture_id": "left_90",
            "severity": "HIGH",
            "observed_defect": "fixture",
            "expected_human_behaviour": "fixture",
            "reference_observations": ["REF-001"],
            "suspected_cause_hypothesis": "fixture",
            "before_evidence": ["before.png"],
            "status": "FIXED_VERIFIED",
            "owner_review": "pending",
        }
        ledger["defects"].append(defect)
        with self.assertRaisesRegex(ValueError, "lacks after/regression evidence"):
            audit.validate_ledger(self.plan, ledger)

    def test_ledger_may_not_claim_production_approval(self):
        ledger = self.fixture()
        ledger["production_approved"] = True
        with self.assertRaisesRegex(ValueError, "may not claim production approval"):
            audit.validate_ledger(self.plan, ledger)


if __name__ == "__main__":
    unittest.main()

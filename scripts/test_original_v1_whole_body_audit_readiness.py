"""Tests for the non-Blender whole-body deformation audit readiness contract."""
import copy
import json
from pathlib import Path
import unittest

import original_v1_whole_body_audit_readiness as readiness

ROOT = Path(__file__).resolve().parents[1]


def load(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


class WholeBodyAuditReadinessTests(unittest.TestCase):
    def live_inputs(self):
        return (
            load("ORIGINAL_V1_WHOLE_BODY_DEFORMATION_AUDIT_PLAN.json"),
            load("ORIGINAL_V1_HUMAN_EVIDENCE_MANIFEST.json"),
            load("ORIGINAL_V1_HUMAN_EVIDENCE_COVERAGE.json"),
            load("ORIGINAL_V1_MOVEMENT_ENVELOPE.json"),
            load("ORIGINAL_V1_WHOLE_BODY_ISSUE_LEDGER.json"),
        )

    def test_live_audit_infrastructure_is_ready_but_open_anatomy_still_blocks_phase4(self):
        result = readiness.assess(*self.live_inputs())
        self.assertTrue(result["audit_support_ready"], result["support_errors"])
        self.assertEqual(result["status"], "AUDIT_INFRASTRUCTURE_READY")
        self.assertFalse(result["phase4_clear"])
        self.assertGreater(result["critical_high_blocker_count"], 0)

    def test_live_shoulder_acceptance_contract_is_part_of_readiness(self):
        inputs = self.live_inputs()
        contract = load("ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json")
        result = readiness.assess(*inputs, contract)
        self.assertTrue(result["audit_support_ready"], result["support_errors"])

    def test_invalid_shoulder_acceptance_contract_blocks_infrastructure(self):
        inputs = self.live_inputs()
        contract = load("ORIGINAL_V1_SHOULDER_ANATOMICAL_ACCEPTANCE_CONTRACT.json")
        contract["promotion_rule"]["fail_closed"] = False
        result = readiness.assess(*inputs, contract)
        self.assertFalse(result["audit_support_ready"])
        self.assertTrue(any("shoulder acceptance contract" in x for x in result["support_errors"]))

    def test_missing_transition_zone_blocks_infrastructure(self):
        plan, manifest, coverage, envelope, ledger = self.live_inputs()
        plan["transition_zones"].pop()
        result = readiness.assess(plan, manifest, coverage, envelope, ledger)
        self.assertFalse(result["audit_support_ready"])
        self.assertTrue(any("WBZ-01..WBZ-16" in x for x in result["support_errors"]))

    def test_unknown_transition_movement_category_blocks(self):
        plan, manifest, coverage, envelope, ledger = self.live_inputs()
        plan["transition_zones"][0]["movement_categories"].append("invented_motion")
        result = readiness.assess(plan, manifest, coverage, envelope, ledger)
        self.assertTrue(any("unknown movement category" in x for x in result["support_errors"]))

    def test_missing_human_evidence_coverage_blocks_infrastructure(self):
        plan, manifest, coverage, envelope, ledger = self.live_inputs()
        coverage["categories"].pop()
        result = readiness.assess(plan, manifest, coverage, envelope, ledger)
        self.assertFalse(result["audit_support_ready"])
        self.assertTrue(any("without evidence coverage" in x for x in result["support_errors"]))

    def test_fixed_high_issue_requires_ledger_evidence_but_does_not_block_when_valid(self):
        plan, manifest, coverage, envelope, ledger = self.live_inputs()
        ledger = copy.deepcopy(ledger)
        for row in ledger["issues"]:
            if row["severity"] in ("Critical", "High"):
                row["state"] = "Fixed"
                row["closure_evidence"] = ["fixture-closure.json"]
        # Direct fixture validation does not resolve filesystem paths; the readiness
        # layer only needs schema-valid committed-path-shaped closure references here.
        result = readiness.assess(plan, manifest, coverage, envelope, ledger)
        self.assertTrue(result["audit_support_ready"], result["support_errors"])
        self.assertEqual(result["critical_high_blocker_count"], 0)
        self.assertTrue(result["phase4_clear"])


if __name__ == "__main__":
    unittest.main()

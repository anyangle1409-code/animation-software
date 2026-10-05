"""Tests for the authoritative ORIGINAL-v1 human-body master plan."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH = Path(__file__).with_name("validate_original_v1_human_body_master_plan.py")
SPEC = importlib.util.spec_from_file_location("human_body_master_plan", MODULE_PATH)
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class HumanBodyMasterPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = mod.validate_plan(mod.read(mod.PLAN))

    def fixture_ledger(self):
        return {
            "schema_version": 1,
            "candidate_under_review": {
                "revision": "r95",
                "sha256": "a" * 64,
            },
            "issues": [
                {
                    "id": "WB-AX-001",
                    "severity": "Critical",
                    "state": "Open",
                },
                {
                    "id": "WB-LOW-999",
                    "severity": "Low",
                    "state": "Open",
                },
            ],
        }

    def test_master_stages_are_exactly_1_to_14(self):
        self.assertEqual([x["id"] for x in self.plan["stages"]], list(range(1, 15)))

    def test_high_detail_is_blocked_while_stage1_active(self):
        by_id = {x["id"]: x for x in self.plan["stages"]}
        self.assertEqual(by_id[1]["state"], "active")
        self.assertEqual(by_id[5]["state"], "blocked")

    def test_axilla_regions_are_explicit(self):
        regions = {x["id"] for x in self.plan["body_regions"]}
        self.assertIn("chest_anterior_axilla", regions)
        self.assertIn("back_posterior_axilla", regions)

    def test_motion_sampling_requires_intermediate_and_return(self):
        self.assertEqual(
            self.plan["default_motion_sampling"],
            ["start", "25%", "50%", "75%", "end", "return"],
        )

    def test_open_critical_issue_blocks_high_detail(self):
        action = mod.next_action(self.plan, self.fixture_ledger())
        self.assertFalse(action["high_detail_anatomy_allowed"])
        self.assertIn("WB-AX-001", action["blocking_issue_ids"])

    def test_low_issue_alone_does_not_become_critical_blocker_but_stage5_still_not_inferred(self):
        ledger = self.fixture_ledger()
        ledger["issues"] = [ledger["issues"][1]]
        action = mod.next_action(self.plan, ledger)
        self.assertFalse(action["high_detail_anatomy_allowed"])
        self.assertEqual(action["blocking_issue_ids"], [])
        self.assertIn("Stage 1-4", action["reason"])

    def test_plan_may_not_claim_production_approval(self):
        bad = copy.deepcopy(self.plan)
        bad["production_approved"] = True
        with self.assertRaisesRegex(ValueError, "may not claim production approval"):
            mod.validate_plan(bad)

    def test_stage5_cannot_be_marked_active_in_current_contract(self):
        bad = copy.deepcopy(self.plan)
        bad["stages"][4]["state"] = "active"
        with self.assertRaisesRegex(ValueError, "Stage 5 high-detail anatomy must currently be blocked"):
            mod.validate_plan(bad)


if __name__ == "__main__":
    unittest.main()

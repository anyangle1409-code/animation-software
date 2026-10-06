"""Cross-phase execution orchestration is complete, ordered and non-executing."""
from __future__ import annotations

import copy
import json
import unittest

import original_v1_execution_orchestration as o


class ExecutionOrchestrationTests(unittest.TestCase):
    def plan(self):
        return json.loads((o.ROOT / o.PLAN).read_text(encoding="utf-8"))

    def current_state(self):
        from original_v1_production_control import build
        return build(o.ROOT)[0]

    def without_recovery_override(self, plan):
        plan = copy.deepcopy(plan)
        plan["current_expected_state"]["active"] = False
        return plan

    def test_live_plan_covers_support_and_selects_active_r96_recovery(self):
        plan = self.plan()
        info = o.validate_plan(o.ROOT, plan)
        self.assertEqual(info["prepared_stage_count"], 12)
        self.assertGreaterEqual(info["critical_path_count"], 10)
        self.assertEqual(plan["branch"], o.RECOVERY_BRANCH)
        self.assertEqual(plan["status"], "PREPARED_EXECUTION_ORCHESTRATION")
        self.assertEqual(plan["recovery_status"], "ANATOMICAL_RECOVERY_TASK7_PREPARED")
        self.assertTrue(plan["current_expected_state"]["active"])
        self.assertEqual(
            o.select_node(plan, self.current_state())["id"],
            "3A_axilla_local",
        )

    def test_recovery_override_wins_over_stale_historical_phase_complete_fields(self):
        plan = self.plan()
        state = {
            "current_subphase": "5A",
            "next_action": {"action": "EXECUTE Phase 5A"},
            "phases": {str(n): {"state": "complete"} for n in range(13)},
        }
        state["phases"]["5"]["state"] = "not_started"
        self.assertEqual(o.select_node(plan, state)["id"], "3A_axilla_local")

    def test_active_recovery_contract_is_hash_bound_and_has_release_condition(self):
        plan = self.plan()
        recovery = plan["current_expected_state"]
        self.assertEqual(
            recovery["topology_only_r96_sha256"],
            "6934594dde9140193882c0e293f8b404fb24bed8b1b1b2722267ff97d13844dd",
        )
        self.assertEqual(recovery["selector_node"], "3A_axilla_local")
        self.assertTrue(recovery["release_condition"])
        bad = copy.deepcopy(plan)
        bad["current_expected_state"]["selector_node"] = "5_anatomy"
        with self.assertRaisesRegex(ValueError, "selector"):
            o.validate_plan(o.ROOT, bad)

    def test_historical_phase3_selection_remains_available_after_override_is_released(self):
        plan = self.without_recovery_override(self.plan())
        base = copy.deepcopy(self.current_state())
        base["phases"]["3"]["state"] = "active"
        expected = {"3C": "3C_grip_thumb", "3D": "3D_wrist", "3E": "3E_lunge"}
        for sub, node_id in expected.items():
            state = copy.deepcopy(base)
            state["current_subphase"] = sub
            self.assertEqual(o.select_node(plan, state)["id"], node_id)

        state = copy.deepcopy(base)
        state["current_subphase"] = "4"
        state["next_action"] = {"action": "RECONCILE freeze regressions"}
        self.assertEqual(o.select_node(plan, state)["id"], "4_freeze")

        state = copy.deepcopy(base)
        state["current_subphase"] = "3B"
        state["next_action"] = {
            "command": next(
                r for r in plan["critical_path"] if r["id"] == "3B_r30"
            )["action"]
        }
        self.assertEqual(o.select_node(plan, state)["id"], "3B_r30")

        state["current_subphase"] = "3X"
        with self.assertRaisesRegex(ValueError, "unsupported active Phase 3 subphase"):
            o.select_node(plan, state)

    def test_phase_progression_selects_first_incomplete_phase_after_recovery_release(self):
        plan = self.without_recovery_override(self.plan())
        state = {
            "current_subphase": None,
            "next_action": {},
            "phases": {str(n): {"state": "complete"} for n in range(13)},
        }
        state["phases"]["7"]["state"] = "not_started"
        for n in range(8, 13):
            state["phases"][str(n)]["state"] = "not_started"
        self.assertEqual(o.select_node(plan, state)["id"], "7_clothing")

    def test_complete_phase_12_routes_to_controlled_release_after_recovery_release(self):
        plan = self.without_recovery_override(self.plan())
        state = {
            "current_subphase": None,
            "next_action": {},
            "phases": {str(n): {"state": "complete"} for n in range(13)},
        }
        self.assertEqual(o.select_node(plan, state)["id"], "controlled_release")

    def test_r30_selector_drift_refused_after_recovery_release(self):
        plan = self.without_recovery_override(self.plan())
        state = copy.deepcopy(self.current_state())
        state["phases"]["3"]["state"] = "active"
        state["current_subphase"] = "3B"
        state["next_action"] = {"command": "RUN_SOMETHING_ELSE.bat"}
        with self.assertRaisesRegex(ValueError, "selector command differs"):
            o.select_node(plan, state)

    def test_operational_tool_artifacts_are_validated(self):
        plan = self.plan()
        info = o.validate_plan(o.ROOT, plan)
        self.assertIn("session_start", plan["operational_tools"])
        self.assertIn("axilla_local_repair", plan["operational_tools"])
        self.assertNotIn(
            "RUN_ORIGINAL_V1_AXILLA_PIT_AUTO.bat",
            plan["operational_tools"]["axilla_local_repair"]["command"],
        )
        self.assertGreater(info["artifact_count"], 0)

    def test_unknown_support_stage_refused(self):
        plan = copy.deepcopy(self.plan())
        plan["critical_path"][1]["support_stages"] = [99]
        with self.assertRaisesRegex(ValueError, "unknown support"):
            o.validate_plan(o.ROOT, plan)

    def test_orchestrator_cannot_claim_phase_or_production_approval(self):
        for field in ("production_approved", "phase_complete"):
            with self.subTest(field=field):
                plan = copy.deepcopy(self.plan())
                plan[field] = True
                with self.assertRaisesRegex(ValueError, "approval or phase"):
                    o.validate_plan(o.ROOT, plan)


if __name__ == "__main__":
    unittest.main()

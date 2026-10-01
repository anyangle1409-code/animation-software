"""Cross-phase execution orchestration is complete, ordered and non-executing."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import unittest

import original_v1_execution_orchestration as o


class ExecutionOrchestrationTests(unittest.TestCase):
    def plan(self):
        return json.loads((o.ROOT / o.PLAN).read_text(encoding="utf-8"))

    def current_state(self):
        from original_v1_production_control import build
        return build(o.ROOT)[0]

    def test_live_plan_covers_all_prepared_support_and_selects_the_live_node(self):
        plan = self.plan()
        info = o.validate_plan(o.ROOT, plan)
        self.assertEqual(info["prepared_stage_count"], 12)
        self.assertGreaterEqual(info["critical_path_count"], 10)
        state = self.current_state()
        node = o.select_node(plan, state)
        # The orchestration node must agree with the live generated state (not a hard-coded historical step).
        phase3 = {"3B": "3B_r30", "3C": "3C_grip_thumb", "3D": "3D_wrist", "3E": "3E_lunge"}
        if state["phases"]["3"]["state"] != "complete":
            if state["current_subphase"] == "4":
                # all 3x subphases done, strict regressions still to reconcile: next node is the prepared Phase 4 package
                self.assertTrue(state["next_action"]["action"].startswith(("RECONCILE", "ENTER development freeze")))
                self.assertEqual(node["id"], "4_freeze")
            else:
                self.assertIn(state["current_subphase"], phase3)
                self.assertEqual(node["id"], phase3[state["current_subphase"]])
        else:
            self.assertNotIn(node["id"], phase3.values())

    def test_each_phase3_subphase_selects_its_own_node(self):
        plan = self.plan()
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
        state["next_action"] = {"action": "REPAIR lunge"}
        with self.assertRaisesRegex(ValueError, "unsupported active Phase 3 subphase"):
            o.select_node(plan, state)
        state["phases"]["3"]["state"] = "active"
        state = copy.deepcopy(base)
        state["current_subphase"] = "3B"
        state["next_action"] = {"command": next(r for r in plan["critical_path"] if r["id"] == "3B_r30")["action"]}
        self.assertEqual(o.select_node(plan, state)["id"], "3B_r30")
        state["current_subphase"] = "3X"
        with self.assertRaisesRegex(ValueError, "unsupported active Phase 3 subphase"):
            o.select_node(plan, state)

    def test_phase_progression_selects_first_incomplete_phase(self):
        plan = self.plan()
        state = {
            "current_subphase": None,
            "next_action": {},
            "phases": {str(n): {"state": "complete"} for n in range(13)},
        }
        state["phases"]["7"]["state"] = "not_started"
        for n in range(8, 13):
            state["phases"][str(n)]["state"] = "not_started"
        self.assertEqual(o.select_node(plan, state)["id"], "7_clothing")

    def test_complete_phase_12_routes_to_controlled_release(self):
        plan = self.plan()
        state = {
            "current_subphase": None,
            "next_action": {},
            "phases": {str(n): {"state": "complete"} for n in range(13)},
        }
        self.assertEqual(o.select_node(plan, state)["id"], "controlled_release")

    def test_r30_selector_drift_refused(self):
        plan = self.plan()
        # Explicit synthetic Phase 3B state (the live state has moved on): a selector command that differs
        # from the orchestration r30 action must still be refused.
        state = copy.deepcopy(self.current_state())
        state["phases"]["3"]["state"] = "active"
        state["current_subphase"] = "3B"
        state["next_action"] = {"command": "RUN_SOMETHING_ELSE.bat"}
        with self.assertRaisesRegex(ValueError, "selector command differs"):
            o.select_node(plan, state)

    def test_operational_tool_artifacts_are_validated(self):
        plan=self.plan()
        info=o.validate_plan(o.ROOT,plan)
        self.assertIn("session_start",plan["operational_tools"])
        self.assertGreater(info["artifact_count"],0)

    def test_unknown_support_stage_refused(self):
        plan = self.plan()
        plan = copy.deepcopy(plan)
        plan["critical_path"][1]["support_stages"] = [99]
        with self.assertRaisesRegex(ValueError, "unknown support"):
            o.validate_plan(o.ROOT, plan)

    def test_orchestrator_cannot_claim_phase_or_production_approval(self):
        for field in ("production_approved", "phase_complete"):
            with self.subTest(field=field):
                plan = self.plan()
                plan = copy.deepcopy(plan)
                plan[field] = True
                with self.assertRaisesRegex(ValueError, "approval or phase"):
                    o.validate_plan(o.ROOT, plan)


if __name__ == "__main__":
    unittest.main()

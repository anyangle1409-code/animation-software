"""Tests for connected-tissue repair regression planning."""
import importlib.util
from pathlib import Path
import unittest
MODULE=Path(__file__).with_name("build_original_v1_repair_regression_plan.py")
SPEC=importlib.util.spec_from_file_location("repair_regression",MODULE)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class RepairRegressionPlanTests(unittest.TestCase):
    def test_pec_repair_pulls_in_shoulder_back_trunk_neighbors(self):
        d=mod.build(["RP-PEC-AX-002"])
        focused=set(d["focused_coupling_system_ids"])
        self.assertIn("CP-PEC-AX-002",focused)
        self.assertIn("CP-DELTOID-004",focused)
        self.assertIn("CP-POSTAX-003",focused)
        self.assertIn("CP-TRUNK-008",focused)
        self.assertTrue(d["whole_body_regression_required"])

    def test_glute_repair_pulls_in_trunk_groin_thigh_neighbors(self):
        d=mod.build(["RP-GLUTE-009"])
        focused=set(d["focused_coupling_system_ids"])
        self.assertIn("CP-TRUNK-008",focused)
        self.assertIn("CP-GROIN-010",focused)
        self.assertIn("CP-QUAD-011",focused)
        self.assertIn("CP-HAM-012",focused)

if __name__=="__main__": unittest.main()

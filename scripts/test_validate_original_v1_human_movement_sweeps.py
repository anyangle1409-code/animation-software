"""Tests for deterministic human movement sweep plan."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_human_movement_sweeps.py")
SPEC=importlib.util.spec_from_file_location("human_movement_sweeps",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class HumanMovementSweepTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=mod.read(mod.PLAN)
        cls.master=mod.read(mod.MASTER)
        cls.human=mod.read(mod.HUMAN)

    def test_live_plan_valid(self):
        self.assertTrue(mod.validate(self.plan,self.master,self.human))

    def test_all_eight_formerly_missing_families_present(self):
        self.assertEqual(set(self.plan["sweeps"]),mod.REQUIRED_SWEEPS)

    def test_return_motion_is_required(self):
        bad=copy.deepcopy(self.plan)
        bad["sweeps"]["trunk_flexion"]["samples"]=["neutral","25%","50%","75%","end","hold"]
        with self.assertRaisesRegex(ValueError,"return-motion"):
            mod.validate(bad,self.master,self.human)

    def test_unknown_evidence_is_rejected(self):
        bad=copy.deepcopy(self.plan)
        bad["sweeps"]["grip_release"]["evidence_ids"]=["HE-NOT-REAL"]
        with self.assertRaisesRegex(ValueError,"unknown evidence"):
            mod.validate(bad,self.master,self.human)

if __name__=="__main__":
    unittest.main()

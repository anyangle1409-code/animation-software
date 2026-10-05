"""Tests for the joint-to-tissue trigger map."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_joint_tissue_triggers.py")
SPEC=importlib.util.spec_from_file_location("joint_tissue",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class JointTissueTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trigger=mod.read(mod.TRIGGER)
        cls.coupling=mod.read(mod.COUPLING)

    def test_live_map_valid(self):
        self.assertTrue(mod.validate(self.trigger,self.coupling))

    def test_upperarm_triggers_shoulder_chest_back(self):
        row=next(x for x in self.trigger["rules"] if x["joint_family"]=="humerus")
        systems=set(row["required_coupling_system_ids"])
        self.assertTrue({"CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004","CP-ARM-005"}.issubset(systems))

    def test_thigh_triggers_all_major_hip_thigh_chains(self):
        row=next(x for x in self.trigger["rules"] if x["joint_family"]=="hip_femur")
        systems=set(row["required_coupling_system_ids"])
        self.assertTrue({"CP-GLUTE-009","CP-GROIN-010","CP-QUAD-011","CP-HAM-012"}.issubset(systems))

    def test_unknown_coupling_system_rejected(self):
        bad=copy.deepcopy(self.trigger)
        bad["rules"][0]["required_coupling_system_ids"].append("CP-NOT-REAL-999")
        with self.assertRaisesRegex(ValueError,"unknown coupling systems"):
            mod.validate(bad,self.coupling)

if __name__=="__main__":
    unittest.main()

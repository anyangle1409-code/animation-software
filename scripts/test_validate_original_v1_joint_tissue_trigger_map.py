"""Tests for joint-to-tissue trigger map validation."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_joint_tissue_trigger_map.py")
SPEC=importlib.util.spec_from_file_location("jt_trigger",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class JointTissueTriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=mod.read(mod.TRIGGERS)
        cls.coupling=mod.read(mod.COUPLING)

    def test_live_map_valid(self):
        self.assertTrue(mod.validate(self.data,self.coupling))

    def test_upperarm_requires_all_shoulder_surface_chains(self):
        out=mod.required_for_bones(self.data,["upperarm_l"])
        req=set(out["required_coupling_system_ids"])
        self.assertTrue({"CP-PEC-AX-002","CP-POSTAX-003","CP-DELTOID-004","CP-ARM-005"}.issubset(req))

    def test_thigh_requires_glute_groin_quad_hamstring(self):
        out=mod.required_for_bones(self.data,["thigh_r"])
        req=set(out["required_coupling_system_ids"])
        self.assertTrue({"CP-GLUTE-009","CP-GROIN-010","CP-QUAD-011","CP-HAM-012"}.issubset(req))

    def test_unknown_coupling_id_fails(self):
        bad=copy.deepcopy(self.data)
        bad["rules"][0]["required_coupling_system_ids"].append("CP-NOT-REAL")
        with self.assertRaisesRegex(ValueError,"unknown coupling ids"):
            mod.validate(bad,self.coupling)

if __name__=="__main__":
    unittest.main()

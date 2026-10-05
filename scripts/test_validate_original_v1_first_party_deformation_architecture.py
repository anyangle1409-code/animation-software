"""Tests for the first-party deformation architecture contract."""
import copy,importlib.util
from pathlib import Path
import unittest

MODULE_PATH=Path(__file__).with_name("validate_original_v1_first_party_deformation_architecture.py")
SPEC=importlib.util.spec_from_file_location("deformation_arch",MODULE_PATH)
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class FirstPartyDeformationArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.a=mod.read(mod.ARCH); cls.m=mod.read(mod.MASTER); cls.c=mod.read(mod.COUPLING); cls.t=mod.read(mod.TRIGGERS)

    def test_live_architecture_valid(self):
        self.assertTrue(mod.validate(self.a,self.m,self.c,self.t))

    def test_exercise_identity_is_forbidden(self):
        forbidden=set(self.a["generic_driver_contract"]["forbidden_inputs"])
        self.assertIn("exercise_name",forbidden)
        self.assertIn("exercise_id",forbidden)

    def test_base_skinning_remains_evidence_selected(self):
        base=next(x for x in self.a["stack"] if x["id"]=="base_skinning")
        self.assertIn("UNRESOLVED",base["current_decision"])

    def test_removing_runtime_parity_fails(self):
        bad=copy.deepcopy(self.a); bad["production_parity_gate"]["standalone_runtime_required"]=False
        with self.assertRaisesRegex(ValueError,"parity requirement"):
            mod.validate(bad,self.m,self.c,self.t)

    def test_allowing_exercise_specific_logic_fails(self):
        bad=copy.deepcopy(self.a); bad["generic_driver_contract"]["forbidden_inputs"].remove("exercise_name")
        with self.assertRaisesRegex(ValueError,"exercise identity"):
            mod.validate(bad,self.m,self.c,self.t)

if __name__=="__main__": unittest.main()

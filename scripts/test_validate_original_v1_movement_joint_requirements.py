"""Tests for movement -> joint-family requirements."""
import copy,importlib.util
from pathlib import Path
import unittest
P=Path(__file__).with_name("validate_original_v1_movement_joint_requirements.py")
S=importlib.util.spec_from_file_location("move_joint",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class MovementJointRequirementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=mod.read(mod.PATH); cls.m=mod.read(mod.MASTER); cls.t=mod.read(mod.TRIGGERS)

    def test_live_authority_valid(self):
        out=mod.validate(self.d,self.m,self.t)
        self.assertEqual(out["movements"],27)

    def test_missing_movement_fails(self):
        bad=copy.deepcopy(self.d); bad["movements"].pop("trunk_axial_rotation")
        with self.assertRaisesRegex(ValueError,"coverage/order"):
            mod.validate(bad,self.m,self.t)

    def test_unknown_joint_family_fails(self):
        bad=copy.deepcopy(self.d); bad["movements"]["trunk_flexion"]["required_joint_families"]=["mystery"]
        with self.assertRaisesRegex(ValueError,"unknown joint families"):
            mod.validate(bad,self.m,self.t)

    def test_active_movement_cannot_have_empty_required_set(self):
        bad=copy.deepcopy(self.d); bad["movements"]["trunk_flexion"]["required_joint_families"]=[]
        with self.assertRaisesRegex(ValueError,"active movement requires"):
            mod.validate(bad,self.m,self.t)

    def test_control_movement_does_not_require_active_joint(self):
        bad=copy.deepcopy(self.d); bad["movements"]["neutral_braced_trunk"]["required_joint_families"]=["trunk_pelvis"]
        with self.assertRaisesRegex(ValueError,"control-only"):
            mod.validate(bad,self.m,self.t)

if __name__=="__main__": unittest.main()

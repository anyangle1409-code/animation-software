"""Tests for generic human movement sweep execution readiness."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_execution.py")
S=importlib.util.spec_from_file_location("sweep_exec",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class HumanMovementSweepExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=mod.read(mod.STATUS); cls.plan=mod.read(mod.PLAN)
        cls.packages=mod.read(mod.PACKAGES); cls.posemap=mod.read(mod.POSEMAP); cls.graph=mod.read(mod.GRAPH)

    def test_live_preparation_state_is_valid_but_not_fully_bound(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,False)
        self.assertEqual(out["sweeps_total"],11)
        self.assertEqual(out["bound"],0)
        self.assertFalse(out["fully_bound"])

    def test_require_bound_blocks_current_unimplemented_state(self):
        with self.assertRaisesRegex(ValueError,"binding incomplete"):
            mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,True)

    def test_current_wave_requires_six_non_pose_sweeps(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,False)
        self.assertEqual(set(out["current_wave_required_sweeps"]),{
          "shoulder_abduction_elevation","humeral_internal_external_rotation",
          "trunk_flexion","trunk_extension","trunk_lateral_bend","trunk_axial_rotation"
        })

    def test_sweep_sample_drift_is_rejected(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["samples"]=["wrong"]
        with self.assertRaisesRegex(ValueError,"samples differ"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_false_bound_claim_without_adapter_is_rejected(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["runner_binding_status"]="BOUND"
        with self.assertRaisesRegex(ValueError,"BOUND without blender_adapter_id"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_unbound_sweep_cannot_claim_adapter(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["blender_adapter_id"]="fake"
        with self.assertRaisesRegex(ValueError,"UNBOUND may not claim"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

if __name__=="__main__": unittest.main()

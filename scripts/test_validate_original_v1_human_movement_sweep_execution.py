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

    def test_live_preparation_state_is_fully_bound_but_not_run(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,False)
        self.assertEqual(out["sweeps_total"],11)
        self.assertEqual(out["bound"],11)
        self.assertTrue(out["fully_bound"])
        self.assertEqual(out["runner_calibration_state"],"PREPARED_UNCALIBRATED")
        self.assertEqual(out["candidate_sweeps_executed"],0)

    def test_require_bound_now_passes_without_implying_execution(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,True)
        self.assertTrue(out["fully_bound"])
        self.assertEqual(out["candidate_sweeps_executed"],0)

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

    def test_wrong_adapter_id_is_rejected(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["blender_adapter_id"]="fake"
        with self.assertRaisesRegex(ValueError,"canonical blender adapter id"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_unbound_sweep_cannot_claim_adapter(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["runner_binding_status"]="UNBOUND"
        with self.assertRaisesRegex(ValueError,"UNBOUND may not claim"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_binding_does_not_equal_candidate_execution(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["candidate_execution_state"]="EVIDENCE_READY"
        out=mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)
        self.assertEqual(out["candidate_sweeps_executed"],1)

    def test_runner_cannot_claim_calibrated_state_before_blender_calibration(self):
        bad=copy.deepcopy(self.d); bad["runner_calibration_state"]="CALIBRATED"
        with self.assertRaisesRegex(ValueError,"PREPARED_UNCALIBRATED"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

if __name__=="__main__": unittest.main()

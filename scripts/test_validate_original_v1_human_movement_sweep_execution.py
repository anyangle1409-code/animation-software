"""Tests for generic human movement sweep execution readiness."""
import copy,importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("validate_original_v1_human_movement_sweep_execution.py")
S=importlib.util.spec_from_file_location("sweep_exec",P)
mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class HumanMovementSweepExecutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=mod.read(mod.STATUS); cls.plan=mod.read(mod.PLAN)
        cls.packages=mod.read(mod.PACKAGES); cls.posemap=mod.read(mod.POSEMAP); cls.graph=mod.read(mod.GRAPH)

    def test_live_state_is_bound_but_not_evidence_ready_or_executed(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph)
        self.assertEqual(out["sweeps_total"],11)
        self.assertEqual(out["bound"],11)
        self.assertTrue(out["fully_bound"])
        self.assertEqual(out["runner_calibration_state"],"PREPARED_UNCALIBRATED")
        self.assertEqual(out["runner_evidence_readiness"],"DIAGNOSTIC_ONLY_INCOMPLETE")
        self.assertFalse(out["runner_evidence_ready"])
        self.assertFalse(out["acceptance_capable"])
        self.assertEqual(out["candidate_sweeps_executed"],0)
        self.assertEqual(out["candidate_sweeps_evidence_ready"],0)
        self.assertFalse(out["current_wave_evidence_ready"])

    def test_require_bound_passes_without_implying_evidence_readiness(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,True)
        self.assertTrue(out["fully_bound"])
        self.assertFalse(out["runner_evidence_ready"])

    def test_require_runner_evidence_ready_blocks_current_state(self):
        with self.assertRaisesRegex(ValueError,"not evidence-ready"):
            mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,False,True,False)

    def test_require_current_wave_evidence_blocks_current_state(self):
        with self.assertRaisesRegex(ValueError,"current Stage 1 wave sweep evidence is incomplete"):
            mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph,False,False,True)

    def test_current_wave_requires_six_non_pose_sweeps(self):
        out=mod.validate(self.d,self.plan,self.packages,self.posemap,self.graph)
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

    def test_candidate_evidence_ready_count_must_match_rows(self):
        bad=copy.deepcopy(self.d); bad["sweeps"][0]["candidate_execution_state"]="EVIDENCE_READY"
        with self.assertRaisesRegex(ValueError,"candidate_evidence_ready_count differs"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_false_evidence_ready_runner_without_visual_contact_capabilities_is_rejected(self):
        bad=copy.deepcopy(self.d)
        bad["runner_evidence_readiness"]="EVIDENCE_READY"
        bad["runner_calibration_state"]="CALIBRATED"
        bad["acceptance_capable"]=True
        bad["acceptance_capability_blockers"]=[]
        with self.assertRaisesRegex(ValueError,"evidence-ready runner capability missing"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_diagnostic_runner_cannot_claim_acceptance_capability(self):
        bad=copy.deepcopy(self.d); bad["acceptance_capable"]=True
        with self.assertRaisesRegex(ValueError,"may not be acceptance_capable"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

    def test_diagnostic_runner_must_expose_blockers(self):
        bad=copy.deepcopy(self.d); bad["acceptance_capability_blockers"]=[]
        with self.assertRaisesRegex(ValueError,"must expose acceptance blockers"):
            mod.validate(bad,self.plan,self.packages,self.posemap,self.graph)

if __name__=="__main__": unittest.main()

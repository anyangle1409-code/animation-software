"""Tests for deterministic Stage 1 wave work packages."""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_stage1_wave_work_package.py")
S=importlib.util.spec_from_file_location("wave_work",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class Stage1WaveWorkPackageTests(unittest.TestCase):
    def test_current_wave_is_shoulder_cluster_and_dependency_blocked(self):
        out=mod.build("current")
        self.assertEqual(out["wave"]["id"],"shoulder_yoke_foundation")
        self.assertEqual(set(out["repair_package_ids"]),{"RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004","RP-NECK-TRAP-001"})
        self.assertFalse(out["dependencies_clear"])
        self.assertFalse(out["editing_allowed"])
        kinds={x["type"] for x in out["blocking_preconditions"]}
        self.assertIn("DEPENDENCY_WAVES_NOT_CLEAR",kinds)
        self.assertIn("GENERIC_SWEEP_RUNNER_REQUIRED_FOR_FULL_MOVEMENT_PROOF",kinds)

    def test_shoulder_closure_scope_does_not_claim_global_all_body_qa_defect(self):
        out=mod.build("shoulder_yoke_foundation")
        self.assertNotIn("WB-QA-012",out["scope"]["closure_eligible_defect_ids"])
        self.assertIn("WB-QA-012",out["scope"]["regression_linked_defect_ids"])

    def test_trunk_wave_is_sweep_driven_and_waits_for_global_foundation(self):
        out=mod.build("trunk_foundation")
        self.assertEqual(out["repair_package_ids"],["RP-TRUNK-008"])
        self.assertEqual(out["validation"]["pose_names"],["neutral"])
        self.assertTrue({"trunk_flexion","trunk_extension","trunk_lateral_bend","trunk_axial_rotation","loaded_hip_hinge"}.issubset(set(out["validation"]["sweep_only_movements_requiring_generic_runner"])))
        self.assertFalse(out["editing_allowed"])

    def test_global_foundation_is_diagnostic_only(self):
        out=mod.build("global_foundation")
        self.assertEqual(out["repair_package_ids"],[])
        self.assertFalse(out["editing_allowed"])
        self.assertTrue(out["diagnostic_capture_allowed"])

    def test_whole_body_integration_is_never_an_edit_wave(self):
        out=mod.build("whole_body_integration")
        self.assertFalse(out["editing_allowed"])
        self.assertEqual(len(out["repair_package_ids"]),14)

    def test_unknown_wave_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown Stage 1 wave"):
            mod.build("not_a_wave")

if __name__=="__main__": unittest.main()

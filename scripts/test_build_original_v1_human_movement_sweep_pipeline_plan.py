"""Tests for package-aware human movement sweep pipeline planning."""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_human_movement_sweep_pipeline_plan.py")
S=importlib.util.spec_from_file_location("sweep_pipeline_plan",P)
mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class SweepPipelinePlanTests(unittest.TestCase):
    def test_shoulder_yoke_requires_expected_sweep_set(self):
        out=mod.build(["RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004","RP-NECK-TRAP-001"])
        req=set(out["required_sweep_only_movements"])
        self.assertIn("shoulder_abduction_elevation",req)
        self.assertIn("humeral_internal_external_rotation",req)
        self.assertIn("trunk_flexion",req)
        self.assertIn("trunk_extension",req)
        self.assertIn("trunk_lateral_bend",req)
        self.assertIn("trunk_axial_rotation",req)
        self.assertEqual(out["contact_bearing_required_sweeps"],[])
        self.assertTrue(out["all_11_raw_calibration_run_required"])

    def test_trunk_package_has_no_contact_sweeps(self):
        out=mod.build(["RP-TRUNK-008"])
        self.assertTrue({"trunk_flexion","trunk_extension","trunk_lateral_bend","trunk_axial_rotation","loaded_hip_hinge"}.issubset(set(out["required_sweep_only_movements"])))
        self.assertEqual(out["contact_bearing_required_sweeps"],["loaded_hip_hinge"])

    def test_calf_foot_includes_plantarflexion_contact(self):
        out=mod.build(["RP-CALF-013","RP-FOOT-014"])
        self.assertIn("ankle_plantarflexion",out["required_sweep_only_movements"])
        self.assertIn("ankle_plantarflexion",out["contact_bearing_required_sweeps"])

    def test_upper_limb_includes_forearm_and_grip_release(self):
        out=mod.build(["RP-ARM-005","RP-WRIST-HAND-006","RP-FINGER-007"])
        self.assertIn("forearm_pronation_supination",out["required_sweep_only_movements"])
        self.assertIn("grip_release",out["required_sweep_only_movements"])
        self.assertIn("grip_release",out["contact_bearing_required_sweeps"])

    def test_unknown_package_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown repair packages"):
            mod.build(["RP-NOT-REAL-999"])

if __name__=="__main__": unittest.main()

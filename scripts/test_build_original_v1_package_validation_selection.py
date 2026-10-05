"""Tests for package -> validation pose/sweep selection."""
import importlib.util
from pathlib import Path
import unittest

P=Path(__file__).with_name("build_original_v1_package_validation_selection.py")
S=importlib.util.spec_from_file_location("package_validation",P); mod=importlib.util.module_from_spec(S); S.loader.exec_module(mod)

class PackageValidationSelectionTests(unittest.TestCase):
    def test_all_14_packages_have_validation_definitions_for_every_proof_movement(self):
        packages=mod.read(mod.PACKAGES)["packages"]
        ids=[x["id"] for x in packages]
        out=mod.build(ids)
        self.assertTrue(out["validation_definition_complete"])
        self.assertEqual(out["uncovered_proof_movements"],[])
        self.assertEqual(len(out["proof_movement_families"]),25)

    def test_shoulder_cluster_selects_pose_fixtures_and_new_sweeps(self):
        out=mod.build(["RP-PEC-AX-002","RP-POSTAX-003","RP-DELTOID-004","RP-NECK-TRAP-001"])
        self.assertIn("neutral",out["pose_names"])
        self.assertIn("press_top",out["pose_names"])
        self.assertIn("pullup_hang",out["pose_names"])
        self.assertIn("shoulder_abduction_elevation",out["sweep_only_movements_requiring_generic_runner"])
        self.assertIn("humeral_internal_external_rotation",out["sweep_only_movements_requiring_generic_runner"])
        self.assertFalse(out["fully_runnable_via_frozen_pose_harness"])

    def test_trunk_package_does_not_invent_unrelated_pose_coverage(self):
        out=mod.build(["RP-TRUNK-008"])
        self.assertEqual(out["pose_names"],["neutral"])
        self.assertTrue({"trunk_flexion","trunk_extension","trunk_lateral_bend","trunk_axial_rotation","loaded_hip_hinge"}.issubset(set(out["sweep_only_movements_requiring_generic_runner"])))

    def test_forearm_rotation_remains_explicit_sweep_requirement(self):
        out=mod.build(["RP-ARM-005"])
        self.assertIn("curl_peak",out["pose_names"])
        self.assertIn("forearm_pronation_supination",out["sweep_only_movements_requiring_generic_runner"])

    def test_unknown_package_is_rejected(self):
        with self.assertRaisesRegex(ValueError,"unknown repair packages"):
            mod.build(["RP-NOT-REAL-999"])

if __name__=="__main__": unittest.main()

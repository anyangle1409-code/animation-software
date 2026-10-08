import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET = ROOT / "ORIGINAL_V1_WORK/anatomy/canonical_skeleton_proportion_targets_v1.json"
REPORT = ROOT / "ORIGINAL_V1_WORK/anatomy/audit/proportion_audit_001/proportion_report.json"


class SkeletonFirstProportionTargetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = json.loads(TARGET.read_text())
        cls.r = json.loads(REPORT.read_text())

    def test_owner_policy_is_explicit(self):
        d = self.t["owner_decision"]
        self.assertTrue(d["skeleton_is_source_of_truth"])
        self.assertTrue(d["mesh_refits_to_skeleton"])
        self.assertTrue(d["current_short_forearm_hand_is_not_final_styling"])
        self.assertTrue(d["current_long_feet_are_not_final_styling"])
        self.assertEqual(d["current_a003_role"], "audit baseline only")

    def test_joint_anchor_numbers_match_audit_evidence(self):
        j = self.r["joint_centres_vs_ansur_landmarks"]
        a = self.t["provisional_joint_centre_anchors"]
        self.assertAlmostEqual(a["HJC"]["current_fit_z_m"], j["HJC"]["fitted_z_m"])
        self.assertAlmostEqual(a["HJC"]["independent_reference_z_m"], j["HJC"]["implied_hjc_z_m"])
        self.assertAlmostEqual(a["KJC"]["current_fit_z_m"], j["KJC"]["fitted_z_m"])
        self.assertAlmostEqual(a["KJC"]["independent_reference_z_m"], j["KJC"]["ansur_lateral_femoral_epicondyle_pred_m"])
        self.assertAlmostEqual(a["GH"]["current_fit_depth_below_acromion_skin_m"], j["GH"]["depth_below_acromion_skin_m"])
        self.assertAlmostEqual(a["EJC_upper_arm_chain"]["current_acromion_to_EJC_m"], j["upper_arm_surface_check"]["character_acromion_skin_to_EJC_m"])

    def test_reopened_distal_arm_and_foot_match_surface_audit(self):
        s = self.r["surface_vs_ansur"]
        d = self.t["reopen_for_canonical_skeleton"]
        arm = d["distal_upper_limb"]
        self.assertAlmostEqual(arm["current_acromion_to_wrist_m"], s["acromion_to_wrist (acromial - wrist height)"]["character_m"])
        self.assertAlmostEqual(arm["stature_conditioned_surface_reference_m"], s["acromion_to_wrist (acromial - wrist height)"]["ansur_predicted_at_stature_m"])
        self.assertAlmostEqual(arm["current_hand_surface_length_m"], s["hand_length"]["character_m"])
        self.assertAlmostEqual(arm["stature_conditioned_hand_reference_m"], s["hand_length"]["ansur_predicted_at_stature_m"])
        self.assertAlmostEqual(arm["current_acromion_to_fingertip_m"], s["acromion_to_dactylion (ARL+RSL+hand)"]["character_m"])
        self.assertAlmostEqual(arm["stature_conditioned_arm_reference_m"], s["acromion_to_dactylion (ARL+RSL+hand)"]["ansur_predicted_at_stature_m"])
        foot = d["foot"]
        self.assertAlmostEqual(foot["current_surface_length_m"], s["foot_length"]["character_m"])
        self.assertAlmostEqual(foot["stature_conditioned_surface_reference_m"], s["foot_length"]["ansur_predicted_at_stature_m"])
        self.assertGreater(foot["current_z"], 2.0)

    def test_surface_diagnostics_are_not_promoted_to_bone_targets(self):
        for item in self.t["surface_only_diagnostics_not_skeletal_targets"].values():
            self.assertIn("note", item)
        self.assertEqual(self.t["status"], "PROVISIONAL_REFERENCE_NOT_FROZEN")


if __name__ == "__main__":
    unittest.main()
